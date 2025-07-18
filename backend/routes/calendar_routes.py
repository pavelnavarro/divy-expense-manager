from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.user import User
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route('/calendar/create', methods=['POST'])
@jwt_required()
def create_calendar_event():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or not user.google_calendar_token:
        return jsonify(error="Google Calendar not connected"), 400

    creds = Credentials(
        token=user.google_calendar_token['token'],
        refresh_token=user.google_calendar_token['refresh_token'],
        token_uri=user.google_calendar_token['token_uri'],
        client_id=user.google_calendar_token['client_id'],
        client_secret=user.google_calendar_token['client_secret'],
        scopes=user.google_calendar_token['scopes']
    )

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Data from request or defaults
        data = request.get_json() or {}
        summary = data.get('summary', 'Reminder: You have a Divy expense!')
        description = data.get('description', 'Time to settle up 💸')
        start_time = datetime.utcnow() + timedelta(days=3)
        end_time = start_time + timedelta(minutes=30)

        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat() + 'Z',
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat() + 'Z',
                'timeZone': 'UTC',
            },
        }

        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return jsonify(event_link=created_event.get('htmlLink')), 200

    except Exception as e:
        return jsonify(error=str(e)), 500
