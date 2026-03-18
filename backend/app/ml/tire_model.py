import os
import joblib
from app.simulation.tire_physics import TirePhysicsEngine

class NeuralTireModel:
    """
    Predicts tire degradation and maps it to a lap time penalty.
    Designed to wrap a trained PyTorch/sklearn ML model, currently falls back to the physics engine.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(NeuralTireModel, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, track_abrasiveness=1.0, track_temp_celsius=35.0):
        if not self.initialized:
            self.model = None
            self.load_model()
            self.physics_engine = TirePhysicsEngine(
                track_abrasiveness=track_abrasiveness, 
                track_temp_celsius=track_temp_celsius
            )
            self.initialized = True
            
    def load_model(self):
        try:
            cur_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(cur_dir, "models", "tire_mlp.joblib")
            
            if not os.path.exists(model_path):
                model_path = "app/ml/models/tire_mlp.joblib"

            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                print("Neural Tire Model loaded successfully.")
            else:
                pass
                # print("Neural Tire Model not found. Falling back to physics engine.")
        except Exception as e:
            print(f"Failed to load Tire MLP model: {e}")
            self.model = None

    def predict_degradation(self, compound: str, track_temp: float, track_abrasiveness: float,
                            driver_push_level: float, lap_number: int, 
                            current_wear: float, current_temp: float):
        """
        Inputs: compound, track_temp, track_abrasiveness, driver_push_level, lap_number, current_wear, current_temp
        Outputs: (delta_wear, delta_temp, lap_time_penalty)
        """
        
        comp_str = getattr(compound, "value", compound) if hasattr(compound, "value") else str(compound)
                
        if self.model:
            import pandas as pd
            # Format inputs directly into a DataFrame for the ColumnTransformer
            X_infer = pd.DataFrame([{
                "compound": comp_str,
                "track_temp": float(track_temp),
                "track_abrasiveness": float(track_abrasiveness),
                "driver_push_level": float(driver_push_level),
                "lap_number": float(lap_number),
                "current_wear": float(current_wear),
                "current_temp": float(current_temp)
            }])
            
            try:
                preds = self.model.predict(X_infer)[0]
                return float(preds[0]), float(preds[1]), float(preds[2])
            except Exception as e:
                print(f"[NeuralTireModel] Inference failed: {e}. Falling back to physics engine.")

        # Physics Fallback
        # Update engine parameters dynamically
        self.physics_engine.track_temp = track_temp
        self.physics_engine.track_abrasiveness = track_abrasiveness
        
        # Build state dict for physics engine
        state_in = {
            'compound': comp_str,
            'wear': current_wear,
            'temperature': current_temp,
            'age': lap_number
        }
        
        # Simulate one lap
        state_out = self.physics_engine.simulate_lap(
            state=state_in,
            driver_aggression=driver_push_level,
            driver_smoothness=0.5, # Default or could be mapped to personality
            in_dirty_air=False, # Could be added to inputs later
            is_safety_car=False # Could be added to inputs later
        )
        
        delta_wear = state_out['wear'] - current_wear
        delta_temp = state_out['temperature'] - current_temp
        lap_time_penalty = self.physics_engine.calculate_lap_time_penalty(state_out)

        return delta_wear, delta_temp, lap_time_penalty
