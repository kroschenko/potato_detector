import threading
from queue import Queue, Empty
from .base import transmitter
from configs import ArduinoConfigs
from logger_config import logger


_command_queue = Queue(maxsize=256)
_worker_started = False


def _ensure_worker_started() -> None:
    global _worker_started
    if _worker_started:
        return
    def _worker_loop() -> None:
        while True:
            try:
                message = _command_queue.get()
                if message is None:
                    continue
                if ArduinoConfigs.ARDUINO_ONLINE and transmitter is not None:
                    transmitter.send_message(message + "\n")
                    logger.info(f"Send message {message} to Arduino board")
            except Exception as e:
                logger.error(f"Arduino dispatcher error: {e}")
    t = threading.Thread(target=_worker_loop, daemon=True)
    t.start()
    _worker_started = True


def activate_nozzle(cam_id: int) -> None:
    nozzle_type = (
        ArduinoConfigs.FIRST_NOZZLE_MNEMONIC
        if cam_id == 0
        else ArduinoConfigs.SECOND_NOZZLE_MNEMONIC
    )
    _ensure_worker_started()
    try:
        _command_queue.put_nowait(nozzle_type)
    except Exception as e:
        logger.error(f"Failed to queue nozzle activation: {e}")


def led_on():
    message = ArduinoConfigs.LED_MNEMONIC + ArduinoConfigs.PIN_HIGH
    _ensure_worker_started()
    try:
        _command_queue.put_nowait(message)
    except Exception as e:
        logger.error(f"Failed to queue LED on: {e}")
