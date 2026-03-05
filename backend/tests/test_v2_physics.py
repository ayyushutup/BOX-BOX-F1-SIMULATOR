"""
Tests for Box-Box v2 physics upgrades:
- Dirty Air 3-Layer Model
- Track Evolution (rubber buildup + grip)
- Driver Momentum
"""

import pytest
import math
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.simulation.physics import (
    calculate_dirty_air_factor, calculate_dirty_air_penalty,
    calculate_dirty_air_tire_effect, calculate_dirty_air_mistake_effect,
    calculate_track_grip, update_rubber_level,
    calculate_momentum_effect, calculate_tire_wear,
    DIRTY_AIR_RANGE, DIRTY_AIR_CORNER_PENALTY,
    DIRTY_AIR_TIRE_COEFF, DIRTY_AIR_MISTAKE_COEFF,
    TRACK_GRIP_MAX,
)
from app.simulation.rng import SeededRNG


# =====================================================================
# DIRTY AIR FACTOR (Exponential Decay)
# =====================================================================

class TestDirtyAirFactor:
    def test_zero_gap_gives_max_factor(self):
        """Bumper-to-bumper should give maximum dirty air."""
        assert calculate_dirty_air_factor(0.0) == 1.0

    def test_beyond_range_is_clean(self):
        """Outside dirty air range should give no effect."""
        assert calculate_dirty_air_factor(DIRTY_AIR_RANGE) == 0.0
        assert calculate_dirty_air_factor(3.0) == 0.0

    def test_exponential_decay(self):
        """Factor should follow exp(-gap/0.8) decay pattern."""
        factor_05 = calculate_dirty_air_factor(0.5)
        factor_10 = calculate_dirty_air_factor(1.0)
        factor_15 = calculate_dirty_air_factor(1.5)
        
        # Values should decrease exponentially
        assert factor_05 > factor_10 > factor_15
        
        # Verify approximate exponential values
        assert factor_05 == pytest.approx(math.exp(-0.5 / 0.8), rel=1e-4)
        assert factor_10 == pytest.approx(math.exp(-1.0 / 0.8), rel=1e-4)

    def test_factor_always_between_0_and_1(self):
        """Factor should be bounded [0, 1]."""
        for gap in [0.0, 0.1, 0.3, 0.5, 0.8, 1.0, 1.5, 2.0, 5.0]:
            factor = calculate_dirty_air_factor(gap)
            assert 0.0 <= factor <= 1.0

    def test_closer_is_worse(self):
        """Closer gap should always produce higher dirty air factor."""
        for gap in [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4]:
            close = calculate_dirty_air_factor(gap)
            far = calculate_dirty_air_factor(gap + 0.2)
            assert close >= far


# =====================================================================
# DIRTY AIR — TIRE OVERHEATING (Layer 2)
# =====================================================================

class TestDirtyAirTireEffect:
    def test_no_effect_in_clean_air(self):
        """Zero dirty air factor should not affect tires."""
        assert calculate_dirty_air_tire_effect(0.0) == 1.0

    def test_max_effect_at_full_dirty_air(self):
        """Full dirty air should increase deg by DIRTY_AIR_TIRE_COEFF."""
        expected = 1.0 + DIRTY_AIR_TIRE_COEFF
        assert calculate_dirty_air_tire_effect(1.0) == pytest.approx(expected)

    def test_linear_scaling(self):
        """Tire effect should scale linearly with factor."""
        half = calculate_dirty_air_tire_effect(0.5)
        expected = 1.0 + DIRTY_AIR_TIRE_COEFF * 0.5
        assert half == pytest.approx(expected)

    def test_clamped_to_valid_range(self):
        """Negative or >1 factors should be clamped."""
        assert calculate_dirty_air_tire_effect(-0.5) == 1.0
        assert calculate_dirty_air_tire_effect(1.5) == pytest.approx(1.0 + DIRTY_AIR_TIRE_COEFF)

    def test_tire_wear_higher_in_dirty_air(self):
        """Tire wear with dirty air should be worse than clean air."""
        rng1, rng2 = SeededRNG(42), SeededRNG(42)
        clean_wear = calculate_tire_wear(0.3, "MEDIUM", rng1, dirty_air_factor=0.0)
        dirty_wear = calculate_tire_wear(0.3, "MEDIUM", rng2, dirty_air_factor=0.8)
        assert dirty_wear > clean_wear


