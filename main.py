import time

import cv2
import serial
from PyQt6 import uic
from PyQt6.QtCore import QObject, Qt, QThread, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox

from configs import MainConfigs
from constants import Messages
from factories import CameraFactory
from tracker import PotatoTracker

potato_defects_queue = []
potato_timing_queue = []


class Worker(QObject):

    switch = {
        0: MainConfigs.FIRST_STAGE_TIME_DELAY,
        1: MainConfigs.SECOND_STAGE_TIME_DELAY,
        2: MainConfigs.THIRD_STAGE_TIME_DELAY,
    }

    def __init__(self):
        super().__init__()
        self.arduino = serial.Serial(MainConfigs.ARDUINO_PATH, 9600)

    def send_impulse(self, duration: int):
        x = str(duration)
        self.arduino.write(x.encode("utf-8"))

    def run(self):
        while True:
            if len(potato_defects_queue) > 0:
                current_time = time.time()
                if current_time - potato_timing_queue[0][0] >= self.switch[potato_timing_queue[0][1]]:
                    self.send_impulse(2)
                    potato_timing_queue.pop(0)
                    potato_defects_queue.pop(0)
            time.sleep(1)


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(MainConfigs.MAIN_FORM_NAME, self)

        self.showMaximized()
        self.camera = None
        self.timer = None
        self.camera_activated = False
        self.counter = 0
        self.prev_total_objects_count = 0
        self.tracker = PotatoTracker(MainConfigs.CAMERA_FRAME_SHAPE, potato_defects_queue, potato_timing_queue)

        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setScaledContents(True)

        self.exit_button.clicked.connect(self.close)
        self.cam_on_button.clicked.connect(self.activate_camera)
        self.cam_off_button.clicked.connect(self.deactivate_camera)
        self.null_counter_button.clicked.connect(self.null_objects_count)
        self.calibrate_button.clicked.connect(self.calibrate)
        if MainConfigs.USE_AIR:
            self.serial_interface_thread = QThread()
            self.worker = Worker()
            self.worker.moveToThread(self.serial_interface_thread)
            self.serial_interface_thread.started.connect(self.worker.run)
            self.serial_interface_thread.start()

    def calibrate(self):
        pass

    def null_objects_count(self):
        self.counter = 0
        self.objects_count.setText(f"{Messages.OBJECTS_COUNT} {self.counter}")

    def activate_camera(self):
        # Запуск камеры
        if not self.camera_activated:
            if self.camera is None:
                self.camera = CameraFactory.get_camera_device(
                    MainConfigs.PREFERRED_CAMERA_DEVICE, "video/2025-01-09_15-19-24_639.avi"
                )
            if self.camera.device_is_activated():
                self.camera_activated = True
                self.camera.start_stream()
                self.camera_status.setText(Messages.CAMERA_IS_ON)
                self.camera_status.setStyleSheet(MainConfigs.CAMERA_STATUS_STYLE_ON)

                self.cam_on_button.setEnabled(False)
                self.cam_off_button.setEnabled(True)

                # Таймер для обновления кадров
                self.timer = QTimer()
                self.timer.timeout.connect(self.update_frame)
                self.timer.start(30)
            else:
                mes_box = QMessageBox()
                mes_box.setText(Messages.ERROR_CAMERA_IS_NOT_FOUNDED)
                mes_box.exec()

    def deactivate_camera(self):
        if self.camera_activated:
            self.camera_activated = False
            self.camera.stop_stream()
            self.timer = None
            self.camera_status.setText(Messages.CAMERA_IS_OFF)
            self.camera_status.setStyleSheet(MainConfigs.CAMERA_STATUS_STYLE_OFF)
            self.cam_on_button.setEnabled(True)
            self.cam_off_button.setEnabled(False)
            self.camera = None

    def update_frame(self):
        frame = self.camera.get_next_frame()
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = self.tracker.update(frame, self.textBrowser)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

            # Масштабируем изображение под размер окна
            scaled_pixmap = QPixmap.fromImage(qt_img).scaled(
                self.label.width(), self.label.height(), Qt.AspectRatioMode.KeepAspectRatio
            )
            self.label.setPixmap(scaled_pixmap)
            current_objects_total_count = self.tracker.get_total_objects_count()
            if current_objects_total_count > self.prev_total_objects_count:
                self.counter += 1
                self.objects_count.setText(f"{Messages.OBJECTS_COUNT} {self.counter}")
                self.prev_total_objects_count = current_objects_total_count
            if self.counter > 0:
                self.null_counter_button.setEnabled(True)
            else:
                self.null_counter_button.setEnabled(False)

    def closeEvent(self, event):
        if self.camera_activated:
            self.camera.stop_stream()
        event.accept()


app = QApplication([])
window = MyApp()
window.show()
app.exec()
