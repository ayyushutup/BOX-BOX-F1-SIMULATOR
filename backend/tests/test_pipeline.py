
import pytest
from unittest.mock import MagicMock, patch
from app.data_ingestion.pipeline import DataIngestionPipeline

@pytest.fixture
def mock_pipeline():
    with patch("app.data_ingestion.pipeline.FastF1DataCollector") as MockCollector:
        pipeline = DataIngestionPipeline()
        pipeline.collector = MockCollector.return_value
        return pipeline

@patch("app.data_ingestion.pipeline.map_real_race_to_states")
@patch("app.data_ingestion.pipeline.save_race")
@patch("app.data_ingestion.pipeline.is_supported_circuit")
def test_ingest_season(mock_is_supported, mock_save, mock_map, mock_pipeline):
    # Setup mocks
    mock_pipeline.collector.list_available_races.return_value = [
        {"round_num": 1, "name": "Monaco GP", "circuit": "Monaco"}, # Supported
        {"round_num": 2, "name": "Random GP", "circuit": "Unknown"} # Unsupported
    ]
    
    mock_is_supported.side_effect = lambda c: c == "Monaco"
    mock_map.return_value = ["state1", "state2"]
    mock_save.return_value = "/path/to/file.json"
    
    # Run
    results = mock_pipeline.ingest_season(2024)
    
    # Verify
    assert len(results["success"]) == 1
    assert "R1" in results["success"][0]
    
    assert len(results["skipped"]) == 1
    assert "R2" in results["skipped"][0]
    
    # Verify calls
    mock_pipeline.collector.fetch_race.assert_called_once_with(2024, 1)
    mock_map.assert_called_once()
    mock_save.assert_called_once()

@patch("app.data_ingestion.pipeline.map_real_race_to_states")
@patch("app.data_ingestion.pipeline.save_race")
def test_ingest_race_success(mock_save, mock_map, mock_pipeline):
    mock_map.return_value = ["state1"]
    mock_save.return_value = "path.json"
    
    res = mock_pipeline.ingest_race(2024, 1)
    
    assert res["success"] is True
    assert res["path"] == "path.json"

@patch("app.data_ingestion.pipeline.map_real_race_to_states")
def test_ingest_race_failure(mock_map, mock_pipeline):
    # Simulate fetch error
    mock_pipeline.collector.fetch_race.side_effect = Exception("Network Error")
    
    res = mock_pipeline.ingest_race(2024, 1)
    
    assert res["success"] is False
    assert "Network Error" in res["error"]
