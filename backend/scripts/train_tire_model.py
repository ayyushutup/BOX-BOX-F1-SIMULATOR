import os
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
import joblib

def train_tire_mlp():
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'app', 'ml', 'data')
    csv_path = os.path.join(data_dir, 'tire_training_data.csv')
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'app', 'ml', 'models')
    model_path = os.path.join(model_dir, 'tire_mlp.joblib')
    
    if not os.path.exists(csv_path):
        print("Data not found. Did you run generate_tire_data.py?")
        return

    print("Loading synthetic data...")
    df = pd.read_csv(csv_path)

    # Features (X)
    feature_cols = [
        "compound", "track_temp", "track_abrasiveness", 
        "driver_push_level", "lap_number", "current_wear", "current_temp"
    ]
    X = df[feature_cols]

    # Targets (y)
    target_cols = ["delta_wear", "delta_temp", "lap_time_penalty"]
    y = df[target_cols]

    print(f"Dataset size: {len(df)} samples")

    # Preprocessing
    categorical_cols = ["compound"]
    numeric_cols = [
        "track_temp", "track_abrasiveness", "driver_push_level", 
        "lap_number", "current_wear", "current_temp"
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols)
        ]
    )

    # MLP Pipeline
    # Using a 64x64 hidden layer setup.
    # It learns the non-linear "cliff" and thermodynamic rules embedded by the physics engine.
    mlp = MLPRegressor(
        hidden_layer_sizes=(64, 64),
        activation='relu',
        solver='adam',
        max_iter=500,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.1
    )

    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('model', mlp)])

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training MLP (this might take a few seconds)...")
    pipeline.fit(X_train, y_train)

    # Evaluate
    score = pipeline.score(X_test, y_test)
    print(f"Test R^2 Score (predicting physics ground truth): {score:.4f}")

    # Save
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(pipeline, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_tire_mlp()
