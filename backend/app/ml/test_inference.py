from app.ml.rl_predictor import RLDriverPredictor

def test():
    predictor = RLDriverPredictor()
    action = predictor.predict_action(speed_kmh=150.0, x=100.0, y=200.0, heading=0.5)
    print(f"Action (Steering, Throttle, Brake): {action}")

if __name__ == "__main__":
    test()
