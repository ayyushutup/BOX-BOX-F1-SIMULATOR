import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Configuration
DATA_PATH = "app/ml/data/synthetic_race_data.csv"
MODEL_DIR = "app/ml/models"
OS_DATA_PATH = "backend/" + DATA_PATH  # For running from root if needed, but we run from backend dir

def train_models():
    print("Loading data...")
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
    elif os.path.exists("../" + DATA_PATH):
        df = pd.read_csv("../" + DATA_PATH)
    else:
        raise FileNotFoundError(f"Could not find data at {DATA_PATH}")

    # Features to use for training
    # We remove identifiers and cheating features (like future data)
    feature_cols = [
        "lap", "lap_progress", "laps_remaining", "position",
        "speed", "gap_to_leader", "gap_to_car_ahead",
        "tire_age", "tire_wear", "pit_stops",
        "sc_active", "vsc_active", "drs_enabled"
    ]
    
    # We also need to encode categorical features like 'tire_compound' and 'team'
    # For now, let's keep it simple and drop complex categoricals or label encode them
    # 'tire_compound' is already a string, needs encoding.
    # 'team' is a string, needs encoding.
    # For a first pass, let's use numeric/boolean features only + simplistic encoding
    
    # Simple encoding
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
    
    # Train Win Model
    print("Training Win Probability Model...")
    win_model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    win_model.fit(X_train, y_win_train)
    
    win_pred = win_model.predict(X_test)
    print(f"Win Model Accuracy: {accuracy_score(y_win_test, win_pred):.4f}")
    
    # Train Podium Model
    print("Training Podium Probability Model...")
    podium_model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    podium_model.fit(X_train, y_podium_train)
    
    podium_pred = podium_model.predict(X_test)
    print(f"Podium Model Accuracy: {accuracy_score(y_podium_test, podium_pred):.4f}")
    
    # Save Models
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(win_model, os.path.join(MODEL_DIR, "win_model.joblib"))
    joblib.dump(podium_model, os.path.join(MODEL_DIR, "podium_model.joblib"))
    
    # Save encoders (simplified - in production we'd use proper sklearn pipelines)
    # For now we just need to know the mapping, but since we use new data, we might need a robust encoder.
    # Let's verify feature importance
    print("\nFeature Importance (Win Model):")
    importances = list(zip(feature_cols, win_model.feature_importances_))
    importances.sort(key=lambda x: x[1], reverse=True)
    for feat, imp in importances[:5]:
        print(f"{feat}: {imp:.4f}")

    print(f"\nModels saved to {MODEL_DIR}")

if __name__ == "__main__":
    train_models()
