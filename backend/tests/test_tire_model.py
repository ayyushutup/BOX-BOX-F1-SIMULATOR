import pytest
from app.ml.tire_model import NeuralTireModel

def test_tire_model_softs_degrade_faster():
    model = NeuralTireModel(track_abrasiveness=1.0, track_temp_celsius=35.0)
    
    # Same inputs, just different compounds
    delta_wear_s, delta_temp_s, soft_penalty = model.predict_degradation(
        compound="SOFT", track_temp=35.0, track_abrasiveness=1.0, 
        driver_push_level=0.8, lap_number=15, current_wear=0.5, current_temp=105.0
    )
    
    delta_wear_m, delta_temp_m, medium_penalty = model.predict_degradation(
        compound="MEDIUM", track_temp=35.0, track_abrasiveness=1.0, 
        driver_push_level=0.8, lap_number=15, current_wear=0.5, current_temp=105.0
    )
    
    # Softs actually generally have a LOWER initial pace penalty at 50% wear than 50% wear Mediums?
    # Actually wait we just want to verify they wear *faster* in a lap.
    assert delta_wear_s > delta_wear_m, "Softs should wear faster per lap than Mediums"

def test_tire_model_cliff():
    model = NeuralTireModel(track_abrasiveness=1.0, track_temp_celsius=35.0)
    
    # 60% wear (pre cliff for SOFT = 0.70)
    _, _, ok_penalty = model.predict_degradation(
        compound="SOFT", track_temp=35.0, track_abrasiveness=1.0, 
        driver_push_level=0.8, lap_number=15, current_wear=0.6, current_temp=105.0
    )

    # 85% wear (well past cliff)
    _, _, cliff_penalty = model.predict_degradation(
        compound="SOFT", track_temp=35.0, track_abrasiveness=1.0, 
        driver_push_level=0.8, lap_number=20, current_wear=0.85, current_temp=105.0
    )
    
    assert cliff_penalty > ok_penalty * 3.0, "Penalty should explode past the cliff threshold"

def test_aggression_accelerates_overheat():
    model = NeuralTireModel(track_abrasiveness=1.0, track_temp_celsius=35.0)
    
    delta_wear_low, delta_temp_low, _ = model.predict_degradation(
        compound="MEDIUM", track_temp=40.0, track_abrasiveness=1.0, 
        driver_push_level=0.1, lap_number=5, current_wear=0.1, current_temp=110.0
    )
    
    delta_wear_high, delta_temp_high, _ = model.predict_degradation(
        compound="MEDIUM", track_temp=40.0, track_abrasiveness=1.0, 
        driver_push_level=1.0, lap_number=5, current_wear=0.1, current_temp=110.0
    )
    
    assert delta_temp_high > delta_temp_low, "Higher aggression should generate more heat"
    assert delta_wear_high > delta_wear_low, "Higher aggression should generate more lap wear"
