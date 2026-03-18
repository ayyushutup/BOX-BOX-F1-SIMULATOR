import pytest
from app.simulation.interaction_graph import RaceInteractionGraph, InteractionEdge, get_track_overtake_factor


class TestInteractionEdge:
    def test_dirty_air_scales_with_gap(self):
        close = InteractionEdge("NOR", "VER", gap=0.5)
        far = InteractionEdge("HAM", "VER", gap=1.8)
        assert close.dirty_air_factor > far.dirty_air_factor
        assert close.dirty_air_time_penalty > far.dirty_air_time_penalty

    def test_drs_available_under_1s(self):
        edge = InteractionEdge("NOR", "VER", gap=0.8)
        assert edge.drs_available is True
        edge_far = InteractionEdge("HAM", "VER", gap=1.2)
        assert edge_far.drs_available is False

    def test_slipstream_available_close(self):
        edge = InteractionEdge("NOR", "VER", gap=0.5)
        assert edge.slipstream_boost > 0.0
        edge_far = InteractionEdge("HAM", "VER", gap=2.0)
        assert edge_far.slipstream_boost == 0.0

    def test_no_dirty_air_beyond_range(self):
        edge = InteractionEdge("NOR", "VER", gap=3.0)
        assert edge.dirty_air_factor == 0.0
        assert edge.dirty_air_time_penalty == 0.0


class TestTrackOvertakeFactor:
    def test_monaco_very_hard(self):
        factor = get_track_overtake_factor("monaco")
        assert factor < 0.3

    def test_monza_easy(self):
        factor = get_track_overtake_factor("monza")
        assert factor > 1.5

    def test_street_circuit_fallback(self):
        factor = get_track_overtake_factor("unknown_street", is_street=True)
        assert factor < 0.5

    def test_expected_overtakes_heuristic(self):
        factor = get_track_overtake_factor("new_track", expected_overtakes=60)
        assert factor > 1.5

    def test_track_factor_scales_overtake_probability(self):
        # Monaco: low overtake probability
        graph_monaco = RaceInteractionGraph()
        graph_monaco.build(
            drivers_sorted=["VER", "NOR"],
            gaps={"NOR": 0.8},
            track_id="monaco",
        )
        monaco_prob = graph_monaco.edges[0].overtake_probability

        # Monza: high overtake probability
        graph_monza = RaceInteractionGraph()
        graph_monza.build(
            drivers_sorted=["VER", "NOR"],
            gaps={"NOR": 0.8},
            track_id="monza",
        )
        monza_prob = graph_monza.edges[0].overtake_probability

        assert monza_prob > monaco_prob


class TestDRSTrainDetection:
    def test_detects_train_of_3(self):
        graph = RaceInteractionGraph()
        graph.build(
            drivers_sorted=["VER", "NOR", "LEC", "HAM"],
            gaps={"NOR": 0.7, "LEC": 0.6, "HAM": 0.8},
        )
        trains = graph.detect_drs_trains()
        assert len(trains) == 1
        assert len(trains[0]) == 4

    def test_no_train_when_gaps_large(self):
        graph = RaceInteractionGraph()
        graph.build(
            drivers_sorted=["VER", "NOR", "LEC"],
            gaps={"NOR": 2.5, "LEC": 3.0},
        )
        trains = graph.detect_drs_trains()
        assert len(trains) == 0

    def test_split_trains(self):
        graph = RaceInteractionGraph()
        graph.build(
            drivers_sorted=["VER", "NOR", "LEC", "SAI", "HAM", "RUS"],
            gaps={"NOR": 0.5, "LEC": 0.6, "SAI": 5.0, "HAM": 0.4, "RUS": 0.7},
        )
        trains = graph.detect_drs_trains()
        assert len(trains) == 2


class TestStackedDirtyAir:
    def test_car_c_gets_more_penalty_than_car_b(self):
        """Car C behind Car B behind Car A should get more cumulative dirty air."""
        graph = RaceInteractionGraph()
        graph.build(
            drivers_sorted=["VER", "NOR", "LEC"],
            gaps={"NOR": 0.5, "LEC": 0.5},
        )
        penalties = graph.get_interaction_penalties()
        # Car C (LEC) should have higher stacked dirty air than Car B (NOR)
        assert penalties["LEC"]["stacked_dirty_air"] > penalties["NOR"]["stacked_dirty_air"]

    def test_no_stacked_air_for_leader(self):
        graph = RaceInteractionGraph()
        graph.build(
            drivers_sorted=["VER", "NOR"],
            gaps={"NOR": 0.5},
        )
        penalties = graph.get_interaction_penalties()
        assert penalties["VER"]["stacked_dirty_air"] == 0.0

    def test_stacked_air_includes_tire_heating(self):
        graph = RaceInteractionGraph()
        graph.build(
            drivers_sorted=["VER", "NOR", "LEC"],
            gaps={"NOR": 0.5, "LEC": 0.5},
        )
        penalties = graph.get_interaction_penalties()
        # Traffic tire heating should be > 0 for cars in dirty air
        assert penalties["LEC"]["tire_heat_from_traffic"] > 0.0
        assert penalties["VER"]["tire_heat_from_traffic"] == 0.0


class TestOvertakeProbability:
    def test_tire_advantage_increases_overtake_chance(self):
        graph = RaceInteractionGraph()
        graph.build(
            drivers_sorted=["VER", "NOR"],
            gaps={"NOR": 0.8},
            tire_deltas={"NOR": 1.5},
        )
        high_tire = graph.edges[0].overtake_probability

        graph2 = RaceInteractionGraph()
        graph2.build(
            drivers_sorted=["VER", "NOR"],
            gaps={"NOR": 0.8},
            tire_deltas={"NOR": 0.0},
        )
        no_tire = graph2.edges[0].overtake_probability
        assert high_tire > no_tire

    def test_drs_boosts_overtake_chance(self):
        graph = RaceInteractionGraph()
        graph.build(
            drivers_sorted=["VER", "NOR"],
            gaps={"NOR": 0.8},
        )
        with_drs = graph.edges[0].overtake_probability

        graph2 = RaceInteractionGraph()
        graph2.build(
            drivers_sorted=["VER", "NOR"],
            gaps={"NOR": 1.5},
        )
        no_drs = graph2.edges[0].overtake_probability
        assert with_drs > no_drs


class TestStrengthModifiers:
    def test_leader_gets_no_penalty(self):
        graph = RaceInteractionGraph()
        graph.build(
            drivers_sorted=["VER", "NOR", "LEC"],
            gaps={"NOR": 0.5, "LEC": 0.8},
        )
        modifiers = graph.get_strength_modifiers()
        assert modifiers["VER"] == 1.0

    def test_close_follower_gets_penalized(self):
        graph = RaceInteractionGraph()
        graph.build(
            drivers_sorted=["VER", "NOR"],
            gaps={"NOR": 0.3},
        )
        modifiers = graph.get_strength_modifiers()
        assert modifiers["NOR"] != 1.0

    def test_sc_disables_drs(self):
        graph = RaceInteractionGraph()
        graph.build(
            drivers_sorted=["VER", "NOR"],
            gaps={"NOR": 0.5},
            sc_active=True,
        )
        penalties = graph.get_interaction_penalties()
        assert penalties["NOR"]["drs_boost"] == 0.0
        assert penalties["NOR"]["slipstream_boost"] == 0.0
