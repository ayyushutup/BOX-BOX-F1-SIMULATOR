
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.simulation.data import create_race_state
from app.simulation.engine import tick
from app.simulation.rng import SeededRNG

def test_weather():
    print("Initializing weather test...")
    state = create_race_state("spa", seed=123, laps=10)
    rng = SeededRNG(123)
    
    initial_weather = state.track.weather
    print(f"Initial Weather: Rain={initial_weather.rain_probability:.4f}, Temp={initial_weather.temperature:.2f}")
    
    print("\nSimulating 100 ticks...")
    for _ in range(100):
        state = tick(state, rng)
        
    final_weather = state.track.weather
    print(f"Final Weather:   Rain={final_weather.rain_probability:.4f}, Temp={final_weather.temperature:.2f}")
    
    rain_diff = abs(final_weather.rain_probability - initial_weather.rain_probability)
    temp_diff = abs(final_weather.temperature - initial_weather.temperature)
    
    if rain_diff > 0 or temp_diff > 0:
        print(f"\nSUCCESS: Weather changed! Rain delta: {rain_diff:.4f}, Temp delta: {temp_diff:.2f}")
    else:
        print("\nFAILURE: Weather did not change.")

if __name__ == "__main__":
    test_weather()
