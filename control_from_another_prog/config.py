# Server configuration
#RASPBERRY_SERVER_URL = "http://localhost:8000"  # Change this to your server's address
RASPBERRY_SERVER_URL = "http://192.168.0.108:8000"  # Change this to your server's address
#RASPBERRY_SERVER_URL = "http://192.168.8.5:8000"  # Change this to your server's address

# Nozzle configuration
NOZZLE_ID = "nozzle1"

# API endpoints
RELAY_ENDPOINT = f"{RASPBERRY_SERVER_URL}/api/v2/relays"
NOZZLE_ENDPOINT = f"{RELAY_ENDPOINT}/{NOZZLE_ID}" 