import datetime
import pprint

from dateutil.relativedelta import *

import sqlalchemy.sql.expression
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Flask, send_from_directory, current_app, session
)
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
import os
import csv

from flask_login import login_required, current_user
from asc import db, create_app
from asc.schema import *  # Aircraft, Tasks, Meters, ACMeters, MaintSchedule, MeterReadings, SqliteDecimal
from sqlalchemy import text as sqltext, delete, select

# WTforms
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import Form, StringField, PasswordField, validators, SubmitField, SelectField, BooleanField, RadioField, \
    TextAreaField, DecimalField, Field, FieldList, ValidationError
from wtforms.fields import EmailField, IntegerField, DateField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, optional, Regexp
# from wtforms_alchemy.fields import QuerySelectField


from asc.oMaint import ACMaint
from asc.mailer import ascmailer
import decimal

app = current_app
applog = app.logger

bp = Blueprint('plantmaint', __name__, url_prefix='/plantmaint')


def mins2hrsdec(value) -> str:
    if value is None:
        return "0"
    hrs = int(value / 60)
    mins = int(value - (hrs * 60))
    return str(hrs + round((mins / 60), 2))


def hrsdec2mins(value) -> int:
    return int(float(value) * 60)


def mins2hrsmins(value) -> str:
    if value is None:
        return "0"
    hrs = int(value / 60)
    mins = int(value - (hrs * 60))
    return str(hrs) + ':' + str(mins).zfill(2)


def hrsmins2mins(value) -> int:
    bits = value.split(':')
    hrs = int(bits[0])
    if len(bits) > 1:  # Occasionally, only hrs iss specified
        mins = int(bits[1])
    else:
        mins = 0
    return int((hrs * 60) + int(mins))

def format_reading(value,fmt) -> str:
    if fmt == 'Hours:Minutes' or fmt == 'Time':
        return str(mins2hrsmins(value))
    elif fmt == 'Decimal Hours':
        return str(mins2hrsdec(value))
    else:
        return str(value)


#########################################################################
#  WT Forms classes                                                     #
#########################################################################

# MEters - the problem is that a meter reading could be in miunutes which could be represented either as decimal hours
# or hours minutes, or it could be units (takeoffs/landings)

class HrsMinsWidget(object):

    def __call__(self, field, **kwargs):
        field_id = kwargs.pop('id', field.id)
        html = []
        html.append(
            '<input style="text-align:right;color:#2277FF" id="{}" name="{}" value="{}">'.format(field_id, field_id,
                                                                                                 mins2hrsmins(
                                                                                                     field.data)))
        return ' '.join(html)


class HrsMinsField(Field):
    widget = HrsMinsWidget()  # Note that the widget deals with converting the data from minutes to 99:99

    def process_formdata(self, valuedata):
        """
        Deals with the data after the form has been submitted
        Verify the data and raise any validation errors if required.
        If all ok set the value of self.data to be a decimal containing the number of minutes
        :param valuedata: List of values from the form.
        :return: None.  Sets self.data
        """
        if len(valuedata) != 0:
            if re.match("^[0-9]{1,5}:[0-5][0-9]$", valuedata[0]) is None \
                    and re.match("^[0-9]{1,5}$", valuedata[0]) is None:
                raise ValidationError("{} is not a valid time.".format(valuedata[0]))
            self.data = decimal.Decimal(hrsmins2mins(valuedata[0]))


class HrsWidget(object):

    def __call__(self, field, **kwargs):
        field_id = kwargs.pop('id', field.id)
        html = []
        html.append(
            '<input style="text-align:right;color:#2277FF" id="{}" name="{}" value="{}">'.format(field_id, field_id,
                                                                                                 mins2hrsdec(
                                                                                                     field.data)))
        return ' '.join(html)


class HrsField(Field):
    widget = HrsWidget()  # Note that the widget converts minutes to the display field

    def process_formdata(self, valuedata):
        """
        Deals with the data after the form has been submitted
        Verify the data and raise any validation errors if required.
        If all ok set the value of self.data to be a decimal containing the number of minutes
        :param valuedata: List of values from the form.
        :return: None.  Sets self.data
        """
        if len(valuedata) != 0:
            if re.match("^[0-9]{0,5}.[0-9]$", valuedata[0]) is None \
                    and re.match("^[0-9]{0,5}$", valuedata[0]) is None:
                raise ValidationError("{} is not a valid decimal time".format(valuedata[0]))
            self.data = decimal.Decimal(hrsdec2mins(valuedata[0]))


class TestForm(Form):
    name = 'My Test form'
    teststring = StringField('Test String', description="a string")
    hrsdec = HrsField('Hrs Field')
    hrsmin = HrsMinsField('Hrs mins field')
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')


