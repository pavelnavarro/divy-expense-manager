from flask import Flask
from flask_cors import CORS
from backend.extensions import db
from backend.routes.shared_routes import shared_bp
import os

app = Flask(__name__)
CORS(app)

# Load config (you can use environment variables here too if needed)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///divy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with the app
db.init_app(app)

# Register routes
app.register_blueprint(shared_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Optional: create tables on first run
    app.run(debug=True)
