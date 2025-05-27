import requests
import time
from .config import NOZZLE_ENDPOINT, IMPULSE_LENGTH_MS


def send_impulse_raspberry():
    """Send a single impulse to the Raspberry Pi controlled nozzle"""
    try:
        # Turn ON
        response = requests.post(
            NOZZLE_ENDPOINT,
            json={"state": True}
        )
        response.raise_for_status()
        
        # Wait for impulse duration
        time.sleep(IMPULSE_LENGTH_MS / 1000)  # Convert ms to seconds
        
        # Turn OFF
        response = requests.post(
            NOZZLE_ENDPOINT,
            json={"state": False}
        )
        response.raise_for_status()
        
        print("Impulse executed successfully")
        
    except requests.exceptions.RequestException as e:
        print(f"Error sending impulse: {e}")


if __name__ == "__main__":
    print(f"Sending {IMPULSE_LENGTH_MS}ms impulse...")
    send_impulse_raspberry()
