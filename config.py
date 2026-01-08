import os
from datetime import timedelta

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
    SESSION_PERMANENT=False
    SESSION_COOKIE_HTTPONLY=True
    SESSION_REFRESH_EACH_REQUEST=True
    SESSION_COOKIE_SECURE=True
    # I changed this to 6 hours because this is where it stores the aircraft registration currently
    # being maintained in the plant maintenance system.
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=360)
    SMTP_MAIL_ADDRESS="ascgliding@gmail.com"
    # This is being obfuscated to stop github from whining.
    # The password is actually stored in the slots table but I'm keeping it here
    # so we don't lose it.
    # it is: lgtm ppbj makb dfei
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

class development(Config):
    # Note that this config assumes windows.
    MAIL_DEBUG = 'ray@rayburns.nz'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.instance_path, 'asc.sqlite')
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=3)
    LOGCLEAR = True
    LOGLEVEL = 'DEBUG'

class dayend(Config):
    MAIL_DEBUG = 'ray@rayburns.nz'
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
