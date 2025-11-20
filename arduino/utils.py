from .base import transmitter
from configs import ArduinoConfigs
from logger_config import logger


def send_message(message: str) -> None:
    if ArduinoConfigs.ARDUINO_ONLINE and transmitter is not None:
        transmitter.send_message(message + "\n")


def format_nozzle_delay_message() -> str:
    top = ArduinoConfigs.NOZZLE_DELAY_BEFORE_OPEN_TOP
    bottom = ArduinoConfigs.NOZZLE_DELAY_BEFORE_OPEN_BOTTOM
    return f"D{top},{bottom}"


def activate_nozzle(cam_id: int) -> None:
    nozzle_type = (
        ArduinoConfigs.FIRST_NOZZLE_MNEMONIC
        if cam_id == 0
        else ArduinoConfigs.SECOND_NOZZLE_MNEMONIC
    )
    send_message(nozzle_type)
    logger.info(f"Send message {nozzle_type} to Arduino board")


def led_on():
    if ArduinoConfigs.ARDUINO_ONLINE:
        message = ArduinoConfigs.LED_MNEMONIC + ArduinoConfigs.PIN_HIGH
        send_message(message)
        logger.info(f"Send message {message} to Arduino board")


def apply_nozzle_delays() -> None:
    message = format_nozzle_delay_message()
    send_message(message)
    logger.info(f"Send message {message} to Arduino board")
