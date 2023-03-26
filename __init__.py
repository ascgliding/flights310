import os
import logging
import getpass
import sys
from logging.handlers import RotatingFileHandler
from flask_login import LoginManager, current_user
from flask_login import __version__ as flogin_version
import argparse
from flask import Flask, session, g, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import __version__ as fsqa_version
from flask import __version__ as flask_version
from flask import Flask
from flask_wtf import __version__ as flaskwtf_version
from wtforms import __version__ as wft_version
from sqlalchemy import __version__ as sqa_version
import asc.jingafilters

if sys.platform != 'win32':
    import pwd


# It is import that the following syntax is used.
# from asc.import * will not work - it will get hung up with the circular reference to db.
# import asc.schema



class UserIDFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.
    """
    # The standard logger does not include an attribute for the user name.  This is done by adding this function
    def filter(record):
        try:
            record.user_id = session.get('user_id')
        except Exception as e:
            if sys.platform == 'win32':
                record.user_id = os.getlogin()
            else:
                record.user_id = pwd.getpwuid(os.getuid()).pw_name
        return True



#System Wide Variables


db = SQLAlchemy()

login_manager = LoginManager()
# login_manager.login_message = "You must be logged into the system to access this page"
# login_manager.login_view = "auth.login"
# login_manager.refresh_view = "auth.login"
# login_manager.needs_refresh_message = u'You must re-fresh your login to access this page'


def create_filters(app):
    app.logger.info('Adding Filters')
    app.jinja_env.filters['tsdate'] = jingafilters.tsdateformat
    app.jinja_env.filters['hrsmins'] = jingafilters.hrsmins
    app.jinja_env.filters['hrsminsfromtime'] = jingafilters.hrsminsfromtime
    app.jinja_env.filters['hrsdec'] = jingafilters.hrsdec
    app.jinja_env.filters['tsdateinput'] = jingafilters.datetimehtml
    app.jinja_env.filters['stddate'] = jingafilters.reformatstddate
    app.jinja_env.filters['datetimehtml'] = jingafilters.datetimehtml
    app.jinja_env.filters['objvariable'] = jingafilters.objvariable
    app.jinja_env.filters['hhmmss'] = jingafilters.hhmmss
    app.jinja_env.filters['currency'] = jingafilters.currency
    app.jinja_env.filters['displayfornone'] = jingafilters.displayfornone
    app.jinja_env.filters['nameinitials'] = jingafilters.nameinitials

def create_app(test_config=None):
    '''
    This function is called automatically when the app starts.
    There is no specific call to it anywhere else
    :param test_config: The configuration
    :return: app
    '''
    # -----------------------------------------------------------------------------------------------------
    # create and configure the app
    # -----------------------------------------------------------------------------------------------------
    # print("create_app being called with Flask {}".format(flask_version))
    app = Flask(__name__, instance_relative_config=True)
    # app.config.from_object('asc.config.' + os.environ.get('FLASK_ENV', default='development'))

    # if sys.platform == 'win32':
    #     app.config.from_object('asc.config.windevel')
    # else:
    #     app.config.from_object('asc.config.' + os.environ.get('FLASK_ENV', default='development'))

    app.config.from_object('asc.config.' + os.environ.get('CONFIG', default='development'))

    # if sys.platform == 'win32':
    #
    #     # Note that to connect to sqlite from a windows platform you need 3 "/" characters in the
    #     # SQLALCHEMY_DATABASE_URI but on unix platforms you need 4 (!!!)
    #     app.config.from_mapping(
    #         SECRET_KEY='dev',
    #         DATABASE=os.path.join(app.instance_path, 'asc.sqlite'),
    #         SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.instance_path, 'asc.sqlite'),
    #         SQLALCHEMY_TRACK_MODIFICATIONS=False,
    #         LOGFILE='asc.log',
    #         LOGCLEAR=True,
    #         LOGLEVEL='DEBUG'
    #     )
    # else:
    #     app.config.from_mapping(
    #         SECRET_KEY='dev',
    #         DATABASE=os.path.join(app.instance_path, 'asc.sqlite'),
    #         SQLALCHEMY_DATABASE_URI = 'sqlite:////' + os.path.join(app.instance_path, 'asc.sqlite'),
    #         SQLALCHEMY_TRACK_MODIFICATIONS=False,
    #         LOGFILE='asc.log',
    #         LOGCLEAR=True,
    #         LOGLEVEL='DEBUG'
    #     )
    # -----------------------------------------------------------------------------------------------------
    # Load Configuration
    # -----------------------------------------------------------------------------------------------------
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)
    # -----------------------------------------------------------------------------------------------------
    # ensure the instance folder exists
    # -----------------------------------------------------------------------------------------------------
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    # -----------------------------------------------------------------------------------------------------
    # Load the filters
    # -----------------------------------------------------------------------------------------------------
    create_filters(app)
    # -----------------------------------------------------------------------------------------------------
    # Load the logger
    # -----------------------------------------------------------------------------------------------------
    establish_logging(app)
    # for x in dir(app.logger):
    #     print(x, getattr(app.logger,x))
    # print("----------------------------------------------------")
    app.logger.info("ASC Application Started")
    app.logger.info("Create_app called with Flask {}".format(flask_version))
    app.logger.info("Python Version {}".format(sys.version))
    # -----------------------------------------------------------------------------------------------------
    # Load the login manager
    # -----------------------------------------------------------------------------------------------------
    establish_login_extension(app)
    # -----------------------------------------------------------------------------------------------------
    # Load the database
    # -----------------------------------------------------------------------------------------------------
    establish_database(app)
    # -----------------------------------------------------------------------------------------------------
    # Register blueprints
    # -----------------------------------------------------------------------------------------------------
    resgister_blueprints(app)

    app.logger.info("WTForms Version {}".format(wft_version))
    app.logger.info("Flask WTForms Version {}".format(flaskwtf_version))
    app.logger.info("app instance path (in create_app __init__.py)_ is {}".format(app.instance_path))
    app.logger.info("pythonpath (in create_app __init__.py)_ is {}".format(os.environ['PYTHONPATH']))
    app.logger.info("ASC Create Complete")

    return app

# -----------------------------------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------------------------------


def establish_logging(app):
    # -----------------------------------------------------------------------------------------------------
    # Establish logging
    # -----------------------------------------------------------------------------------------------------
    try:
        loghandler = RotatingFileHandler(os.path.join(app.instance_path,app.config['LOGFILE']), maxBytes=1000000, backupCount=3)

        if app.config['LOGLEVEL'] == 'CRITICAL':
            app.logger.setLevel(logging.CRITICAL)
        elif app.config['LOGLEVEL'] == 'ERROR':
            app.logger.setLevel(logging.ERROR)
        elif app.config['LOGLEVEL'] == 'WARNING':
            app.logger.setLevel(logging.WARNING)
        elif app.config['LOGLEVEL'] == 'INFO':
            app.logger.setLevel(logging.INFO)
        else:
            app.logger.setLevel(logging.DEBUG)
        fmt = '%(asctime)s|%(filename)s|%(funcName)s|%(levelname)s|%(user_id)s|%(message)s'
        fmt_date = '%Y-%m-%d|%H:%M:%S'
        loghandler.addFilter(UserIDFilter)
        formatter = logging.Formatter(fmt, fmt_date)
        loghandler.setFormatter(formatter)
        # TODO: Fix pycharm logging:
        #  There appears to be a problem with Pycharm on windows.  The following code causes an error - it appears
        #  to need exclusive access to the file.  So not sure how this is supppwed to work.

        # Assign this loghandler to the apps logger object
        app.logger.addHandler(loghandler)

        try:
            if app.config['LOGCLEAR']:
                loghandler.doRollover()
        except Exception as e:
            app.logger.error("Note: Unable to roll log at Startup ({})".format(e))

        app.logger.info("Logging Established")
    except Exception as e:
        print("Failed to establish Logging: {}".format(e))


def establish_login_extension(app):
    # -----------------------------------------------------------------------------------------------------
    # Load the login manager
    # -----------------------------------------------------------------------------------------------------
    try:
        login_manager = LoginManager(app)
        login_manager.init_app(app)
        app.logger.debug("Login Manager initialised")
        app.logger.debug("Flask Login Version {}".format(flogin_version))
    except Exception as e:
        app.logger.debug("Failed to initialise login manager {}".format(e))
    login_manager.login_message = "You must be logged into the system to access this page"
    login_manager.login_view = "auth.login"
    login_manager.refresh_view = "auth.login"
    login_manager.needs_refresh_message = u'You must re-fresh your login to access this page'
    from asc.schema import User

    @login_manager.user_loader
    def load_user(user_id):
        app.logger.debug("Loading User {}".format(user_id))
        thisuser = User.query.filter_by(name=user_id).one_or_none()
        if thisuser is None:
            app.logger.error("The user object is none")
        else:
            if thisuser.authenticated:
                app.logger.debug("{} is Authenticated".format(thisuser.name))
            else:
                app.logger.debug("{} is not authenticated.".format(thisuser.name))
        return thisuser



def establish_database(app):
    # -----------------------------------------------------------------------------------------------------
    # Load and initialise the db
    # ----------------------------------------------------------------------------------------------------
    app.logger.info("app Instance Path {}".format(app.instance_path))
    try:
        from asc.schema import db
        app.logger.info("Flask SQLAlchemy version {}".format(fsqa_version))
        app.logger.info("SQL Alchemy version {}".format(sqa_version))
        app.logger.info("Schema Imported")
    except Exception as e:
        app.logger.error("There as a problem Importing the schema: {}".format(e))
    try:
        db.init_app(app)
        app.logger.info("Flask Alchemy {} initialised".format(sqa_version))
    except Exception as e:
        app.logger.error("There as a problem initialising flask alchemy: {}".format(e))
    try:
        with app.app_context():
            db.create_all()
            app.logger.info("Flask Alchemy Tables Created")
    except Exception as e:
        app.logger.error("There as a problem creating the tables: {}".format(e))
    ## Quick tests - both of these should access data::
    # try:
    #     with app.app_context():
    #         recs = db.engine.execute("select id,pic,p2,ac_regn,takeoff,landed from flights limit 10;").fetchall()
    #         print(recs)
    #         for r in recs:
    #             print(r)
    # except Exception as e:
    #     app.logger.error("There as a problem with direct sql: {}".format(e))
    # try:
    #     with app.app_context():
    #         flights = fschema.Flight.query.limit(10).all()
    #         for f in flights:
    #             print(f)
    # except Exception as e:
    #     app.logger.error("There as a problem accessing sql alchemy: {}".format(e))


def resgister_blueprints(app):
    # -----------------------------------------------------------------------------------------------------
    # Load the blueprints
    # -----------------------------------------------------------------------------------------------------

    try:

        # register authentication blueprint
        app_for_log = 'auth'
        from . import auth
        app.register_blueprint(auth.bp)
        #
        app_for_log = 'index'
        from . import index
        app.register_blueprint(index.bp)
        app.add_url_rule('/', endpoint='index')
        #
        # # Register the flights blueprint
        app_for_log = 'flights'
        from . import flights
        app.register_blueprint(flights.bp)
        app.add_url_rule('/flights', endpoint='daysummary')
        #
        app_for_log = 'mastmaint'
        from . import mastmaint
        app.register_blueprint(mastmaint.bp)
        app.add_url_rule('/mastmaint', endpoint='index')
        # # Register the membership blueprint
        app_for_log = 'membership'
        from . import membership
        app.register_blueprint(membership.bp)
        app.add_url_rule('/membership', endpoint='memberlist')
        #  Register the logbook blueprint
        app_for_log = 'logbook'
        from . import logbook
        app.register_blueprint(logbook.bp)
        app.add_url_rule('/logbook', endpoint='logbook')
        # Register the RESTAPI
        app_for_log = 'restapi'
        from . import restapi
        app.register_blueprint(restapi.bp)
        # Register the Excel Export
        from . import export
        app.register_blueprint(export.bp)
        #
        app.logger.info("All blueprints successfully registered")
    except Exception as e:
        app.logger.error("There was a problem registering a blueprint : {} ({})".format(str(e), app_for_log))

