import os
import sys
# Ensure environment path is set for app imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.callbacks import EvalCallback

from app.ml.env import F1RaceEnv

MODEL_DIR = "app/ml/models"
MODEL_PATH = os.path.join(MODEL_DIR, "ppo_f1_driver")

def train_rl_agent():
    print("Setting up F1 Race Environment (Monza Synthetic)...")
    env = F1RaceEnv(track_id="monza")
    
    print("Checking environment compatibility with Stable-Baselines3...")
    check_env(env)
    
    print("Environment OK. Starting PPO Training...")
    
    # Using a small MLP policy since our observation space is simple
    model = PPO(
        "MlpPolicy", 
        env, 
        learning_rate=0.0003,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        verbose=1,
        tensorboard_log="./ppo_f1_tensorboard/"
    )
    
    eval_callback = EvalCallback(
        env, 
        best_model_save_path=MODEL_DIR,
        log_path=MODEL_DIR, 
        eval_freq=5000,
        deterministic=True, 
        render=False
    )
    
    print(f"Training agent for 15,000 timesteps...")
    # Short train just to ensure the pipeline functions correctly
    model.learn(total_timesteps=15000, callback=eval_callback, progress_bar=False)
    
    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save(MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}.zip")
    
    print("\nEvaluating trained policy...")
    mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=5)
    print(f"Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")

if __name__ == "__main__":
    train_rl_agent()
