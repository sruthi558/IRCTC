from flask import Flask, jsonify, session
from datetime import timedelta
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)
import os
import werkzeug.exceptions
import logging
import logging.handlers as handlers
from flask.logging import default_handler



# Login Manager config setup
login_manager = LoginManager()
login_manager.login_view = "auth.login"

# DB Object init
db = SQLAlchemy()


def setup_upload_folder():
    path = os.getcwd()
    # file Upload
    UPLOAD_FOLDER = os.path.join(path, 'uploads')
    # Make directory if "uploads" folder not exists
    if not os.path.isdir(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)

    return UPLOAD_FOLDER

def setup_log_folder():
    path = os.getcwd()
    LOG_FOLDER = os.path.join(path, 'logger')

    if not os.path.isdir(LOG_FOLDER):
        os.mkdir(LOG_FOLDER)
    return LOG_FOLDER


def create_app():
    app = Flask(__name__)

    cors = CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True,
                headers=['Content-Type', 'Authorization', 'Set-Cookie'])

    UPLOAD_FOLDER = setup_upload_folder()
    LOG_FOLDER = setup_log_folder()
    # Config Setup
    app.config['SECRET_KEY'] = 'secret_key'
    # app.config['SESSION_COOKIE_SECURE'] = True
    # app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['LOG_FOLDER'] = LOG_FOLDER
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./db.sqlite'
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 * 1024
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Login and DB init
    login_manager.init_app(app)
    db.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    # Blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # #### Error Handler

    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({'detail': 'SERVER_ERROR'}), 500

    @app.errorhandler(werkzeug.exceptions.BadRequest)
    def handle_bad_request(e):
        return jsonify({'detail': 'BAD_REQUEST'}), 400

    # @app.errorhandler(400)
    # def internal_server_error(e):
    #     return jsonify({'detail':'SERVER_ERROR'}), 400

    # Session handling starter

    @app.before_request
    def session_handler():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=25)

    app.logger.removeHandler(default_handler)
    app.logger.setLevel(logging.INFO)

    ## Here we define our formatter
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

    logHandler = handlers.TimedRotatingFileHandler('logger/record.log', when='midnight')
    logHandler.setLevel(logging.INFO)
    logHandler.setFormatter(formatter)
    app.logger.addHandler(logHandler)

    return app