# =====================================================================
# DIRTY AIR — MISTAKE EFFECT (Layer 3)
# =====================================================================

class TestDirtyAirMistakeEffect:
    def test_no_effect_in_clean_air(self):
        assert calculate_dirty_air_mistake_effect(0.0) == 1.0

    def test_max_effect_at_full_dirty_air(self):
        expected = 1.0 + DIRTY_AIR_MISTAKE_COEFF
        assert calculate_dirty_air_mistake_effect(1.0) == pytest.approx(expected)

    def test_moderate_dirty_air(self):
        """0.5 factor should give half the mistake increase."""
        result = calculate_dirty_air_mistake_effect(0.5)
        assert result == pytest.approx(1.0 + DIRTY_AIR_MISTAKE_COEFF * 0.5)


# =====================================================================
# TRACK EVOLUTION
# =====================================================================

class TestTrackEvolution:
    def test_base_grip_at_zero_rubber(self):
        """No rubber should give base grip level."""
        assert calculate_track_grip(1.0, 0.0) == 1.0

    def test_grip_increases_with_rubber(self):
        """Rubber buildup should increase grip."""
        low = calculate_track_grip(1.0, 0.02)
        high = calculate_track_grip(1.0, 0.10)
        assert high > low > 1.0

    def test_grip_capped_at_maximum(self):
        """Grip should never exceed TRACK_GRIP_MAX."""
        grip = calculate_track_grip(1.0, 0.50)
        assert grip <= TRACK_GRIP_MAX

    def test_grip_has_minimum(self):
        """Grip should not go below 0.8 even with bad base."""
        grip = calculate_track_grip(0.5, 0.0)
        assert grip >= 0.8

    def test_rubber_buildup_increases_over_laps(self):
        """Rubber level should increase each lap."""
        rubber = 0.0
        for _ in range(20):
            rubber = update_rubber_level(rubber, cars_on_track=20)
        assert rubber > 0

    def test_rain_resets_rubber(self):
        """Heavy rain should wash away most rubber."""
        rubber = update_rubber_level(0.10, rain_probability=0.8)
        assert rubber < 0.02  # Near-complete reset

    def test_light_rain_doesnt_reset(self):
        """Light rain should not reset rubber."""
        rubber = update_rubber_level(0.10, rain_probability=0.3)
        assert rubber >= 0.10  # Still builds up

    def test_rubber_capped(self):
        """Rubber should not exceed 0.15."""
        rubber = 0.0
        for _ in range(1000):
            rubber = update_rubber_level(rubber, cars_on_track=20)
        assert rubber <= 0.15


# =====================================================================
# DRIVER MOMENTUM
# =====================================================================

class TestMomentum:
    def test_neutral_momentum(self):
        """Zero momentum should give zero modifiers."""
        effects = calculate_momentum_effect(0.0)
        assert effects["aggression_mod"] == 0.0
        assert effects["mistake_mod"] == 0.0

    def test_positive_momentum_reduces_mistakes(self):
        """Positive momentum (on fire) should reduce mistake probability."""
        effects = calculate_momentum_effect(0.8)
        assert effects["aggression_mod"] > 0  # More aggressive
        assert effects["mistake_mod"] < 0     # Fewer mistakes

    def test_negative_momentum_increases_both(self):
        """Negative momentum (tilting) should increase aggression AND mistakes."""
        effects = calculate_momentum_effect(-0.8)
        assert effects["aggression_mod"] > 0  # Desperate aggression
        assert effects["mistake_mod"] > 0     # More mistakes (tilting)

    def test_momentum_clamped(self):
        """Effects should work even with extreme inputs."""
        effects_high = calculate_momentum_effect(5.0)  # Should be clamped to 1.0
        effects_low = calculate_momentum_effect(-5.0)  # Should be clamped to -1.0
        # Should not crash and should give bounded results
        assert -1.0 <= effects_high["mistake_mod"] <= 1.0
        assert -1.0 <= effects_low["mistake_mod"] <= 1.0

    def test_max_positive_momentum(self):
        effects = calculate_momentum_effect(1.0)
        assert effects["aggression_mod"] == pytest.approx(0.2)
        assert effects["mistake_mod"] == pytest.approx(-0.1)
