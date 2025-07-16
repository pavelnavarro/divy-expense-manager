# app.py
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import timedelta

from extensions import db, bcrypt
from backend.routes.shared_routes import shared_bp
from backend.routes.personal_routes import personal_bp
from backend.routes.auth_routes import auth_bp  # if you add one

load_dotenv()

def create_app():
    app = Flask(__name__)

    # App Config
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///expense_manager.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-dev-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    JWTManager(app)
    CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

    # Register Blueprints
    app.register_blueprint(shared_bp)
    app.register_blueprint(personal_bp)
    app.register_blueprint(auth_bp)  # if exists

    # Basic health check
    @app.route("/health")
    def health():
        return jsonify({"status": "healthy"})

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
