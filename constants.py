from dataclasses import dataclass
from typing import Tuple


@dataclass
class Color:
    RED: Tuple = (255, 0, 0)


class Messages:
    APPEND_DAMAGED_POTATOES: str = "добавлен в список поврежденных клубней"
    OBJECTS_COUNT: str = "Количество объектов:"
    FIRST_STAGE_SCANNED: str = "отсканирован в первой зоне"
    SECOND_STAGE_SCANNED: str = "отсканирован во второй зоне"
    THIRD_STAGE_SCANNED: str = "отсканирован в третьей зоне"
    FIRST_STAGE_ADDED: str = "добавлен в список сканирования в первой зоне"
    SECOND_STAGE_ADDED: str = "добавлен в список сканирования во второй зоне"
    THIRD_STAGE_ADDED: str = "добавлен в список сканирования в третьей зоне"
    CAMERA_IS_OFF: str = "Камера выключена"
    CAMERA_IS_ON: str = "Камера включена"
    ERROR_CAMERA_IS_NOT_FOUNDED: str = "Ошибка: не найдена камера!"
