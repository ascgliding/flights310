import functools
import datetime

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Flask, jsonify, make_response, abort
)
from flask_sqlalchemy import SQLAlchemy
from asc.schema import *
from asc import db,create_app # but isnt't this already imported by the previous line ?
from flask_login import current_user, login_user, login_required, logout_user, fresh_login_required, login_manager

# WTforms
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import Form, StringField, PasswordField, validators, SubmitField, SelectField, BooleanField, RadioField, \
    TextAreaField, DecimalField, Field, FieldList, ValidationError
from wtforms.fields import EmailField, IntegerField, DateField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, optional, Regexp
from asc.wtforms_ext import MatButtonField, TextButtonField


from asc.mailer import ascmailer

app = Flask(__name__)
# app = create_app()
applog = app.logger


bp = Blueprint('auth', __name__, url_prefix='/auth')

#
# @app.before_request
# def before_request():
#     applog.debug("In before_request")


# def is_safe_url(target):
#     ref_url = urllib.parse(request.host_url)
#     test_url = urllib.parse(urllib.parse.urljoin(request.host_url, target))
#     return test_url.scheme in ('http', 'https') and \
#            ref_url.netloc == test_url.netloc

class RoleMaint(FlaskForm):
    name = StringField('Role', description='The name of the Role')
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')
    delete = SubmitField('delete', id='deletebtn', render_kw={"OnClick": "ConfirmDelete()"})

class ViewMaint(FlaskForm):
    viewname = StringField('View', description='The leading characters of the view including the path')
    role_id = SelectField('Role', description='Role who has access')
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')
    delete = SubmitField('delete', id='deletebtn', render_kw={"OnClick": "ConfirmDelete()"})

class UserRoleMaint(FlaskForm):
    user_id = SelectField('User', description='User id')
    role_id = SelectField('Role', description='Role user plays')
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')
    delete = SubmitField('delete', id='deletebtn', render_kw={"OnClick": "ConfirmDelete()"})


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        # usernames must always be lowercase.
        # the usernamechanged boolean is important because
        # we do a session.clear a bit later on so we just need to remember to flash the message
        # otherwise it will disappear.
        usernamechanged = False
        if username != username.lower():
            usernamechanged = True
        username = username.lower()
        password = request.form['password']
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        else:
            # check user is unique
            exists = User.query.filter_by(name=username).count()
            if exists > 0:
                flash("This user id has already been used by someone else.")
                return render_template('auth/register.html')
            if current_user.is_authenticated:
                flash("Already authenticated!")
                return redirect(url_for('auth.profile'))
            thisuser = User(username)
            thisuser.set_password(request.form['password'])
            thisuser.fullname=request.form['fullname']
            thisuser.authenticated = True
            db.session.add(thisuser)
            db.session.commit()
            flash("You have been registered")
            app.logger.info('New user : {} registered'.format(username))
            # return redirect(url_for('auth.profile'))
            # Now login in the user (otherwise they will be forced to via @login)
            session.clear()
            if usernamechanged:
                flash("Note that your entered username has been changed to lowercase","warning")
                flash("You have been registered.  The sysadmin needs to approve your registration before you can access the system.")
            # email appropriate person
            # emaillist =  db.session.query(Slot).filter(Slot.slot_type == 'APPROVEUSERMAIL').all()
            emaillist = Slot.query.filter_by(slot_type='SYSTEM').filter_by(slot_key='APPROVEUSERMAIL').all()
            if len(emaillist) > 0:
                for email in emaillist:
                    thisemail = email.slot_data
                    mail = ascmailer(thisuser.name + ' has registered and needs approving')
                    mail.add_body('User with fullname ' + thisuser.fullname + ' has newly registered and needs approving')
                    mail.add_recipient(thisemail)
                    mail.send()
            login_user(User(username), remember=True, duration=datetime.timedelta(days=5))
            app.logger.info('User : {} Logged in'.format(username))
            app.logger.info("User Agent:{}".format(request.user_agent.string))
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    applog.debug("Starting Login Process")
    if request.method == 'POST':
        username = request.form['username']
        username = username.lower()
        password = request.form['password']
        error = None
        thisuser = User.query.filter_by(name=username).one_or_none()
        if thisuser is None:
            error = 'Incorrect username.'
        elif not thisuser.is_correct_password(password):
            error = 'Incorrect password.'
        if error is None:
            if not thisuser.is_approved:
                flash('Your Registration has not yet been approved by the system administrator')
                return render_template('auth/login.html')
            try:
                session.clear()
                thisuser.authenticated = True
                db.session.commit()
                login_user(thisuser, remember=True, duration=datetime.timedelta(days=5))
                app.logger.info('User : {} Logged in'.format(thisuser.fullname or thisuser.name))
                app.logger.info("User Agent:{}".format(request.user_agent.string))
                # when this page has been called due to a fresh login required function then it has a "next" parameter
                # which is the page the person originally asked for, so we should go there if defined
                next = request.args.get('next')
                # return redirect(next or url_for('index'))
                return redirect(next or url_for('flights.daysummary'))
            except Exception as e:
                flash(e)
        flash(error)
    applog.debug("About to render login.html")
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    app.logger.info("User {} user logging out".format(current_user.fullname or current_user.name))
    # update the user object
    current_user.authenticated = False
    db.session.commit()
    # logout the user via flask_login
    logout_user()
    # clear the session
    session.clear()
    # remove the cookie
    resp = redirect(url_for("auth.login"))
    resp.set_cookie('remember_token', expires=0)
    app.logger.info("Logout Successful")
    return resp


