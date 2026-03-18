import pytest
import numpy as np
from app.ml.state_estimator import (
    DriverStateEstimator,
    RaceStateAssimilator,
    IDX_TIRE_WEAR, IDX_TIRE_TEMP, IDX_FUEL_LOAD,
    IDX_PACE_OFFSET, IDX_PUSH_LEVEL, IDX_RELIABILITY,
)


class TestDriverStateEstimator:
    def test_initial_state(self):
        est = DriverStateEstimator("VER", initial_fuel=105.0)
        state = est.get_state()
        assert state["tire_wear"] == 0.0
        assert state["fuel_load"] == 105.0
        assert state["reliability"] == 1.0

    def test_predict_increases_tire_wear(self):
        est = DriverStateEstimator("VER")
        initial_wear = est.x[IDX_TIRE_WEAR]
        est.predict(compound="SOFT")
        assert est.x[IDX_TIRE_WEAR] > initial_wear

    def test_predict_decreases_fuel(self):
        est = DriverStateEstimator("VER", initial_fuel=100.0)
        initial_fuel = est.x[IDX_FUEL_LOAD]
        est.predict()
        assert est.x[IDX_FUEL_LOAD] < initial_fuel

    def test_soft_wears_faster_than_hard(self):
        est_soft = DriverStateEstimator("VER")
        est_hard = DriverStateEstimator("HAM")
        
        for _ in range(10):
            est_soft.predict(compound="SOFT")
            est_hard.predict(compound="HARD")
        
        assert est_soft.x[IDX_TIRE_WEAR] > est_hard.x[IDX_TIRE_WEAR]

    def test_sc_reduces_wear(self):
        est_normal = DriverStateEstimator("VER")
        est_sc = DriverStateEstimator("HAM")
        
        for _ in range(5):
            est_normal.predict(compound="MEDIUM")
            est_sc.predict(compound="MEDIUM", sc_active=True)
        
        assert est_sc.x[IDX_TIRE_WEAR] < est_normal.x[IDX_TIRE_WEAR]

    def test_reliability_slowly_degrades(self):
        est = DriverStateEstimator("VER")
        for _ in range(20):
            est.predict()
        assert est.x[IDX_RELIABILITY] < 1.0


class TestKalmanUpdate:
    def test_lap_time_corrects_pace_offset(self):
        """If observed lap time is faster than expected, pace_offset should decrease."""
        est = DriverStateEstimator("VER")
        est.predict()
        
        # Get expected lap time
        expected = est._expected_lap_time()
        
        # Observe a FASTER lap time (0.5s faster)
        est.update(lap_time=expected - 0.5)
        
        # Pace offset should have been corrected toward negative (faster)
        assert est.x[IDX_PACE_OFFSET] < 0.0

    def test_reported_wear_corrects_state(self):
        est = DriverStateEstimator("VER")
        # Predict a few laps
        for _ in range(5):
            est.predict(compound="SOFT")
        
        # Force-observe specific wear level
        est.update(reported_wear=0.3)
        
        # Tire wear should move toward observed value
        assert abs(est.x[IDX_TIRE_WEAR] - 0.3) < abs(0.125 - 0.3)  # Closer to 0.3 than uninformed

    def test_fuel_observation_corrects_state(self):
        est = DriverStateEstimator("VER", initial_fuel=100.0)
        for _ in range(10):
            est.predict()
        
        predicted_fuel = est.x[IDX_FUEL_LOAD]
        # Observe fuel level that's different from predicted
        est.update(reported_fuel=predicted_fuel + 3.0)
        
        # Fuel should move toward observation
        assert est.x[IDX_FUEL_LOAD] > predicted_fuel

    def test_convergence_over_laps(self):
        """Filter should converge toward true pace offset with repeated observations."""
        est = DriverStateEstimator("VER")
        true_pace_offset = -0.3  # Driver is actually 0.3s faster
        
        for lap in range(20):
            est.predict()
            # Simulate observed lap time with the true pace offset
            expected_base = est._expected_lap_time() - est.x[IDX_PACE_OFFSET]  # Remove model's estimate
            observed = expected_base + true_pace_offset + np.random.normal(0, 0.1)
            est.update(lap_time=observed)
        
        # After 20 laps, pace should have converged reasonably close
        assert abs(est.x[IDX_PACE_OFFSET] - true_pace_offset) < 0.5

    def test_uncertainty_decreases_with_observations(self):
        est = DriverStateEstimator("VER")
        initial_uncertainty = est.P[IDX_PACE_OFFSET, IDX_PACE_OFFSET]
        
        for _ in range(10):
            est.predict()
            est.update(lap_time=est._expected_lap_time() + 0.1)
        
        final_uncertainty = est.P[IDX_PACE_OFFSET, IDX_PACE_OFFSET]
        assert final_uncertainty < initial_uncertainty


class TestResetTires:
    def test_pit_stop_resets_wear(self):
        est = DriverStateEstimator("VER")
        for _ in range(15):
            est.predict(compound="SOFT")
        
        assert est.x[IDX_TIRE_WEAR] > 0.2  # Significant wear
        est.reset_tires("MEDIUM")
        assert est.x[IDX_TIRE_WEAR] == 0.0
        assert est.x[IDX_TIRE_TEMP] == 70.0


class TestGetState:
    def test_returns_all_fields(self):
        est = DriverStateEstimator("VER")
        state = est.get_state()
        
        required_fields = [
            "tire_wear", "tire_temp", "fuel_load",
            "pace_offset", "push_level", "reliability",
            "tire_wear_uncertainty", "pace_offset_uncertainty",
            "reliability_uncertainty",
        ]
        for field in required_fields:
            assert field in state

    def test_pace_correction_return(self):
        est = DriverStateEstimator("VER")
        assert est.get_pace_correction() == 0.0


class TestRaceStateAssimilator:
    def test_creates_estimators_per_driver(self):
        assimilator = RaceStateAssimilator()
        # Manually create estimators
        est1 = assimilator._get_or_create("VER")
        est2 = assimilator._get_or_create("HAM")
        
        assert "VER" in assimilator.estimators
        assert "HAM" in assimilator.estimators
        assert len(assimilator.estimators) == 2

    def test_get_corrected_states(self):
        assimilator = RaceStateAssimilator()
        assimilator._get_or_create("VER")
        assimilator._get_or_create("HAM")
        
        states = assimilator.get_corrected_states()
        assert "VER" in states
        assert "HAM" in states
        assert "tire_wear" in states["VER"]

    def test_get_pace_corrections(self):
        assimilator = RaceStateAssimilator()
        assimilator._get_or_create("VER")
        
        corrections = assimilator.get_pace_corrections()
        assert "VER" in corrections
        assert corrections["VER"] == 0.0  # Initial state
