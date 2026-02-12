"""Test that the simulation is deterministic."""

from app.simulation.data import create_race_state
from app.simulation.engine import tick
from app.simulation.rng import SeededRNG


def test_same_seed_same_race():
    """Same seed should produce identical race results."""
    
    # Run simulation with seed 42
    state1 = create_race_state(seed=42, laps=5)
    rng1 = SeededRNG(42)
    for _ in range(100):
        state1 = tick(state1, rng1)
    
    # Run simulation with same seed 42
    state2 = create_race_state(seed=42, laps=5)
    rng2 = SeededRNG(42)
    for _ in range(100):
        state2 = tick(state2, rng2)
    
    # They should be identical!
    assert state1.meta.tick == state2.meta.tick
    
    for car1, car2 in zip(state1.cars, state2.cars):
        assert car1.timing.lap == car2.timing.lap
        assert car1.telemetry.lap_progress == car2.telemetry.lap_progress
        assert car1.telemetry.speed == car2.telemetry.speed
        assert car1.telemetry.fuel == car2.telemetry.fuel


def test_different_seed_different_race():
    """Different seeds should produce different results."""
    
    state1 = create_race_state(seed=42, laps=5)
    rng1 = SeededRNG(42)
    for _ in range(100):
        state1 = tick(state1, rng1)
    
    state2 = create_race_state(seed=99, laps=5)
    rng2 = SeededRNG(99)
    for _ in range(100):
        state2 = tick(state2, rng2)
    
    # At least some cars should have different speeds
    different = False
    for car1, car2 in zip(state1.cars, state2.cars):
        if car1.telemetry.speed != car2.telemetry.speed:
            different = True
            break
    
    assert different, "Different seeds should produce different results!"