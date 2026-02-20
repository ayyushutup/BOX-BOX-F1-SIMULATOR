
import joblib
import pandas as pd
import os
from typing import Dict, List, Optional
from app.models.race_state import RaceState, RaceControl
from app.ml.monte_carlo import MonteCarloRaceSimulator

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
            self.load_models()
            self.initialized = True
            
            # HARDCODED ENCODERS (Reconstructed from alphabetical sort)
            # Essential because we didn't save the encoders during training.
            self.driver_map = {d: i for i, d in enumerate(sorted([
                "VER", "HAM", "LEC", "NOR", "RUS", "SAI", "PER", "ALO", "PIA", 
                "GAS", "OCO", "STR", "HUL", "TSU", "RIC", "ALB", "BOT", "MAG", "ZHO", "SAR"
            ]))}
            
            self.team_map = {t: i for i, t in enumerate(sorted([
                "Red Bull Racing", "Mercedes", "Ferrari", "McLaren", "Aston Martin", 
                "Alpine", "Williams", "RB", "Haas", "Sauber"
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

    def predict(self, state: RaceState) -> Dict:
        """
        Generate predictions for the current race state.
        Uses LightGBM + Isotonic Calibration for raw probabilities,
        then Monte Carlo simulation for win distributions.
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

        # Calibrated probabilities from LightGBM
        win_probs = self.win_model.predict_proba(X)
        podium_probs = self.podium_model.predict_proba(X)
        
        # Build raw probability dicts
        win_prob_dict = {}
        podium_prob_dict = {}
        
        for i, car in enumerate(state.cars):
            p_win = float(win_probs[i][1]) if len(win_probs[i]) > 1 else 0.0
            p_podium = float(podium_probs[i][1]) if len(podium_probs[i]) > 1 else 0.0
            
            win_prob_dict[car.identity.driver] = p_win
            podium_prob_dict[car.identity.driver] = p_podium

        # Run Monte Carlo simulation on top of calibrated probabilities
        mc_results = self.mc_simulator.simulate(
            win_probs=win_prob_dict,
            podium_probs=podium_prob_dict
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
            "position_distributions": mc_results["position_distributions"]
        }
            
        return results