# app.py

import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from backend.config import Config

# extensions
from backend.extensions import db, bcrypt, jwt
# blueprints
from backend.routes.auth_routes      import auth_bp
from backend.routes.personal_routes  import personal_bp
from backend.routes.shared_routes    import shared_bp
from backend.routes.calendar_routes  import calendar_bp



def create_app():

    # 2) create app and load config
    app = Flask(__name__)
    app.config.from_object(Config)

    # 3) init extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])

    # 4) register blueprints
    app.register_blueprint(auth_bp,      url_prefix='/api/auth')
    app.register_blueprint(personal_bp,  url_prefix='/api/personal')
    app.register_blueprint(shared_bp,    url_prefix='/api/shared')
    app.register_blueprint(calendar_bp,  url_prefix='/api/calendar')

    return app

if __name__ == '__main__':
    app = create_app()
    # create tables if they don't exist
    with app.app_context():
        db.create_all()
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true',
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000))
    )
