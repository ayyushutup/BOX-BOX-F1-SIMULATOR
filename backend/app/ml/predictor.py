
import joblib
import numpy as np
import pandas as pd
import os
from typing import Dict, List, Optional
from app.models.race_state import RaceState, RaceControl
from app.ml.monte_carlo import MonteCarloRaceSimulator
from app.ml.rl_predictor import RLDriverPredictor
from app.simulation.physics import (
    calculate_dirty_air_factor, calculate_dirty_air_mistake_effect,
    calculate_track_grip, update_rubber_level,
    calculate_momentum_effect,
)

# Configuration
MODEL_DIR = "app/ml/models"

class RacePredictor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RacePredictor, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if not self.initialized:
            self.win_model = None
            self.podium_model = None
            self.mc_simulator = MonteCarloRaceSimulator(n_simulations=1000)
            self.rl_predictor = RLDriverPredictor()
            self.load_models()
            self.initialized = True
            
            # HARDCODED ENCODERS (2025 Season)
            # Essential because we didn't save the encoders during training.
            # NOTE: Model was trained on 2024 codes — slight misalignment until retrained.
            # The Bayesian modifier layers compensate for this.
            self.driver_map = {d: i for i, d in enumerate(sorted([
                "VER", "HAM", "LEC", "NOR", "RUS", "SAI", "ALO", "PIA",
                "GAS", "ALB", "HUL", "OCO", "TSU", "LAW", "STR",
                "ANT", "BEA", "DOO", "HAD", "BOR"
            ]))}
            
            self.team_map = {t: i for i, t in enumerate(sorted([
                "Red Bull Racing", "Mercedes", "Ferrari", "McLaren", "Aston Martin", 
                "Alpine", "Williams", "Racing Bulls", "Haas", "Sauber"
            ]))}
            
            self.tire_map = {t: i for i, t in enumerate(sorted([
                "SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"
            ]))}

    def load_models(self):
        """Load trained models from disk (LightGBM + Calibration wrapped in joblib)"""
        try:
            cur_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(cur_dir, "models") 
            
            if not os.path.exists(model_path):
                model_path = "app/ml/models"

            print(f"Loading models from {model_path}...")
            self.win_model = joblib.load(os.path.join(model_path, "win_model.joblib"))
            self.podium_model = joblib.load(os.path.join(model_path, "podium_model.joblib"))
            print("ML Models loaded successfully (LightGBM + Calibration).")
        except Exception as e:
            print(f"Failed to load ML models: {e}")
            print("Predictions will be unavailable.")

    def predict(self, state: RaceState, scenario_config=None) -> Dict:
        """
        Bayesian Prediction Pipeline:
        
        Prior (LightGBM) → Likelihood (Log-odds modifiers + RL) → Posterior (MC sampling)
        
        All scenario modifiers operate in log-odds (logit) space for clean
        mathematical composition. Probabilities are recovered via sigmoid.
        """
        if not self.win_model or not self.podium_model:
            return None

        data = []
        total_laps = state.meta.laps_total
        
        for car in state.cars:
            gap_leader = car.timing.gap_to_leader if car.timing.gap_to_leader is not None else 0.0
            gap_ahead = car.timing.interval if car.timing.interval is not None else 0.0
            
            driver_code = self.driver_map.get(car.identity.driver, -1)
            team_code = self.team_map.get(car.identity.team, -1)
            tire_code = self.tire_map.get(car.telemetry.tire_state.compound.value, -1)
            
            row = {
                "lap": car.timing.lap,
                "lap_progress": car.telemetry.lap_progress,
                "laps_remaining": total_laps - car.timing.lap,
                "position": car.timing.position,
                "speed": car.telemetry.speed,
                "gap_to_leader": gap_leader,
                "gap_to_car_ahead": gap_ahead,
                "tire_age": car.telemetry.tire_state.age,
                "tire_wear": car.telemetry.tire_state.wear,
                "pit_stops": car.pit_stops,
                "sc_active": 1 if state.race_control == RaceControl.SAFETY_CAR else 0,
                "vsc_active": 1 if state.race_control == RaceControl.VSC else 0,
                "drs_enabled": 1 if state.drs_enabled else 0,
                "tire_compound_code": tire_code, 
                "team_code": team_code,
                "driver_code": driver_code
            }
            data.append(row)

        df = pd.DataFrame(data)
        
        # Column order MUST match training
        feature_cols = [
            "lap", "lap_progress", "laps_remaining", "position",
            "speed", "gap_to_leader", "gap_to_car_ahead",
            "tire_age", "tire_wear", "pit_stops",
            "sc_active", "vsc_active", "drs_enabled",
            "tire_compound_code", "team_code", "driver_code"
        ]
        
        X = df[feature_cols]

        # =================================================================
        # STAGE 1: PRIOR — LightGBM Calibrated Probabilities
        # =================================================================
        win_probs_raw = self.win_model.predict_proba(X)
        podium_probs_raw = self.podium_model.predict_proba(X)
        
        # Extract scenario-level parameters
        chaos_multiplier = 1.0
        sc_multiplier = 1.0
        tire_deg_multiplier = 1.0
        rain_probability = 0.0
        field_compression = 1.0
        reliability_variance = 1.0
        qualifying_delta = 0.0
        driver_form_drift = False
        chaos_scaling = "linear"
        
        if scenario_config:
            chaos_multiplier = getattr(scenario_config.chaos, 'incident_frequency', 1.0)
            sc_multiplier = getattr(scenario_config.chaos, 'safety_car_probability', 1.0)
            tire_deg_multiplier = getattr(scenario_config.engineering, 'tire_deg_multiplier', 1.0)
            field_compression = getattr(scenario_config.chaos, 'field_compression', 1.0)
            reliability_variance = getattr(scenario_config.chaos, 'reliability_variance', 1.0)
            qualifying_delta = getattr(scenario_config.chaos, 'qualifying_delta_override', 0.0)
            driver_form_drift = getattr(scenario_config.chaos, 'driver_form_drift', False)
            chaos_scaling = getattr(scenario_config.chaos, 'chaos_scaling', 'linear')
            if scenario_config.weather.timeline:
                rain_probability = scenario_config.weather.timeline[0].rain_probability
        
        # =================================================================
        # STAGE 2: LIKELIHOOD — Log-Odds Scenario Modifiers + RL
        # =================================================================
        # All modifiers are additive in logit space (equivalent to multiplicative
        # odds ratios). This prevents probability explosion and gives clean
        # Bayesian composition: logit(posterior) = logit(prior) + Σ log-likelihood terms
        
        win_prob_dict = {}
        podium_prob_dict = {}
        causal_factors = {}
        rl_signals_dict = {}  # Flows to Monte Carlo for per-driver noise
        
        for i, car in enumerate(state.cars):
            p_win = float(win_probs_raw[i][1]) if len(win_probs_raw[i]) > 1 else 0.0
            p_podium = float(podium_probs_raw[i][1]) if len(podium_probs_raw[i]) > 1 else 0.0
            
            raw_p_win = p_win  # Store for surprise index
            
            # Clamp prior to (0.001, 0.999) to keep logit finite
            p_win = np.clip(p_win, 0.001, 0.999)
            p_podium = np.clip(p_podium, 0.001, 0.999)
            
            # Convert to logit space: logit(p) = log(p / (1-p))
            logit_win = np.log(p_win / (1.0 - p_win))
            logit_podium = np.log(p_podium / (1.0 - p_podium))
            
            # --- Chaos term: pulls probabilities toward 50% (logit → 0) ---
            env_variance = max(0.0, (chaos_multiplier - 1.0) * 0.5 + (sc_multiplier - 1.0) * 0.3 + rain_probability * 0.4)
            chaos_term = -(env_variance * 0.8) * np.sign(logit_win) * min(1.0, abs(logit_win))
            
            # --- Tire degradation term ---
            tire_age = car.telemetry.tire_state.age
            tire_term = 0.0
            if tire_deg_multiplier > 1.0 and tire_age > 8:
                deg_penalty = max(0.3, 1.0 - ((tire_deg_multiplier - 1.0) * 0.15 * (tire_age / 15.0)))
                tire_term = np.log(deg_penalty)  # Negative: hurts probability
            elif tire_deg_multiplier < 1.0:
                deg_boost = 1.0 + (1.0 - tire_deg_multiplier) * 0.1
                tire_term = np.log(deg_boost)  # Positive: helps probability
            
            # --- Rain term ---
            rain_term = 0.0
            if rain_probability > 0.3:
                wet_skill = 0.5
                if scenario_config:
                    driver_cfg = scenario_config.drivers.get(car.identity.driver)
                    if driver_cfg:
                        wet_skill = getattr(driver_cfg, 'wet_weather_skill', 0.5)
                rain_modifier = 1.0 + (wet_skill - 0.5) * rain_probability * 0.6
                rain_term = np.log(max(0.3, rain_modifier))
                
            # --- Skill term (dampened) ---
            skill_bonus = max(0.5, car.driver_skill / 0.90)
            skill_term = 0.3 * np.log(skill_bonus)
            
            # --- RL term: Personality-driven behavioral signal ---
            personality = {'aggression': 0.5, 'consistency': 0.5, 'wet_skill': 0.5, 'tire_management': 0.5, 'risk_tolerance': 0.5}
            if scenario_config:
                driver_cfg = scenario_config.drivers.get(car.identity.driver)
                if driver_cfg:
                    personality = {
                        'aggression': getattr(driver_cfg, 'aggression', 0.5),
                        'consistency': 1.0 - getattr(driver_cfg, 'radio_emotionality', 0.5) * 0.5,
                        'wet_skill': getattr(driver_cfg, 'wet_weather_skill', 0.5),
                        'tire_management': getattr(driver_cfg, 'tire_preservation', 0.5),
                        'risk_tolerance': getattr(driver_cfg, 'risk_tolerance', 0.5),
                    }
            
            rl_signals = self.rl_predictor.simulate_lap_performance(
                track_length=state.track.length,
                driver_skill=car.driver_skill,
                personality=personality
            )
            rl_signals_dict[car.identity.driver] = rl_signals
            
            rl_bonus = 1.0 / rl_signals["time_modifier"]
            rl_term = np.log(max(0.5, rl_bonus))
            
            # --- Qualifying delta term: position-based bias ---
            quali_term = 0.0
            if qualifying_delta != 0.0:
                # Front-runners (low position) get boosted, back-markers get penalized
                # Scale by inverse position: P1 gets full effect, P20 gets 1/20th
                position_factor = max(0.05, 1.0 - (car.timing.position - 1) / 20.0)
                quali_term = qualifying_delta * position_factor * 0.5  # damped
            
            # --- Dirty air term: penalize drivers stuck following closely ---
            dirty_air_term = 0.0
            gap_ahead = car.timing.interval if car.timing.interval is not None else 99.0
            da_factor = calculate_dirty_air_factor(gap_ahead)
            if da_factor > 0.05:
                # Dirty air hurts your chances
                dirty_air_term = np.log(max(0.5, 1.0 - da_factor * 0.15))  # Up to -15% odds
            
            # --- Track grip term: evolving grip benefits race progress ---
            track_grip_term = 0.0
            if hasattr(state.track, 'track_evolution') and state.track.track_evolution:
                te = state.track.track_evolution
                # Simulate grip at current lap based on rubber buildup
                race_progress = car.timing.lap / max(1, state.meta.laps_total)
                sim_rubber = te.rubber_level + te.rubber_buildup_rate * car.timing.lap * (len(state.cars) / 20.0)
                sim_grip = calculate_track_grip(te.grip_level, sim_rubber)
                if sim_grip > 1.02:
                    track_grip_term = np.log(1.0 + (sim_grip - 1.0) * 0.05)  # Subtle boost
            
            # --- Momentum term: psychological state ---
            momentum_term = 0.0
            driver_momentum = getattr(car, 'momentum', 0.0)
            if abs(driver_momentum) > 0.1:
                mom_effects = calculate_momentum_effect(driver_momentum)
                # Positive momentum boosts, negative penalizes
                momentum_term = np.log(max(0.5, 1.0 + mom_effects['aggression_mod'] * 0.5 - mom_effects['mistake_mod'] * 0.3))
            
            # --- Championship pressure term ---
            championship_term = 0.0
            if scenario_config:
                driver_cfg = scenario_config.drivers.get(car.identity.driver)
                if driver_cfg:
                    champ_pos = getattr(driver_cfg, 'championship_position', 0)
                    champ_pts = getattr(driver_cfg, 'championship_points', 0)
                    if champ_pos > 0:
                        pressure_handling = getattr(driver_cfg, 'pressure_handling', 1.0)
                        if champ_pos <= 3:  # Title contender
                            # Leaders are conservative (slightly penalized for risk aversion)
                            # Chasers are aggressive (boosted but mistake-prone)
                            if champ_pos == 1:
                                championship_term = -0.05 * (2.0 - pressure_handling)  # Conservative penalty
                            else:
                                championship_term = 0.08 * pressure_handling  # Aggressive boost
            
            # =================================================================
            # COMPOSE: logit(posterior) = logit(prior) + Σ likelihood terms
            # =================================================================
            logit_win += (chaos_term + tire_term + rain_term + skill_term + rl_term 
                         + quali_term + dirty_air_term + track_grip_term + momentum_term + championship_term)
            logit_podium += (chaos_term * 0.7 + tire_term + rain_term + skill_term * 0.6 + rl_term * 0.8 
                           + quali_term * 0.7 + dirty_air_term * 0.8 + track_grip_term * 0.8 
                           + momentum_term * 0.7 + championship_term * 0.6)
            
            # Convert back to probability via sigmoid
            p_win = 1.0 / (1.0 + np.exp(-logit_win))
            p_podium = 1.0 / (1.0 + np.exp(-logit_podium))
            
            # Build causal factors explanation
            factors = []
            if raw_p_win > 0.10:
                factors.append("Strong Historical Baseline")
                
            if rl_bonus > 1.02:
                factors.append(f"AI Trait Advantage (+{round((rl_bonus-1.0)*100)}%)")
            elif rl_bonus < 0.98:
                factors.append(f"AI Trait Penalty ({round((rl_bonus-1.0)*100)}%)")
            
            if rl_signals["mistake_probability"] > 0.04:
                factors.append(f"High Mistake Risk ({rl_signals['mistake_probability']*100:.0f}%)")
                
            if skill_bonus > 1.05:
                factors.append("High Driver Skill Bonus")
                
            if tire_age < 5:
                factors.append("Fresh Tires Advantage")
            elif tire_age > 18:
                factors.append("High Tire Deg Warning")
            
            if tire_deg_multiplier > 1.3:
                factors.append(f"High Deg Scenario ({tire_deg_multiplier}x)")
                
            if rain_probability > 0.3:
                factors.append(f"Rain Impact ({int(rain_probability*100)}%)")
                
            if env_variance > 0.3:
                factors.append(f"Chaos Flattening ({int(env_variance*100)}%)")
                
            if qualifying_delta != 0.0:
                factors.append(f"Quali Delta Override ({qualifying_delta:+.1f}s)")
                
            if driver_form_drift:
                factors.append("Form Drift Active")
            
            # New v2 factors
            if da_factor > 0.2:
                factors.append(f"Dirty Air Penalty ({int(da_factor * 100)}%)")
            if da_factor > 0.5 and gap_ahead < 1.0:
                factors.append("Stuck in DRS Train")
            
            if track_grip_term > 0.001:
                factors.append("Track Grip Improving")
            
            if driver_momentum > 0.3:
                factors.append(f"Positive Momentum (+{driver_momentum:.1f})")
            elif driver_momentum < -0.3:
                factors.append(f"Tilting ({driver_momentum:.1f})")
            
            if championship_term > 0:
                factors.append("Championship Chaser Aggression")
            elif championship_term < 0:
                factors.append("Championship Leader Caution")
                
            factors.append(f"Track Pos: P{car.timing.position}")
            causal_factors[car.identity.driver] = factors
            
            win_prob_dict[car.identity.driver] = p_win
            podium_prob_dict[car.identity.driver] = p_podium

        # =================================================================
        # STAGE 3: POSTERIOR PREPARATION — Temperature Softmax + Dirichlet
        # =================================================================
        # Replace sqrt+floor with mathematically clean compression:
        # 1. Temperature softmax controls dominance spread
        # 2. Dirichlet blend with uniform removes need for hard floors
        # 3. Hard probability cap prevents unrealistic dominance
        
        n_drivers = len(win_prob_dict)
        chaos_level = max(chaos_multiplier, sc_multiplier)
        
        # Temperature: chaos=1 → T=1.5 (meaningful baseline compression), chaos=3 → T=2.5
        chaos_temperature = 1.5 + (chaos_level - 1.0) * 0.5
        chaos_temperature = max(0.5, chaos_temperature)
        
        # Win probabilities through temperature softmax
        win_values = np.array([win_prob_dict[d] for d in win_prob_dict])
        logits_win = np.log(win_values + 1e-10)
        tempered_win = logits_win / chaos_temperature
        tempered_win -= tempered_win.max()  # numerical stability
        exp_win = np.exp(tempered_win)
        softmax_win = exp_win / exp_win.sum()
        
        # Dirichlet smoothing: blend with uniform — minimum 5% blend even at neutral chaos
        chaos_blend = min(0.5, 0.05 + (chaos_level - 1.0) * 0.25)
        chaos_blend = max(0.05, chaos_blend)
        uniform = np.ones(n_drivers) / n_drivers
        final_win = (1.0 - chaos_blend) * softmax_win + chaos_blend * uniform
        
        # === PROBABILITY CAP COMPRESSION ===
        # No single driver can exceed 55% pre-MC win probability.
        # Excess is redistributed proportionally across the rest of the field.
        MAX_WIN_CAP = 0.55
        for cap_pass in range(3):  # Multiple passes to handle edge cases
            for idx in range(n_drivers):
                if final_win[idx] > MAX_WIN_CAP:
                    excess = final_win[idx] - MAX_WIN_CAP
                    final_win[idx] = MAX_WIN_CAP
                    # Redistribute excess proportionally to other drivers
                    others_total = final_win.sum() - MAX_WIN_CAP
                    if others_total > 0:
                        for j in range(n_drivers):
                            if j != idx:
                                final_win[j] += excess * (final_win[j] / others_total)
        
        # Renormalize to ensure sum = 1.0
        final_win = final_win / final_win.sum()
        
        # === FIELD COMPRESSION ===
        # field_compression > 1.0 compresses the field (i.e. makes it more equal)
        # field_compression < 1.0 amplifies differences (more dominant leader)
        if field_compression != 1.0:
            mean_win = final_win.mean()
            # Interpolate toward mean: at fc=2.0, 50% compression toward mean
            fc_alpha = min(0.5, (field_compression - 1.0) * 0.5) if field_compression > 1.0 else \
                       max(-0.3, (field_compression - 1.0) * 0.3)
            final_win = final_win * (1.0 - fc_alpha) + mean_win * fc_alpha
            final_win = np.maximum(final_win, 1e-6)
            final_win = final_win / final_win.sum()
        
        for i, d in enumerate(win_prob_dict):
            win_prob_dict[d] = float(final_win[i])
        
        # Podium probabilities — same treatment
        pod_values = np.array([podium_prob_dict[d] for d in podium_prob_dict])
        logits_pod = np.log(pod_values + 1e-10)
        tempered_pod = logits_pod / chaos_temperature
        tempered_pod -= tempered_pod.max()
        exp_pod = np.exp(tempered_pod)
        softmax_pod = exp_pod / exp_pod.sum()
        final_pod = (1.0 - chaos_blend) * softmax_pod + chaos_blend * uniform
        final_pod = final_pod * 3.0  # Scale to ~3 podium spots
        
        for i, d in enumerate(podium_prob_dict):
            podium_prob_dict[d] = float(final_pod[i])

        # =================================================================
        # STAGE 4: POSTERIOR — Monte Carlo with RL-informed noise
        # =================================================================
        # Build championship data for dynamic rivalries
        championship_data = None
        if scenario_config:
            championship_data = {}
            for d_code, d_cfg in scenario_config.drivers.items():
                champ_pos = getattr(d_cfg, 'championship_position', 0)
                champ_pts = getattr(d_cfg, 'championship_points', 0)
                if champ_pos > 0 or champ_pts > 0:
                    championship_data[d_code] = {'position': champ_pos, 'points': champ_pts}
            if not championship_data:
                championship_data = None
        
        # Track SC probability
        track_sc_prob = state.track.sc_probability / 100.0 if state.track.sc_probability else 0.2
        
        mc_results = self.mc_simulator.simulate(
            win_probs=win_prob_dict,
            podium_probs=podium_prob_dict,
            chaos_level=chaos_level,
            incident_frequency=chaos_multiplier,
            rl_signals=rl_signals_dict,
            driver_form_drift=driver_form_drift,
            chaos_scaling=chaos_scaling,
            championship_data=championship_data,
            track_sc_probability=track_sc_prob,
        )

        # Assemble full prediction response
        results = {
            "lap": state.cars[0].timing.lap,
            "win_prob": win_prob_dict,
            "podium_prob": podium_prob_dict,
            "confidence": min(1.0, state.meta.tick / (total_laps * 300)),
            # Monte Carlo fields
            "mc_win_distribution": mc_results["mc_win_distribution"],
            "predicted_order": mc_results["predicted_order"],
            "position_distributions": mc_results["position_distributions"],
            "volatility_bands": mc_results.get("volatility_bands", {}),
            "causal_factors": causal_factors
        }
            
        return results