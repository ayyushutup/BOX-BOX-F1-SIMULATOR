import pandas as pd
import joblib
import os
import lightgbm as lgb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss, classification_report

# Configuration
DATA_PATH = "app/ml/data/synthetic_race_data.csv"
MODEL_DIR = "app/ml/models"

def train_models():
    print("Loading data...")
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
    elif os.path.exists("../" + DATA_PATH):
        df = pd.read_csv("../" + DATA_PATH)
    else:
        raise FileNotFoundError(f"Could not find data at {DATA_PATH}")

    # Features to use for training
    feature_cols = [
        "lap", "lap_progress", "laps_remaining", "position",
        "speed", "gap_to_leader", "gap_to_car_ahead",
        "tire_age", "tire_wear", "pit_stops",
        "sc_active", "vsc_active", "drs_enabled"
    ]
    
    # Encode categorical features
    df['tire_compound_code'] = df['tire_compound'].astype('category').cat.codes
    df['team_code'] = df['team'].astype('category').cat.codes
    df['driver_code'] = df['driver'].astype('category').cat.codes
    
    feature_cols.extend(['tire_compound_code', 'team_code', 'driver_code'])
    
    X = df[feature_cols]
    y_win = df['label_win']
    y_podium = df['label_podium']
    
    print(f"Training on {len(df)} samples with {len(feature_cols)} features...")
    
    # Split data
    X_train, X_test, y_win_train, y_win_test, y_podium_train, y_podium_test = train_test_split(
        X, y_win, y_podium, test_size=0.2, random_state=42
    )
    
    # ── Win Model: LightGBM + Isotonic Calibration ──
    print("\nTraining Win Probability Model (LightGBM + Calibration)...")
    base_win = lgb.LGBMClassifier(
        n_estimators=200, max_depth=8, learning_rate=0.05,
        random_state=42, verbose=-1,
        num_leaves=31, min_child_samples=20
    )
    win_model = CalibratedClassifierCV(base_win, method='isotonic', cv=3)
    win_model.fit(X_train, y_win_train)
    
    win_pred = win_model.predict(X_test)
    win_proba = win_model.predict_proba(X_test)[:, 1]
    
    print(f"  Accuracy:    {accuracy_score(y_win_test, win_pred):.4f}")
    print(f"  Log Loss:    {log_loss(y_win_test, win_proba):.4f}")
    print(f"  Brier Score: {brier_score_loss(y_win_test, win_proba):.4f}")
    
    # ── Podium Model: LightGBM + Isotonic Calibration ──
    print("\nTraining Podium Probability Model (LightGBM + Calibration)...")
    base_podium = lgb.LGBMClassifier(
        n_estimators=200, max_depth=8, learning_rate=0.05,
        random_state=42, verbose=-1,
        num_leaves=31, min_child_samples=20
    )
    podium_model = CalibratedClassifierCV(base_podium, method='isotonic', cv=3)
    podium_model.fit(X_train, y_podium_train)
    
    podium_pred = podium_model.predict(X_test)
    podium_proba = podium_model.predict_proba(X_test)[:, 1]
    
    print(f"  Accuracy:    {accuracy_score(y_podium_test, podium_pred):.4f}")
    print(f"  Log Loss:    {log_loss(y_podium_test, podium_proba):.4f}")
    print(f"  Brier Score: {brier_score_loss(y_podium_test, podium_proba):.4f}")
    
    # ── Save Models ──
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(win_model, os.path.join(MODEL_DIR, "win_model.joblib"))
    joblib.dump(podium_model, os.path.join(MODEL_DIR, "podium_model.joblib"))
    
    # Feature importance from the base estimators inside the calibrated wrapper
    print("\nFeature Importance (Win Model - LightGBM base):")
    # CalibratedClassifierCV stores base estimators in calibrated_classifiers_
    # Each has a base_estimator with feature_importances_
    try:
        base = win_model.calibrated_classifiers_[0].estimator
        importances = list(zip(feature_cols, base.feature_importances_))
        importances.sort(key=lambda x: x[1], reverse=True)
        for feat, imp in importances[:5]:
            print(f"  {feat}: {imp}")
    except Exception as e:
        print(f"  (Could not extract feature importance: {e})")

    print(f"\nModels saved to {MODEL_DIR}")
    print("Model type: LightGBM + Isotonic Calibration (CalibratedClassifierCV)")

if __name__ == "__main__":
    train_models()
