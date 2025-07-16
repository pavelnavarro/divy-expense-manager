from flask import Blueprint, request, jsonify

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route('/test', methods=['GET'])
def test_calendar():
    return jsonify(message="Calendar routes OK"), 200

@calendar_bp.route('/health', methods=['GET'])
def health():
    return jsonify(status="ok"), 200

