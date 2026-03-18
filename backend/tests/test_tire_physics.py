import pytest
from app.simulation.tire_physics import TirePhysicsEngine

def test_tire_physics_initialization():
    engine = TirePhysicsEngine(track_abrasiveness=1.0, track_temp_celsius=40.0)
    state = engine.get_initial_state('SOFT')
    assert state['wear'] == 0.0
    assert 'temperature' in state
    assert state['compound'] == 'SOFT'

def test_soft_vs_hard_wear_rates():
    engine = TirePhysicsEngine()
    
    soft_state = engine.get_initial_state('SOFT')
    hard_state = engine.get_initial_state('HARD')
    
    # Simulate 5 racing laps identically
    for _ in range(5):
        soft_state = engine.simulate_lap(soft_state, driver_aggression=0.5, driver_smoothness=0.8)
        hard_state = engine.simulate_lap(hard_state, driver_aggression=0.5, driver_smoothness=0.8)
        
    assert soft_state['wear'] > hard_state['wear']

def test_dirty_air_overheating():
    engine = TirePhysicsEngine()
    
    clean_air = engine.get_initial_state('MEDIUM')
    dirty_air = engine.get_initial_state('MEDIUM')
    
    # Simulate 3 laps
    for _ in range(3):
        clean_air = engine.simulate_lap(clean_air, in_dirty_air=False)
        dirty_air = engine.simulate_lap(dirty_air, in_dirty_air=True)
        
    assert dirty_air['temperature'] > clean_air['temperature']

def test_the_cliff():
    engine = TirePhysicsEngine()
    state = engine.get_initial_state('SOFT')
    
    # State zero
    base_pace = engine.calculate_lap_time_penalty(state)
    
    # Push the tire to 65% wear (approaching cliff threshold of 0.70)
    state['wear'] = 0.65
    state['temperature'] = 105.0 # Perfect temp
    edge_pace = engine.calculate_lap_time_penalty(state)
    
    # Push it over the cliff
    state['wear'] = 0.85
    cliff_pace = engine.calculate_lap_time_penalty(state)
    
    # Edge pace should be slower than new
    assert edge_pace > base_pace
    
    # Cliff pace should be massively slower than edge pace (non-linear jump)
    assert (cliff_pace - edge_pace) > (edge_pace - base_pace) * 3 
