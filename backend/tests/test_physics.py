"""
Tests for all the physics stuff - dirty air, DRS, ERS, slipstream, driving modes etc
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.simulation.physics import (
    calculate_dirty_air_penalty, calculate_speed, calculate_tire_wear,
    calculate_fuel_consumption, can_activate_drs, is_in_drs_zone,
    calculate_drs_boost, calculate_slipstream_boost,
    calculate_ers_deployment, calculate_ers_harvest,
    should_yield_for_blue_flag, calculate_blue_flag_penalty,
    BASE_SPEED, DIRTY_AIR_RANGE, DIRTY_AIR_CORNER_PENALTY,
    DRS_SPEED_BOOST, ERS_SPEED_BOOST, ERS_MAX_BATTERY, ERS_DEPLOY_RATE,
    SLIPSTREAM_MAX_BOOST,
)
from app.simulation.rng import SeededRNG


# --- dirty air ---

class TestDirtyAir:
    def test_no_penalty_far_away(self):
        # 3s gap, should be clean air
        penalty = calculate_dirty_air_penalty(gap_to_car_ahead=3.0, sector_type="SLOW")
        assert penalty == 0.0

    def test_penalty_in_corners(self):
        penalty = calculate_dirty_air_penalty(gap_to_car_ahead=0.5, sector_type="SLOW")
        assert penalty > 0.0
        assert penalty <= DIRTY_AIR_CORNER_PENALTY

    def test_no_penalty_on_straights(self):
        # slipstream handles straights, dirty air shouldn't apply
        penalty = calculate_dirty_air_penalty(gap_to_car_ahead=0.5, sector_type="FAST")
        assert penalty == 0.0

    def test_closer_means_worse(self):
        far = calculate_dirty_air_penalty(gap_to_car_ahead=1.5, sector_type="SLOW")
        close = calculate_dirty_air_penalty(gap_to_car_ahead=0.3, sector_type="SLOW")
        assert close > far

    def test_medium_sector_gets_80pct(self):
        slow_p = calculate_dirty_air_penalty(1.0, "SLOW")
        med_p = calculate_dirty_air_penalty(1.0, "MEDIUM")
        assert med_p == pytest.approx(slow_p * 0.8, rel=1e-6)


# --- driving modes ---

class TestDrivingModes:
    def test_push_faster(self):
        rng1, rng2 = SeededRNG(42), SeededRNG(42)
        push = calculate_speed(200.0, 0.3, 50.0, 0.95, rng1, driving_mode="PUSH")
        balanced = calculate_speed(200.0, 0.3, 50.0, 0.95, rng2, driving_mode="BALANCED")
        assert push > balanced

    def test_conserve_slower(self):
        rng1, rng2 = SeededRNG(42), SeededRNG(42)
        conserve = calculate_speed(200.0, 0.3, 50.0, 0.95, rng1, driving_mode="CONSERVE")
        balanced = calculate_speed(200.0, 0.3, 50.0, 0.95, rng2, driving_mode="BALANCED")
        assert conserve < balanced

    def test_push_wears_tires_more(self):
        rng1, rng2 = SeededRNG(42), SeededRNG(42)
        push_w = calculate_tire_wear(0.3, "MEDIUM", rng1, driving_mode="PUSH")
        bal_w = calculate_tire_wear(0.3, "MEDIUM", rng2, driving_mode="BALANCED")
        assert push_w > bal_w

    def test_conserve_saves_tires(self):
        rng1, rng2 = SeededRNG(42), SeededRNG(42)
        con_w = calculate_tire_wear(0.3, "MEDIUM", rng1, driving_mode="CONSERVE")
        bal_w = calculate_tire_wear(0.3, "MEDIUM", rng2, driving_mode="BALANCED")
        assert con_w < bal_w

    def test_push_burns_more_fuel(self):
        push_f = calculate_fuel_consumption(50.0, driving_mode="PUSH")
        bal_f = calculate_fuel_consumption(50.0, driving_mode="BALANCED")
        assert push_f < bal_f  # less remaining = more consumed

    def test_conserve_saves_fuel(self):
        con_f = calculate_fuel_consumption(50.0, driving_mode="CONSERVE")
        bal_f = calculate_fuel_consumption(50.0, driving_mode="BALANCED")
        assert con_f > bal_f


# --- DRS ---

def _make_zone(start, end):
    """quick helper for DRS zone objects"""
    class Z:
        pass
    z = Z()
    z.start = start
    z.end = end
    return z

class TestDRS:
    def test_activates_when_close_in_zone(self):
        zones = [_make_zone(0.5, 0.7)]
        assert can_activate_drs(0.6, 0.8, zones, 0.0) == True

    def test_no_drs_in_rain(self):
        zones = [_make_zone(0.5, 0.7)]
        assert can_activate_drs(0.6, 0.5, zones, 0.5) == False

    def test_no_drs_under_sc(self):
        zones = [_make_zone(0.5, 0.7)]
        assert can_activate_drs(0.6, 0.5, zones, 0.0, sc_active=True) == False

    def test_no_drs_gap_too_big(self):
        zones = [_make_zone(0.5, 0.7)]
        # 1.5s gap, needs to be under 1s
        assert can_activate_drs(0.6, 1.5, zones, 0.0) == False

    def test_no_drs_outside_zone(self):
        zones = [_make_zone(0.5, 0.7)]
        assert can_activate_drs(0.2, 0.5, zones, 0.0) == False

    def test_boost_values(self):
        assert calculate_drs_boost(True) == DRS_SPEED_BOOST
        assert calculate_drs_boost(False) == 0.0


# --- slipstream ---

class TestSlipstream:
    def test_boost_on_straight(self):
        boost = calculate_slipstream_boost(0.1, "FAST")
        assert 0 < boost <= SLIPSTREAM_MAX_BOOST

    def test_no_boost_too_far(self):
        assert calculate_slipstream_boost(1.0, "FAST") == 0.0

    def test_less_in_corners(self):
        straight = calculate_slipstream_boost(0.2, "FAST")
        corner = calculate_slipstream_boost(0.2, "SLOW")
        assert corner < straight


# --- ERS ---

class TestERS:
    def test_deploys_on_fast(self):
        batt, boost, deploying = calculate_ers_deployment(2.0, "FAST", False)
        assert boost == ERS_SPEED_BOOST
        assert deploying
        assert batt < 2.0

    def test_wont_deploy_slow_sector(self):
        _, boost, dep = calculate_ers_deployment(2.0, "SLOW", False)
        assert boost == 0.0 and not dep

    def test_wont_deploy_empty_battery(self):
        _, boost, dep = calculate_ers_deployment(0.05, "FAST", False)
        assert boost == 0.0

    def test_harvests_in_braking(self):
        new_batt = calculate_ers_harvest(1.0, "SLOW")
        assert new_batt > 1.0

    def test_no_harvest_on_straight(self):
        assert calculate_ers_harvest(1.0, "FAST") == 1.0

    def test_cant_exceed_max(self):
        assert calculate_ers_harvest(ERS_MAX_BATTERY - 0.001, "SLOW") <= ERS_MAX_BATTERY


# --- blue flags ---

def test_yield_when_lapped():
    assert should_yield_for_blue_flag(car_lap=3, leader_lap=4)
    assert should_yield_for_blue_flag(car_lap=3, leader_lap=5)

def test_no_yield_same_lap():
    assert not should_yield_for_blue_flag(3, 3)

def test_blue_flag_penalty():
    assert calculate_blue_flag_penalty() == 0.10


# --- tire wear edge cases ---

class TestTireWear:
    def test_softs_wear_faster(self):
        rng1, rng2 = SeededRNG(99), SeededRNG(99)
        soft = calculate_tire_wear(0.2, "SOFT", rng1)
        hard = calculate_tire_wear(0.2, "HARD", rng2)
        assert soft > hard

    def test_cliff_effect(self):
        # tires over 50% should degrade faster
        rng1, rng2 = SeededRNG(42), SeededRNG(42)
        fresh_delta = calculate_tire_wear(0.2, "MEDIUM", rng1) - 0.2
        worn_delta = calculate_tire_wear(0.6, "MEDIUM", rng2) - 0.6
        assert worn_delta > fresh_delta

    def test_capped_at_100(self):
        rng = SeededRNG(42)
        assert calculate_tire_wear(0.99, "SOFT", rng) <= 1.0


# --- speed calculation ---

class TestSpeed:
    def test_minimum_speed(self):
        # even worst conditions should give at least 50kph
        rng = SeededRNG(42)
        speed = calculate_speed(120.0, 1.0, 100.0, 0.90, rng, rain_probability=0.9)
        assert speed >= 50.0

    def test_skill_matters(self):
        rng1, rng2 = SeededRNG(42), SeededRNG(42)
        fast = calculate_speed(200.0, 0.3, 50.0, 0.99, rng1)
        slow = calculate_speed(200.0, 0.3, 50.0, 0.91, rng2)
        assert fast > slow

    def test_dirty_air_slows_you_down(self):
        rng1, rng2 = SeededRNG(42), SeededRNG(42)
        clean = calculate_speed(200.0, 0.3, 50.0, 0.95, rng1, dirty_air_penalty=0.0)
        dirty = calculate_speed(200.0, 0.3, 50.0, 0.95, rng2, dirty_air_penalty=0.1)
        assert dirty < clean
