"""
AI Race Commentary Engine — Template-Based

Generates rich, F1-style race commentary from prediction data.
Uses randomized templates, data-driven narratives, and contextual
F1 terminology to produce analysis that feels alive.
No external LLM required.
"""

import random
from typing import Dict, List, Optional


class RaceCommentator:
    """Generates contextual F1 commentary from prediction data."""

    DRIVER_NAMES = {
        'VER': 'Max Verstappen', 'HAM': 'Lewis Hamilton', 'LEC': 'Charles Leclerc',
        'NOR': 'Lando Norris', 'SAI': 'Carlos Sainz', 'RUS': 'George Russell',
        'ALO': 'Fernando Alonso', 'PIA': 'Oscar Piastri',
        'GAS': 'Pierre Gasly', 'OCO': 'Esteban Ocon', 'STR': 'Lance Stroll',
        'HUL': 'Nico Hülkenberg', 'TSU': 'Yuki Tsunoda', 'ALB': 'Alexander Albon',
        'LAW': 'Liam Lawson', 'ANT': 'Kimi Antonelli', 'BEA': 'Oliver Bearman',
        'DOO': 'Jack Doohan', 'HAD': 'Isack Hadjar', 'BOR': 'Gabriel Bortoleto'
    }

    TEAM_NAMES = {
        'Red Bull Racing': 'Red Bull', 'Mercedes': 'Mercedes', 'Ferrari': 'Ferrari',
        'McLaren': 'McLaren', 'Aston Martin': 'Aston Martin', 'Alpine': 'Alpine',
        'Williams': 'Williams', 'Racing Bulls': 'Racing Bulls', 'Haas': 'Haas', 'Sauber': 'Kick Sauber'
    }

    def __init__(self):
        self._prev_mc = {}
        self._prev_order = []
        self._prev_tick = 0

    def _name(self, code: str) -> str:
        return self.DRIVER_NAMES.get(code, code)

    def _short(self, code: str) -> str:
        return self._name(code).split()[-1]

    def generate(self, predictions: Dict, baseline_state: Dict, scenario_config: Optional[Dict] = None, mode: str = "standard", intensity: str = "cinematic_high") -> str:
        """Generate race commentary from prediction data.
        
        Args:
            predictions: Dictionary of ML predictions (win probs, factors, bands)
            baseline_state: The current RaceState dict representing the true state
            scenario_config: Optional configuration for scenario-specific commentary
            mode: "standard" or "cinematic"
            intensity: Optional tone modifier for cinematic mode
        """
        if not predictions:
            return "⏳ Awaiting simulation data..."

        mc = predictions.get('mc_win_distribution', {})
        order = predictions.get('predicted_order', [])
        factors = predictions.get('causal_factors', {})
        bands = predictions.get('volatility_bands', {})

        if not order or not mc:
            return "📡 Insufficient data for commentary."

        # Route to appropriate generator
        if mode == "cinematic":
            result = self._generate_cinematic(mc, order, factors, bands, baseline_state, scenario_config, intensity)
        else:
            result = self._generate_standard(mc, order, factors, bands, baseline_state, scenario_config)

        # Update state for momentum tracking
        self._prev_mc = mc.copy()
        self._prev_order = list(order)
        self._prev_tick = baseline_state.get('meta', {}).get('tick', self._prev_tick)

        return result

    def _generate_standard(self, mc: Dict, order: List[str], factors: Dict, bands: Dict, baseline_state: Dict, scenario_config: Optional[Dict]) -> str:
        """Original analytical generation method."""
        sections = []

        # === HEADLINE ===
        sections.append(self._headline(order, mc))

        # === LEADER ANALYSIS ===
        sections.append(self._leader_analysis(order, mc, factors, bands))

        # === CHALLENGER STORY ===
        if len(order) >= 2:
            sections.append(self._challenger_story(order, mc, factors))

        # === CHAOS / SCENARIO CONTEXT ===
        if scenario_config:
            ctx = self._scenario_context(scenario_config, mc, order)
            if ctx:
                sections.append(ctx)

        # === CAUSAL FACTORS INSIGHT ===
        sections.append(self._factor_insight(order[:3], factors))

        # === VOLATILITY CLOSING ===
        sections.append(self._volatility_closing(order, mc, bands))

        return "\n\n".join([s for s in sections if s])

    def _generate_cinematic(self, mc: Dict, order: List[str], factors: Dict, bands: Dict, baseline_state: Dict, scenario_config: Optional[Dict], intensity: str) -> str:
        """
        Cinematic Broadcast Mode generation.
        Translates probabilities into tension, stakes, and storyline.
        """
        sections = []
        
        # Determine Race Phase
        tick = baseline_state.get('meta', {}).get('tick', 0)
        # Using a rough heuristic for phase: Assuming ~600000 ticks per race on average
        if tick < 200000:
            phase = "Early"
        elif tick < 450000:
            phase = "Mid"
        else:
            phase = "Late"

        # === 1. OPENING TENSION ===
        sections.append(self._cinematic_opening(order, mc, phase, bands))

        # === 2. MOMENTUM & CONFLICT ===
        escalation = self._cinematic_escalation(order, mc, factors)
        if escalation:
            sections.append(escalation)

        # === 3. UNCERTAINTY SPIKE ===
        if scenario_config:
            ctx = self._cinematic_scenario(scenario_config, mc, order, intensity)
            if ctx:
                sections.append(ctx)

        # === 4. RADIO-STYLE CLOSING ===
        sections.append(self._cinematic_closing(order, mc, phase))

        return "\n\n".join([s for s in sections if s])

    def _cinematic_opening(self, order: List[str], mc: Dict, phase: str, bands: Dict) -> str:
        leader = order[0]
        leader_pct = mc.get(leader, 0) * 100
        pes = bands.get(leader, {}).get('pessimistic', 5)
        
        risk_pct = 100 - leader_pct

        if leader_pct > 65:
            openers = [
                f"⚔️ {self._name(leader)} stands at the front — {leader_pct:.0f}% model confidence — looking untouchable.",
                f"🏎️ A masterclass unfolding. {self._name(leader)} commands this race with a dominant {leader_pct:.0f}% probability.",
                f"🔥 {self._short(leader)} is breaking their spirit. The simulation sees him walking away with this ({leader_pct:.0f}%)."
            ]
        elif leader_pct > 40:
            openers = [
                f"⚔️ {self._name(leader)} commands the race — {leader_pct:.0f}% model confidence — but that means nearly half the simulations say this slips away.",
                f"⏱️ {self._short(leader)} holds the lead at {leader_pct:.0f}%, but the volatility window stretches down to P{pes}. This is hanging by a thread.",
                f"🛡️ {self._name(leader)} is on the defensive. At {leader_pct:.0f}%, the numbers say he is vulnerable."
            ]
        else:
            openers = [
                f"🌪️ Absolute chaos at the front. {self._name(leader)} leads with a fragile {leader_pct:.0f}% confidence — the models have no idea who wins this.",
                f"⚠️ The simulation is breaking down. {self._short(leader)} holds a marginal {leader_pct:.0f}% edge, but across thousands of runs, this is anyone's race.",
                f"👀 A wide-open brutal fight. {self._name(leader)} edges the numbers at {leader_pct:.0f}%, but the volatility is massive."
            ]
            
        return random.choice(openers)

    def _cinematic_escalation(self, order: List[str], mc: Dict, factors: Dict) -> str:
        if len(order) < 2:
            return ""

        leader = order[0]
        challenger = order[1]
        chall_pct = mc.get(challenger, 0) * 100
        
        prev_chall_pct = self._prev_mc.get(challenger, 0) * 100
        prev_leader_pct = self._prev_mc.get(leader, 0) * 100
        leader_pct = mc.get(leader, 0) * 100
        
        shift_chall = chall_pct - prev_chall_pct
        shift_leader = leader_pct - prev_leader_pct
        
        lines = []
        
        # Momentum Callouts
        if shift_chall > 5.0:
            lines.append(f"📈 **Momentum is swinging!** {self._short(challenger)} is surging up the probability tables (now {chall_pct:.0f}%).")
        elif shift_leader < -5.0:
            lines.append(f"📉 **Confidence is collapsing.** {self._short(leader)} is bleeding probability fast.")
            
        # Conflict
        gap = leader_pct - chall_pct
        if gap < 10:
            lines.append(f"⚔️ {self._short(challenger)} is circling. {chall_pct:.0f}%. Close enough to strike.")
        elif gap < 25:
            lines.append(f"💨 {self._short(challenger)} is the dark horse at {chall_pct:.0f}% — hunting the leader down.")
            
        if any('Fresh Tires' in f for f in factors.get(challenger, [])):
            lines.append("He has the fresh rubber. He has the pace. Now it's about execution.")
            
        return " ".join(lines) if lines else ""

    def _cinematic_scenario(self, config: Dict, mc: Dict, order: List[str], intensity: str) -> str:
        lines = []
        chaos = config.get('chaos', {})
        weather = config.get('weather', {})
        sc_prob = chaos.get('safety_car_probability', 1.0)
        
        rain = 0.0
        timeline = weather.get('timeline', [])
        if timeline and isinstance(timeline, list) and len(timeline) > 0:
            rain = timeline[0].get('rain_probability', 0.0) if isinstance(timeline[0], dict) else 0.0

        is_high_intensity = intensity in ["cinematic_high", "cinematic"]

        if sc_prob > 1.5:
            if is_high_intensity:
                lines.append(f"🚨 **Chaos in the numbers.** With a {sc_prob:.1f}x risk factor, the Monte Carlo runs are screaming for a Safety Car.")
            else:
                lines.append(f"⚠️ Incident probability is extremely elevated ({sc_prob:.1f}x). Strategy is heavily compromised.")
                
        if rain > 0.4:
            if is_high_intensity:
                lines.append("🌩️ **The sky is pregnant with rain.** A single wet pit stop will tear this predicted order to shreds.")
            else:
                lines.append("🌦️ Wet conditions imminent. Analytical baselines are losing relevance as grip drops.")

        return "\n\n".join(lines) if lines else ""

    def _cinematic_closing(self, order: List[str], mc: Dict, phase: str) -> str:
        leader = order[0]
        leader_pct = mc.get(leader, 0) * 100
        
        lines = []
        
        # Phase-Aware Tension
        if phase == "Early":
            lines.append("Plenty of laps left to play with. This story is just beginning.")
        elif phase == "Mid":
            lines.append("Strategy windows are tightening. The pit wall has to be perfect now.")
        else:
            lines.append("Now it's about nerve. One mistake ends it all.")
            
        # Radio Insert
        if leader_pct > 65:
            radios = [
                f"📻 *\"Keep the rhythm, {self._short(leader)}. Bring it home.\"*",
                f"📻 *\"Pace is good. Don't take unnecessary risks.\"*"
            ]
        elif leader_pct > 40:
            radios = [
                f"📻 *\"Push now, push now! We are not safe from the undercut.\"*",
                f"📻 *\"Tyres are critical, {self._short(leader)}. We need pace right this second.\"*"
            ]
        else:
            radios = [
                f"📻 *\"{self._short(leader)}, absolute maximum pace. Give me everything you have.\"*",
                f"📻 *\"It's chaos out there. Keep your head down.\"*"
            ]
            
        lines.append(random.choice(radios))
        return "\n\n".join(lines)

    # --- Standard Methods Below ---

    def _headline(self, order: List[str], mc: Dict) -> str:
        leader = order[0]
        leader_pct = mc.get(leader, 0) * 100
        margin = leader_pct - mc.get(order[1], 0) * 100 if len(order) > 1 else 0

        # Surprise index: how unexpected is the predicted winner?
        # 1.0 = total surprise (0% prior), 0.0 = fully expected (100% prior)
        surprise_index = 1.0 - mc.get(leader, 0)

        if surprise_index > 0.85 and leader_pct < 25:
            # Low-probability winner — chaos has flipped the script
            openers = [
                f"🌪️ **In a race defined by unpredictability, {self._name(leader)} emerges** at just {leader_pct:.0f}%. Nobody saw this coming.",
                f"💥 **Against all odds: {self._short(leader)} at {leader_pct:.0f}%.** The chaos engine has rewritten the form book.",
                f"🎲 **{self._short(leader)}?!** At {leader_pct:.0f}%, this is one of the wildest predictions the model has ever produced."
            ]
        elif leader_pct > 60:
            # Dominant expected winner
            openers = [
                f"🏁 **Clinical. Inevitable. {self._name(leader)}** at {leader_pct:.0f}% — the data sees no realistic challenger.",
                f"🏎️ **It's {self._short(leader)}'s race to lose** — the models give him a dominant {leader_pct:.0f}% chance.",
                f"🔴 **{self._short(leader)} holds the hammer.** {leader_pct:.0f}% — that's serious confidence from the engine."
            ]
        elif leader_pct > 35:
            openers = [
                f"⚔️ **{self._name(leader)} leads a competitive field** at {leader_pct:.0f}% — but this one is far from decided.",
                f"🔥 **{self._short(leader)} is favourite, but the margins are tight.** {leader_pct:.0f}% — anything can happen.",
                f"📊 **{self._short(leader)} edges ahead** in the probability model at {leader_pct:.0f}%, but the pack is hunting."
            ]
        else:
            openers = [
                f"🎲 **It's chaos out there!** {self._name(leader)} leads at just {leader_pct:.0f}% — this race is wide open.",
                f"🌪️ **No clear favourite.** {self._short(leader)} has the slimmest of edges at {leader_pct:.0f}% — a coin flip at the front.",
                f"💥 **The models can't call this one.** {self._short(leader)} at {leader_pct:.0f}% — we could see anyone on the top step."
            ]

        return random.choice(openers)

    def _leader_analysis(self, order: List[str], mc: Dict, factors: Dict, bands: Dict) -> str:
        leader = order[0]
        pct = mc.get(leader, 0) * 100
        leader_factors = factors.get(leader, [])
        leader_band = bands.get(leader, {})

        lines = []

        # Position analysis
        pos_factor = [f for f in leader_factors if 'Track Pos' in f]
        if pos_factor:
            pos = pos_factor[0].split('P')[-1]
            if pos == '1':
                lines.append(f"{self._short(leader)} starts from pole — clean air, no traffic, the ideal setup.")
            else:
                lines.append(f"Starting from P{pos}, {self._short(leader)} will need to fight through the pack.")

        # Key advantages
        if 'Strong Historical Baseline' in leader_factors:
            lines.append("The historical data strongly backs this driver's pedigree at this level.")
        if any('AI Trait Advantage' in f for f in leader_factors):
            trait_f = [f for f in leader_factors if 'AI Trait Advantage' in f][0]
            lines.append(f"Driver personality model shows: {trait_f.lower().replace('ai trait ', '')}.")
        if 'High Driver Skill Bonus' in leader_factors:
            lines.append("Raw driver skill gives a clear edge in the pace calculations.")

        # Volatility bands
        opt = leader_band.get('optimistic', 1)
        pes = leader_band.get('pessimistic', 5)
        if pes > 3:
            lines.append(f"But the volatility window is wide — anywhere from P{opt} to P{pes} across simulations. This isn't locked in.")
        elif pes <= 2:
            lines.append(f"Crucially, the volatility band is tight: P{opt}–P{pes}. Very little downside in the Monte Carlo runs.")

        return " ".join(lines) if lines else ""

    def _challenger_story(self, order: List[str], mc: Dict, factors: Dict) -> str:
        if len(order) < 2:
            return ""

        leader = order[0]
        challenger = order[1]
        leader_pct = mc.get(leader, 0) * 100
        chall_pct = mc.get(challenger, 0) * 100
        gap = leader_pct - chall_pct

        chall_factors = factors.get(challenger, [])

        if gap < 5:
            intros = [
                f"👀 **{self._name(challenger)} is RIGHT THERE** at {chall_pct:.0f}% — just {gap:.0f} points off the lead.",
                f"🔄 **{self._short(challenger)} is the main threat** at {chall_pct:.0f}% — the gap to {self._short(leader)} is razor-thin.",
            ]
        elif gap < 20:
            intros = [
                f"📈 **{self._name(challenger)} is the best-placed challenger** at {chall_pct:.0f}%.",
                f"🎯 **{self._short(challenger)} at {chall_pct:.0f}%** — there's a realistic path to victory if the leader falters.",
            ]
        else:
            intros = [
                f"🏃 **{self._name(challenger)} sits in P2 probability at {chall_pct:.0f}%** — a long shot but stranger things have happened.",
                f"📉 **The drop-off to {self._short(challenger)} at {chall_pct:.0f}%** shows the leader's advantage.",
            ]

        result = random.choice(intros)

        # Add challenger-specific narrative
        if 'Fresh Tires Advantage' in chall_factors:
            result += f" Fresh rubber could be the equalizer."
        if any('Tire Deg' in f for f in chall_factors):
            result += f" But tire degradation is a concern for the challenge."

        # Third driver mention
        if len(order) >= 3:
            third = order[2]
            third_pct = mc.get(third, 0) * 100
            if third_pct > 10:
                result += f" Don't sleep on {self._short(third)} either — {third_pct:.0f}% is not negligible."

        return result

    def _scenario_context(self, config: Dict, mc: Dict, order: List[str]) -> str:
        """Add commentary about the scenario conditions."""
        lines = []

        chaos = config.get('chaos', {})
        weather = config.get('weather', {})
        engineering = config.get('engineering', {})

        sc_prob = chaos.get('safety_car_probability', 1.0)
        incident_freq = chaos.get('incident_frequency', 1.0)
        tire_deg = engineering.get('tire_deg_multiplier', 1.0)

        rain = 0.0
        timeline = weather.get('timeline', [])
        if timeline and isinstance(timeline, list) and len(timeline) > 0:
            rain = timeline[0].get('rain_probability', 0.0) if isinstance(timeline[0], dict) else 0.0

        if sc_prob > 1.5 or incident_freq > 1.5:
            chaos_level = max(sc_prob, incident_freq)
            templates = [
                f"⚠️ **Scenario Alert**: Chaos is dialled up to {chaos_level:.1f}x — the Safety Car looms large over this race.",
                f"🚨 **High-chaos scenario active.** With {chaos_level:.1f}x incident frequency, expect the unexpected. Strategy becomes a lottery.",
                f"💣 **This is a chaos race.** At {chaos_level:.1f}x volatility, the Monte Carlo simulations show massive spread — any strategy could win or lose."
            ]
            lines.append(random.choice(templates))

            # Explain impact
            leader_pct = mc.get(order[0], 0) * 100
            if leader_pct < 30:
                lines.append("The chaos has completely eroded any pace advantage. This is a pure coin-flip at the front.")
            elif leader_pct < 50:
                lines.append("Even the favourite can't escape the variance. Multiple drivers have genuine upset potential.")

        if rain > 0.3:
            if rain > 0.7:
                lines.append(f"🌧️ **Full wet conditions** ({int(rain*100)}% rain probability). Tyre choices and driver wet-weather ability are now critical differentiators.")
            else:
                lines.append(f"🌦️ **Rain is in the air** ({int(rain*100)}% probability). Teams will be watching the radar — a weather-triggered pit stop could reshuffle the entire order.")

        if tire_deg > 1.3:
            lines.append(f"🔴 **Tire degradation at {tire_deg:.1f}x** — this is a tyre management race. Aggressive drivers will pay a heavy price in the final stint.")
        elif tire_deg < 0.7:
            lines.append(f"🟢 **Low degradation ({tire_deg:.1f}x)** — one-stop strategies become viable. Track position is everything.")

        return "\n\n".join(lines) if lines else ""

    def _factor_insight(self, top_drivers: List[str], factors: Dict) -> str:
        """Pick the most interesting causal factor and narrativize it."""
        insights = []

        for d in top_drivers:
            driver_factors = factors.get(d, [])
            for f in driver_factors:
                if 'Chaos Flattening' in f:
                    pct = f.split('(')[1].split('%')[0] if '(' in f else '?'
                    insights.append(f"🎲 The chaos engine is applying {pct}% probability flattening — this closes the gap between all drivers.")
                    break
                if 'Rain Impact' in f:
                    insights.append(f"🌧️ Rain conditions are actively reshaping the probability landscape for {self._short(d)}.")
                    break
                if 'High Deg Scenario' in f:
                    insights.append(f"📉 Elevated tyre degradation is punishing {self._short(d)}'s current tyre age.")
                    break

        return insights[0] if insights else ""

    def _volatility_closing(self, order: List[str], mc: Dict, bands: Dict) -> str:
        """Close with a volatility-aware sign-off, including deviation from expectation."""
        leader = order[0]
        leader_pct = mc.get(leader, 0) * 100

        # Deviation analysis: how spread is the field?
        if len(mc) > 1:
            probs = list(mc.values())
            spread = max(probs) - min(probs)
        else:
            spread = 0

        if leader_pct > 60:
            closings = [
                f"📻 *\"Box box, {self._short(leader)}. We're in the zone.\"* — A strong position, but the race isn't over until the chequered flag.",
                f"📻 *\"Copy, {self._short(leader)}. Keep pushing.\"* — The data says this should be his race, barring a Safety Car twist.",
                f"💡 **Bottom line**: {self._short(leader)} is the clear favourite. The question isn't IF he wins, but by how much."
            ]
        elif leader_pct > 30:
            closings = [
                f"📻 *\"It's close, {self._short(leader)}. Stay on top of the tyres.\"* — Every tenth counts in a race this tight.",
                f"💡 **Bottom line**: This is a multi-driver fight. {self._short(leader)} has the edge but can't afford a single mistake.",
                f"🏎️ *This is what we watch Formula 1 for.* The margin between glory and disaster is paper-thin."
            ]
        else:
            if spread < 0.05:
                closings = [
                    f"📻 *\"Anything can happen, stay alert!\"* — The probability spread is just {spread*100:.0f}% — we've never seen it this tight.",
                    f"💡 **Bottom line**: The Bayesian engine shows near-total uncertainty. This is a pure lottery at the front.",
                    f"🏎️ *Pure chaos. Pure racing.* The statistical deviation from expectation is off the charts — and that's beautiful."
                ]
            else:
                closings = [
                    f"📻 *\"Anything can happen, stay alert!\"* — The models show complete uncertainty. Buckle up.",
                    f"💡 **Bottom line**: The scenarios have broken the hierarchy. We're in uncharted territory.",
                    f"🏎️ *Pure chaos. Pure racing.* No analytics model in the world can call this one — and that's beautiful."
                ]

        return random.choice(closings)

    def generate_reasoning_tree(self, predictions: Dict, baseline_state: Dict, scenario_config: Optional[Dict] = None) -> Dict:
        """
        Generate a structured reasoning tree for the frontend expandable panel.
        Returns JSON with headline, factors, confidence, bias warnings, and race phase.
        """
        mc = predictions.get('mc_win_distribution', {})
        order = predictions.get('predicted_order', [])
        factors = predictions.get('causal_factors', {})
        bands = predictions.get('volatility_bands', {})

        if not order or not mc:
            return {"headline": "Insufficient data", "factors": [], "confidence_score": 0, "bias_warnings": [], "race_phase": "unknown"}

        leader = order[0]
        leader_pct = mc.get(leader, 0) * 100

        # === RACE PHASE DETECTION ===
        tick = baseline_state.get('meta', {}).get('tick', 0)
        if tick < 200000:
            race_phase = "early"
        elif tick < 450000:
            race_phase = "mid"
        else:
            race_phase = "late"

        # === CONFIDENCE SCORE ===
        # Based on how concentrated the distribution is — higher = more confident
        probs = list(mc.values())
        if probs:
            max_p = max(probs)
            entropy = -sum(p * (p and __import__('math').log2(p) or 0) for p in probs if p > 0)
            max_entropy = __import__('math').log2(len(probs)) if len(probs) > 1 else 1
            # Confidence: 100 when one driver dominates, 0 when perfectly uniform
            confidence_score = max(0, min(100, int((1.0 - entropy / max(max_entropy, 1)) * 100)))
        else:
            confidence_score = 0

        # === KEY FACTORS ===
        key_factors = []
        leader_factors = factors.get(leader, [])
        for f in leader_factors[:6]:
            direction = "positive"
            if any(neg in f for neg in ['Penalty', 'Warning', 'Deg', 'Chaos', 'Risk']):
                direction = "negative"
            elif any(neu in f for neu in ['Track Pos', 'Form Drift']):
                direction = "neutral"

            # Estimate impact magnitude
            if 'Strong Historical' in f or 'High Driver Skill' in f:
                impact = "high"
            elif 'AI Trait' in f or 'Fresh Tires' in f:
                impact = "medium"
            else:
                impact = "low"

            key_factors.append({
                "factor": f,
                "impact": impact,
                "direction": direction
            })

        # === BIAS WARNINGS ===
        bias_warnings = []

        # Check: same-team dominance
        if len(order) >= 2:
            top_2_factors = [factors.get(order[0], []), factors.get(order[1], [])]
            top_teams = set()
            cars = baseline_state.get('cars', [])
            for car in cars:
                if car.get('driver') in order[:3]:
                    top_teams.add(car.get('team', ''))
            if len(top_teams) == 1 and top_teams != {''}:
                bias_warnings.append(f"Mono-team dominance: Top 3 all from {list(top_teams)[0]}")

        # Check: extremely high confidence may indicate overfitting
        if confidence_score > 85:
            bias_warnings.append("Very high confidence — may underestimate tail risks")

        # Check: if rain is active but no rain factors in leader analysis
        if scenario_config:
            rain = 0.0
            timeline = scenario_config.get('weather', {}).get('timeline', [])
            if timeline and isinstance(timeline, list) and len(timeline) > 0:
                rain = timeline[0].get('rain_probability', 0.0) if isinstance(timeline[0], dict) else 0.0
            if rain > 0.5 and not any('Rain' in f for f in leader_factors):
                bias_warnings.append("Wet conditions active but leader has no rain-specific adjustment")

        # === HEADLINE ===
        if leader_pct > 50:
            headline = f"{self._name(leader)} is the clear favourite at {leader_pct:.0f}%"
        elif leader_pct > 30:
            headline = f"Competitive fight led by {self._name(leader)} at {leader_pct:.0f}%"
        else:
            headline = f"Wide open race — {self._name(leader)} edges at {leader_pct:.0f}%"

        return {
            "headline": headline,
            "factors": key_factors,
            "confidence_score": confidence_score,
            "bias_warnings": bias_warnings,
            "race_phase": race_phase
        }

