from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Flask, send_from_directory, current_app
)
from werkzeug.exceptions import abort
from flask_login import current_user
from asc.schema import *
from sqlalchemy import text as sqltext

# app = Flask(__name__)
# from asc import create_app
# app = create_app()
app = current_app

bp = Blueprint('index', __name__)
applog = app.logger

@app.before_request
def before_request():
    # applog.debug("Accessing {}".format(request.path))
    # print("index.py - before_request")
    # print('Path {}'.format(request.path))
    # print('User {}'.format(current_user))
    # print('User ID {}'.format(current_user.id))
    # print('Current User Name {}'.format(current_user.name))
    # m= Member.query.filter(Member.gnz_no==current_user.gnz_no).first()
    # print('Member Name {}'.format(m.fullname))
    # does this view have any security defined:
    sql = sqltext('''
        select count(*)
    	from viewsecurity 
    	where substr(:page,1,length(viewname)) = viewname
        ''')
    secdefined = db.engine.scalar(sql, page=request.path)
    if secdefined > 0:
        # there is security defined so who has access?
        applog.debug("Access Page: {}".format(request.path))
        sql = sqltext('''
        select count(*)
--        DISTINCT  t3.name
        from viewsecurity t0, roles t1, user_roles t2, users t3
        where t1.id = t0.role_id 
        and t2.role_id  = t0.role_id 
        and t3.id  = t2.user_id 
        and substr(:page,1,length(viewname)) = viewname
        and t3.name = :user
        ''')
        useracccess = db.engine.scalar(sql, page=request.path, user=current_user.name)
        if useracccess == 0:
            flash('Sorry, you do not have access to that page.', "error")
            applog.info("Access Denied {}".format(request.path))
            return redirect(url_for("index"))
        else:
            return None  #  carry on with view
    else:
        return None  # carry on with view

    #pass

@bp.route('/')
def index():

    app.logger.info("Main Page accessed")

    return render_template('index.html')