@bp.route('/testform', methods=['GET', 'POST'])
def testform():
    if request.method == 'GET':
        # if we are in get, then we need to instantiate the formobject with blanks (or whatever)
        thisform = TestForm()
        thisform.hrsdec.data = 126  # 2.1 hours
        thisform.hrsmin.data = 244  # 4:04 mins
    if request.method == 'POST':
        if 'cancel' in request.form:
            return render_template("plantmaint/index.html")
        # If we are in post, then we need to instantiate the form object with request.form.
        thisform = TestForm(request.form)  # this step converts the custom time fields to minutes.
        if thisform.validate():
            print('in View: hrsdec is  {}'.format(thisform.hrsdec.data))
            print('in View: hrsmin is  {}'.format(thisform.hrsmin.data))
            # for entry in thisform.data:
            #     thisfld = getattr(thisform,entry)
            #     print('field {} has the value {}'.format(entry,thisfld.data))
            flash('done')
        else:
            flash('There was an error')
    return render_template('plantmaint/testform.html', form=thisform)


class StdTaskForm(FlaskForm):

    def __init__(self, *args, **kwargs):
        super(StdTaskForm, self).__init__(*args, **kwargs)
        self.task_meter_id.choices = [(None, "Not Applicable")]
        self.task_meter_id.choices.extend([
            (m.id, m.meter_name) for m in Meters.query.all()])

    def coerce_none(value):
        if value == 'None':
            return None
        return value

    name = 'Standard Task Maintenance'
    task_description = StringField('Description',
                                   [Length(min=1, message="The Code must be at least 1 characters long."),
                                    validators.DataRequired(message='You cannot have a blank Description'),
                                    ],
                                   description='A Short description of the task')

    task_basis = RadioField('Task Basis', choices=['Calendar', 'Meter'])
    task_calendar_uom = RadioField('Calendar Unit', choices=['Years', 'Months', 'Days'])
    task_calendar_period = IntegerField('Period', [validators.optional()],
                                        description='The number of years/months/days')
    task_meter_id = SelectField('Meter Id',
                                description="Meter",
                                coerce=coerce_none
                                )
    task_meter_period = IntegerField('Meter Count', [validators.optional()],
                                     description='The difference in meter readings between tasks', )

    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')
    delete = SubmitField('delete', id='deletebtn', render_kw={"OnClick": "ConfirmDelete()"})


class StdMeterForm(FlaskForm):
    name = "Standard Meter Maintenance"
    meter_name = StringField('Meter Name', [Length(min=1, message="The Meter must be at least 1 characters long."),
                                            validators.DataRequired(message='You cannot have a blank meter name'),
                                            ],
                             description='The Name for this meter')
    uom = SelectField('Unit of Measure',
                      choices=[('Time', 'Time such as hours'), ('Qty', 'Qty such as number of lauches or landings')])

    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')
    delete = SubmitField('delete', id='deletebtn', render_kw={"OnClick": "ConfirmDelete()"})


class StdUserAccessForm(FlaskForm):
    name = "User Access"

    ac_id = SelectField('Aircraft Id', description="Aircraft Registration")
    user_id = SelectField('User Id', description="User Login Id")
    maint_level = SelectField('Security Level', description="Security Level",
                              choices=[('Aircraft', 'Access to specific Aircraft'),
                                       ('All', 'Access to all maintenance functions including std meters and tasks'),
                                       ('Readings', 'Access only to enter readings')])

    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')
    delete = SubmitField('delete', id='deletebtn', render_kw={"OnClick": "ConfirmDelete()"})


class ACSelectNewMeterForm(FlaskForm):
    name = 'Select new meter to add to a/c'
    meter_id = SelectField('Meter',
                           description='The Meter Number',
                           render_kw={'style': 'width:300px'}
                           )
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')


class ACMeterMaintForm(FlaskForm):
    name = 'Maintain Meter on this A/c'
    id = IntegerField('ID')
    ac_id = IntegerField('Aircraft ID')
    meter_id = IntegerField('Meter ID')
    entry_prompt = StringField('Meter Prompt', description='Text to appear as label in meter reading screen')
    entry_uom = SelectField('Entry/Display Unit',
                            choices=[('Decimal Hours', 'Decimal Hours'), ('Hours:Minutes', 'Hours:Minutes'),
                                     ('Qty', 'Qty')])
    entry_method = SelectField('Entry Method',
                               description='Whether to enter ending meter readings or the change between between each reading',
                               choices=[('Reading', 'Enter the end meter reading'),
                                        ('Delta', 'Enter the CHANGE in meter readings (i.e. the incremental value)')]
                               )
    auto_update = BooleanField('Auto Update', description='Automatically update from club flying records (overnight).')
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')
    delete = SubmitField('delete', id='deletebtn', render_kw={"OnClick": "ConfirmDelete()"})


class ACSelectNewTaskForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(ACSelectNewTaskForm, self).__init__(*args, **kwargs)
        self.task_id.choices = [(t.id, t.task_description) for t in Tasks.query.all()]
        # now remove ones already there
        thisac = ACMaint(kwargs['ac'])
        if thisac is None:
            print('bugger...', kwargs['ac'])
        currentactaskids = [a.task_id for a in thisac.tasks]
        self.task_id.choices = []
        for t in Tasks.query.all():
            if t.id not in currentactaskids:
                self.task_id.choices.append((t.id, t.task_description))

        self.task_id.validate_choice = False

    name = 'Select new task to add to a/c'
    task_id = SelectField('Task',
                          description='The Task Number',
                          render_kw={'style': 'width:300px', 'readonly': True}
                          )
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')


class ACTaskForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(ACTaskForm, self).__init__(*args, **kwargs)
        # todo:  Should really be just the meters in that aeroplane
        self.meter_id.choices = [(None, "Not Applicable (calendar based)")]
        self.meter_id.choices.extend([
            (m.id, m.meter_name) for m in Meters.query.all()])
        self.meter_id.validate_choice = False
        self.task_id.choices = [(t.id, t.task_description) for t in Tasks.query.all()]
        self.task_id.validate_choice = False
        if kwargs['task_basis'] == 'Meter':
            self.meter_id.render_kw = {'disabled': True}
        # we can access all the data related to the object being displayed like this:
        # print('UOM in class is : {}'.format(kwargs['obj'].meter_rec().uom))
        # self.thisobj = kwargs['obj']

    def coerce_none(value):
        if value == 'None':
            return None
        return value

    name = "Aircraft Task Maintenance"
    # Even though we don't display the ac_id, we want on the form as a sort of place to store it
    # (Rather than a session cookie) so we can refer to it in the form POST.
    ac_id = IntegerField('Aircraft ID', description='Aircraft ID.')
    task_id = SelectField('Task',
                          description='The Task Number',
                          render_kw={'style': 'width:300px', 'disabled': True}
                          )
    # TODO:  Meter can ONLY be changed if the task is calendar based.
    meter_id = SelectField('Meter',
                           description="Meter used to drive this task",
                           coerce=coerce_none
                           )
    last_done = DateField('Last Done', [validators.optional()], description='The date this task was last performed')
    # This form is never used.  A form that inherits from this form will ve created with the correct uom for the display type.
    estimate_days = IntegerField('Average over Days',
                                 description='The number of days to average meter readings in order to estimate the next completion for a meter based task')
    warning_days = IntegerField('Warning Days', [validators.optional()],
                                description='The number of days prior to expiry to start sending warning emails')
    warning_email = StringField('Warning Email',
                                description='comma separated list of email addresses for warning emails')
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')
    delete = SubmitField('delete', id='deletebtn', render_kw={"OnClick": "ConfirmDelete()"})


class ACAddNewReadingForm(Form):
    name = "Enter New Readings"
    reading_date = DateField('Date', description='Date for these readings', default=datetime.date.today())
    note = StringField('Notes', description='Add any notes to describe the flying')
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')


def maintpagecheck(checkpagename=None):
    '''
    This is called by every page.  If checks if we are already dealing with an aircraft (via the session cookie)
    and if not redirects to the aircraft selection page.
    If there is a session cookie it builds the ac object ready for returning to the callling routine
    and checks the security.

    :param pagename:  This is optional.  If None, then it is assumed that the security level is for any page
                        Otherwise individual security can be checked.  Initially this will only be for
                        having some users who can enter readings or other users who can do anything.
    :return: The ac object or None if there is no security access.
    '''
    if 'regn' in session:
        thisac = ACMaint(session['regn'])
        if thisac is None:
            return redirect(url_for('plantmaint.maintainedac'))
        else:
            # TODO: now check security for page
            if thisac.get_security_level(current_user.id) is None:
                return None
            else:
                if checkpagename is None:
                    if thisac.get_security_level(current_user.id) in ['Aircraft', 'All']:
                        return thisac
                    else:
                        return None
                else:
                    if thisac.get_security_level(current_user.id) in ['Aircraft', 'All']:
                        return thisac
                    else:
                        if checkpagename == 'acaddnewreading':
                            if thisac.get_security_level(current_user.id) in ['Aircraft', 'All', 'Readings']:
                                return thisac
                            else:
                                return None
                        else:  # A page has been passed but we don't know which one AND the user does not have aircraft access
                            return None
    else:
        return None
        return redirect(url_for('plantmaint.maintainedac'))


# Aircraft with maintenance Schedules
@bp.route('/maintainedac', methods=['GET'])
@login_required
def maintainedac():
    if request.method == 'GET':
        sqlstmt = """
        select 
            t0.regn ,
            t0.id,
            t0.owner
        from aircraft t0 
        """
        sql_to_execute = sqlalchemy.sql.text(sqlstmt)
        # sql_to_execute = sql_to_execute.columns(transdate=db.Date)
        list = db.engine.execute(sql_to_execute).fetchall()
        return render_template('plantmaint/maintainedac.html', list=list)

