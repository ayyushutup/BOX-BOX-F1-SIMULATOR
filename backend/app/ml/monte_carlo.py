"""
Monte Carlo Race Simulator v3 — Race Intelligence Engine

Converts per-driver ML probabilities into simulation-driven
win distributions by running N stochastic race outcome trials.

v3 CHANGES:
- Incident-driven Safety Car / VSC replacing flat probability
- Dynamic rivalry calculation from championship points gap
- DRS train cluster simulation
- Enhanced dirty air integration
- Championship pressure on mistake rates
"""

import math
import numpy as np
from typing import Dict, List, Optional
from collections import Counter, defaultdict


class MonteCarloRaceSimulator:
    def __init__(self, n_simulations: int = 5000, seed: Optional[int] = None):
        self.n_simulations = n_simulations
        self.rng = np.random.default_rng(seed)

    def simulate(
        self,
        win_probs: Dict[str, float],
        podium_probs: Optional[Dict[str, float]] = None,
        n_simulations: Optional[int] = None,
        chaos_level: float = 1.0,        # 1.0 = neutral, higher = more chaos
        incident_frequency: float = 1.0,  # multiplier for shock event probability
        rl_signals: Optional[Dict[str, Dict]] = None,  # Per-driver RL behavioral signals
        driver_form_drift: bool = False,  # P4: enable doubled form variance
        chaos_scaling: str = "linear",    # P4: linear, exponential, clustered
        championship_data: Optional[Dict[str, Dict]] = None,  # {driver: {position, points}}
        track_sc_probability: float = 0.2,  # Base SC probability for this track
    ) -> Dict:
        """
        Run Monte Carlo simulations with anti-determinism layers.

        Args:
            win_probs: {driver: probability_of_winning} from the ML model
            podium_probs: {driver: probability_of_podium}
            n_simulations: override default simulation count
            chaos_level: controls Gumbel noise scaling and shock frequency
            incident_frequency: multiplier for incident/DNF probability

        Returns:
            {
                "mc_win_distribution": {driver: fraction_of_sims_won},
                "predicted_order": [driver1, driver2, ...],
                "position_distributions": {driver: {1: frac, 2: frac, ...}},
                "volatility_bands": {driver: {optimistic: p10, pessimistic: p90}}
            }
        """
        n = n_simulations or self.n_simulations
        drivers = list(win_probs.keys())
        n_drivers = len(drivers)

        if n_drivers == 0:
            return {
                "mc_win_distribution": {},
                "predicted_order": [],
                "position_distributions": {},
                "volatility_bands": {}
            }

        # Build raw strength scores blending win + podium signals
        raw_strengths = np.array([win_probs.get(d, 0.0) for d in drivers], dtype=np.float64)

        if podium_probs:
            podium_arr = np.array([podium_probs.get(d, 0.0) for d in drivers], dtype=np.float64)
            raw_strengths = 0.6 * raw_strengths + 0.4 * podium_arr

        # Floor to prevent zeros
        raw_strengths = np.maximum(raw_strengths, 1e-4)

        # =========================================================
        # LAYER 1: Temperature Softmax — compress dominance
        # =========================================================
        # Temperature > 1.0 flattens the distribution (more uncertainty)
        # At T=2.0 (neutral), solid compression. At T=3.0+ (chaos), near-uniform.
        temperature = 2.0 + (chaos_level - 1.0) * 0.8  # chaos=1 → T=2.0, chaos=3 → T=3.6
        temperature = max(0.5, temperature)
        
        log_strengths = np.log(raw_strengths + 1e-10)
        tempered = log_strengths / temperature
        tempered -= tempered.max()  # numerical stability
        exp_tempered = np.exp(tempered)
        strengths = exp_tempered / exp_tempered.sum()  # softmax output
        
        # Internal probability cap: no driver > 45% after softmax
        MAX_STRENGTH_CAP = 0.45
        for idx in range(len(strengths)):
            if strengths[idx] > MAX_STRENGTH_CAP:
                excess = strengths[idx] - MAX_STRENGTH_CAP
                strengths[idx] = MAX_STRENGTH_CAP
                others_total = strengths.sum() - MAX_STRENGTH_CAP
                if others_total > 0:
                    for j in range(len(strengths)):
                        if j != idx:
                            strengths[j] += excess * (strengths[j] / others_total)
        strengths = strengths / strengths.sum()  # renormalize

        # =========================================================
        # LAYER 5: Exponential Chaos Scaling on Gumbel noise
        # =========================================================
        # At chaos=1: noise_scale = 0.5 (moderate upset potential)
        # At chaos=2: noise_scale = 1.35 (frequent upsets)
        # At chaos=3: noise_scale = 3.7 (anything can happen)
        base_noise_scale = 0.8
        if chaos_scaling == "exponential":
            noise_scale = base_noise_scale * np.exp((chaos_level - 1.0) * 1.5)  # steeper
        elif chaos_scaling == "clustered":
            # Clustered: bursts of high noise with calm stretches
            noise_scale = base_noise_scale * (1.0 + (chaos_level - 1.0) * 0.5)  # lower base but bursts below
        else:  # linear
            noise_scale = base_noise_scale * np.exp((chaos_level - 1.0) * 1.0)

        # Per-driver incident and mistake probabilities
        # LAYER 3 & 4 parameters
        base_incident_prob = 0.02 * incident_frequency  # 2% base DNF/incident per sim per driver
        
        # Build per-driver noise scales and mistake rates from RL signals
        if rl_signals is None:
            rl_signals = {}
        
        # Per-driver Gumbel noise scaling: erratic drivers (high time_variance) get more noise
        driver_noise_scales = np.array([
            noise_scale * (1.0 + rl_signals.get(d, {}).get('time_variance', 0.0) * 2.0)
            for d in drivers
        ])
        
        # Per-driver mistake probabilities from RL behavioral model
        driver_mistake_probs = np.array([
            rl_signals.get(d, {}).get('mistake_probability', 0.015)
            for d in drivers
        ])

        # Track results
        win_counts = Counter()
        position_counts = defaultdict(lambda: Counter())

        for _ in range(n):
            # =========================================================
            # LAYER 2: Performance Drift — weekend form variance
            # =========================================================
            # Each sim represents a "possible weekend" where drivers have form variance
            form_sigma = 0.24 if driver_form_drift else 0.12  # P4: doubled when drift enabled
            form_drift_arr = self.rng.normal(0, form_sigma, size=n_drivers)
            
            # Team execution variance
            team_drift = self.rng.normal(0, 0.06, size=n_drivers)
            
            # Clustered chaos: occasionally spike noise for this sim
            chaos_burst = 1.0
            if chaos_scaling == "clustered" and self.rng.random() < 0.20:
                chaos_burst = 2.5  # 20% of sims get a chaos burst
            
            # Apply drift to strengths for this sim
            sim_strengths = strengths * np.exp(form_drift_arr + team_drift)
            sim_strengths = np.maximum(sim_strengths, 1e-6)

            # =========================================================
            # LAYER 2.5: Fatigue Drift — concentration loss over race
            # =========================================================
            # Simulates accumulated fatigue: some drivers lose more concentration
            fatigue_vulnerability = self.rng.uniform(0.85, 1.0, size=n_drivers)
            sim_strengths *= fatigue_vulnerability

            # =========================================================
            # LAYER 2.6: Nonlinear Tire Cliff
            # =========================================================
            # 5% chance per driver of hitting a sudden tire cliff
            for j in range(n_drivers):
                if self.rng.random() < 0.05:
                    cliff_severity = self.rng.uniform(0.15, 0.40)
                    sim_strengths[j] *= cliff_severity

            # =========================================================
            # LAYER 3: Shock Events — heavy-tail incidents
            # =========================================================
            for j in range(n_drivers):
                if self.rng.random() < base_incident_prob:
                    # Incident! Apply heavy-tail penalty (exponential distribution)
                    # This can range from minor (0.3x strength) to catastrophic DNF (0.01x)
                    shock_severity = self.rng.exponential(0.5)
                    penalty = max(0.01, 1.0 - shock_severity)
                    sim_strengths[j] *= penalty

            # =========================================================
            # LAYER 4: Driver Mistake Model — rare catastrophic errors
            # =========================================================
            for j in range(n_drivers):
                # RL-informed mistake probability per driver, scaled by relative strength and chaos
                relative_strength = raw_strengths[j] / raw_strengths.max()
                mistake_prob = driver_mistake_probs[j] * (2.0 - relative_strength) * chaos_level
                
                if self.rng.random() < min(0.08, mistake_prob):
                    # Catastrophic mistake: spin, crash, or major error
                    sim_strengths[j] *= self.rng.uniform(0.01, 0.15)

            # =========================================================
            # LAYER 5.5: Strategy Execution Risk
            # =========================================================
            # Pit stop delay: 3% chance of slow pit per driver
            for j in range(n_drivers):
                if self.rng.random() < 0.03:
                    pit_penalty = self.rng.uniform(0.60, 0.85)
                    sim_strengths[j] *= pit_penalty
            
            # Cold tire penalty: 8% chance per driver of cold-tire struggle
            for j in range(n_drivers):
                if self.rng.random() < 0.08:
                    cold_tire_penalty = self.rng.uniform(0.75, 0.90)
                    sim_strengths[j] *= cold_tire_penalty

            # =========================================================
            # LAYER 5.6: Incident-Driven Safety Car / VSC (v3)
            # =========================================================
            # Instead of flat 8%, SC probability is derived from:
            # 1. Track chaos level
            # 2. Whether any drivers had incidents in this sim
            sc_triggered = False
            vsc_triggered = False
            incident_count = sum(1 for j in range(n_drivers) 
                                if sim_strengths[j] / max(strengths[j], 1e-6) < 0.3)  # severe incidents
            
            # Base probability + incident-driven boost
            sc_prob = track_sc_probability * chaos_level * 0.15  # ~3% base at neutral
            if incident_count > 0:
                sc_prob += 0.40 * incident_count  # 40% per incident
            
            if self.rng.random() < min(0.60, sc_prob):  # Cap at 60%
                if self.rng.random() < 0.30:
                    # VSC (30% of triggered) — lighter compression
                    vsc_triggered = True
                    mean_strength = sim_strengths.mean()
                    sim_strengths = sim_strengths * 0.60 + mean_strength * 0.40
                else:
                    # Full Safety Car — heavy compression
                    sc_triggered = True
                    mean_strength = sim_strengths.mean()
                    sim_strengths = sim_strengths * 0.30 + mean_strength * 0.70

            # =========================================================
            # LAYER 5.7: DRS Train Cluster Penalty (v3)
            # =========================================================
            # Simulate drivers stuck in traffic getting penalized
            # Sort by current sim strength, apply dirty air cascade
            strength_order = np.argsort(-sim_strengths)
            for rank in range(1, n_drivers):
                idx = strength_order[rank]
                leader_idx = strength_order[rank - 1]
                # If close in strength (within 15%), dirty air penalty
                ratio = sim_strengths[idx] / max(sim_strengths[leader_idx], 1e-6)
                if ratio > 0.85:
                    # In dirty air — 0.97x penalty
                    sim_strengths[idx] *= 0.97

            # =========================================================
            # LAYER 6: Driver Interaction — Dynamic Rivalry (v3)
            # =========================================================
            # Dynamic rivalry strength from championship points gap
            if championship_data:
                for j in range(n_drivers):
                    d_j = drivers[j]
                    d_j_data = championship_data.get(d_j, {})
                    d_j_pts = d_j_data.get('points', 0)
                    
                    boost_ratio = sim_strengths[j] / max(strengths[j], 1e-6)
                    if boost_ratio > 1.15:  # >15% boost
                        for k in range(n_drivers):
                            if k == j:
                                continue
                            d_k = drivers[k]
                            d_k_data = championship_data.get(d_k, {})
                            d_k_pts = d_k_data.get('points', 0)
                            
                            # Dynamic rivalry: closer points = stronger response
                            pts_gap = abs(d_j_pts - d_k_pts)
                            rivalry_strength = math.exp(-pts_gap / 20.0) if pts_gap > 0 else 0.8
                            
                            if rivalry_strength > 0.3 and self.rng.random() < rivalry_strength:
                                response_boost = 1.0 + (boost_ratio - 1.0) * self.rng.uniform(0.3, 0.6)
                                sim_strengths[k] *= response_boost
            else:
                # Fallback: hardcoded rivalry pairs (legacy behavior)
                RIVALRY_PAIRS = {
                    ('VER', 'NOR'), ('NOR', 'VER'),
                    ('HAM', 'LEC'), ('LEC', 'HAM'),
                    ('SAI', 'NOR'), ('NOR', 'SAI'),
                    ('RUS', 'HAM'), ('HAM', 'RUS'),
                    ('ALO', 'VER'), ('VER', 'ALO'),
                    ('PIA', 'NOR'), ('NOR', 'PIA'),
                }
                for j in range(n_drivers):
                    d_j = drivers[j]
                    boost_ratio = sim_strengths[j] / max(strengths[j], 1e-6)
                    if boost_ratio > 1.15:
                        for k in range(n_drivers):
                            if k == j:
                                continue
                            d_k = drivers[k]
                            if (d_j, d_k) in RIVALRY_PAIRS:
                                if self.rng.random() < 0.60:
                                    response_boost = 1.0 + (boost_ratio - 1.0) * self.rng.uniform(0.3, 0.6)
                                    sim_strengths[k] *= response_boost

            # Now sample finishing order using the modified strengths
            # Apply chaos_burst to noise scales for clustered mode
            sim_noise_scales = driver_noise_scales * chaos_burst
            remaining = list(range(n_drivers))
            order = []

            for pos in range(n_drivers):
                rem_strengths = sim_strengths[remaining]
                total = rem_strengths.sum()
                if total <= 0:
                    probs = np.ones(len(remaining)) / len(remaining)
                else:
                    probs = rem_strengths / total

                # Gumbel trick with per-driver RL-informed noise scaling
                remaining_arr = np.array(remaining)
                per_driver_noise = sim_noise_scales[remaining_arr]
                noise = self.rng.gumbel(size=len(remaining)) * per_driver_noise
                noisy_scores = np.log(probs + 1e-10) + noise

                chosen_idx = np.argmax(noisy_scores)
                chosen_driver_idx = remaining[chosen_idx]
                order.append(chosen_driver_idx)
                remaining.pop(chosen_idx)

            # Record results
            winner = drivers[order[0]]
            win_counts[winner] += 1

            for pos, driver_idx in enumerate(order):
                position_counts[drivers[driver_idx]][pos + 1] += 1

        # Compute distributions
        mc_win_dist = {d: win_counts[d] / n for d in drivers}

        # Predicted order: sort by average position
        avg_positions = {}
        for d in drivers:
            if position_counts[d]:
                total_pos = sum(pos * count for pos, count in position_counts[d].items())
                total_count = sum(position_counts[d].values())
                avg_positions[d] = total_pos / total_count
            else:
                avg_positions[d] = n_drivers

        predicted_order = sorted(drivers, key=lambda d: avg_positions[d])

        # Position distributions + Volatility bands for ALL drivers (full P1-P20)
        pos_dists = {}
        volatility_bands = {}
        for d in drivers:  # All drivers, not just top 5
            pos_dists[d] = {
                pos: round(count / n, 3)
                for pos, count in sorted(position_counts[d].items())
                # No position cap — show full P1-P20 range
            }

            positions = []
            for pos, count in position_counts[d].items():
                positions.extend([pos] * count)
            if positions:
                p10 = int(np.percentile(positions, 10))
                p90 = int(np.percentile(positions, 90))
            else:
                p10, p90 = n_drivers, n_drivers

            volatility_bands[d] = {
                "optimistic": p10,
                "pessimistic": p90
            }

        # Build interaction matrix for top drivers
        RIVALRY_MAP = {
            'VER': ['NOR', 'ALO'],
            'NOR': ['VER', 'SAI', 'PIA'],
            'HAM': ['LEC', 'RUS'],
            'LEC': ['HAM', 'SAI'],
            'SAI': ['NOR', 'LEC'],
            'RUS': ['HAM'],
            'ALO': ['VER'],
            'PIA': ['NOR'],
        }
        interaction_matrix = {}
        for d in predicted_order[:10]:
            rivals_in_field = [r for r in RIVALRY_MAP.get(d, []) if r in drivers]
            if rivals_in_field:
                interaction_matrix[d] = {
                    "rivals": rivals_in_field,
                    "response_probability": 0.60,
                    "effect": "counter-boost"
                }

        return {
            "mc_win_distribution": mc_win_dist,
            "predicted_order": predicted_order,
            "position_distributions": pos_dists,
            "volatility_bands": volatility_bands,
            "interaction_matrix": interaction_matrix
        }
