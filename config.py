import os

import flask
from flask import Flask, current_app


# --------------------------------------------------------------------
# Be careful here... in order to access current_app this module
# must be loaded within an application context (whatever thay may be).
# This is done __init__.py.  Look at the create_filters function
# to see how this is done.
# --------------------------------------------------------------------

from flask import current_app
app = current_app

class Config(object):
    SECRET_KEY='dev'
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    LOGFILE='asc.log'
    LOGCLEAR=True
    LOGLEVEL='INFO'


class development(Config):
    # Note that this config assumes windows.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.instance_path, 'asc.sqlite')
    LOGCLEAR = True
    LOGLEVEL = 'DEBUG'

class dayend(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.instance_path, 'asc.sqlite')
    LOGCLEAR = False
    LOGLEVEL = 'DEBUG'

class production(Config):
    # Note that this config assumes Unix.
    SQLALCHEMY_DATABASE_URI = 'sqlite:////' + os.path.join(app.instance_path, 'asc.sqlite')
    LOGLEVEL='INFO'

# class windevel(Config):
#     # Note that this config assumes windows.
#     # SQLALCHEMY_DATABASE_URI = 'sqlite:////' + os.path.join(app.instance_path, 'asc.sqlite')
#     SQLALCHEMY_DATABASE_URI = 'sqlite:///c:\\users\\rayb\\pythonvenv\\flask310\\var\\asc-instance\\asc.sqlite'
#     LOGCLEAR = True
#     LOGLEVEL = 'DEBUG'
