import pytest
from app.ml.timeline_simulator import TimelineSimulator, DriverSnapshot


class TestDriverSnapshot:
    def test_copy(self):
        s = DriverSnapshot("VER", 1, 0.0, "MEDIUM", 0.1, 90.0, 80.0)
        s.pace = 91.5
        c = s.copy()
        assert c.driver_id == "VER"
        assert c.pace == 91.5
        # Mutating copy doesn't affect original
        c.tire_wear = 0.9
        assert s.tire_wear == 0.1


class TestSimulateLap:
    def test_tire_wear_increases(self):
        sim = TimelineSimulator(n_simulations=1)
        drivers = [
            DriverSnapshot("VER", 1, 0.0, "SOFT", 0.1, 90.0, 80.0),
            DriverSnapshot("NOR", 2, 1.5, "MEDIUM", 0.1, 90.0, 80.0),
        ]
        initial_wear = {d.driver_id: d.tire_wear for d in drivers}
        sim._simulate_lap(drivers, 10, 35.0, 1.0)
        for d in drivers:
            assert d.tire_wear > initial_wear[d.driver_id]

    def test_fuel_decreases(self):
        sim = TimelineSimulator(n_simulations=1)
        drivers = [
            DriverSnapshot("VER", 1, 0.0, "MEDIUM", 0.1, 90.0, 80.0),
        ]
        initial_fuel = drivers[0].fuel_load
        sim._simulate_lap(drivers, 10, 35.0, 1.0)
        assert drivers[0].fuel_load < initial_fuel

    def test_sc_compresses_gaps(self):
        sim = TimelineSimulator(n_simulations=1)
        drivers = [
            DriverSnapshot("VER", 1, 0.0, "MEDIUM", 0.1, 90.0, 80.0),
            DriverSnapshot("NOR", 2, 5.0, "MEDIUM", 0.1, 90.0, 80.0),
        ]
        # Force SC by setting probability = 1.0
        _, sc = sim._simulate_lap(drivers, 10, 35.0, 1.0, sc_probability=1.0)
        assert sc is True
        assert drivers[1].gap_ahead < 5.0  # Gap compressed


class TestTimelineSimulation:
    def setup_method(self):
        self.sim = TimelineSimulator(n_simulations=50)  # Fewer for test speed
        self.positions = ["VER", "NOR", "LEC"]
        self.gaps = {"VER": 0.0, "NOR": 1.2, "LEC": 0.8}
        self.compounds = {"VER": "MEDIUM", "NOR": "MEDIUM", "LEC": "SOFT"}
        self.wears = {"VER": 0.15, "NOR": 0.12, "LEC": 0.20}
        self.temps = {"VER": 90.0, "NOR": 88.0, "LEC": 92.0}
        self.fuels = {"VER": 60.0, "NOR": 60.0, "LEC": 60.0}

    def test_returns_timeline_for_all_drivers(self):
        result = self.sim.simulate_timeline(
            self.positions, self.gaps, self.compounds,
            self.wears, self.temps, self.fuels,
            current_lap=20, total_laps=57,
        )
        assert "timeline" in result
        for d in self.positions:
            assert d in result["timeline"]
            assert len(result["timeline"][d]) > 0

    def test_position_distributions_valid(self):
        result = self.sim.simulate_timeline(
            self.positions, self.gaps, self.compounds,
            self.wears, self.temps, self.fuels,
            current_lap=20, total_laps=57,
        )
        # Check that position probabilities sum to ~1.0 for each driver at each lap
        for d in self.positions:
            for lap_data in result["timeline"][d]:
                total_prob = sum(lap_data["position_distribution"].values())
                assert abs(total_prob - 1.0) < 0.05

    def test_tire_wear_increases_over_timeline(self):
        result = self.sim.simulate_timeline(
            self.positions, self.gaps, self.compounds,
            self.wears, self.temps, self.fuels,
            current_lap=20, total_laps=57,
        )
        tl = result["timeline"]["VER"]
        first_wear = tl[0]["avg_tire_wear"]
        last_wear = tl[-1]["avg_tire_wear"]
        assert last_wear > first_wear

    def test_gap_forecast_exists(self):
        result = self.sim.simulate_timeline(
            self.positions, self.gaps, self.compounds,
            self.wears, self.temps, self.fuels,
            current_lap=20, total_laps=57,
        )
        assert "gap_forecast" in result
        assert len(result["gap_forecast"]) > 0

    def test_sc_forecast_structure(self):
        result = self.sim.simulate_timeline(
            self.positions, self.gaps, self.compounds,
            self.wears, self.temps, self.fuels,
            current_lap=20, total_laps=57,
        )
        assert "sc_forecast" in result
        for entry in result["sc_forecast"]:
            assert "lap" in entry
            assert "sc_probability" in entry
            assert 0.0 <= entry["sc_probability"] <= 1.0

    def test_tire_cliff_detected(self):
        """Soft tires with high initial wear should hit cliff."""
        result = self.sim.simulate_timeline(
            positions=["VER"],
            gaps={"VER": 0.0},
            tire_compounds={"VER": "SOFT"},
            tire_wears={"VER": 0.55},
            tire_temps={"VER": 100.0},
            fuel_loads={"VER": 50.0},
            current_lap=25, total_laps=57,
        )
        # With 55% wear on softs for 30+ laps, cliff should be detected
        assert "VER" in result.get("tire_cliff_lap", {})

    def test_horizon_capped(self):
        result = self.sim.simulate_timeline(
            self.positions, self.gaps, self.compounds,
            self.wears, self.temps, self.fuels,
            current_lap=5, total_laps=70,
        )
        # Horizon should be capped at 30 laps
        assert result["horizon_laps"] <= 30

    def test_no_remaining_laps(self):
        result = self.sim.simulate_timeline(
            self.positions, self.gaps, self.compounds,
            self.wears, self.temps, self.fuels,
            current_lap=57, total_laps=57,
        )
        assert result["timeline"] == {}
