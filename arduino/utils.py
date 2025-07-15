from .base import transmitter
import time
from multiprocessing import Queue
from configs import ArduinoConfigs
from logger_config import logger


def activate_nozzle(input_queue: Queue, cam_id: int):
    nozzle_type = (
        ArduinoConfigs.TOP_NOZZLE_MNEMONIC
        if cam_id == 0
        else ArduinoConfigs.BOTTOM_NOZZLE_MNEMONIC
    )

    while True:
        sample = input_queue.get()
        if sample == -1:
            break
        time.sleep(sample - time.time())
        message = nozzle_type + ArduinoConfigs.PIN_HIGH
        transmitter.send_message(message + "\n")
        logger.info(f"Send message {message} to Arduino board")


def led_on():
    if ArduinoConfigs.ARDUINO_ONLINE:
        message = ArduinoConfigs.LED_MNEMONIC + ArduinoConfigs.PIN_HIGH
        transmitter.send_message(message + "\n")
        logger.info(f"Send message {message} to Arduino board")
