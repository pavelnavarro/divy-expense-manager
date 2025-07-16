from flask import Blueprint, request, jsonify
from backend.extensions import db, bcrypt
from backend.models.user import User
from flask_jwt_extended import create_access_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    email    = data.get('email')
    pw       = data.get('password')
    if not all([username, email, pw]):
        return jsonify(error="Faltan campos"), 400
    if User.query.filter((User.username==username)|(User.email==email)).first():
        return jsonify(error="Usuario o email ya existe"), 409

    user = User(username=username, email=email)
    user.set_password(pw)
    db.session.add(user)
    db.session.commit()
    return jsonify(message="Usuario registrado"), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    pw       = data.get('password')
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(pw):
        return jsonify(error="Credenciales inválidas"), 401

    token = create_access_token(identity=str(user.id))
    return jsonify(access_token=token), 200
