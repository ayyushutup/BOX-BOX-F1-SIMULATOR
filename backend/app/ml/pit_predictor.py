import os
import joblib
import numpy as np
import warnings

# Suppress LightGBM feature name warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

from app.models.race_state import Car, RaceState
from app.models.strategy import PitStrategyResult

class PitStrategyPredictor:
    """Singleton for Pit Strategy Evaluation."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PitStrategyPredictor, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if not self.initialized:
            self.model = None
            self.load_model()
            self.initialized = True
            
            # Use same encoding as training
            self.team_map = {t: i for i, t in enumerate(sorted([
                "Red Bull Racing", "Mercedes", "Ferrari", "McLaren", "Aston Martin", 
                "Alpine", "Williams", "RB", "Haas", "Sauber"
            ]))}
            
            self.tire_map = {t: i for i, t in enumerate(sorted([
                "SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"
            ]))}

    def load_model(self):
        try:
            cur_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(cur_dir, "models", "pit_model.joblib")
            
            if not os.path.exists(model_path):
                # Fallback for alternative working directory
                model_path = "app/ml/models/pit_model.joblib"

            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                print("ML Pit Strategy Model loaded successfully.")
            else:
                print("Pit Strategy Model not found. Falling back to heuristics.")
        except Exception as e:
            print(f"Failed to load Pit model: {e}")
            self.model = None

    def calculate_pit_ev(self, car: Car, state: RaceState) -> PitStrategyResult:
        """
        Calculates the Positional Expected Value (EV) of pitting THIS lap.
        """
        # Baseline variables
        pit_loss_time = state.track.pit_stop_loss if state.track and hasattr(state.track, 'pit_stop_loss') else 22.0
        gap_ahead = car.timing.interval if car.timing.interval is not None else 0.0
        
        # 1. Drop Zone Analysis (Where will we land?)
        # Simulate position drop based on gaps behind
        cars_behind = [c for c in state.cars if c.timing.position > car.timing.position]
        cumulative_gap_behind = 0.0
        drop_position = car.timing.position
        
        for p in cars_behind:
            gap_to_p = p.timing.gap_to_leader - car.timing.gap_to_leader if p.timing.gap_to_leader and car.timing.gap_to_leader else 0.0
            cumulative_gap_behind = abs(gap_to_p)
            if cumulative_gap_behind < pit_loss_time:
                drop_position += 1
            else:
                break
                
        # Are we landing in dirty air? (If gap to car ahead of drop_pos is < 1.0s)
        # Simplified: if we dropped positions, assume some traffic.
        positions_lost = drop_position - car.timing.position

        # 2. Pace Delta (Undercut Potential)
        # Fast estimation: fresh tires are ~2.0s faster than 15-lap old tires.
        tire_age = float(car.telemetry.tire_state.age)
        tire_deg_multiplier = 1.0
        # Basic heuristic pace advantage
        fresh_tire_advantage = min(2.5, (tire_age / 10.0) * tire_deg_multiplier)
        
        # Warmup penalty depends on track conditions and compound
        warmup_penalty = 0.8
        net_outlap_advantage = fresh_tire_advantage - warmup_penalty
        
        # 3. Calculate EV Score
        ev_score = 0.0
        undercut_viable = False
        target_undercut_delta = None
        
        if car.timing.position > 1 and gap_ahead > 0:
            if gap_ahead < net_outlap_advantage * 2.0: # Assuming they stay out 2 laps
                undercut_viable = True
                target_undercut_delta = gap_ahead
                ev_score += 1.0 # Positional gain
                
        # Penalties for dropping into traffic
        traffic_penalty = positions_lost * 0.2
        ev_score -= traffic_penalty
        
        # Overcut (Defensive)
        if tire_age < 5:
            ev_score -= 1.0 # Too early to pit
            
        # Hard limits
        tire_wear = car.telemetry.tire_state.wear
        if tire_wear > 0.85:
           ev_score += 2.0 # Must pit
           
        ideal_lap = car.timing.lap + (1 if ev_score < 0 else 0)

        # Baseline LightGBM integration for hybrid approach
        if self.model:
            team_code = self.team_map.get(car.identity.team, -1)
            tire_code = self.tire_map.get(car.telemetry.tire_state.compound.value, -1)
            sc_active = 1.0 if state.race_control in ["SAFETY_CAR"] else 0.0
            vsc_active = 1.0 if state.race_control in ["VSC"] else 0.0
            
            X = np.array([[
                float(car.timing.lap),
                float(car.timing.position),
                tire_age,
                float(tire_wear),
                float(tire_code),
                float(gap_ahead),
                sc_active,
                vsc_active,
                float(car.pit_stops),
                float(team_code)
            ]])
            prob = self.model.predict_proba(X)[0][1]
            if prob > 0.65:
                ev_score += 0.5 # Boost EV if ML model strongly suggests it
                
        # SC/VSC window: dynamically scale EV boost
        # Longer stints benefit MORE from a free SC stop
        if state.race_control in ["SAFETY_CAR", "VSC"]:
            sc_multiplier = 1.5 if state.race_control == "SAFETY_CAR" else 0.8
            age_bonus = min(1.5, tire_age / 15.0)  # Older tires = bigger benefit
            ev_score += sc_multiplier + age_bonus
        else:
            # Even if SC isn't active, high SC probability tracks should boost EV slightly
            track_sc_prob = state.track.sc_probability / 100.0 if state.track and hasattr(state.track, 'sc_probability') else 0.2
            if track_sc_prob > 0.3 and tire_age > 12:
                ev_score += 0.3  # Speculative pit on high-SC tracks

        return PitStrategyResult(
            should_pit=bool(ev_score > 0.5),
            ev_score=float(ev_score),
            undercut_viable=undercut_viable,
            drop_pos=int(drop_position),
            ideal_lap=int(ideal_lap)
        )
