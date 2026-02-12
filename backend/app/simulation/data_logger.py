import csv
import os
from datetime import datetime
from ..models.race_state import Car, Track

class DataLogger:
    def __init__(self, filepath="data/race_data.csv"):
        self.filepath = filepath
        self._ensure_directory()
        self._initialize_csv()

    def _ensure_directory(self):
        """Ensure the directory for the CSV file exists."""
        directory = os.path.dirname(self.filepath)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError:
                pass  # Directory might have been created concurrently

    def _initialize_csv(self):
        """Create the CSV file with headers if it doesn't exist."""
        file_exists = os.path.exists(self.filepath)
        
        # Define headers for our dataset
        self.headers = [
            "timestamp",
            "track_id", 
            "driver", 
            "lap", 
            "lap_time", 
            "sector_1", "sector_2", "sector_3", # Placeholders for sector times
            "compound", 
            "tire_age", 
            "tire_wear", 
            "fuel", 
            "rain_prob", 
            "track_temp", 
            "mode", 
            "drs_active", 
            "ers_battery"
        ]
        
        # Only write headers if file is new or empty
        if not file_exists or os.path.getsize(self.filepath) == 0:
            with open(self.filepath, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

    def log_lap(self, car: Car, track: Track):
        """Log data at the completion of a lap."""
        # Only log if a valid lap time exists
        if car.timing.last_lap_time is None:
            return

        with open(self.filepath, mode='a', newline='') as f:
            writer = csv.writer(f)
            row = [
                datetime.now().isoformat(),
                track.id,
                car.identity.driver,
                car.timing.lap,  # Lap number just completed
                f"{car.timing.last_lap_time:.3f}",
                0, 0, 0,  # Sector times (0 for now)
                car.telemetry.tire_state.compound.value,
                car.telemetry.tire_state.age,
                f"{car.telemetry.tire_state.wear:.4f}",
                f"{car.telemetry.fuel:.2f}",
                f"{track.weather.rain_probability:.2f}",
                f"{track.weather.temperature:.1f}",
                car.strategy.driving_mode.value,
                "YES" if car.systems.drs_active else "NO",
                f"{car.systems.ers_battery:.2f}"
            ]
            writer.writerow(row)