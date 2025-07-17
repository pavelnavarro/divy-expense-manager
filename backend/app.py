# app.py

import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from backend.config import Config
# extensions
from backend.extensions import db, bcrypt, jwt
# JWT identity for templates
from flask_jwt_extended import get_jwt_identity
# blueprints
from backend.routes.auth_routes      import auth_bp
from backend.routes.personal_routes  import personal_bp
from backend.routes.shared_routes    import shared_bp
from backend.routes.calendar_routes  import calendar_bp
from backend.routes.frontend_routes  import frontend_bp


def create_app():
    # Base directory of this file
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Template & static folders
    TEMPLATE_DIR = os.path.join(BASE_DIR, '..', 'frontend', 'templates')
    STATIC_DIR   = os.path.join(BASE_DIR, '..', 'frontend', 'static')

    app = Flask(
        __name__,
        template_folder=TEMPLATE_DIR,
        static_folder=STATIC_DIR,
        static_url_path='/static'
    )
    app.config.from_object(Config)

    # Expose JWT identity function in Jinja templates
    app.jinja_env.globals['get_jwt_identity'] = get_jwt_identity

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    # Enable CORS with credentials support for cookies
    CORS(
        app,
        origins=app.config['CORS_ORIGINS'],
        supports_credentials=True
    )

    # Register blueprints
    app.register_blueprint(auth_bp,      url_prefix='/api/auth')
    app.register_blueprint(personal_bp,  url_prefix='/api/personal')
    app.register_blueprint(shared_bp,    url_prefix='/api/shared')
    app.register_blueprint(calendar_bp,  url_prefix='/api/calendar')
    app.register_blueprint(frontend_bp,  url_prefix='')

    return app


if __name__ == '__main__':
    load_dotenv()
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true',
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000))
    )
