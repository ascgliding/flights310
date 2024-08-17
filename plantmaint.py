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
from asc.wtforms_ext import MatButtonField, TextButtonField

# xlsx
import xlsxwriter
from flask import send_file
from asc.export import ExcelPromptForm

from asc.oMaint import ACMaint
from asc.mailer import ascmailer
from asc.common import *
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


def format_reading(value, fmt) -> str:
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
            if re.match("^[0-9]{0,5}.[0-9]{0,2}$", valuedata[0]) is None \
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
            return render_template("plantmaint/index.html", ac=thisac)
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
    importreading = TextButtonField('Import',
                                    id="import",
                                    text='Import Readings',
                                    help="Import Readings from the flight system")
    resetreading = TextButtonField('Reset',
                                   id="reset",
                                   text='Reset Readings',
                                   help="Recalculate readings based on an entered final reading.")

    delete = SubmitField('delete', id='deletebtn', render_kw={"OnClick": "ConfirmDelete()"})


class ACSelectNewTaskForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(ACSelectNewTaskForm, self).__init__(*args, **kwargs)
        thisac = ACMaint(kwargs['ac'])
        if thisac is None:
            print('bugger...', kwargs['ac'])
        current_ac_task_ids = [a.task_id for a in thisac.tasks]
        current_ac_meters_ids = [m.meter_id for m in thisac.meters]
        self.task_id.choices = []
        for t in Tasks.query.all():
            if t.id not in current_ac_task_ids \
                    and (t.task_meter_id is None or t.task_meter_id in current_ac_meters_ids):
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
        self.task_id.choices = [(t.id, t.task_description) for t in Tasks.query.all()]

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
    last_done = DateField('Last Done', [validators.optional()], description='The date this task was last performed')
    # This form is never used.  A form that inherits from this form will ve created with the correct uom for the display type.
    estimate_days = IntegerField('Average over Days',
                                 description='The number of days to average meter readings in order to estimate the next completion for a meter based task')
    warning_days = IntegerField('Warning Days', [validators.optional()],
                                description='The number of days prior to expiry to start sending warning emails')
    warning_email = StringField('Warning Email',
                                description='comma separated list of email addresses for warning emails')
    note = TextAreaField('Note',
                         description='Any note associated with the task',
                         render_kw={'rows': '4'})
    logbook_include = BooleanField('Include in Logbook',
                                   description='Include this item as a counter in the logbook spreadsheet')
    logbook_column_title = StringField('Spreadsheet Title',
                                       description='Title to be used as a column title in the logbook'    )
    logbook_start_date = DateField('Starting Date',
                                   description='The date that you have a reference counter for this field')
    logbook_start_value = IntegerField('Starting Value',
                                       description='The value of this reading at the date specifed')

    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')
    complete = TextButtonField('Transactions',
                               id="complete",
                               text='Complete',
                               help="Record Task Completion")
    history = TextButtonField('History',
                              id="history",
                              text='History',
                              help="Display task completion history")

    delete = SubmitField('delete', id='deletebtn', render_kw={"OnClick": "ConfirmDelete()"})


class ACAddNewReadingForm(Form):
    name = "Enter New Readings"
    reading_date = DateField('Date', description='Date for these readings', default=datetime.date.today())
    note = StringField('Notes', description='Add any notes to describe the flying')
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')


class ACTaskComplete(FlaskForm):
    name = "Record Task Completion"
    ac_id = IntegerField('Ac Id', description='not displayed')
    task_id = IntegerField('task Id', description='not displayed')
    history_date = DateField('Completion Date', description='The date the task was completed',
                             default=datetime.date.today())
    task_description = TextAreaField('Task Description', description='Add any relevant Notes')
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')


class ACImportReading(FlaskForm):
    name = "Import Readings from Flight Details"
    ac_id = IntegerField('Ac Id', description='not displayed')
    meter_id = IntegerField('task Id', description='not displayed')
    start_date = DateField('Start Date', description='The date to start importing', default=datetime.date.today())
    end_date = DateField('End Date', description='The date to end importing', default=datetime.date.today())
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')


class ACResetReadings(FlaskForm):
    name = "Import Readings from Flight Details"
    # Actual Fields added in the view function.
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
        try:
            thisac = ACMaint(session['regn'])
        except Exception as e:
            flash(str(e), "error")
            raise RuntimeError('There is a problem in the maintenance program setup for {}'.format(session['regn']))

        if thisac is None:
            return redirect(url_for('plantmaint.maintainedac'))
        else:
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


