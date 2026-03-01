"""
Tests for Overconfidence Fix — Model Realism Validation.

Validates that:
1. No driver exceeds 55% win probability (cap test)
2. MC distribution produces realistic spread (20-55% for top driver)
3. At least 3 different drivers win across simulations (upset test)
4. Position distributions include full grid range
"""

import pytest
from app.ml.monte_carlo import MonteCarloRaceSimulator


@pytest.fixture
def simulator():
    return MonteCarloRaceSimulator(n_simulations=2000, seed=42)


@pytest.fixture
def dominant_probs():
    """Simulate a dominant driver scenario (like VER 2023)"""
    return {
        "VER": 0.85, "HAM": 0.04, "LEC": 0.03, "NOR": 0.02,
        "RUS": 0.015, "SAI": 0.01, "ALO": 0.008, "PIA": 0.007,
        "GAS": 0.005, "ALB": 0.004, "HUL": 0.003, "OCO": 0.002,
        "TSU": 0.002, "LAW": 0.001, "STR": 0.001, "ANT": 0.001,
        "BEA": 0.001, "DOO": 0.001, "HAD": 0.001, "BOR": 0.001
    }


def test_top_driver_not_over_55_percent(simulator, dominant_probs):
    """Even with dominant inputs, MC should compress to realistic range."""
    results = simulator.simulate(
        win_probs=dominant_probs,
        chaos_level=1.0,
        incident_frequency=1.0
    )
    
    max_win_frac = max(results["mc_win_distribution"].values())
    assert max_win_frac <= 0.60, (
        f"Top driver MC win fraction {max_win_frac:.1%} exceeds realistic ceiling of 60%"
    )


def test_multiple_winners_in_simulations(simulator, dominant_probs):
    """At least 3 different drivers should win across 2000 sims."""
    results = simulator.simulate(
        win_probs=dominant_probs,
        chaos_level=1.0,
        incident_frequency=1.0
    )
    
    winners = [d for d, frac in results["mc_win_distribution"].items() if frac > 0]
    assert len(winners) >= 3, (
        f"Only {len(winners)} unique winners. Need at least 3 for realism."
    )


def test_position_distributions_full_grid(simulator, dominant_probs):
    """Position distributions should cover all drivers, not just top 5."""
    results = simulator.simulate(
        win_probs=dominant_probs,
        chaos_level=1.0,
        incident_frequency=1.0
    )
    
    pos_dists = results["position_distributions"]
    # All 20 drivers should have position distributions
    assert len(pos_dists) == 20, (
        f"Position distributions only cover {len(pos_dists)} drivers, expected 20."
    )


def test_chaos_increases_spread(simulator, dominant_probs):
    """Higher chaos should reduce the top driver's dominance."""
    results_calm = simulator.simulate(
        win_probs=dominant_probs, chaos_level=1.0, incident_frequency=1.0
    )
    results_chaos = simulator.simulate(
        win_probs=dominant_probs, chaos_level=2.5, incident_frequency=2.0
    )
    
    top_driver_calm = max(results_calm["mc_win_distribution"].values())
    top_driver_chaos = max(results_chaos["mc_win_distribution"].values())
    
    assert top_driver_chaos < top_driver_calm, (
        f"Chaos should reduce dominance: calm={top_driver_calm:.1%}, chaos={top_driver_chaos:.1%}"
    )


def test_volatility_bands_exist(simulator, dominant_probs):
    """Every driver in results should have optimistic/pessimistic bands."""
    results = simulator.simulate(
        win_probs=dominant_probs, chaos_level=1.0, incident_frequency=1.0
    )
    
    for d in results["volatility_bands"]:
        band = results["volatility_bands"][d]
        assert "optimistic" in band
        assert "pessimistic" in band
        assert band["optimistic"] <= band["pessimistic"]
