# Raspberry Pi Nozzle Control

This directory contains example code for controlling the Raspberry Pi nozzle system from external Python applications.

## Setup

1. Install required package:
```bash
pip install requests
```

2. Configure the server address in `config.py`:
```python
RASPBERRY_SERVER_URL = "http://localhost:8000"  # Change to your Raspberry Pi's address
```

## Usage

### Simple Impulse Example

The `simple_impulse.py` script demonstrates how to send a single impulse to the nozzle:

```python
from simple_impulse import send_impulse_raspberry

# Send a single impulse
send_impulse_raspberry()
```

Or run directly:
```bash
python simple_impulse.py
```

### Configuration

All parameters are in `config.py`:
- `RASPBERRY_SERVER_URL`: Raspberry Pi server address
- `NOZZLE_ID`: Target nozzle (default: "nozzle1")
- `IMPULSE_LENGTH_MS`: Impulse duration in milliseconds (default: 500ms)

## API Details

The script uses the following API endpoints:
- `{RASPBERRY_SERVER_URL}/api/v2/relays/{NOZZLE_ID}`

Example request:
```python
response = requests.post(
    NOZZLE_ENDPOINT,
    json={"state": True}  # True for ON, False for OFF
)
```

## Error Handling

The script includes basic error handling for:
- Connection errors
- Server errors
- Invalid responses

## Requirements

- Python 3.6+
- requests library
- Network access to Raspberry Pi server 