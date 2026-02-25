import pytest
from app.scenarios.types import ScenarioConfig, RaceStructureConfig, GridCarConfig, ChaosConfig, DriverPersonalityConfig
from app.scenarios.compiler import compile_scenario
from app.models.race_state import TireCompound, RaceControl

def test_compile_scenario_base():
    config = ScenarioConfig(
        seed=123,
        race_structure=RaceStructureConfig(
            track_id="monaco",
            total_laps=10,
            starting_lap=0,
            grid=[
                GridCarConfig(
                    driver="VER",
                    team="Red Bull Racing",
                    position=1,
                    tire_compound=TireCompound.SOFT
                ),
                GridCarConfig(
                    driver="HAM",
                    team="Mercedes",
                    position=2,
                    tire_compound=TireCompound.MEDIUM
                )
            ],
            sc_enabled=True,
            drs_enabled=True,
        ),
        chaos=ChaosConfig(
            incident_frequency=2.0,
            safety_car_probability=1.5
        ),
        drivers={
            "VER": DriverPersonalityConfig(driver_id="VER", aggression=1.5),
            "HAM": DriverPersonalityConfig(driver_id="HAM", aggression=0.8)
        }
    )

    state = compile_scenario(config)

    assert state.meta.seed == 123
    assert state.meta.laps_total == 10
    assert len(state.cars) == 2
    
    ver = next(c for c in state.cars if c.identity.driver == "VER")
    ham = next(c for c in state.cars if c.identity.driver == "HAM")
    
    assert ver.timing.position == 1
    assert ham.timing.position == 2
    assert ver.telemetry.tire_state.compound == TireCompound.SOFT
    assert ham.telemetry.tire_state.compound == TireCompound.MEDIUM
    
    # Check that chaos modifiers scaled track props
    assert state.track.chaos_level > 0
    # Make sure aggression altered skills differently
    assert ver.driver_skill > ham.driver_skill
    assert state.race_control == RaceControl.GREEN
