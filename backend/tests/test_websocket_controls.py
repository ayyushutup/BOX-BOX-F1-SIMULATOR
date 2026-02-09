
from fastapi.testclient import TestClient
from app.main import app
import time

def test_websocket_controls():
    print("Connecting to WebSocket...")
    with TestClient(app) as client:
        with client.websocket_connect("/ws/race") as websocket:
            print("Connected. Converting to race mode...")
            # Init
            websocket.send_json({"command": "init", "track_id": "monaco"})
            data = websocket.receive_json()
            assert data["type"] == "init"
            
            print("Starting race...")
            # Start
            websocket.send_json({"command": "start", "speed": 1})
            
            # Read a few updates to ensure it's running
            for _ in range(3):
                data = websocket.receive_json()
                assert data["type"] == "update"
            
            print("Sending pause command...")
            # Pause - this should work immediately if the loop is non-blocking
            websocket.send_json({"command": "pause"})
            
            # We might get one or two pending updates, but eventually must get "paused"
            # or the test will timeout if the server is blocked
            
            found_pause = False
            for _ in range(10): # Try reading up to 10 messages
                data = websocket.receive_json()
                if data["type"] == "paused":
                    found_pause = True
                    break
            
            assert found_pause, "Did not receive 'paused' message!"
            print("Successfully paused!")