@bp.route('/profile', methods=['GET', 'POST'])
@fresh_login_required
def profile():
    if request.method == 'POST':
        if 'pwdbtn' in request.form:
            return redirect(url_for('auth.password'))
        current_user.fullname = request.form['fullname']
        current_user.email = request.form['email']
        if 'administrator' in request.form:
            current_user.administrator = True
        # Can't have this else here (and more importantly - approval).
        # The user registers and is approved.  They login and change their email
        # address - then they lose their approval status!!!
        # else:
         #    current_user.administrator = False
        if 'approved' in request.form:
            current_user.approved = True
        # See note above.
        # else:
         #    current_user.approved = False
        db.session.commit()
        return redirect(url_for('index'))
    else:
        return render_template("auth/profile.html")

# This routine is for changing the current user's password

@bp.route('/password', methods=['GET', 'POST'])
@fresh_login_required
def password():
    if request.method == 'POST':
        # Validate current password
        if not current_user.is_correct_password(request.form['oldpwd']):
            flash('Current Password is not correct')
        else:
            if request.form['newpwd'] != request.form['newpwd2']:
                flash("The new password that you have entered twice are different")
            else:
                current_user.set_password(request.form['newpwd'])
                db.session.commit()
                return redirect(url_for('index'))
        return render_template("auth/password.html")
    else:
        return render_template("auth/password.html")

# This routine is for setting someone else's password.
@bp.route('/userpassword/<id>', methods=['GET', 'POST'])
@fresh_login_required
def userpassword(id):
    thisuser = User.query.get(id)
    if request.method == 'POST':
        # Validate current password
        if request.form['newpwd'] != request.form['newpwd2']:
            flash("The new password that you have entered twice are different")
        else:
            thisuser.set_password(request.form['newpwd'])
            db.session.commit()
            return redirect(url_for('index'))
        return render_template("auth/userpassword.html", user=thisuser)
    else:
        return render_template("auth/userpassword.html", user=thisuser)


@bp.route('/userlist')
@fresh_login_required
def userlist():
    if not current_user.administrator:
        flash("You are not authorised to this page.")
        return redirect(url_for('index'))
    users = db.session.query(User).all()
    return render_template("auth/userlist.html", users=users)


@bp.route('/usermaint/<id>', methods=['GET', 'POST'])
@fresh_login_required
def usermaint(id):
    if not current_user.administrator:
        flash("You are not authorised to this page.")
        return redirect(url_for('index'))
    thisuser = User.query.filter_by(id=id).one_or_none()
    if request.method == 'POST' and 'cancelbtn' in request.form:
        return redirect(url_for("auth.userlist"))
    if request.method == 'POST' and 'pwdbtn' in request.form:
        return redirect(url_for('auth.userpassword', id=id))
    if request.method == 'POST' and 'donebtn' in request.form:
        if thisuser is None:  # then new user
            # Create one and set the name
            thisuser = User()
            thisuser.name = request.form['name']
            thisuser.set_password(request.form['password'])
            db.session.add(thisuser)
        thisuser.fullname = request.form['fullname']
        thisuser.email = request.form['email']
        thisuser.gnz_no = request.form['gnz_no']
        if 'administrator' in request.form:
            thisuser.administrator = True
        else:
            thisuser.administrator = False
        if 'approved' in request.form:
            thisuser.approved = True
        else:
            thisuser.approved = False
        db.session.commit()
        return redirect(url_for("auth.userlist"))
    if request.method == 'POST' and 'deletebtn' in request.form:
        try:
            db.session.delete(thisuser)
            db.session.commit()
            return redirect(url_for("auth.userlist"))
        except Exception as ex:
            flash(str(ex))
    return render_template("auth/usermaint.html", user=thisuser)

# Todo:  Add role maintenance (list and edit), assign role to user, View Maintenance (list and edit)
@bp.route('/rolelist')
@fresh_login_required
def rolelist():
    if not current_user.administrator:
        flash("You are not authorised to this page.")
        return redirect(url_for('index'))
    roles = db.session.query(Role).all()
    return render_template("auth/rolelist.html", roles=roles)