@bp.route('/index',defaults={'pregn':None}, methods=['GET'])
@bp.route('/index/<pregn>', methods=['GET'])
@login_required
def index(pregn=None):
    if pregn is None:
        if 'regn' in session:
            thisac = ACMaint(session['regn'])
            return render_template('plantmaint/index.html', regn=thisac.regn)
        else:  # regn not in session:
            return render_template('../index.html')
    else:
        session['regn'] = pregn
        return render_template('plantmaint/index.html', regn=pregn)


@bp.route('/changeac', methods=['GET'])
@login_required
def changeac():
    session.pop('regn')
    return redirect(url_for('plantmaint.maintainedac'))


@bp.route('/stdtasklist', methods=['GET'])
@login_required
def stdtasklist():
    list = Tasks.query.all()
    return render_template('plantmaint/stdtasklist.html', list=list)


@bp.route('/stdtaskmaint/<id>', methods=['GET', 'POST'])
@login_required
def stdtaskmaint(id):
    if not current_user.administrator:
        flash("Sorry, this is an admin only function")
        return render_template('index.html')
    thisrec = Tasks.query.get(id)
    if thisrec is None:
        thisrec = Tasks()
    thisform = StdTaskForm(obj=thisrec)
    if request.method == 'POST' and thisform.validate:
        if thisform.cancel.data:
            return redirect(url_for('plantmaint.stdtasklist'))
        if thisform.delete.data:
            db.session.delete(thisrec)
            try:
                db.session.commit()
            except Exception as e:
                applog.error(str(e))
                flash(
                    "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                    "error")
            return redirect(url_for('plantmaint.stdtasklist'))
        # we have dealt with cancel and delete so deal with any data from the form....
        thisform.populate_obj(thisrec)
        # deal with select fields.  Data type is always strings.
        if thisrec.task_meter_id is not None:
            thisrec.task_meter_id = int(thisform.task_meter_id.data)
        # # add programming based validations
        if thisrec.task_basis == 'Calendar' and thisrec.task_calendar_uom is None:
            flash('You must specify a calendar uom for Calendar Based tasks', "error")
            return render_template('plantmaint/stdtaskmaint.html', form=thisform)
        if thisrec.task_basis == 'Calendar' and thisrec.task_calendar_period is None:
            flash('You must specify a calendar period for Calendar Based tasks', 'error')
            return render_template('plantmaint/stdtaskmaint.html', form=thisform)
        if thisrec.task_basis == 'Calendar' and thisrec.task_calendar_period <= 0:
            flash('You must specify a non-zero calendar period for Calendar Based tasks', 'error')
            return render_template('plantmaint/stdtaskmaint.html', form=thisform)
        if thisrec.task_basis == 'Meter' and thisrec.task_meter_id is None:
            flash('You must specify a meter for Meter Based tasks', "error")
            return render_template('plantmaint/stdtaskmaint.html', form=thisform)
        if thisrec.task_basis == 'Meter' and thisrec.task_meter_period is None:
            flash('You must specify a meter period for Meter Based tasks', "error")
            return render_template('plantmaint/stdtaskmaint.html', form=thisform)
        if thisrec.task_basis == 'Meter' and thisrec.task_meter_period <= 0:
            flash('You must specify a positive non-zero meter period for Meter Based tasks', "error")
            return render_template('plantmaint/stdtaskmaint.html', form=thisform)
        if thisrec.task_meter_id is not None:
            if thisrec.task_meter_period is None:
                flash('You must specify a meter period when a Meter has been selected', 'error')
                return render_template('plantmaint/stdtaskmaint.html', form=thisform)
            if thisrec.task_meter_period is None:
                flash('You must specify a non-zero meter when a meter has been selected', 'error')
                return render_template('plantmaint/stdtaskmaint.html', form=thisform)
        # Add if required
        if thisrec.id is None:
            db.session.add(thisrec)
        try:
            db.session.commit()
        except Exception as e:
            applog.error(str(e))
            flash(
                "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                "error")
        return redirect(url_for('plantmaint.stdtasklist'))

    return render_template('plantmaint/stdtaskmaint.html', form=thisform, thisdesc=thisrec.recurrence_description())


@bp.route('/stdmeterlist', methods=['GET'])
@login_required
def stdmeterlist():
    list = db.engine.execute(sqlalchemy.sql.text("select id,meter_name,uom from meters")).fetchall()
    return render_template('plantmaint/stdmeterlist.html', list=list)


@bp.route('/stdmetermaint/<id>', methods=['GET', 'POST'])
@login_required
def stdmetermaint(id):
    if not current_user.administrator:
        flash("Sorry, this is an admin only function")
        return render_template('index.html')
    thisrec = Meters.query.get(id)
    if thisrec is None:
        thisrec = Meters()
    thisform = StdMeterForm(obj=thisrec)
    if thisform.validate_on_submit():
        if thisform.cancel.data:
            return redirect(url_for('plantmaint.stdmeterlist'))
        if thisform.delete.data:
            db.session.delete(thisrec)
            try:
                db.session.commit()
            except Exception as e:
                applog.error(str(e))
                flash(
                    "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                    "error")
            return redirect(url_for('plantmaint.stdmeterlist'))
        thisform.populate_obj(thisrec)
        # code based validation

        if thisrec.id is None:
            db.session.add(thisrec)
        try:
            db.session.commit()
        except Exception as e:
            applog.error(str(e))
            flash(
                "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                "error")
        return redirect(url_for('plantmaint.stdmeterlist'))
    return render_template('plantmaint/stdmetermaint.html', form=thisform)


@bp.route('/stduserlist', methods=['GET'])
@login_required
def stduserlist():
    thissql = """
        select t0.id,
            t1.regn,
            t2.fullname,
            t0.maint_level
            from acmaintuser t0
            join aircraft t1 on t0.ac_id = t1.id
            join users t2 on t2.id = t0.user_id
    """
    list = db.engine.execute(sqlalchemy.sql.text(thissql)).fetchall()
    return render_template('plantmaint/stduserlist.html', list=list)


@bp.route('/stdusermaint/<id>', methods=['GET', 'POST'])
@login_required
def stdusermaint(id):
    if not current_user.administrator:
        flash("Sorry, this is an amdin only function")
        return (render_template('index.html'))
    thisrec = ACMaintUser.query.get(id)
    if thisrec is None:
        thisrec = ACMaintUser()
    thisform = StdUserAccessForm(obj=thisrec)
    thisform.ac_id.choices = [(a.id, a.regn) for a in Aircraft.query.all()]
    thisform.user_id.choices = [(u.id, u.fullname) for u in User.query.all()]

    if thisform.validate_on_submit():
        if thisform.cancel.data:
            return redirect(url_for('plantmaint.stduserlist'))
        if thisform.delete.data:
            db.session.delete(thisrec)
            try:
                db.session.commit()
            except Exception as e:
                applog.error(str(e))
                flash(
                    "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                    "error")
            return redirect(url_for('plantmaint.stduserlist'))
        thisform.populate_obj(thisrec)
        if thisrec.id is None:
            db.session.add(thisrec)
            try:
                db.session.commit()
            except Exception as e:
                applog.error(str(e))
                flash(
                    "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                    "error")
        return redirect(url_for('plantmaint.stduserlist'))
    return render_template('plantmaint/stdusermaint.html', form=thisform)


@bp.route('/actasklist', methods=['GET', 'POST'])
@login_required
def actasklist():
    thisac = maintpagecheck()
    # I Don't think we want the view option secured.  Everyone should be able to see what is coming up.
    # if thisac is None:
    #     flash("Sorry, You do not have access to this function", "error")
    #     return render_template('plantmaint/index.html')
    return render_template('plantmaint/actasklist.html', acmaint=thisac)


# Note that this route will not support Add.  Remove and edit only...
@bp.route('/actaskmaint/<id>', methods=['GET', 'POST'])
@login_required
def actaskmaint(id):
    class ThisViewFrm(ACTaskForm):
        pass

    thisac = maintpagecheck()
    if thisac is None:
        flash("Sorry, You do not have access to this function", "error")
        return render_template('plantmaint/index.html')
    # remember the regn becuase we will need to go back to the list
    thisrec = ACTasks.query.get(id)
    stdtask = Tasks.query.get(thisrec.task_id)
    if thisrec is None:
        flash('No such task')
        return redirect(url_for('plantmaint.actasklist'))
    else:
        if thisrec.meter_id is not None:
            if thisrec.meter_rec().entry_uom == 'Qty':
                ThisViewFrm.last_done_reading = IntegerField('Last Done Meter Reading in units',
                                                             [validators.optional()],
                                                             description='The QTY meter reading when this was last done')
            elif thisrec.meter_rec().entry_uom == 'Hours:Minutes':
                ThisViewFrm.last_done_reading = HrsMinsField('Last Done Meter Reading in Hrs:Mins',
                                                             [validators.optional()],
                                                             description='The meter reading when this was last done in Hours and Minutes')
            else:
                ThisViewFrm.last_done_reading = HrsField('Last Done Meter Reading in Decimal Hrs',
                                                         [validators.optional()],
                                                         description='The meter reading when this was last done in Decimal Hours')
    thisform = ThisViewFrm(obj=thisrec, task_basis=stdtask.task_basis)
    if request.method == 'POST':
        if thisform.cancel.data:
            return redirect(url_for('plantmaint.actasklist'))
        if thisform.delete.data:
            db.session.delete(thisrec)
            try:
                db.session.commit()
            except Exception as e:
                applog.error(str(e))
                flash(
                    "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                    "error")
            return redirect(url_for('plantmaint.actasklist'))
        # don't check errors unless NOT cancel or delte.
        if not thisform.validate_on_submit():
            for e in thisform.errors:
                flash(e, "error")
            return render_template('plantmaint/actaskmaint.html', form=thisform, meter=thisrec.meter_rec())
        thisform.populate_obj(thisrec)
        # Code based validation:
        # todo: verify that the task is not already present on this ac
        if thisrec.meter_id is not None:
            thisrec.meter_id = int(thisform.meter_id.data)
            if thisrec.meter_id not in [m.meter_id for m in thisac.meters]:
                flash('This Meter is not installed in this a/c.', 'error')
                return render_template('plantmaint/actaskmaint.html', form=thisform, meter=None)
            if thisrec.meter_id is not None:
                # existing tasks only....
                if thisrec.id is not None:
                    currenttask = [tsk for tsk in thisac.tasks if tsk.id == thisrec.id][0]
                    if currenttask.last_meter_reading_value is not None:
                        if thisrec.last_done_reading > currenttask.last_meter_reading_value:
                            # we need to get the formatting correct for the error message:
                            acmeter = ACMeters.query.filter(ACMeters.ac_id == thisac.id).filter(ACMeters.meter_id == thisrec.meter_id).first()
                            flash(
                                '{} has a last done reading of {} which is later than the last reading of {}. Is that right?'.format(
                                    currenttask.description, format_reading(thisrec.last_done_reading,acmeter.entry_uom),
                                    format_reading(currenttask.last_meter_reading_value, acmeter.entry_uom)), "warning")
        if thisrec.id is None:
            db.session.add(thisrec)
        try:
            db.session.commit()
        except Exception as e:
            applog.error(str(e))
            flash(
                "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                "error")
        return redirect(url_for('plantmaint.actasklist'))
    return render_template('plantmaint/actaskmaint.html', form=thisform, meter=thisrec.meter_rec)


@bp.route('/acselectnewtask', methods=['GET', 'POST'])
@login_required
def acselectnewtask():
    thisac = maintpagecheck()
    if thisac is None:
        flash("Sorry, You do not have access to this function", "error")
        return render_template('plantmaint/index.html')
    thisform = ACSelectNewTaskForm(ac=thisac.regn)
    if request.method == 'GET':
        return render_template('plantmaint/acselectnewtask.html', form=thisform)
    if request.method == 'POST':
        if thisform.cancel.data:
            return redirect(url_for('plantmaint.actasklist'))
        try:
            thisac.add_new_task(int(thisform.task_id.data))
        except Exception as e:
            flash(str(e))
            return render_template('plantmaint/acselectnewtask.html', form=thisform)
    return redirect(url_for('plantmaint.actasklist'))


@bp.route('/acmeterlist', methods=['GET', 'POST'])
@login_required
def acmeterlist():
    thisac = maintpagecheck()
    if thisac is None:
        flash("Sorry, You do not have access to this function", "error")
        return render_template('plantmaint/index.html')
    return render_template('plantmaint/acmeterlist.html', ac=thisac)


# Note that this route will not support Add.  Remove and edit only...
@bp.route('/acmetermaint/<id>', methods=['GET', 'POST'])
@login_required
def acmetermaint(id):
    thisac = maintpagecheck()
    if thisac is None:
        flash("Sorry, You do not have access to this function", "error")
        return render_template('plantmaint/index.html')
    # remember the regn becuase we will need to go back to the list
    thisrec = ACMeters.query.get(id)
    if thisrec is None:
        flash('No such Meter')
        return redirect(url_for('plantmaint.acmeterlist'))
    thisform = ACMeterMaintForm(obj=thisrec)
    if request.method == 'POST':
        if thisform.cancel.data:
            return redirect(url_for('plantmaint.acmeterlist'))
        if thisform.delete.data:
            db.session.delete(thisrec)
            try:
                db.session.commit()
            except Exception as e:
                applog.error(str(e))
                flash(
                    "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                    "error")
            return redirect(url_for('plantmaint.acmeterlist'))
        # don't check errors unless NOT cancel or delte.
        if not thisform.validate_on_submit():
            for e in thisform.errors:
                flash(e, "error")
            return render_template('plantmaint/acmetermaint.html', form=thisform)
        thisform.populate_obj(thisrec)
        # Code based validation:
        if thisrec.id is None:
            db.session.add(thisrec)
        try:
            db.session.commit()
        except Exception as e:
            applog.error(str(e))
            flash(
                "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                "error")
        return redirect(url_for('plantmaint.acmeterlist'))
    return render_template('plantmaint/acmetermaint.html', form=thisform)


@bp.route('/acselectnewmeter', methods=['GET', 'POST'])
@login_required
def acselectnewmeter():
    thisac = maintpagecheck()
    if thisac is None:
        flash("Sorry, You do not have access to this function", "error")
        return render_template('plantmaint/index.html')
    #
    thisform = ACSelectNewMeterForm(ac=thisac.regn)

    currentacmeterids = [a.meter_id for a in thisac.meters]
    thisform.meter_id.choices = []
    for m in Meters.query.all():
        if m.id not in currentacmeterids:
            thisform.meter_id.choices.append((m.id, m.meter_name))
    if len(thisform.meter_id.choices) == 0:
        flash('All possible meters have been added', "warning")
        return redirect(url_for('plantmaint.acmeterlist'))

    if request.method == 'GET':
        return render_template('plantmaint/acselectnewmeter.html', form=thisform)

    if request.method == 'POST':
        if thisform.cancel.data:
            return redirect(url_for('plantmaint.acmeterlist'))
        try:
            thisac.add_new_meter(int(thisform.meter_id.data))
            # Change the prompt
        except Exception as e:
            flash(str(e))
            return render_template('plantmaint/acselectnewmeter.html', form=thisform)
    return redirect(url_for('plantmaint.acmeterlist'))


def get_wt_meter_fld(thisac, id):
    """
    builds a field object for a given meter
    :param thisac: An ACMaint object
    :param id: An integer for a particular meter
    :return: A WtForms fld object
    """
    if not isinstance(thisac, ACMaint):
        raise ValueError('thisac not a valid acmaint object')
    if not isinstance(id, int):
        raise ValueError('Passed id is not an integer')
    for thismeter in [x for x in thisac.meters if x.id == id]:
        flddefn = None
        fldid = 'Meter' + str(thismeter.id)
        textdefn = None
        textid = 'Help' + str(thismeter.id)
        if thismeter.last_reading_date is None:
            textline = 'No readings recorded'
            help_line = 'Enter the FINAL meter reading at the end of the day / event.'
        else:
            textline = 'Last Reading : ' + thismeter.last_reading_date.strftime('%d/%m/%y') + ':' + str(
                thismeter.last_meter_reading_formatted)
            help_line = 'Enter the FINAL meter reading at the end of the day / event.  (' + thismeter.last_reading_date.strftime(
                '%Y%m%d') + '-' + str(thismeter.last_meter_reading_formatted) + ')'
        # Now, what to do.....
        if thismeter.entry_method == 'Delta':
            help_line = 'Enter the increment at end of the day / event.'
        if thismeter.entry_uom == 'Qty':
            flddefn = IntegerField(thismeter.entry_prompt,
                                   [validators.optional()],
                                   description=help_line + "  (Qty)"
                                   , name=thismeter.meter_name, id=thismeter.meter_name)
            # ,name=thismeter.meter_name,id=fldid)
        elif thismeter.entry_uom == 'Hours:Minutes':
            flddefn = HrsMinsField(thismeter.entry_prompt,
                                   [validators.optional()],
                                   description=help_line + "  (Hours:Minutes)"
                                   , name=thismeter.meter_name, id=thismeter.meter_name)
        else:
            flddefn = HrsField(thismeter.entry_prompt,
                               [validators.optional()],
                               description=help_line + "  (Decimal Hours)",
                               name=thismeter.meter_name, id=thismeter.meter_name)
            # name = thismeter.meter_name, id = fldid)
        # flddefn = IntegerField(thismeter.entry_prompt,description='Meter reading value',name=thismeter.meter_name,id=fldid)
        return (flddefn, textline)
    return None


@bp.route('acaddnewreading', methods=['GET', 'POST'])
@login_required
def acaddnewreading():
    class ThisViewFrm(ACAddNewReadingForm):
        pass

    thisac = maintpagecheck('acaddnewreading')
    if thisac is None:
        flash("Sorry, You do not have access to this function", "error")
        return render_template('plantmaint/index.html')
    lastreadings = {}
    for thismeter in thisac.meters:
        runtime_flds = get_wt_meter_fld(thisac, thismeter.id)
        thisfld = runtime_flds[0]
        setattr(ThisViewFrm, thisfld.kwargs['id'], thisfld)
        lastreadings[thisfld.kwargs['id']] = runtime_flds[1]
    if request.method == 'GET':
        thisform = ThisViewFrm()
        return render_template('plantmaint/acaddnewreading.html', form=thisform, lastreadings=lastreadings)
    if request.method == 'POST':
        if 'cancel' in request.form:
            return render_template('plantmaint/index.html')
        thisform = ThisViewFrm(request.form)  # because we are inheriting from FORM and not FLASKFORM
        if not thisform.validate():
            for e in thisform.errors:
                flash("Error: {}".format(str(e)), "error")
            return redirect(url_for('plantmaint.index'))
        addedreadingcount = 0
        thisdate = thisform.reading_date.data
        error_occurred = False
        for thismeter in [m for m in thisac.meters if m.meter_name in thisform.data]:
            # In this loop, thismeter is a meter from thisac.meters (but only if it appears on the form with data)
            # thisform.data is a list of the names (ie.e strings) of those attributes
            print("Processing Meter {}".format(thismeter.meter_name))
            thisformfield = getattr(thisform, thismeter.meter_name)
            if hasattr(thisformfield, 'data'):
                print("--> It has data")
                # then the form as this field somewhere
                if thisformfield.data is not None:
                    print("----> Its not none: {}".format(thisformfield.data))
                    if thisformfield.data != 0:
                        if isinstance(thisformfield.data, decimal.Decimal) \
                                or isinstance(thisformfield.data, int):
                            # thismeter = [m for m in thisac.meters if m.meter_name == f][0]
                            if thismeter is not None and float(thisformfield.data) != 0:
                                if thismeter.last_reading_date is not None:
                                    if thisdate < thismeter.last_reading_date:
                                        flash("Date for {} is earlier than last reading value".format(thismeter.meter_name),
                                              "error")
                                        error_occurred = True
                                    if thismeter.entry_uom != 'Delta':
                                        if thismeter.entry_method == 'Reading':
                                            if thismeter.last_meter_reading > float(thisformfield.data):
                                                flash("{} Reading is less than last reading value".format(thismeter.meter_name),
                                                      "error")
                                                error_occurred = True
                                # we have a valid meter
                                newreading = MeterReadings()
                                newreading.ac_id = thisac.id
                                newreading.meter_id = thismeter.meter_id
                                newreading.reading_date = thisdate
                                if thismeter.last_meter_reading is None:
                                    newreading.meter_delta = decimal.Decimal(thisformfield.data)
                                    newreading.meter_reading = decimal.Decimal(thisformfield.data)
                                else:
                                    if thismeter.entry_method == 'Delta':
                                        newreading.meter_delta = decimal.Decimal(thisformfield.data)
                                        newreading.meter_reading = thismeter.last_meter_reading + decimal.Decimal(
                                            newreading.meter_delta)
                                    else:
                                        newreading.meter_reading = decimal.Decimal(thisformfield.data)
                                        newreading.meter_delta = newreading.meter_reading - thismeter.last_meter_reading
                                newreading.note = thisform.note.data
                                db.session.add(newreading)
                                addedreadingcount += 1
                            else:
                                flash("Failed to locate meter for " + thismeter.meter_name, "error")
                                error_occurred = True
        if error_occurred:
            return render_template('plantmaint/acaddnewreading.html', form=thisform,
                                   lastreadings=lastreadings)
        else:
            try:
                db.session.commit()
            except Exception as e:
                applog.error(str(e))
                flash(
                    "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                    "error")
        flash(str(addedreadingcount) + ' Meter readings added successfully')
        applog.info(str(addedreadingcount) + ' Meter readings added successfully')
        return render_template('plantmaint/index.html')

#todo: review every maintenance screen and log any succcessful updates

@bp.route('/acmeterreadinglist/<meter_id>', methods=['GET', 'POST'])
@login_required
def acmeterreadinglist(meter_id):
    # The id is the id of the acmeters table
    thisac = maintpagecheck()
    if thisac is None:
        flash("Sorry, You do not have access to this function", "error")
        return render_template('plantmaint/index.html')
    if request.method == 'GET':
        sql = sqltext("""
        select 
            t0.id,
            t2.regn,
            t1.meter_name,
            t1.uom,
            t0.reading_date ,
            t0.meter_reading,
            t0.meter_delta,
            t0.note,
            row_number() over(order by t0.id desc) seq
        from meterreadings t0 
            left outer join meters t1 on t1.id = t0.meter_id
            left outer join aircraft t2 on t2.id = t0.ac_id
        where t0.meter_id  = :meter_id
        and t0.ac_id = :ac_id
        order by reading_date desc, t0.id desc
        """)
        sql = sql.columns(reading_date=db.Date, meter_reading=SqliteDecimal(10, 2), meter_delta=SqliteDecimal(10, 2))
        list = db.engine.execute(sql, ac_id=thisac.id, meter_id=meter_id).fetchall()
        if len(list) == 0:
            flash("No Meter Readings")
            return redirect(url_for('plantmaint.acmeterlist'))
        return render_template('plantmaint/acmeterreadinglist.html', list=list)

# TODO: xlsx download for logbook so that all readings go across the page.  Will need delta and running total.

@bp.route('/acmeterreadingremove/<reading_id>', methods=['GET'])
@login_required
def acmeterreadingremove(reading_id):
    thisac = maintpagecheck()
    if thisac is None:
        flash("Sorry, You do not have access to this function", "error")
        return render_template('plantmaint/index.html')
    thisrec = MeterReadings.query.get(reading_id)
    thismeter = thisrec.meter_id
    if thisrec is None:
        flash('No such Reading')
        return redirect(url_for('plantmaint.acmeterreadingslist', meter_id = thismeter))
    if request.method == 'GET':
        db.session.delete(thisrec)
        try:
            db.session.commit()
        except Exception as e:
            applog.error(str(e))
            flash(
                "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                "error")
    flash("Meter Reading Removed")
    return redirect(url_for('plantmaint.acmeterreadinglist', meter_id = thismeter))
