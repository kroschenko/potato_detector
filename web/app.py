import time
import sys
import os
from collections import deque
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configs import CameraConfigs
from main_types import CameraType
from logger_config import logger
from services.web_runner import WebRunner
from socketio_log_handler import SocketIOLogHandler
from blueprints.api import create_api_blueprint




app = Flask(__name__)
app.config['SECRET_KEY'] = 'potato_detector_secret'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

web_runner = WebRunner()

recent_log_entries = deque(maxlen=1000)

socketio_log_handler = SocketIOLogHandler(socketio, recent_log_entries)
logger.addHandler(socketio_log_handler)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/@libs/<path:filename>')
def serve_libs(filename):
    return send_from_directory(os.path.join(app.static_folder, 'js', 'libs'), filename)


api = create_api_blueprint(web_runner, logger)


@socketio.on('connect')
def handle_connect():
    emit('connected', {'status': 'Connected to Potato Detector'})


@socketio.on('request_statistics')
def handle_statistics_request():
    stats = web_runner.get_statistics()
    emit('statistics_update', stats)


def background_statistics_updater():
    while True:
        if web_runner.camera_activated:
            stats = web_runner.get_statistics()
            socketio.emit('statistics_update', stats)
        time.sleep(1)


def start_web_server():
    if CameraConfigs.PREFERRED_CAMERA_DEVICE == CameraType.DO3THINK_CAMERA:
        web_runner.activate_camera()
    socketio.start_background_task(background_statistics_updater)
    app.register_blueprint(api)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    start_web_server()
