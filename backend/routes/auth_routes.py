# backend/routes/auth_routes.py

from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    unset_jwt_cookies
)
from backend.extensions import db, bcrypt
from backend.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify(error="Missing fields"), 400

    # Check for existing user or email
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify(error="Username or email already exists"), 409

    # Create & save new user
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify(message="User registered successfully"), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify(error="Invalid credentials"), 401

    # create JWT
    access_token = create_access_token(identity=str(user.id))
    # respond and set cookie
    resp = make_response(jsonify(message="Login successful"), 200)
    resp.set_cookie(
        'access_token',
        access_token,
        httponly=True,
        secure=False,      # True in production
        samesite='Lax'
    )
    return resp

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    resp = make_response(jsonify(message="Logout successful"), 200)
    unset_jwt_cookies(resp)
    return resp
