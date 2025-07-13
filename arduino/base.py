import serial
from configs import ArduinoConfigs


class ArduinoTransmitter:
    def __init__(
        self,
        port: str = ArduinoConfigs.ARDUINO_PORT,
        baud_rate: int = ArduinoConfigs.ARDUINO_BAUD_RATE,
    ) -> None:
        self.port = serial.Serial(port, baud_rate)

    def send_message(self, message: str) -> None:
        self.port.write(message.encode("utf-8"))


transmitter = ArduinoTransmitter()
