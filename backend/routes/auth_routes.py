from flask import Blueprint, request, jsonify, make_response, redirect, url_for
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    unset_jwt_cookies,
    get_jwt_identity
)
from backend.extensions import db, bcrypt
from backend.models.user import User

from google_auth_oauthlib.flow import Flow
import os

auth_bp = Blueprint('auth', __name__)

# ========== Registro ==========
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify(error="Missing fields"), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify(error="Username or email already exists"), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify(message="User registered successfully"), 201

# ========== Login ==========
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    identifier = data.get('username')
    password = data.get('password')

    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()

    if not user or not user.check_password(password):
        return jsonify(error="Invalid credentials"), 401

    access_token = create_access_token(identity=str(user.id))
    resp = make_response(jsonify(message="Login successful"), 200)
    resp.set_cookie(
        'access_token',
        access_token,
        path='/',
        httponly=True,
        secure=False,
        samesite='Lax'
    )
    return resp

# ========== Logout ==========
@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    resp = make_response(jsonify(message="Logout successful"), 200)
    unset_jwt_cookies(resp)
    return resp

# ========== Iniciar conexión con Google Calendar ==========
@auth_bp.route('/calendar/connect')
@jwt_required()
def calendar_connect():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": os.getenv("GOOGLE_CALENDAR_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=['https://www.googleapis.com/auth/calendar.events'],
        redirect_uri=url_for('auth.oauth2callback', _external=True)
    )

    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )

    return redirect(auth_url)

# ========== Callback de Google para guardar tokens ==========
@auth_bp.route('/oauth2callback')
@jwt_required()
def oauth2callback():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": os.getenv("GOOGLE_CALENDAR_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=['https://www.googleapis.com/auth/calendar.events'],
        redirect_uri=url_for('auth.oauth2callback', _external=True)
    )

    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials

    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if user:
        user.google_calendar_token = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        db.session.commit()

    return redirect(url_for('frontend.dashboard'))  
