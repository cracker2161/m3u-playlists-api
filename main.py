from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import datetime
import json
import os
import logging
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CONFIG_FILE = 'config.json'
PLAYLIST_FILE = 'playlist.txt'
DEFAULT_CONFIG = {
    "is_active": True,
    "schedule": {
        "start_time": "00:00",
        "end_time": "23:59"
    },
    "maintenance_mode": False,
    "last_updated": None
}

def error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e),
                "message": "An internal error occurred"
            }), 500
    return wrapper

class PlaylistManager:
    @staticmethod
    def load_config():
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Update with any new default fields
                    return {**DEFAULT_CONFIG, **config}
            return DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return DEFAULT_CONFIG.copy()

    @staticmethod
    def save_config(config):
        try:
            config['last_updated'] = datetime.datetime.now().isoformat()
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
            return False

    @staticmethod
    def read_playlist():
        try:
            with open(PLAYLIST_FILE, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading playlist: {str(e)}")
            return "#EXTM3U\n# Error reading playlist file"

# Initialize global state
playlist_manager = PlaylistManager()
api_status = playlist_manager.load_config()

@app.route('/')
@error_handler
def home():
    return render_template('index.html', 
                         api_status=api_status,
                         last_updated=api_status.get('last_updated', 'Never'))

@app.route('/playlist.m3u8')
@error_handler
def get_playlist():
    if not api_status["is_active"]:
        return "#EXTM3U\n# Service is currently disabled", 200, {'Content-Type': 'application/x-mpegURL'}

    if api_status.get("maintenance_mode", False):
        return "#EXTM3U\n# Service is under maintenance", 200, {'Content-Type': 'application/x-mpegURL'}

    try:
        current_time = datetime.datetime.now().time()
        start_time = datetime.datetime.strptime(api_status["schedule"]["start_time"], "%H:%M").time()
        end_time = datetime.datetime.strptime(api_status["schedule"]["end_time"], "%H:%M").time()

        if start_time <= current_time <= end_time:
            content = playlist_manager.read_playlist()
            return content, 200, {'Content-Type': 'application/x-mpegURL'}
        else:
            return "#EXTM3U\n# Service is not available at this time", 200, {'Content-Type': 'application/x-mpegURL'}
    except Exception as e:
        logger.error(f"Error serving playlist: {str(e)}")
        return "#EXTM3U\n# Error serving playlist", 200, {'Content-Type': 'application/x-mpegURL'}

@app.route('/api/toggle', methods=['POST'])
@error_handler
def toggle_api():
    global api_status
    api_status["is_active"] = not api_status["is_active"]
    success = playlist_manager.save_config(api_status)
    return jsonify({
        "success": success,
        "status": api_status["is_active"],
        "message": "API status updated successfully" if success else "Failed to update API status"
    })

@app.route('/api/schedule', methods=['POST'])
@error_handler
def update_schedule():
    global api_status
    data = request.get_json()

    if not data or 'start_time' not in data or 'end_time' not in data:
        return jsonify({
            "success": False,
            "error": "Invalid schedule data"
        }), 400

    # Validate time format
    try:
        datetime.datetime.strptime(data["start_time"], "%H:%M")
        datetime.datetime.strptime(data["end_time"], "%H:%M")
    except ValueError:
        return jsonify({
            "success": False,
            "error": "Invalid time format. Use HH:MM"
        }), 400

    api_status["schedule"]["start_time"] = data["start_time"]
    api_status["schedule"]["end_time"] = data["end_time"]
    success = playlist_manager.save_config(api_status)

    return jsonify({
        "success": success,
        "message": "Schedule updated successfully" if success else "Failed to update schedule"
    })

@app.route('/api/maintenance', methods=['POST'])
@error_handler
def toggle_maintenance():
    global api_status
    api_status["maintenance_mode"] = not api_status.get("maintenance_mode", False)
    success = playlist_manager.save_config(api_status)
    return jsonify({
        "success": success,
        "maintenance_mode": api_status["maintenance_mode"],
        "message": "Maintenance mode updated successfully" if success else "Failed to update maintenance mode"
    })

@app.route('/api/status', methods=['GET'])
@error_handler
def get_status():
    return jsonify({
        "success": True,
        "status": api_status,
        "last_updated": api_status.get('last_updated', 'Never')
    })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        "success": False,
        "error": "Not found",
        "message": "The requested resource was not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500

if __name__ == '__main__':
    # Ensure the config file exists
    if not os.path.exists(CONFIG_FILE):
        playlist_manager.save_config(DEFAULT_CONFIG)

    # Start the Flask application
    app.run(host='0.0.0.0', port=8080, debug=True)