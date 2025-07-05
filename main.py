import time

from PyQt6 import uic
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
import utils

from configs import MainConfigs, TrackerConfigs
from constants import Messages
from multiprocessing import Process, Queue
from logger_config import logger
from control_from_another_prog.simple_impulse import send_impulse_raspberry
from configs import AVICameraConfig, OpenCVCameraConfig, Do3ThinkCameraConfig
from camera_manager import CameraManager

global top_impulse, bottom_impulse
potato_defects_queue = []
potato_timing_top_queue = Queue()
potato_timing_bottom_queue = Queue()


def send_impulse(input_queue: Queue, cam_id: int):
    while True:
        sample = input_queue.get()
        time.sleep(TrackerConfigs.NOZZLE_ACTIVATION_DELAY - (time.time() - sample))
        send_impulse_raspberry(cam_id)
        logger.info(f"Send impulse {cam_id} to raspberry board")


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(MainConfigs.MAIN_FORM_NAME, self)
        self.showMaximized()
        self.camera_manager = CameraManager()
        self.camera_manager.add_camera(AVICameraConfig())
        self.camera_manager.add_camera(AVICameraConfig())
        self.timer = None
        self.counter = 0
        self.prev_total_objects_count = 0
        # Auto-start camera if configured
        # if CameraConfigs.CAMERA_AUTOSTART:
        #     utils.logger.info("Auto-starting camera as per configuration")
        #     self.activate_camera()

        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setScaledContents(True)

        self.exit_button.clicked.connect(self.close)
        self.cam_on_button.clicked.connect(self.activate_camera)
        # self.cam_off_button.clicked.connect(self.deactivate_camera)
        # self.null_counter_button.clicked.connect(self.null_objects_count)
        self.other_cam_button.clicked.connect(self.calibrate)

    def calibrate(self):
        self.camera_manager.circular_switch_current_camera()
        # self.camera_manager.set_current_camera()
        # self.current_camera.setText(Messages.CURRENT_CAMERA + str(self.active_camera))

    # def null_objects_count(self):
    #     self.counter = 0
    #     self.objects_count.setText(f"{Messages.OBJECTS_COUNT} {self.counter}")

    def activate_camera(self):
        if self.camera_manager.activate_all_cameras():
            self.current_camera.setText(
                Messages.CURRENT_CAMERA + str(self.camera_manager.current_camera)
            )
            # Таймер для обновления кадров
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_frame)
            self.timer.start(30)
        else:
            mes_box = QMessageBox()
            mes_box.setText(Messages.ERROR_CAMERA_IS_NOT_FOUNDED)
            mes_box.exec()
            #     self.current_camera.setStyleSheet(CameraConfigs.CAMERA_STATUS_STYLE_ON)
            #     self.camera_status.setText(Messages.CAMERA_IS_ON)
            #     self.camera_status.setStyleSheet(CameraConfigs.CAMERA_STATUS_STYLE_ON)

                # self.cam_on_button.setEnabled(False)
                # self.cam_off_button.setEnabled(True)
                # shape = self.camera_1.get_shape()

    #         self.current_camera.setStyleSheet(CameraConfigs.CAMERA_STATUS_STYLE_OFF)
    #         self.camera_status.setText(Messages.CAMERA_IS_OFF)
    #         self.camera_status.setStyleSheet(CameraConfigs.CAMERA_STATUS_STYLE_OFF)
    #         self.cam_on_button.setEnabled(True)
    #         self.cam_off_button.setEnabled(False)

    def update_frame(self):
        frame = self.camera_manager.get_next_frame()
        if frame is not None:
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_img = QImage(
                frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888
            )

            # Масштабируем изображение под размер окна
            scaled_pixmap = QPixmap.fromImage(qt_img).scaled(
                self.label.width(),
                self.label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
            )
            self.label.setPixmap(scaled_pixmap)
            self.objects_count.setText(f"{Messages.OBJECTS_COUNT} {self.camera_manager.tracker.get_total_objects_count()}")

    def closeEvent(self, event):
        """Override closeEvent to log statistics before closing"""
        utils.logger.info("Application is closing...")
        # self.tracker.log_final_statistics(self.counter)
        self.camera_manager.deactivate_all_cameras()
        if TrackerConfigs.USE_AIR and hasattr(self, "serial_interface_thread"):
            self.serial_interface_thread.quit()
            self.serial_interface_thread.wait()
        event.accept()
        if top_impulse:
            top_impulse.terminate()
        if bottom_impulse:
            bottom_impulse.terminate()


if __name__ == "__main__":
    if TrackerConfigs.USE_AIR:
        top_impulse = Process(
            target=send_impulse, args=(potato_timing_top_queue, 0), daemon=True
        )
        bottom_impulse = Process(
            target=send_impulse, args=(potato_timing_bottom_queue, 1), daemon=True
        )
        top_impulse.start()
        bottom_impulse.start()
    app = QApplication([])
    window = MyApp()
    window.show()
    app.exec()
