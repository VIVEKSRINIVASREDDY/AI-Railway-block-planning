"""
Live IoT Sensor Simulator.

Streams synthetic sensor readings to the FastAPI backend to demonstrate
real-time data ingestion and autonomous AI replanning capabilities.
"""

import time
import json
import random
import urllib.request
import urllib.error

API_URL = "http://localhost:8000/api/telemetry/ingest"

def send_reading(payload: dict):
    req = urllib.request.Request(API_URL, method="POST")
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(payload).encode('utf-8')
    try:
        urllib.request.urlopen(req, data=data)
        print(f"Sent: {payload['sensor_type']} = {payload['reading_value']:.2f} {payload['unit']} @ Km {payload['km_marker']}")
    except urllib.error.URLError as e:
        print(f"Connection failed: Is the FastAPI server running on port 8000? ({e.reason})")

def run_simulation(duration_seconds=120):
    print("=" * 60)
    print("  Starting Live IoT Sensor Simulator...")
    print("=" * 60)
    
    start_time = time.time()
    
    # We'll trigger an anomaly after 15 seconds
    anomaly_triggered = False
    
    while time.time() - start_time < duration_seconds:
        elapsed = time.time() - start_time
        
        # Decide what to send
        if elapsed > 15 and not anomaly_triggered:
            # Trigger a massive vibration spike (Broken Rail simulation)
            payload = {
                "sensor_id": "TTRACK-CAM-04",
                "sensor_type": "vibration",
                "km_marker": 45.2,
                "reading_value": 9.4,  # > 8.0 threshold
                "unit": "g"
            }
            print("\n!!! INJECTING CRITICAL ANOMALY !!!")
            anomaly_triggered = True
        else:
            # Normal telemetry
            sensor_type = random.choice(["vibration", "voltage_drop", "acoustic"])
            km = round(random.uniform(10.0, 150.0), 1)
            
            if sensor_type == "vibration":
                val = random.uniform(1.0, 4.0)
                unit = "g"
            elif sensor_type == "voltage_drop":
                val = random.uniform(-100.0, 50.0)
                unit = "V"
            else:
                val = random.uniform(50.0, 80.0)
                unit = "dB"
                
            payload = {
                "sensor_id": f"SENS-{random.randint(100, 999)}",
                "sensor_type": sensor_type,
                "km_marker": km,
                "reading_value": val,
                "unit": unit
            }
            
        send_reading(payload)
        
        # Sleep randomly between 2 to 4 seconds to simulate continuous feed
        time.sleep(random.uniform(2.0, 4.0))

    print("\nSimulation complete.")

if __name__ == "__main__":
    run_simulation()
