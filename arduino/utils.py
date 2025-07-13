from .base import transmitter
import time
from multiprocessing import Queue
from configs import ArduinoConfigs
from logger_config import logger


def activate_nozzle(input_queue: Queue, cam_id: int):
    delay = (
        ArduinoConfigs.TOP_NOZZLE_ACTIVATION_DELAY
        if cam_id == 0
        else ArduinoConfigs.BOTTOM_NOZZLE_ACTIVATION_DELAY
    )
    nozzle_type = (
        ArduinoConfigs.TOP_NOZZLE_MNEMONIC
        if cam_id == 0
        else ArduinoConfigs.BOTTOM_NOZZLE_MNEMONIC
    )
    while True:
        sample = input_queue.get()
        if sample == -1:
            break
        time.sleep(delay - (time.time() - sample))
        message = nozzle_type + ArduinoConfigs.PIN_HIGH
        transmitter.send_message(message + "\n")
        logger.info(f"Send message {message} to Arduino board")
        time.sleep(ArduinoConfigs.NOZZLE_ACTIVE_PERIOD)
        message = nozzle_type + ArduinoConfigs.PIN_LOW
        transmitter.send_message(message + "\n")
        logger.info(f"Send message {message} to Arduino board")


def led_on():
    message = ArduinoConfigs.LED_MNEMONIC + ArduinoConfigs.PIN_HIGH
    transmitter.send_message(message + "\n")
    logger.info(f"Send message {message} to Arduino board")
