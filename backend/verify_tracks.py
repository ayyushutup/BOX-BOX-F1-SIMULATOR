from app.simulation.data import TRACKS

for track_id, track in TRACKS.items():
    print(f"Track: {track.name}")
    print(f"  Country: {track.country_code}")
    print(f"  Avg Lap: {track.avg_lap_time}")
    print(f"  Pit Window: {track.pit_lap_window}")
    print(f"  Chaos: {track.chaos_level}%")
    print("-" * 20)
