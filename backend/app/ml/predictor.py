
import joblib
import pandas as pd
import os
from typing import Dict, List
from app.models.race_state import RaceState

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
        """Load trained models from disk"""
        try:
            cur_dir = os.path.dirname(os.path.abspath(__file__))
            # Adjust path to match where models are actually saved relative to this file
            model_path = os.path.join(cur_dir, "models") 
            
            # Fallback if running from root
            if not os.path.exists(model_path):
                model_path = "app/ml/models"

            print(f"Loading models from {model_path}...")
            self.win_model = joblib.load(os.path.join(model_path, "win_model.joblib"))
            self.podium_model = joblib.load(os.path.join(model_path, "podium_model.joblib"))
            print("ML Models loaded successfully.")
        except Exception as e:
            print(f"Failed to load ML models: {e}")
            print("Predictions will be unavailable.")

    def predict(self, state: RaceState) -> Dict:
        """
        Generate predictions for the current race state.
        Returns a dictionary with win and podium probabilities.
        """
        if not self.win_model or not self.podium_model:
            return None

        # 1. Extract Features (Must match training columns EXACTLY)
        # We process car-by-car
        data = []
        total_laps = state.meta.laps_total
        
        for car in state.cars:
            # Handle Nones
            gap_leader = car.gap_to_leader if car.gap_to_leader is not None else 0.0
            gap_ahead = car.interval if car.interval is not None else 0.0
            
            # Map Categoricals
            driver_code = self.driver_map.get(car.driver, -1)
            team_code = self.team_map.get(car.team, -1)
            tire_code = self.tire_map.get(car.tire_state.compound.value, -1)
            
            row = {
                "lap": car.lap,
                "lap_progress": car.lap_progress,
                "laps_remaining": total_laps - car.lap,
                "position": car.position,
                "speed": car.speed,
                "gap_to_leader": gap_leader,
                "gap_to_car_ahead": gap_ahead,
                "tire_age": car.tire_state.age,
                "tire_wear": car.tire_state.wear,
                "pit_stops": car.pit_stops,
                "sc_active": 1 if state.safety_car_active else 0,
                "vsc_active": 1 if state.vsc_active else 0,
                "drs_enabled": 1 if state.drs_enabled else 0,
                "tire_compound_code": tire_code, 
                "team_code": team_code,
                "driver_code": driver_code
            }
            data.append(row)

        df = pd.DataFrame(data)
        
        # Ensure column order matches training
        feature_cols = [
            "lap", "lap_progress", "laps_remaining", "position",
            "speed", "gap_to_leader", "gap_to_car_ahead",
            "tire_age", "tire_wear", "pit_stops",
            "sc_active", "vsc_active", "drs_enabled",
            "tire_compound_code", "team_code", "driver_code"
        ]
        
        X = df[feature_cols]

        # 2. Predict Probas
        win_probs = self.win_model.predict_proba(X)
        podium_probs = self.podium_model.predict_proba(X)
        
        # 3. Format Output
        # The models return shape (n_cars, 2) where col 1 is probability of class '1' (True)
        # BUT wait:
        # - Win model was trained on 'label_win' (1 for winner, 0 for others). 
        #   So for each car, we want the probability of it being class 1.
        
        results = {
            "lap": state.cars[0].lap,
            "win_prob": {},
            "podium_prob": {},
            "confidence": min(1.0, state.meta.tick / (total_laps * 300)) # Fake confidence ramp
        }
        
        for i, car in enumerate(state.cars):
            # win_probs[i][1] is probability of this car winning
            p_win = float(win_probs[i][1]) if len(win_probs[i]) > 1 else 0.0
            p_podium = float(podium_probs[i][1]) if len(podium_probs[i]) > 1 else 0.0
            
            results["win_prob"][car.driver] = p_win
            results["podium_prob"][car.driver] = p_podium
            
        return results