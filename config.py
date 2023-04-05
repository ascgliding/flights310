import os

import flask
from flask import Flask, current_app

print("in config")
# from asc import create_app

app = Flask(__name__, instance_relative_config=True)
# # app = Flask(__name__)
# app = create_app()

class Config(object):
    SECRET_KEY='dev'
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    LOGFILE='asc.log'
    LOGCLEAR=True
    LOGLEVEL='INFO'
    DATABASE = os.path.join(app.instance_path, 'asc.sqlite'),


class development(Config):
    # Note that this config assumes windows.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.instance_path, 'asc.sqlite')
    LOGCLEAR = True
    LOGLEVEL = 'DEBUG'

class production(Config):
    # Note that this config assumes Unix.
    SQLALCHEMY_DATABASE_URI = 'sqlite:////' + os.path.join(app.instance_path, 'asc.sqlite')
    LOGLEVEL='INFO'

class windevel(Config):
    # Note that this config assumes windows.
    # SQLALCHEMY_DATABASE_URI = 'sqlite:////' + os.path.join(app.instance_path, 'asc.sqlite')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///c:\\users\\rayb\\pythonvenv\\flask310\\var\\asc-instance\\asc.sqlite'
    LOGCLEAR = True
    LOGLEVEL = 'DEBUG'
