from backend.app.ml.rl_predictor import RLDriverPredictor

print("Initializing Predictor...")
predictor = RLDriverPredictor()
print("Initialized!")

# Test prediction
print("Predicting Action...")
action = predictor.predict_action(200.0, 0.0, 0.0, 0.0)
print(f"Action Output: {action}")
