"""
Data Ingestion Pipeline.
Orchestrates the flow: FastF1 -> Mapper -> Storage.
"""

from typing import List, Dict
import traceback
from .collector import FastF1DataCollector
from .mapper import map_real_race_to_states
from .storage import save_race
from .circuit_mapping import is_supported_circuit

class DataIngestionPipeline:
    def __init__(self):
        self.collector = FastF1DataCollector()
        
    def ingest_season(self, season: int) -> Dict[str, List[str]]:
        """
        Ingest all supported races for a given season.
        """
        print(f"[Pipeline] Starting ingestion for Season {season}...")
        
        try:
            races = self.collector.list_available_races(season)
        except Exception as e:
            return {"error": [str(e)], "success": []}
            
        results = {
            "success": [],
            "skipped": [],
            "failed": []
        }
        
        for race in races:
            round_num = race['round_num']
            race_name = race['name']
            circuit = race['circuit']
            
            # 1. Check if track is supported
            if not is_supported_circuit(circuit):
                print(f"[Pipeline] Skipping Round {round_num} ({circuit}) - Unsupported track")
                results["skipped"].append(f"R{round_num}: {circuit}")
                continue
                
            print(f"[Pipeline] Processing Round {round_num}: {race_name} at {circuit}...")
            
            try:
                # 2. Fetch Data
                session = self.collector.fetch_race(season, round_num)
                
                # 3. Map to RaceState
                states = map_real_race_to_states(session)
                
                if not states:
                    print(f"[Pipeline] No valid states generated for {race_name}")
                    results["failed"].append(f"R{round_num}: Mapping failed")
                    continue
                    
                # 4. Save
                path = save_race(season, round_num, states)
                print(f"[Pipeline] Successfully saved to {path}")
                results["success"].append(f"R{round_num}: {race_name}")
                
            except Exception as e:
                print(f"[Pipeline] Failed Round {round_num}: {e}")
                traceback.print_exc()
                results["failed"].append(f"R{round_num}: {str(e)}")
                
        return results

    def ingest_race(self, season: int, round_num: int) -> Dict:
        """Ingest a single race."""
        try:
            session = self.collector.fetch_race(season, round_num)
            states = map_real_race_to_states(session)
            
            if not states:
                return {"success": False, "error": "Mapping generated no states"}
                
            path = save_race(season, round_num, states)
            return {"success": True, "path": path, "snapshots": len(states)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
# Singleton instance
pipeline = DataIngestionPipeline()
