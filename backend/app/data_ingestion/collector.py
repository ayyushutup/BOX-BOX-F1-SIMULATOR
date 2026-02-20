"""
FastF1 data collector — fetches real F1 race sessions.
Handles caching, error recovery, and session validation.
"""

import fastf1
import os


class FastF1DataCollector:
    """Downloads and caches real F1 session data via the FastF1 library."""

    def __init__(self, cache_dir="./f1_cache"):
        os.makedirs(cache_dir, exist_ok=True)
        fastf1.Cache.enable_cache(cache_dir)
        self._cache_dir = cache_dir

    def fetch_race(self, season: int, round_num: int):
        """
        Fetch a race session. Downloads on first call, cached after that.
        
        Args:
            season: Year (e.g. 2024)
            round_num: Round number in the calendar (1-indexed)
            
        Returns:
            fastf1.core.Session with laps, telemetry, weather loaded
            
        Raises:
            ValueError: If the session can't be found or has no lap data
        """
        print(f"[Collector] Fetching {season} Round {round_num}...")

        try:
            session = fastf1.get_session(season, round_num, 'R')
            session.load(
                laps=True,
                telemetry=False,   # skip high-freq telemetry for now (huge)
                weather=True,
                messages=True      # race control messages for SC/VSC detection
            )
        except Exception as e:
            raise ValueError(f"Failed to load session {season} R{round_num}: {e}")

        # Sanity check — make sure we got actual race data
        if session.laps is None or len(session.laps) == 0:
            raise ValueError(
                f"Session {season} R{round_num} returned no lap data. "
                "This might be a sprint or cancelled session."
            )

        circuit = session.event.get("CircuitShortName")
        if not circuit:
             circuit = session.event.get("Location")
        if not circuit:
             circuit = session.event.get("EventName", "Unknown")
        total_laps = int(session.laps['LapNumber'].max())
        n_drivers = session.laps['Driver'].nunique()
        print(f"[Collector] Loaded: {circuit} — {total_laps} laps, {n_drivers} drivers")

        return session

    def list_available_races(self, season: int) -> list[dict]:
        """
        List all races in a given season.
        
        Returns:
            List of dicts with round_num, name, circuit, date
        """
        try:
            schedule = fastf1.get_event_schedule(season)
        except Exception as e:
            raise ValueError(f"Could not fetch {season} schedule: {e}")

        races = []
        for _, row in schedule.iterrows():
            # Skip testing sessions (round 0) 
            if row.get('RoundNumber', 0) == 0:
                continue
            races.append({
                "round_num": int(row['RoundNumber']),
                "name": row.get('EventName', 'Unknown'),
                "circuit": row.get('CircuitShortName', 'Unknown'),
                "country": row.get('Country', 'Unknown'),
                "date": str(row.get('EventDate', '')),
            })

        return races