import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CGSAPP_ADMIN = os.environ.get('CGSAPP_ADMIN')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    CGSAPP_ADMIN = os.environ.get('CGSAPP_ADMIN')

config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig,
    }
