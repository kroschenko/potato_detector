import serial
from configs import NozzleConfigs


class ArduinoTransmitter:
    def __init__(
        self,
        port: str = NozzleConfigs.ARDUINO_PORT,
        baud_rate: int = NozzleConfigs.ARDUINO_BAUD_RATE,
    ) -> None:
        self.port = serial.Serial(port, baud_rate)

    def send_message(self, message: str) -> None:
        self.port.write(message.encode("utf-8"))


transmitter = ArduinoTransmitter()
