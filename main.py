import time

import cv2
from PyQt6 import uic
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
import utils

from configs import MainConfigs
from constants import Messages
from factories import CameraFactory
from tracker import PotatoTracker
from multiprocessing import Process, Queue
from logger_config import logger
from control_from_another_prog.simple_impulse import send_impulse_raspberry

global send_proc
potato_defects_queue = []
potato_timing_queue = Queue()


def impulse_sender(input_queue: Queue):
    while True:
        sample = input_queue.get()
        time.sleep(MainConfigs.NOZZLE_ACTIVATION_DELAY - (time.time() - sample))
        # send_impulse_raspberry()
        logger.info(f"Send impulse to raspberry board")


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
        self.tracker = PotatoTracker(MainConfigs.CAMERA_FRAME_SHAPE, MainConfigs.SCAN_ZONES_COUNT, potato_timing_queue)

        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setScaledContents(True)

        self.exit_button.clicked.connect(self.close)
        self.cam_on_button.clicked.connect(self.activate_camera)
        self.cam_off_button.clicked.connect(self.deactivate_camera)
        self.null_counter_button.clicked.connect(self.null_objects_count)
        self.calibrate_button.clicked.connect(self.calibrate)

        # Auto-start camera if configured
        if MainConfigs.CAMERA_AUTOSTART:
            utils.logger.info("Auto-starting camera as per configuration")
            self.activate_camera()

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
                    MainConfigs.PREFERRED_CAMERA_DEVICE, "video/17-09.avi"
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
        else:
            pass

    def closeEvent(self, event):
        """Override closeEvent to log statistics before closing"""
        utils.logger.info("Application is closing...")
        self.tracker.log_final_statistics(self.counter)
        if self.camera:
            self.camera.stop_stream()
        if MainConfigs.USE_AIR and hasattr(self, 'serial_interface_thread'):
            self.serial_interface_thread.quit()
            self.serial_interface_thread.wait()
        event.accept()
        if send_proc:
            send_proc.terminate()


if __name__ == '__main__':
    if MainConfigs.USE_AIR:
        send_proc = Process(target=impulse_sender, args=(potato_timing_queue,), daemon=True)
        send_proc.start()
    app = QApplication([])
    window = MyApp()
    window.show()
    app.exec()
