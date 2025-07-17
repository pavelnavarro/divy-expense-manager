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

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify(error="Username or email already exists"), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify(message="User registered successfully"), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    identifier = data.get('username')  # aquí llega lo que el usuario ingresó (puede ser username o email)
    password = data.get('password')

    # Permitimos login por username O por email
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
        path='/',       # se enviará la cookie en todas las rutas
        httponly=True,
        secure=False,   # en producción: True
        samesite='Lax'
    )
    return resp

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    resp = make_response(jsonify(message="Logout successful"), 200)
    unset_jwt_cookies(resp)
    return resp
