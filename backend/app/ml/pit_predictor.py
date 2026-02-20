import os
import joblib
import numpy as np
import warnings

# Suppress LightGBM feature name warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

from app.models.race_state import Car

class PitStrategyPredictor:
    """Singleton for the LightGBM Pit Strategy Model."""
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

    def predict_should_pit(self, car: Car, sc_active: bool, vsc_active: bool) -> bool:
        """
        Predicts whether the car should pit. Fast optimized numpy array approach.
        """
        if not self.model:
            return False # Fall back to heuristics if model is missing
            
        gap_ahead = car.timing.interval if car.timing.interval is not None else 0.0
        team_code = self.team_map.get(car.identity.team, -1)
        tire_code = self.tire_map.get(car.telemetry.tire_state.compound.value, -1)
        
        # Features: lap, position, tire_age, tire_wear, tire_compound_code, gap_to_ahead, sc_active, vsc_active, pit_stops, team_code
        X = np.array([[
            float(car.timing.lap),
            float(car.timing.position),
            float(car.telemetry.tire_state.age),
            float(car.telemetry.tire_state.wear),
            float(tire_code),
            float(gap_ahead),
            1.0 if sc_active else 0.0,
            1.0 if vsc_active else 0.0,
            float(car.pit_stops),
            float(team_code)
        ]])
        
        prob = self.model.predict_proba(X)[0][1]
        
        # Threshold tuning: Because it was trained on balanced weights, 0.5 is the natural threshold.
        # We use 0.65 to be slightly more conservative than early-pitting.
        return bool(prob > 0.65)
