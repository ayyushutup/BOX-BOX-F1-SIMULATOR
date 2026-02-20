import os
import pandas as pd
import lightgbm as lgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

DATA_PATH = "app/ml/data/pit_strategy_data.csv"
MODEL_DIR = "app/ml/models"
MODEL_PATH = os.path.join(MODEL_DIR, "pit_model.joblib")

def train_pit_model():
    if not os.path.exists(DATA_PATH):
        print(f"Data file {DATA_PATH} not found. Run extract_pit_data.py first.")
        return

    print("Loading data...")
    df = pd.read_csv(DATA_PATH)

    # Encode categorical features
    df['tire_compound_code'] = df['tire_compound'].astype('category').cat.codes
    df['team_code'] = df['team'].astype('category').cat.codes

    # Feature columns
    feature_cols = [
        "lap", "position", "tire_age", "tire_wear", "tire_compound_code",
        "gap_to_ahead", "sc_active", "vsc_active", "pit_stops", "team_code"
    ]
    
    X = df[feature_cols]
    y = df['pit_next_lap']

    print(f"Training on {len(df)} samples with {len(feature_cols)} features...")
    print(f"Class distribution: {y.value_counts().to_dict()}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Since pitting is rare (imbalanced classes), we use class_weight='balanced'
    model = lgb.LGBMClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.05,
        class_weight='balanced',
        random_state=42,
        verbose=-1
    )

    print("Training LightGBM model for Pit Strategy...")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    
    # Evaluate model
    print("\n--- Model Evaluation ---")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # Feature Importance
    print("\n--- Feature Importance ---")
    importances = list(zip(feature_cols, model.feature_importances_))
    importances.sort(key=lambda x: x[1], reverse=True)
    for feat, imp in importances:
        print(f"  {feat}: {imp}")

    # Save model
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_pit_model()
