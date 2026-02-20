
import sys
import os

# Ensure backend modules are found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.data_ingestion.pipeline import pipeline

def verify():
    print("Testing Ingestion for Monaco 2023 (Round 6)...")
    # Monaco 2023
    try:
        result = pipeline.ingest_race(2023, 6)
        print("Result:", result)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify()
