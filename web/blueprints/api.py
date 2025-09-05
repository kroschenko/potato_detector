import os
from flask import Blueprint, jsonify, request, Response

from configs import SorterConfigs, ModelsConfigs, TrackerConfigs, CameraConfigs


def create_api_blueprint(web_runner, logger):
    api = Blueprint('api', __name__, url_prefix='/api')

    @api.route('/config')
    def get_config():
        video_file = os.path.basename(CameraConfigs.AVI_CAMERA_PATH) if hasattr(CameraConfigs, 'AVI_CAMERA_PATH') else 'Unknown'
        return jsonify({
            'SORT_BY_POTATO_SIZE': SorterConfigs.SORT_BY_POTATO_SIZE,
            'SORT_BY_OUTER_DEFECTS': SorterConfigs.SORT_BY_OUTER_DEFECTS,
            'POTATO_SIZE_LIMIT_CENTIMETERS': SorterConfigs.POTATO_SIZE_LIMIT_CENTIMETERS,
            'POTATO_DETECTION_CONFIDENCE_THRESHOLD': ModelsConfigs.POTATO_DETECTION_CONFIDENCE_THRESHOLD,
            'FRAME_SIZE': TrackerConfigs.FRAME_SIZE,
            'VISIBLE_AREA_WIDTH_CENTIMETERS': TrackerConfigs.VISIBLE_AREA_WIDTH_CENTIMETERS,
            'VISIBLE_AREA_HEIGHT_CENTIMETERS': TrackerConfigs.VISIBLE_AREA_HEIGHT_CENTIMETERS,
            'CAMERA_TYPE': CameraConfigs.PREFERRED_CAMERA_DEVICE.name,
            'VIDEO_FILE': video_file
        })

    @api.route('/config', methods=['POST'])
    def update_config():
        data = request.json or {}
        try:
            if 'SORT_BY_POTATO_SIZE' in data:
                SorterConfigs.SORT_BY_POTATO_SIZE = bool(data['SORT_BY_POTATO_SIZE'])
            if 'SORT_BY_OUTER_DEFECTS' in data:
                SorterConfigs.SORT_BY_OUTER_DEFECTS = bool(data['SORT_BY_OUTER_DEFECTS'])
            if 'POTATO_SIZE_LIMIT_CENTIMETERS' in data:
                SorterConfigs.POTATO_SIZE_LIMIT_CENTIMETERS = float(data['POTATO_SIZE_LIMIT_CENTIMETERS'])
            if 'POTATO_DETECTION_CONFIDENCE_THRESHOLD' in data:
                ModelsConfigs.POTATO_DETECTION_CONFIDENCE_THRESHOLD = float(data['POTATO_DETECTION_CONFIDENCE_THRESHOLD'])
            if 'VISIBLE_AREA_WIDTH_CENTIMETERS' in data:
                TrackerConfigs.VISIBLE_AREA_WIDTH_CENTIMETERS = float(data['VISIBLE_AREA_WIDTH_CENTIMETERS'])
            if 'VISIBLE_AREA_HEIGHT_CENTIMETERS' in data:
                TrackerConfigs.VISIBLE_AREA_HEIGHT_CENTIMETERS = float(data['VISIBLE_AREA_HEIGHT_CENTIMETERS'])
            if 'VIDEO_FILE' in data:
                video_file = data['VIDEO_FILE']
                if video_file and os.path.exists(os.path.join('video', video_file)):
                    CameraConfigs.AVI_CAMERA_PATH = os.path.join(os.path.expanduser("./video/"), video_file)
                else:
                    return jsonify({'status': 'error', 'message': 'Video file not found'}), 400
            return jsonify({'status': 'success'})
        except (ValueError, TypeError) as e:
            return jsonify({'status': 'error', 'message': f'Invalid data: {str(e)}'}), 400

    @api.route('/video-files')
    def get_video_files():
        try:
            video_dir = 'video'
            if not os.path.exists(video_dir):
                return jsonify({'files': []})
            
            video_extensions = ['.avi', '.wmv', '.mp4', '.mov']
            files = []
            for filename in os.listdir(video_dir):
                if any(filename.lower().endswith(ext) for ext in video_extensions):
                    files.append(filename)
            
            files.sort()
            return jsonify({'files': files})
        except Exception as e:
            if logger:
                logger.error(f"Error listing video files: {e}")
            return jsonify({'files': []})

    @api.route('/camera/start', methods=['POST'])
    def start_camera():
        success = web_runner.activate_camera()
        return jsonify({'status': 'success' if success else 'error'})

    @api.route('/camera/stop', methods=['POST'])
    def stop_camera():
        web_runner.deactivate_camera()
        return jsonify({'status': 'success'})

    @api.route('/camera/status')
    def camera_status():
        return jsonify({'active': web_runner.camera_activated, 'camera_type': CameraConfigs.PREFERRED_CAMERA_DEVICE.name})

    @api.route('/annotations/enabled', methods=['GET'])
    def get_annotations_enabled():
        try:
            enabled = web_runner.annotation_service.is_enabled()
            return jsonify({'enabled': bool(enabled)})
        except Exception as e:
            logger.error(f"Failed to get annotations enabled state: {e}")
            return jsonify({'enabled': True})

    @api.route('/annotations/enabled', methods=['POST'])
    def set_annotations_enabled():
        try:
            data = request.json or {}
            enabled = bool(data.get('enabled', True))
            web_runner.annotation_service.set_enabled(enabled)
            return jsonify({'status': 'success', 'enabled': enabled})
        except Exception as e:
            logger.error(f"Failed to set annotations enabled state: {e}")
            return jsonify({'status': 'error'}), 500

    def generate_frames():
        from time import sleep
        try:
            while True:
                frame_data = web_runner.get_current_frame_jpeg()
                if not frame_data:
                    frame_data = web_runner.get_current_frame_jpeg()
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
                sleep(1.0 / CameraConfigs.TARGET_STREAM_FPS)
        except Exception as e:
            logger.error(f"Error in generate_frames: {e}")

    @api.route('/camera/stream')
    def video_feed():
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    @api.route('/logs/recent')
    def get_recent_logs():
        from web.app import recent_log_entries  # reuse shared deque
        return jsonify(list(recent_log_entries))

    return api


