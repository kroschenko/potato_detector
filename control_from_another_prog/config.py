# Server configuration
#RASPBERRY_SERVER_URL = "http://localhost:8000"  # Change this to your server's address
RASPBERRY_SERVER_URL = "http://192.168.0.108:8000"  # Change this to your server's address

# Nozzle configuration
NOZZLE_ID_1 = "nozzle1"
NOZZLE_ID_2 = "nozzle2"
IMPULSE_LENGTH_MS = 10  # Impulse duration in milliseconds

# API endpoints
RELAY_ENDPOINT = f"{RASPBERRY_SERVER_URL}/api/v2/relays"
TOP_NOZZLE_ENDPOINT = f"{RELAY_ENDPOINT}/{NOZZLE_ID_1}"
BOTTOM_NOZZLE_ENDPOINT = f"{RELAY_ENDPOINT}/{NOZZLE_ID_2}"
