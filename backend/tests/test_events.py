"""
test event generation - overtakes, dnf, fastest lap
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.race_state import (
    RaceState, Car, TireState, TireCompound, CarStatus,
    EventType, Meta, DrivingMode,
    CarIdentity, CarTelemetry, CarSystems, CarStrategy, CarTiming
)
from app.simulation.engine import recalculate_positions, create_dnf
from app.simulation.data import TRACKS


def _car(driver, position, lap, progress, **kwargs):
    """shorthand to build a Car without all the boilerplate"""
    return Car(
        identity=CarIdentity(driver=driver, team="Test Team"),
        telemetry=CarTelemetry(
            speed=kwargs.get('speed', 200.0),
            fuel=50.0,
            lap_progress=progress,
            tire_state=TireState(compound=TireCompound.MEDIUM, age=5, wear=0.3),
            dirty_air_effect=0.0,
        ),
        systems=CarSystems(),
        strategy=CarStrategy(),
        timing=CarTiming(
            position=position,
            lap=lap,
            sector=0,
            last_lap_time=kwargs.get('last_lap_time'),
            best_lap_time=kwargs.get('best_lap_time'),
            lap_start_tick=0,
        ),
        pit_stops=0,
        status=kwargs.get('status', CarStatus.RACING),
        driver_skill=0.95,
        in_pit_lane=False,
        pit_lane_progress=0.0,
    )


# -- overtakes --

class TestOvertakes:
    def test_basic_overtake(self):
        track = TRACKS["monaco"]
        old_pos = {"VER": 1, "HAM": 2}

        # HAM now ahead of VER
        cars = [
            _car("VER", 1, lap=3, progress=0.4),
            _car("HAM", 2, lap=3, progress=0.6),
        ]
        new_cars, events = recalculate_positions(cars, track, old_pos, tick=100, current_lap=3)

        ham = next(c for c in new_cars if c.identity.driver == "HAM")
        assert ham.timing.position == 1

        ot_events = [e for e in events if e.event_type == EventType.OVERTAKE]
        assert len(ot_events) >= 1
        assert "HAM" in ot_events[0].description

    def test_no_overtake_when_same(self):
        track = TRACKS["monaco"]
        old_pos = {"VER": 1, "HAM": 2}

        cars = [
            _car("VER", 1, lap=3, progress=0.6),
            _car("HAM", 2, lap=3, progress=0.4),
        ]
        _, events = recalculate_positions(cars, track, old_pos, tick=100, current_lap=3)
        assert len([e for e in events if e.event_type == EventType.OVERTAKE]) == 0

    def test_multi_car_overtake(self):
        track = TRACKS["monaco"]
        old_pos = {"VER": 1, "HAM": 2, "LEC": 3}

        # LEC jumps both
        cars = [
            _car("VER", 1, lap=3, progress=0.3),
            _car("HAM", 2, lap=3, progress=0.4),
            _car("LEC", 3, lap=3, progress=0.7),
        ]
        new_cars, events = recalculate_positions(cars, track, old_pos, tick=100, current_lap=3)

        lec = next(c for c in new_cars if c.identity.driver == "LEC")
        assert lec.timing.position == 1
        assert any(e.event_type == EventType.OVERTAKE for e in events)


# -- DNF --

def test_dnf_event_type():
    car = _car("VER", 1, lap=5, progress=0.5)
    _, event = create_dnf(car, tick=500, reason="Mechanical failure")
    assert event.event_type == EventType.DNF
    assert "VER" in event.description

def test_dnf_stops_car():
    car = _car("VER", 1, lap=5, progress=0.5)
    dnf_car, _ = create_dnf(car, tick=500, reason="Crashed")
    assert dnf_car.status == CarStatus.DNF
    assert dnf_car.telemetry.speed == 0.0


# -- fastest lap --

def test_fastest_lap_detection():
    cars = [
        _car("VER", 1, lap=5, progress=0.5, best_lap_time=82.3, last_lap_time=82.3),
        _car("HAM", 2, lap=5, progress=0.4, best_lap_time=83.0, last_lap_time=83.0),
        _car("LEC", 3, lap=5, progress=0.3, best_lap_time=84.0, last_lap_time=84.0),
    ]
    # VER should have fastest
    best = min(cars, key=lambda c: c.timing.best_lap_time or float('inf'))
    assert best.identity.driver == "VER"
    assert best.timing.best_lap_time == 82.3