@bp.route('/rolemaint/<id>', methods=['GET', 'POST'])
@login_required
def rolemaint(id):
    if not current_user.administrator:
        flash("You are not authorised to this page.")
        return redirect(url_for('index'))
    thisrec = Role.query.get(id)
    if thisrec is None:
        thisrec = Role()
    thisform = RoleMaint(obj=thisrec)
    if request.method == 'POST':
        if thisform.cancel.data:
            return redirect(url_for('auth.rolelist'))
        if thisform.delete.data:
            db.session.delete(thisrec)
            try:
                applog.info('DELETE:' + repr(thisrec))
                db.session.commit()
            except Exception as e:
                applog.error(str(e))
                flash(
                    "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                    "error")
            return redirect(url_for('auth.rolelist'))
        if not thisform.validate_on_submit():
            for e in thisform.errors:
                flash(e, "error")
                return render_template('auth/rolemaint.html', form=thisform)
        # By this point, we are either adding or updating.
        thisform.populate_obj(thisrec)
        # Code based validation:
        if thisrec.id is None:
            db.session.add(thisrec)
        applog.info('UPDATE:' + repr(thisrec))
        try:
            db.session.commit()
        except Exception as e:
            applog.error(str(e))
            flash(
                "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                "error")
        return redirect(url_for('auth.rolelist'))
    return render_template('auth/rolemaint.html', form=thisform)

# View Security
@bp.route('/viewlist')
@fresh_login_required
def viewlist():
    if not current_user.administrator:
        flash("You are not authorised to this page.")
        return redirect(url_for('index'))
    if not current_user.administrator:
        flash("You are not authorised to this page.")
        return redirect(url_for('index'))
    views = db.session.query(ViewSecurity).all()
    return render_template("auth/viewlist.html", views=views)

@bp.route('/viewmaint/<id>', methods=['GET', 'POST'])
@login_required
def viewmaint(id):
    if not current_user.administrator:
        flash("You are not authorised to this page.")
        return redirect(url_for('index'))
    thisrec = ViewSecurity.query.get(id)
    if thisrec is None:
        thisrec = ViewSecurity()
    thisform = ViewMaint(obj=thisrec)
    thisform.role_id.choices = [(r.id, r.name) for r in Role.query.all()]
    if request.method == 'POST':
        if thisform.cancel.data:
            return redirect(url_for('auth.viewlist'))
        if thisform.delete.data:
            db.session.delete(thisrec)
            try:
                applog.info('DELETE:' + repr(thisrec))
                db.session.commit()
            except Exception as e:
                applog.error(str(e))
                flash(
                    "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                    "error")
            return redirect(url_for('auth.viewlist'))
        if not thisform.validate_on_submit():
            for e in thisform.errors:
                flash(e, "error")
                return render_template('auth/viewmaint.html', form=thisform)
        # By this point, we are either adding or updating.
        thisform.populate_obj(thisrec)
        # Code based validation:
        if thisrec.id is None:
            db.session.add(thisrec)
        applog.info('UPDATE:' + repr(thisrec))
        try:
            db.session.commit()
        except Exception as e:
            applog.error(str(e))
            flash(
                "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                "error")
        return redirect(url_for('auth.viewlist'))
    return render_template('auth/viewmaint.html', form=thisform)


# User / Roles Security
@bp.route('/userrolelist')
@fresh_login_required
def userrolelist():
    if not current_user.administrator:
        flash("You are not authorised to this page.")
        return redirect(url_for('index'))
    views = db.session.query(UserRoles).all()
    return render_template("auth/userrolelist.html", views=views)

@bp.route('/userrolemaint/<id>', methods=['GET', 'POST'])
@login_required
def userrolemaint(id):
    if not current_user.administrator:
        flash("You are not authorised to this page.")
        return redirect(url_for('index'))
    thisrec = UserRoles.query.get(id)
    if thisrec is None:
        thisrec = UserRoles()
    thisform = UserRoleMaint(obj=thisrec)
    thisform.user_id.choices = [(r.id, r.fullname) for r in User.query.all()]
    thisform.role_id.choices = [(r.id, r.name) for r in Role.query.all()]
    if request.method == 'POST':
        if thisform.cancel.data:
            return redirect(url_for('auth.userrolelist'))
        if thisform.delete.data:
            db.session.delete(thisrec)
            try:
                applog.info('DELETE:' + repr(thisrec))
                db.session.commit()
            except Exception as e:
                applog.error(str(e))
                flash(
                    "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                    "error")
            return redirect(url_for('auth.userrolelist'))
        if not thisform.validate_on_submit():
            for e in thisform.errors:
                flash(e, "error")
                return render_template('auth/userrolemaint.html', form=thisform)
        # By this point, we are either adding or updating.
        thisform.populate_obj(thisrec)
        # Code based validation:
        if thisrec.id is None:
            db.session.add(thisrec)
        applog.info('UPDATE:' + repr(thisrec))
        try:
            db.session.commit()
        except Exception as e:
            applog.error(str(e))
            flash(
                "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                "error")
        return redirect(url_for('auth.userrolelist'))
    return render_template('auth/userrolemaint.html', form=thisform)