@bp.route('/index', defaults={'pregn': None}, methods=['GET'])
@bp.route('/index/<pregn>', methods=['GET'])
@login_required
def index(pregn=None):
    applog.info("User agent: {}".format(request.headers.get('User-Agent')))
    if pregn is None:
        if 'regn' in session:
            thisac = ACMaint(session['regn'])
            return render_template('plantmaint/index.html', regn=thisac.regn, ac=thisac)
        else:  # regn not in session:
            return render_template('../index.html')
    else:
        session['regn'] = pregn
        try:
            thisac = ACMaint(session['regn'])
        except Exception as e:
            flash("There is a problem in the maintenance program setup for {}".format(session['regn']))
            flash(str(e), "error")
            return render_template('plantmaint/index.html', regn=pregn, ac=None)
        return render_template('plantmaint/index.html', regn=pregn, ac=thisac)


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
    thisrec = Tasks.query.get(id)
    if thisrec is None:
        thisrec = Tasks()
    thisform = StdTaskForm(obj=thisrec)
    if request.method == 'POST' and thisform.validate:
        if thisform.cancel.data:
            return redirect(url_for('plantmaint.stdtasklist'))
        if thisform.delete.data:
            # check if present on any a/c before delete
            if db.session.query(ACTasks.query.filter(ACTasks.task_id == thisrec.id).exists()).scalar():
                flash("Cannot Delete - this task is defined on an A/C", "error")
                return redirect(url_for('plantmaint.stdtasklist'))
            db.session.delete(thisrec)
            try:
                applog.info('DELETE:' + repr(thisrec))
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
            applog.info('ADD:' + repr(thisrec))
        applog.info('UPDATE:' + repr(thisrec))
        try:
            db.session.commit()
        except Exception as e:
            applog.error(str(e))
            flash(
                "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                "error")
        return redirect(url_for('plantmaint.stdtasklist'))

    return render_template('plantmaint/stdtaskmaint.html', form=thisform, thisdesc=thisrec.recurrence_description)


@bp.route('/stdmeterlist', methods=['GET'])
@login_required
def stdmeterlist():
    list = db.engine.execute(sqlalchemy.sql.text("select id,meter_name,uom from meters")).fetchall()
    return render_template('plantmaint/stdmeterlist.html', list=list)


@bp.route('/stdmetermaint/<id>', methods=['GET', 'POST'])
@login_required
def stdmetermaint(id):
    thisrec = Meters.query.get(id)
    if thisrec is None:
        thisrec = Meters()
    thisform = StdMeterForm(obj=thisrec)
    if thisform.validate_on_submit():
        if thisform.cancel.data:
            return redirect(url_for('plantmaint.stdmeterlist'))
        if thisform.delete.data:
            # check if present on any a/c before delete
            # chk = db.session.query(Tasks).filter(Tasks.task_meter_id == thisrec.id).count()
            # if chk > 0:
            if db.session.query(Tasks.query.filter(Tasks.task_meter_id == thisrec.id).exists()).scalar():
                flash("Cannot Delete - this Meter is used on an Task", "error")
                return redirect(url_for('plantmaint.stdmeterlist'))
            if db.session.query(ACMeters.query.filter(ACMeters.meter_id == thisrec.id).exists()).scalar():
                flash("Cannot Delete - this Meter is used on an aircraft", "error")
                return redirect(url_for('plantmaint.stdmeterlist'))
            if db.session.query(MeterReadings.query.filter(MeterReadings.meter_id == thisrec.id).exists()).scalar():
                flash("Cannot Delete - this Meter has readings", "error")
                return redirect(url_for('plantmaint.stdmeterlist'))
            db.session.delete(thisrec)
            try:
                applog.info('DELETE:' + repr(thisrec))
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
            applog.info('ADD:' + repr(thisrec))
        applog.info('UPDATE:' + repr(thisrec))
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
                applog.info('DELETE:' + repr(thisrec))
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
            applog.info('ADD:' + repr(thisrec))
        applog.info('UPDATE:' + repr(thisrec))
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
    try:
        thisac = maintpagecheck()
    except Exception as e:
        flash(str(e))
        return redirect(url_for('plantmaint.maintainedac'))
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

    try:
        thisac = maintpagecheck()
    except Exception as e:
        flash(str(e))
        return redirect(url_for('plantmaint.maintainedac'))
    if thisac is None:
        flash("Sorry, You do not have access to this function", "error")
        return render_template('plantmaint/index.html', ac=None)
    # remember the regn becuase we will need to go back to the list
    thisrec = ACTasks.query.get(id)
    stdtask = thisrec.std_task_rec  # Tasks.query.get(thisrec.task_id)
    if thisrec is None:
        flash('No such task')
        return redirect(url_for('plantmaint.actasklist'))
    else:
        # todo: need same kind of logic for Qty based readings.
        if stdtask.task_meter_id is not None:
            if thisrec.ac_meter_rec.entry_uom == 'Qty':
                ThisViewFrm.last_done_reading = IntegerField('Last Done Meter Reading in units',
                                                             [validators.optional()],
                                                             description='The QTY meter reading when this was last done')
            elif thisrec.ac_meter_rec.entry_uom == 'Hours:Minutes':
                ThisViewFrm.last_done_reading = HrsMinsField('Last Done Meter Reading in Hrs:Mins',
                                                             [validators.optional()],
                                                             description='The meter reading when this was last done in Hours and Minutes')
            else:
                ThisViewFrm.last_done_reading = HrsField('Last Done Meter Reading in Decimal Hrs',
                                                         [validators.optional()],
                                                         description='The meter reading when this was last done in Decimal Hours')
        # Add a field for the override due basis depending on the type of task and type of meter
        if stdtask.task_basis == 'Calendar':
            ThisViewFrm.due_basis_date = DateField('Basis Date for regeneration',
                                                   [validators.optional()],
                                                   description='If task regeneration is independant of when it was last done, enter a date here')
        else:
            if thisrec.ac_meter_rec.entry_uom == 'Qty':
                ThisViewFrm.due_basis_reading = IntegerField('Regneration Basis Reading',
                                                             [validators.optional()],
                                                             description='If task regeneration is independant of when it was last done, enter a value here')
            elif thisrec.ac_meter_rec.entry_uom == 'Hours:Minutes':
                ThisViewFrm.due_basis_reading = HrsMinsField('Regneration Basis Reading (Hrs:Mins)',
                                                             [validators.optional()],
                                                             description='If task regeneration is independant of when it was last done, enter a value here')
            else:
                ThisViewFrm.due_basis_reading = HrsField('Regneration Basis Reading (Decimal Hrs)',
                                                         [validators.optional()],
                                                         description='If task regeneration is independant of when it was last done, enter a value here')

    thisform = ThisViewFrm(obj=thisrec, task_basis=stdtask.task_basis)
    if request.method == 'POST':
        if thisform.cancel.data:
            return redirect(url_for('plantmaint.actasklist'))
        if thisform.complete.data:
            return redirect(url_for('plantmaint.actaskcomplete', task=thisrec.id))
        if thisform.history.data:
            return redirect(url_for('plantmaint.achistorylist', task=thisrec.id))
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
            return redirect(url_for('plantmaint.actasklist'))
        # don't check errors unless NOT cancel or delte.
        if not thisform.validate_on_submit():
            for e in thisform.errors:
                flash(e, "error")
            return render_template('plantmaint/actaskmaint.html', form=thisform, meter=stdtask.std_meter_rec, ac=thisac)
        thisform.populate_obj(thisrec)
        # Code based validation:
        # Todo:  Starting date must be a valid reading
        if stdtask.std_meter_rec is not None:
            if stdtask.std_meter_rec.id not in [m.meter_id for m in thisac.meters]:
                flash('This Meter is not installed in this a/c.', 'error')
                return render_template('plantmaint/actaskmaint.html', form=thisform, meter=stdtask.meter_rec(),
                                       ac=thisac)
            currenttask = [tsk for tsk in thisac.tasks if tsk.id == thisrec.id][0]
            if currenttask.last_meter_reading_value is not None:
                if thisrec.last_done_reading > currenttask.last_meter_reading_value:
                    # we need to get the formatting correct for the error message:
                    acmeter = ACMeters.query.filter(ACMeters.ac_id == thisac.id).filter(
                        ACMeters.meter_id == thisrec.meter_id).first()
                    flash(
                        '{} has a last done reading of {} which is later than the last reading of {}. Is that right?'.format(
                            currenttask.description, format_reading(thisrec.last_done_reading, acmeter.entry_uom),
                            format_reading(currenttask.last_meter_reading_value, acmeter.entry_uom)), "warning")
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
        return redirect(url_for('plantmaint.actasklist'))
    return render_template('plantmaint/actaskmaint.html', form=thisform, meter=thisrec.std_task_rec.std_meter_rec,
                           ac=thisac)


@bp.route('/acselectnewtask', methods=['GET', 'POST'])
@login_required
def acselectnewtask():
    try:
        thisac = maintpagecheck()
    except Exception as e:
        flash(str(e))
        return redirect(url_for('plantmaint.maintainedac'))
    if thisac is None:
        flash("Sorry, You do not have access to this function", "error")
        return render_template('plantmaint/index.html', ac=None)
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
    try:
        thisac = maintpagecheck()
    except Exception as e:
        flash(str(e))
        return redirect(url_for('plantmaint.maintainedac'))
    if thisac is None:
        flash("Sorry, You do not have access to this function", "error")
        return render_template('plantmaint/index.html', ac=None)
    return render_template('plantmaint/acmeterlist.html', ac=thisac)


# Note that this route will not support Add.  Remove and edit only...
@bp.route('/acmetermaint/<id>', methods=['GET', 'POST'])
@login_required
def acmetermaint(id):
    try:
        thisac = maintpagecheck()
    except Exception as e:
        flash(str(e))
        return redirect(url_for('plantmaint.maintainedac'))
    if thisac is None:
        flash("Sorry, You do not have access to this function", "error")
        return render_template('plantmaint/index.html', ac=None)
    # remember the regn becuase we will need to go back to the list
    thisrec = ACMeters.query.get(id)
    if thisrec is None:
        flash('No such Meter')
        return redirect(url_for('plantmaint.acmeterlist'))
    thisform = ACMeterMaintForm(obj=thisrec)
    if request.method == 'POST':
        if thisform.cancel.data:
            return redirect(url_for('plantmaint.acmeterlist'))
        if thisform.importreading.data:
            return redirect(url_for('plantmaint.acimportreading', acmeters_id=id))
        if thisform.resetreading.data:
            return redirect(url_for('plantmaint.acresetreadings', acmeters_id=id))
        if thisform.delete.data:
            # Check there are no tasks on this ac for this meter
            for actsk in db.session.query(ACTasks).filter(ACTasks.ac_id == thisac.id):
                if actsk.std_task_rec.task_meter_id == thisrec.meter_id:
                    flash("Cannot Delete - There are tasks for this meter on this a/c", "error")
                    return redirect(url_for('plantmaint.acmeterlist'))
            # check there are no readings for this ac for this meter
            for rdg in db.session.query(MeterReadings).filter(MeterReadings.ac_id == thisac.id):
                if rdg.meter_id == thisrec.meter_id:
                    flash("Cannot Delete - there are Meter Readings for this a/c", "error")
                    return redirect(url_for('plantmaint.acmeterlist'))
            db.session.delete(thisrec)
            try:
                applog.info('DELETE:' + repr(thisrec))
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
        applog.info('UPDATE:' + repr(thisrec))
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
    try:
        thisac = maintpagecheck()
    except Exception as e:
        flash(str(e))
        return redirect(url_for('plantmaint.maintainedac'))
    if thisac is None:
        flash("Sorry, You do not have access to this function", "error")
        return render_template('plantmaint/index.html', ac=None)
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

    try:
        thisac = maintpagecheck()
    except Exception as e:
        flash(str(e))
        return redirect(url_for('plantmaint.maintainedac'))
    if thisac is None:
        flash("Sorry, You do not have access to this function", "error")
        return render_template('plantmaint/index.html', ac=None)
    lastreadings = {}
    for thismeter in thisac.meters:
        runtime_flds = get_wt_meter_fld(thisac, thismeter.id)
        thisfld = runtime_flds[0]
        setattr(ThisViewFrm, thisfld.kwargs['id'], thisfld)
        lastreadings[thisfld.kwargs['id']] = runtime_flds[1]
    if request.method == 'GET':
        thisform = ThisViewFrm()
        return render_template('plantmaint/acaddnewreading.html', form=thisform, lastreadings=lastreadings, ac=thisac)
    if request.method == 'POST':
        if 'cancel' in request.form:
            return render_template('plantmaint/index.html', ac=thisac)
        thisform = ThisViewFrm(request.form)  # because we are inheriting from FORM and not FLASKFORM
        if not thisform.validate():
            for e in thisform.errors:
                flash("Error: {}".format(str(e)), "error")
            return redirect(url_for('plantmaint.index', ac=thisac))
        addedreadingcount = 0
        thisdate = thisform.reading_date.data
        error_occurred = False
        for thismeter in [m for m in thisac.meters if m.meter_name in thisform.data]:
            # In this loop, thismeter is a meter from thisac.meters (but only if it appears on the form with data)
            # thisform.data is a list of the names (ie.e strings) of those attributes
            thisformfield = getattr(thisform, thismeter.meter_name)
            if hasattr(thisformfield, 'data'):
                # then the form as this field somewhere
                if thisformfield.data is not None:
                    if thisformfield.data != 0:
                        if isinstance(thisformfield.data, decimal.Decimal) \
                                or isinstance(thisformfield.data, int):
                            # thismeter = [m for m in thisac.meters if m.meter_name == f][0]
                            if thismeter is not None and float(thisformfield.data) != 0:
                                if thismeter.last_reading_date is not None:
                                    if thisdate < thismeter.last_reading_date:
                                        flash("Date for {} is earlier than last reading value".format(
                                            thismeter.meter_name),
                                            "error")
                                        error_occurred = True
                                    if thismeter.entry_uom != 'Delta':
                                        if thismeter.entry_method == 'Reading':
                                            if thismeter.last_meter_reading > float(thisformfield.data):
                                                flash("{} Reading is less than last reading value".format(
                                                    thismeter.meter_name),
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
                                        newreading.meter_reading = thismeter.last_meter_reading + \
                                                                   decimal.Decimal(newreading.meter_delta)
                                    else:
                                        newreading.meter_reading = decimal.Decimal(thisformfield.data)
                                        newreading.meter_delta = newreading.meter_reading - \
                                                                 thismeter.last_meter_reading
                                newreading.note = thisform.note.data
                                db.session.add(newreading)
                                applog.info('ADD:' + repr(newreading))
                                addedreadingcount += 1
                            else:
                                flash("Failed to locate meter for " + thismeter.meter_name, "error")
                                error_occurred = True
        if error_occurred:
            return render_template('plantmaint/acaddnewreading.html', form=thisform,
                                   lastreadings=lastreadings, ac=thisac)
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
        return render_template('plantmaint/index.html', ac=thisac)


@bp.route('/acmeterreadinglist/<meter_id>', methods=['GET', 'POST'])
@login_required
def acmeterreadinglist(meter_id):
    # The id is the id of the acmeters table
    # Todo:  Add new functions - recalculate meter readings - either delta from readings
    #    Or Readings from delta.  Need to be able to specfy start position and
    #    Whether it is forwards or backwards through the data.
    try:
        thisac = maintpagecheck()
    except Exception as e:
        flash(str(e))
        return redirect(url_for('plantmaint.maintainedac'))
    if thisac is None:
        flash("Sorry, You do not have access to this function", "error")
        return render_template('plantmaint/index.html', ac=None)
    if request.method == 'GET':
        sql = sqltext("""
        select 
            t0.id,
            t2.regn,
            t1.meter_name,
            t1.uom,
            t3.entry_uom,
            t0.reading_date ,
            t0.meter_reading,
            t0.meter_delta,
            t0.note,
            row_number() over(order by t0.id desc) seq
        from meterreadings t0 
            left outer join meters t1 on t1.id = t0.meter_id
            left outer join aircraft t2 on t2.id = t0.ac_id
            left outer join acmeters t3 on t3.ac_id = t0.ac_id  and t3.meter_id = t0.meter_id 
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


@bp.route('/acmeterreadingremove/<reading_id>', methods=['GET'])
@login_required
def acmeterreadingremove(reading_id):
    try:
        thisac = maintpagecheck()
    except Exception as e:
        flash(str(e))
        return redirect(url_for('plantmaint.maintainedac'))
    if thisac is None:
        flash("Sorry, You do not have access to this function", "error")
        return render_template('plantmaint/index.html', ac=None)
    thisrec = MeterReadings.query.get(reading_id)
    thismeter = thisrec.meter_id
    if thisrec is None:
        flash('No such Reading')
        return redirect(url_for('plantmaint.acmeterreadingslist', meter_id=thismeter))
    if request.method == 'GET':
        db.session.delete(thisrec)
        try:
            applog.info('DELETE:' + repr(thisrec))
            db.session.commit()
        except Exception as e:
            applog.error(str(e))
            flash(
                "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                "error")
    flash("Meter Reading Removed")
    return redirect(url_for('plantmaint.acmeterreadinglist', meter_id=thismeter))


@bp.route('/acmaintainhist', methods=['GET'])
@login_required
def acmaintainhist():
    try:
        thisac = maintpagecheck()
    except Exception as e:
        flash(str(e))
        return redirect(url_for('plantmaint.index', ac=None))

    list = db.session.query(ACMaintHistory).filter(ac_id == thisac.id)
    if request.method == 'GET':
        return render_template('plantmaint/maintainhist.html', list=list)


@bp.route('/actaskcomplete/<task>', methods=['GET', 'POST'])
@login_required
def actaskcomplete(task):
    class ThisViewFrm(ACTaskComplete):
        pass

    try:
        thisac = maintpagecheck()
    except Exception as e:
        flash(str(e))
        return redirect(url_for('plantmaint.index', ac=None))
    # check we have a valid task
    thistask = ACTasks.query.get(task)
    if thistask is None:
        flash('Invalid AC Task Record', "error")
        return redirect(url_for('plantmaint.actasklist'))
    if thistask.ac_id != thisac.id:
        flash('Something very wrong.  Task for wrong a/c', "error")
        return redirect(url_for('plantmaint.actasklist'))
    thisrec = ACMaintHistory()
    if thistask.std_task_rec.std_meter_rec is not None:
        # then we need to add the reading
        thisacmeter = db.session.query(ACMeters) \
            .filter(ACMeters.ac_id == thistask.ac_id) \
            .filter(ACMeters.meter_id == thistask.std_task_rec.task_meter_id) \
            .first()
        if thisacmeter is None:
            flash("Could not determine the correct meter to prompt", "error")
        else:
            if thisacmeter.entry_uom == 'Qty':
                ThisViewFrm.meter_reading = IntegerField('Completion Meter Reading in units',
                                                         [validators.optional()],
                                                         description='The QTY meter reading when this was last done')
            elif thisacmeter.entry_uom == 'Hours:Minutes':
                ThisViewFrm.meter_reading = HrsMinsField('Completion Meter Reading in Hrs:Mins',
                                                         [validators.optional()],
                                                         description='The meter reading when this was last done in Hours and Minutes')
            else:
                ThisViewFrm.meter_reading = HrsField('Completion Meter Reading in Decimal Hrs',
                                                     [validators.optional()],
                                                     description='The meter reading when this was last done in Decimal Hours')
    # Set default values
    if thisrec.id is None:  # add mode - first time in
        thisrec.ac_id = thisac.id
        thisrec.task_id = task
        thisrec.history_date = datetime.date.today()
        thisrec.task_description = thistask.std_task_rec.task_description
    thisform = ThisViewFrm(obj=thisrec)
    # Add a field for the meter reading
    if thisform.validate_on_submit():
        if thisform.cancel.data:
            return redirect(url_for('plantmaint.actasklist'))
        thisform.populate_obj(thisrec)
        # Look at the meter readings.  If this completion date is LATER than the last
        # reading, then add a new reading.  Otherwise echo a message.
        thistask = [t for t in thisac.tasks if t.id == int(task)]
        if len(thistask) == 0:
            flash('This task cannot be found on the aircraft', 'error')
            return redirect(url_for('plantmaint.actasklist'))
        thistask = thistask[0]
        print(thistask)
        # Is a meter associated with this task?
        if thistask.contains_meter:
            if (thistask.last_meter_reading_date or datetime.date(2200, 1, 1)) >= thisform.history_date.data:
                flash('The meter reading was not added to readings because there are later readings')
            else:
                # we only get here if the last meter reading date is < than the date on the form.
                if thisform.meter_reading.data < thistask.last_meter_reading_value:
                    flash(
                        'You have entered a meter reading that is less than latest reading.  Completion not recorded - Please Retry'
                        , "error")
                    return redirect(url_for('plantmaint.actaskmaint', id=task))
                # add a meter reading.
                newreading = MeterReadings(ac_id=thisac.id, meter_id=thistask.meter_id,
                                           meter_reading=thisform.meter_reading.data,
                                           meter_delta=thisform.meter_reading.data - thistask.last_meter_reading_value,
                                           note=str(thistask) + ' Completion Recording')
                flash('Completion Meter Reading Recorded.')
                db.session.add(newreading)
        if thisrec.id is None:
            db.session.add(thisrec)
            applog.info("ADD:" + repr(thisrec))
        applog.info('UPDATE:' + repr(thisrec))
        # now set the last done date
        actask = ACTasks.query.get(thisrec.task_id)
        actask.last_done = thisrec.history_date
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            applog.error(str(e))
            flash(
                "An error cccurred while updating the database.  The details are in the system log.  Best to call the system administrator.",
                "error")
        return redirect(url_for('plantmaint.actasklist'))
    return render_template('plantmaint/actaskcomplete.html', form=thisform, ac=thisac)


@bp.route('/achistorylist/<task>', methods=['GET', 'POST'])
@login_required
def achistorylist(task):
    '''
    List history for given task
    :param task: the ACTask id - not Tasks!!
    :return:
    '''
    try:
        thisac = maintpagecheck()
    except Exception as e:
        flash(str(e))
        return redirect(url_for('plantmaint.index', thiac=None))
    print("achistorylist {}".format(task))
    if int(task) == 0:
        list = db.session.query(ACMaintHistory).filter(ACMaintHistory.ac_id == thisac.id) \
            .order_by(ACMaintHistory.history_date.desc()).all()
    else:
        list = db.session.query(ACMaintHistory).filter(ACMaintHistory.ac_id == thisac.id) \
            .filter(ACMaintHistory.task_id == task) \
            .order_by(ACMaintHistory.history_date.desc()).all()
    return render_template("plantmaint/achistorylist.html", list=list, ac=thisac)


@bp.route('/acimportreading/<acmeters_id>', methods=['GET', 'POST'])
@login_required
def acimportreading(acmeters_id):
    try:
        thisac = maintpagecheck()
    except Exception as e:
        flash(str(e))
        return redirect(url_for('plantmaint.index', ac=None))
    # The id is the key to acmetersid
    acmeter = db.session.query(ACMeters).filter(ACMeters.id == acmeters_id).first()
    if acmeter is None:
        flash('Meter id invalid', 'error')
        return render_template('plantmaint/index.html', ac=thisac)
    thisform = ACImportReading()
    if request.method == 'GET':
        thisform.ac_id.data = thisac.id
        thisform.meter_id.data = acmeter.meter_id
        thisform.start_date.data = datetime.date.today() - relativedelta(months=6)
        thisform.end_date.data = datetime.date.today()
        return render_template('plantmaint/acimportreading.html', form=thisform, ac=thisac, acmeter=acmeter)
    if request.method == 'POST':
        if 'cancel' in request.form:
            return render_template('plantmaint/index.html', ac=thisac)
        if 'btnsubmit' in request.form:
            try:
                readingscreated = create_readings_from_flights(thisac.regn,
                                                               thisform.start_date.data,
                                                               thisform.end_date.data,
                                                               acmeter.meter_id)
                flash('{} Readings Created'.format(readingscreated))
            except Exception as e:
                flash('An Error Occurred: {}'.format(str(e)), 'error')
            return render_template('plantmaint/index.html', ac=thisac)


@bp.route('/acresetreadings/<acmeters_id>', methods=['GET', 'POST'])
@login_required
def acresetreadings(acmeters_id):
    class ThisViewFrm(ACResetReadings):
        pass

    try:
        thisac = maintpagecheck()
    except Exception as e:
        flash(str(e))
        return redirect(url_for('plantmaint.index', ac=None))
    acmeter = db.session.query(ACMeters).filter(ACMeters.id == acmeters_id).first()
    try:
        meter = [m for m in thisac.meters if m.id == int(acmeters_id)][0]
    except Exception as e:
        flash('Meter id invalid ({})'.format(str(e)), 'error')
        return render_template('plantmaint/index.html', ac=thisac)
    # Add the right kind of field for the meter.
    if meter.entry_uom == 'Qty':
        ThisViewFrm.lastreading = IntegerField('Final Meter Reading in units',
                                               [validators.optional()],
                                               description='The final QTY meter reading ')
    elif meter.entry_uom == 'Hours:Minutes':
        ThisViewFrm.lastreading = HrsMinsField('Final Meter Reading in Hrs:Mins',
                                               [validators.optional()],
                                               description='The final reading  in Hours and Minutes')
    else:
        ThisViewFrm.lastreading = HrsField('Final Meter Reading in Decimal Hrs',
                                           [validators.optional()],
                                           description='The final meter reading  in Decimal Hours')
    thisform = ThisViewFrm()
    if request.method == 'GET':
        thisform.lastreading.data = meter.last_meter_reading
        return render_template('plantmaint/acresetreadings.html', form=thisform, ac=thisac, acmeter=meter)
    if request.method == 'POST':
        if 'cancel' in request.form:
            return render_template('plantmaint/index.html', ac=thisac)
        if 'btnsubmit' in request.form:
            common_set_log(applog)
            try:
                valueschanged = reset_readings_from_end(thisac.regn, meter.meter_id, thisform.lastreading.data)
                flash('{} Readings Reset'.format(valueschanged))
            except Exception as e:
                flash('An Error Occurred: {}'.format(str(e)), 'error')
            return render_template('plantmaint/index.html', ac=thisac)


@bp.route('/acmaintlogbook', methods=['GET', 'POST'])
@login_required
def acmaintlogbook():
    try:
        thisac = maintpagecheck()
    except Exception as e:
        flash(str(e))
        return redirect(url_for('plantmaint.index', ac=None))
    thisform = ExcelPromptForm(name='Export ' + thisac.regn + ' Logbook')
    if request.method == 'GET':
        thisform.start_date.data = datetime.date.today() - relativedelta(years=1)
        thisform.end_date.data = datetime.date.today()
        return render_template('export/exp_daterange.html', form=thisform, title='Export ' + thisac.regn + ' Logbook')
    if request.method == 'POST':
        if 'cancel' in request.form:
            return render_template('plantmaint/index.html', ac=thisac)
        readings = db.session.query(MeterReadings) \
            .filter(MeterReadings.reading_date >= thisform.start_date.data) \
            .filter(MeterReadings.reading_date <= thisform.end_date.data).first()
        if readings is None:
            flash("No readings in this date range")
            return redirect(url_for('plantmaint.index', thiac=None))
        common_set_log(applog)
        useragent = request.headers.get('User-Agent')
        if user_agent_os_match(useragent, "Mac"):
            # "numbers" in macos does not support the hours mins formatting so make it a string
            try:
                return send_file(createmntlogbookxlsx(thisac, thisform.start_date.data, thisform.end_date.data, True),
                                 as_attachment=True)
            except Exception as e:
                flash(str(e))
        else:
            try:
                return send_file(createmntlogbookxlsx(thisac, thisform.start_date.data, thisform.end_date.data),
                                 as_attachment=True)
            except Exception as e:
                flash(str(e))
        return render_template('plantmaint/index.html', ac=thisac)


def build_lifed_item_dict(thisac, m):
    """
    Create a dictionary item for the lifed item
    :param m: an sql returned row
    :return:
    """
    thisdict = {"ac_task_id": m.task_id,
                "task_id": m.task_id,
                "meter_id": m.meter_id,
                "description": m.task_description,
                "title": m.logbook_column_title,
                "start_date": m.logbook_start_date,
                "start_value": m.logbook_start_value
                }
    # what we need to do is build a list of readings where the counters are
    # initialised at the value this thing was last done.
    # find in readings a reading value that is equal to or just after this item
    readings = MeterReadings.query.filter(MeterReadings.ac_id == thisac.id) \
        .filter(MeterReadings.meter_id == m.meter_id) \
        .filter(MeterReadings.meter_reading >= m.last_done_reading) \
        .filter(MeterReadings.reading_date >= m.logbook_start_date) \
        .order_by(MeterReadings.reading_date) \
        .all()
    closingreading = m.logbook_start_value
    readinglist = []
    for r in readings:
        onereading = {'reading_date': r.reading_date}
        onereading["meter_delta"] = r.meter_delta
        closingreading +=  r.meter_delta
        onereading["meter_reading"]  = closingreading
        readinglist.append(onereading)
    thisdict['readinglist'] = readinglist
    return thisdict

def get_readings(readingdict,date):
    for r in readingdict["readinglist"]:
        if r["reading_date"] == date:
            return r["meter_delta"], r["meter_reading"]
    # if we get to here then we didn't find it.
    return None,None



def createmntlogbookxlsx(thisac, pstart, pend, p_hrs_mins_as_string=False):
    """
    Creates a spreadsheet ready for download for flights between two dates.
    :param self:
    :param flights:  List of flights to write
    :return: Name of excel file.
    """

    sql = sqltext("""
        select 
            t0.id ac_task_id,
            t1.id task_id,
            t2.id meter_id,
            t1.task_description,
            t2.meter_name,
            t2.uom,
            t0.last_done_reading,
            t0.logbook_column_title,
            t0.logbook_start_date,
            t0.logbook_start_value 
            from actasks t0
            join tasks t1 on t0.task_id  = t1.id
            join meters t2 on t1.task_meter_id  = t2.id
            where ac_id = :ac_id
            and (task_meter_id   is not null)
            and t0.logbook_include
        """)
    sql = sql.columns(last_done_reading=SqliteDecimal(10, 2), logbook_start_value=SqliteDecimal(10,2))
    meter_based_tasks = db.engine.execute(sql, ac_id=thisac.id).fetchall()
    task_based_columns = []
    for m in meter_based_tasks:
        task_based_columns.append(build_lifed_item_dict(thisac, m))
    for i in task_based_columns:
        print(i["description"])
        print("---------------------------------------")
        for r in i["readinglist"]:
            print(r)

    sql = sqltext("""
    select 
        t0.id,
        t2.regn,
        t1.meter_name,
        t1.uom,
        t3.entry_uom,
        t0.reading_date ,
        t0.meter_reading,
        t0.meter_delta,
        t0.note
    from meterreadings t0 
        left outer join meters t1 on t1.id = t0.meter_id
        left outer join aircraft t2 on t2.id = t0.ac_id
        left outer join acmeters t3 on t3.ac_id = t0.ac_id  and t3.meter_id = t0.meter_id 
    where t0.ac_id = :ac_id
    and t0.reading_date >= :start
    and t0.reading_date <= :end
    order by reading_date, t1.meter_name 
    """)
    sql = sql.columns(reading_date=db.Date, meter_reading=SqliteDecimal(10, 2), meter_delta=SqliteDecimal(10, 2))
    readings = db.engine.execute(sql, ac_id=thisac.id, start=pstart, end=pend).fetchall()
    installed_meters = db.session.query(ACMeters).filter(ACMeters.ac_id == thisac.id).all()
    row = 0
    if len(readings) == 0:
        raise ValueError("No Meter Readings in this range")
    try:
        filename = os.path.join(app.instance_path,
                                "downloads/" + thisac.regn + "_LOGBOOK" + ".xlsx")
        workbook = xlsxwriter.Workbook(filename)
        ws = workbook.add_worksheet("Meter Readings")
        borderdict = {'border': 1}
        noborderdict = {'border': 0}
        datedict = {'num_format': 'dd-mmm-yy'}
        timedict = {'num_format': 'h:mm'}
        dollardict = {'num_format': '$#, ##0.00'}
        merge_format = workbook.add_format(
            {
                "bold": 1,
                "border": 1,
                "align": "center",
                "valign": "vcenter",
                # "fg_color": "blue",
                "font_color": "#377ba8",
                "font_size": 14
            }
        )
        border_fmt = workbook.add_format({'border': 1, 'text_wrap': 1})
        # merge_format = workbook.add_format({'align': 'center', 'border': 1})
        date_format = workbook.add_format(dict(datedict, **noborderdict))
        dollar_fmt = workbook.add_format(dict(dollardict, **noborderdict))
        time_fmt = workbook.add_format(dict(timedict, **noborderdict))
        hrsmins_fmt = workbook.add_format({'num_format': '[h]:mm'})
        row = 3
        ws.write(row, 0, "Date", border_fmt)
        nextcol = 1
        metercol = []
        for i in installed_meters:
            ws.write(row, nextcol, i.std_meter_rec.meter_name + ' Reading', border_fmt)
            ws.write(row, nextcol + 1, i.std_meter_rec.meter_name + ' Change', border_fmt)
            metercol.append({"col": nextcol, "meter_name": i.std_meter_rec.meter_name})
            nextcol += 2
        notecol = (len(metercol) * 2) + 1
        ws.write(row, nextcol, "Note", border_fmt)
        nextcol += 1
        for i in task_based_columns:
            i["col"] = nextcol
            ws.write(row, nextcol, i["title"] + 'Reading', border_fmt)
            ws.write(row, nextcol + 1, i["title"] + ' Change', border_fmt)
            nextcol += 2
        row += 2
        last_row_reading_date = datetime.date(1900, 1, 1)
        for r in readings:
            if r.reading_date != last_row_reading_date:
                # new line in logbook
                row += 1
                ws.write(row, 0, r.reading_date, date_format)
                last_row_reading_date = r.reading_date
            # find which column to add this record
            mcol = [c for c in metercol if c["meter_name"] == r.meter_name][0]
            if mcol is not None:
                if r.entry_uom == 'Hours:Minutes':
                    if p_hrs_mins_as_string:
                        ws.write(row, mcol["col"], mins2hrsmins(r.meter_reading))
                        ws.write(row, mcol["col"] + 1, mins2hrsmins(r.meter_delta))
                    else:
                        ws.write(row, mcol["col"], round(r.meter_reading / (24 * 60), 2), hrsmins_fmt)
                        # in excel this has to be a decimal of one day.  There are 24*60 minutes
                        # in a day
                        ws.write(row, mcol["col"] + 1, r.meter_delta / (24 * 60), hrsmins_fmt)
                elif r.entry_uom == 'Decimal Hours':
                    ws.write(row, mcol["col"], round(r.meter_reading / 60, 2))
                    ws.write(row, mcol["col"] + 1, round(r.meter_delta / 60, 2))
                else:
                    ws.write(row, mcol["col"], r.meter_reading)
                    ws.write(row, mcol["col"] + 1, r.meter_delta)
            # Now find the meter_based_tasks columns
            for tbc in task_based_columns:
                delta,reading = get_readings(tbc,r.reading_date)
                ws.write(row, tbc["col"], reading)
                ws.write(row, tbc["col"] + 1, delta)
            ws.write(row, notecol, r.note)
        # col widths
        ws.autofit()
        # autfit overrides
        # ws.set_column(0, 0, 12)
        col = 1
        for i in range(len(installed_meters)):
            ws.set_column(col, col, 12)
            ws.set_column(col + 1, col + 1, 12)
            col += 2
        # Put in the title last so that the autofit works nicely
        row = 1
        ws.merge_range("A1:H1", "Aircraft Meter Readings for " + thisac.regn, merge_format)
        #
        # History
        #
        ws = workbook.add_worksheet("History")
        sql = sqltext("""
            select
            t0.history_date,
            t0.task_description description ,
            t0.task_id ,
            t4.meter_name,
            t3.entry_uom, 
            t0.meter_reading ,
            t2.task_description
            from acmainthistory t0
            left outer join actasks t1 on t1.ac_id = t0.ac_id and t0.task_id  = t1.id
            left outer join tasks t2 on t1.task_id = t2.id 
            left outer join acmeters t3 on t3.ac_id = t0.ac_id and t3.meter_id  =  t2.task_meter_id 
            left outer join meters t4 on t4.id = t3.meter_id 
            where t0.ac_id = :ac_id
            and t0.history_date >= :start
            and t0.history_date <= :end
            order by t0.history_date
        """)
        sql = sql.columns(reading_date=db.Date, meter_reading=SqliteDecimal(10, 2))
        history = db.engine.execute(sql, ac_id=thisac.id, start=pstart, end=pend).fetchall()
        row = 3
        ws.write(row, 0, "Date", border_fmt)
        ws.write(row, 1, "Reading", border_fmt)
        ws.write(row, 2, "Description", border_fmt)
        ws.write(row, 3, "Task Description", border_fmt)
        row += 1
        for h in history:
            ws.write(row, 0, h.history_date, date_format)
            if h.meter_name is not None:
                if h.entry_uom == 'Hours:Minutes':
                    ws.write(row, 1, round(h.meter_reading / (24 * 60), 2), hrsmins_fmt)
                elif h.entry_uom == 'Decimal Hours':
                    ws.write(row, 1, round(h.meter_reading / 60, 2))
                else:
                    ws.write(row, 1, h.meter_reading)
            ws.write(row, 2, h.description)
            ws.write(row, 3, h.task_description)
            row += 1
        ws.autofit()
        # Add Headings
        row = 1
        ws.merge_range("A1:D1", "Aircraft History for " + thisac.regn, merge_format)
    except Exception as e:
        applog.error("An error ocurred during spreadsheet create:{}".format(str(e)))
        applog.debug("Row was:{}".format(row))
        raise
    workbook.close()
    return filename
