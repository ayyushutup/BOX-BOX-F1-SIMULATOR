import pytest
from app.ml.strategy_optimizer import StrategyOptimizer, StrategyCandidate


class TestStrategyCandidate:
    def test_label_format(self):
        c = StrategyCandidate(pit_laps=[20], compounds=["SOFT", "MEDIUM"])
        assert "1-stop" in c.label
        assert "S→M" in c.label

    def test_two_stop_label(self):
        c = StrategyCandidate(pit_laps=[15, 35], compounds=["SOFT", "MEDIUM", "HARD"])
        assert "2-stop" in c.label


class TestCandidateGeneration:
    def test_generates_candidates(self):
        opt = StrategyOptimizer()
        candidates = opt.generate_candidates(
            current_lap=5, total_laps=57, current_compound="SOFT", current_wear=0.15
        )
        assert len(candidates) > 0

    def test_includes_zero_stop(self):
        opt = StrategyOptimizer()
        candidates = opt.generate_candidates(
            current_lap=5, total_laps=57, current_compound="MEDIUM"
        )
        zero_stop = [c for c in candidates if len(c.pit_laps) == 0]
        assert len(zero_stop) == 1

    def test_two_stop_only_with_enough_laps(self):
        opt = StrategyOptimizer()
        # Short remaining race: no 2-stop
        candidates = opt.generate_candidates(
            current_lap=40, total_laps=57, current_compound="MEDIUM"
        )
        two_stop = [c for c in candidates if len(c.pit_laps) == 2]
        assert len(two_stop) == 0


class TestStintSimulation:
    def test_soft_stint_degrades_faster_than_hard(self):
        opt = StrategyOptimizer()
        soft_penalty, _, _ = opt.simulate_stint("SOFT", 0, 20)
        hard_penalty, _, _ = opt.simulate_stint("HARD", 0, 20)
        assert soft_penalty > hard_penalty

    def test_longer_stint_more_penalty(self):
        opt = StrategyOptimizer()
        short_penalty, _, _ = opt.simulate_stint("MEDIUM", 0, 10)
        long_penalty, _, _ = opt.simulate_stint("MEDIUM", 0, 25)
        assert long_penalty > short_penalty


class TestStrategyOptimization:
    def test_optimize_returns_recommendation(self):
        opt = StrategyOptimizer()
        result = opt.optimize(
            current_lap=5, total_laps=57,
            current_compound="SOFT", current_wear=0.15,
        )
        assert result["recommended_strategy"] is not None
        assert "pit_laps" in result["recommended_strategy"]
        assert "compounds" in result["recommended_strategy"]
        assert "label" in result["recommended_strategy"]
        assert len(result["all_strategies"]) > 0

    def test_pit_window_populated(self):
        opt = StrategyOptimizer()
        result = opt.optimize(
            current_lap=5, total_laps=57,
            current_compound="MEDIUM", current_wear=0.1,
        )
        assert "Lap" in result["pit_window"] or "No stop" in result["pit_window"]

    def test_stop_count_comparison(self):
        opt = StrategyOptimizer()
        result = opt.optimize(
            current_lap=5, total_laps=57,
            current_compound="SOFT", current_wear=0.2,
        )
        assert "0_stop" in result["stop_count_comparison"]
        assert "1_stop" in result["stop_count_comparison"]

    def test_high_wear_prefers_pit(self):
        opt = StrategyOptimizer()
        result = opt.optimize(
            current_lap=20, total_laps=57,
            current_compound="SOFT", current_wear=0.7,
            pit_stop_loss=20.0,
        )
        # With 70% worn softs, staying out should NOT be optimal
        best = result["recommended_strategy"]
        assert len(best["pit_laps"]) > 0, "Should recommend pitting with 70% worn softs"
