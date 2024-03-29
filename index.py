from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Flask, send_from_directory, current_app
)
from werkzeug.exceptions import abort

# app = Flask(__name__)
# from asc import create_app
# app = create_app()
app = current_app

bp = Blueprint('index', __name__)
applog = app.logger

@app.before_request
def before_request():
    # applog.debug("In before_request")
    pass

@bp.route('/')
def index():
    # print(request.headers.get('User-Agent'))
    # print(request.user_agent.platform)
    # print(request.user_agent.browser)
    # print(request.user_agent.version)
    # print(request.user_agent.language)
    # thisagent = request.user_agent
    app.logger.info("Main Page accessed")

    return render_template('index.html')

