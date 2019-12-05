from flask import Flask, Blueprint
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from config import config


bootstrap = Bootstrap()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_message = (
    u"Пожалуйста войдите в учетную запись для"
    u" доступа к данной странице"
    )

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name]) #load config for app

    #init flask-exstensions:
    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    # redirect user to login page 'auth/login' if needed
    login_manager.login_view = 'auth.login'

    #register blueprint
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app
