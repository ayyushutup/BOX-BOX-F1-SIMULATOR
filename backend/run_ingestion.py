import argparse
from app.data_ingestion.pipeline import DataIngestionPipeline

def main():
    parser = argparse.ArgumentParser(description="Ingest historical F1 tabular data (lap times, weather, compounds) for training ML models.")
    parser.add_argument("--season", type=int, default=2023, help="The F1 season year to ingest (e.g., 2023).")
    parser.add_argument("--round", type=int, help="Optional: A specific round number to ingest. If omitted, the entire season is ingested.")
    
    args = parser.parse_args()
    
    pipeline = DataIngestionPipeline()
    
    if args.round:
        print(f"Starting ingestion for Season {args.season}, Round {args.round}...")
        result = pipeline.ingest_race(args.season, args.round)
        if result.get("success"):
            print(f"Successfully ingested round {args.round}. Saved to {result.get('path')} open to {result.get('snapshots')} snapshots.")
        else:
            print(f"Failed to ingest round {args.round}: {result.get('error')}")
    else:
        print(f"Starting ingestion for entire {args.season} season...")
        results = pipeline.ingest_season(args.season)
        print("\n--- Ingestion Report ---")
        print(f"Successful: {len(results['success'])}")
        print(f"Skipped: {len(results['skipped'])}")
        print(f"Failed: {len(results['failed'])}")
        if results['skipped']:
            print("\nSkipped races (Unsupported Tracks):")
            for r in results['skipped']:
                print(f"  - {r}")
        if results['failed']:
            print("\nFailed races:")
            for r in results['failed']:
                print(f"  - {r}")

if __name__ == "__main__":
    main()
