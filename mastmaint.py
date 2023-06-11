import datetime

import sqlalchemy.sql.expression
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Flask, send_from_directory, current_app
)
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
import os
import csv

from flask_login import login_required, current_user
from asc import db, create_app
from asc.schema import Flight, Pilot, Aircraft, Slot, User, Roster, SqliteDecimal
from sqlalchemy import text as sqltext, delete

# WTforms
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import Form, StringField, PasswordField, validators, SubmitField, SelectField, BooleanField, RadioField, \
    TextAreaField, DecimalField
from wtforms.fields import EmailField, IntegerField, DateField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length

from asc.mailer import ascmailer
import decimal


##########################################################################
#  WT Forms classes                                                      #
#########################################################################A

class PilotForm(FlaskForm):
    code = StringField('Code', [Length(min=1, message="The Code must be at least 1 characters long."),
                                validators.DataRequired(message='You cannot have a blank code'),
                                ],
                       description='GNZ ID')
    fullname = StringField('Full Name', [validators.DataRequired(message='You cannot have a blank code')],
                           description="Enter the full name - shown on reports and screens")
    email = StringField('Email', [Length(min=6, message=(u'Little short for an email address?')),
                                  Email(message=('That\'s not a valid email address.')),
                                  DataRequired(message=('That\'s not a valid email address.'))],
                        description='If an email is provided then information can be emailed to the pilot')
    instructor = BooleanField('Instructor', description='Tick if Instructor')
    towpilot = BooleanField('Tow Pilot', description='Tick if Tow Pilot')
    username = StringField("User Name"
                           , description="User id of this web site"
                           , render_kw={'list': "usernames"})
    # datejoined = DateField('Date Joined', description='Date Pilot Joined the club')
    bscheme = BooleanField('B Scheme Participant', description='Tick if included in B Scheme')
    yg_member = BooleanField('Youth Glide Member', description='Tick if pilot is a member of Youth Glide')
    gnz_no = IntegerField('GNZ No', description="Enter the GNZ No")
    accts_cust_code = StringField('Customer Code', description='The Customer code in the accounts system',
                                  render_kw={'class': 'mobile_port_supress mobile_land_supress'})

    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')
    delete = SubmitField('delete', id='deletebtn', render_kw={"OnClick": "ConfirmDelete()"})

    def validate_email(self, email):
        """Email validation."""
        pilot = Pilot.query.filter_by(email=email.data).first()
        if pilot is not None and pilot.code != self.code.data:
            raise ValidationError('Please use a different email address.')


class AircraftForm(FlaskForm):
    regn = StringField('Registration', [Length(min=3, message="The Code must be at least three characters long."),
                                        validators.DataRequired(message='You cannot have a blank registration)'),
                                        ],
                       description='Three Letter Aircraft Registration')
    type = StringField('Type',
                       description='Use the type that should be in the pilots logbook')
    rate_per_hour = DecimalField('Rate per hour')
    launch = BooleanField('Valid Launch method', description="Tick if this a/c can be used as a launch method")
    flat_charge_per_launch = DecimalField('Flat Charge per Launch',
                                          description="Enter an amount that is added to each launch (primarily for winch launches)")
    rate_per_height = DecimalField('Rate per Height',
                                   description="The rate per height basis - using release height from launch")
    per_height_basis = DecimalField('Height in Feet', description="Denominator for height based rates")
    rate_per_hour_tug_only = DecimalField('Non Launch Rate per hour',
                                          description="Std rate for non-launch flying the tug")
    bscheme = BooleanField('Affected by B Scheme')
    default_launch = StringField('Default Launch', description="Leave blank to use the system wide default")
    seat_count = IntegerField('Seat Count', description="Number of available seats on the a/c")
    owner = StringField('Owner', description="Aircraft Owner")
    default_pilot = StringField('Default Pilot', description='Default pilot for pic')
    accts_income_acct = StringField('Income Account', description='GL Income account',
                                    render_kw={'class': 'mobile_port_supress mobile_land_supress longnote'})

    accts_income_tow = StringField('Income Account - Tow Fees', description='GL Income account - Tow Fees',
                                   render_kw={'class': 'mobile_port_supress mobile_land_supress longnote'})
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')
    delete = SubmitField('delete', id='deletebtn', render_kw={"OnClick": "ConfirmDelete()"})


class SlotForm(FlaskForm):
    userid = StringField('User Id', description='Only applies to user based slots')
    slot_type = StringField('Type', description='Code looks for these.  They man something to the underlying Code.')
    slot_key = StringField('Key Value',
                           [validators.DataRequired(message='You cannot leave this blank')],
                           description='The code that will be stored in the database'
                           )
    slot_desc = StringField('Description', description='A description - displayed if field choice')
    slot_data = StringField('Data Field', description='Usually maintained in code somewhere')
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')
    delete = SubmitField('delete', id='deletebtn', render_kw={"OnClick": "ConfirmDelete()"})


class RosterUploadForm(FlaskForm):
    roster_file = FileField('Roster', validators=[FileRequired()], render_kw={"class": "longnote"})
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')


class PaidUploadForm(FlaskForm):
    payments_file = FileField('Payments', validators=[FileRequired()], render_kw={"class": "longnote"})
    btnsubmit = SubmitField('done', id='donebtn')  # the name must match the CSS content clause for material icons
    cancel = SubmitField('cancel', id='cancelbtn')


# app = Flask(__name__)
# app = create_app()
app = current_app
applog = app.logger

bp = Blueprint('mastmaint', __name__, url_prefix='/mastmaint')


@bp.route('/index')
@login_required
def index():
    app.logger.info("Maintenance Page accessed")
    return render_template('mastmaint/index.html')


@bp.route('/pilotlist', methods=['GET', 'POST'])
@login_required
def pilotlist():
    if not current_user.administrator:
        flash("Sorry, this is an admin only function")
        return render_template('index.html')
    if request.method == 'GET':
        list = Pilot.query.order_by(Pilot.fullname)
        return render_template('mastmaint/pilotlist.html', list=list)


@bp.route('/pilotmaint/<id>', methods=['GET', 'POST'])
@login_required
def pilotmaint(id):
    if not current_user.administrator:
        flash("Sorry, this is an admin only function")
        return render_template('index.html')
    thispilot = Pilot.query.get(id)
    usernames = [u.name for u in db.session.query(User).distinct()]
    # if thispilot is None then we will be adding
    if thispilot is None:
        thispilot = Pilot()
    thisform = PilotForm(obj=thispilot)
    if thispilot.userid is not None:
        if thispilot.userid != 0:
            thisusername = db.session.query(User).filter(User.id == thispilot.userid).first()
            thisform.username.data = thisusername.name
    # this is the line that does the work
    if thisform.validate_on_submit():
        if thisform.cancel.data:
            return redirect(url_for('mastmaint.pilotlist'))
        if thisform.delete.data:
            db.session.delete(thispilot)
            db.session.commit()
            return redirect(url_for('mastmaint.pilotlist'))
        # Provided the field names are the same, this function updates all the fields
        # on the table.  If there are any that are different then each field needs to be
        # assigned manually.
        thisform.populate_obj(thispilot)
        # Check what is in the username field.
        try:
            if thisform.username.data is None or len(thisform.username.data) == 0:
                thispilot.userid = None
            else:
                thisuser = db.session.query(User).filter(User.name == thisform.username.data).first()
                thispilot.userid = thisuser.id
        except Exception as e:
            flash("Invalid User id", "error")
            return render_template('mastmaint/pilotmaint.html', form=thisform, usernames=usernames)
        if thispilot.id is None:
            db.session.add(thispilot)
        db.session.commit()
        return redirect(url_for('mastmaint.pilotlist'))
    return render_template('mastmaint/pilotmaint.html', form=thisform, usernames=usernames)


@bp.route('/aircraftlist', methods=['GET', 'POST'])
@login_required
def aircraftlist():
    if not current_user.administrator:
        flash("Sorry, this is an admin only function")
        return render_template('index.html')
    if request.method == 'GET':
        list = Aircraft.query.order_by(Aircraft.regn)
        return render_template('mastmaint/aircraftlist.html', list=list)


@bp.route('/aircraftmaint/<id>', methods=['GET', 'POST'])
@login_required
def aircraftmaint(id):
    if not current_user.administrator:
        flash("Sorry, this is an admin only function")
        return render_template('index.html')
    thisaircraft = Aircraft.query.get(id)
    # if thispilot is None then we will be adding
    if thisaircraft is None:
        thisaircraft = Aircraft()
    thisform = AircraftForm(obj=thisaircraft)
    # this is the line that does the work
    if thisform.validate_on_submit():
        if thisform.cancel.data:
            return redirect(url_for('mastmaint.aircraftlist'))
        if thisform.delete.data:
            db.session.delete(thisaircraft)
            db.session.commit()
            return redirect(url_for('mastmaint.aircraftlist'))
        # Provided the field names are the same, this function updates all the fields
        # on the table.  If there are any that are different then each field needs to be
        # assigned manually.
        thisform.populate_obj(thisaircraft)
        if thisaircraft.id is None:
            db.session.add(thisaircraft)
        db.session.commit()
        return redirect(url_for('mastmaint.aircraftlist'))
    return render_template('mastmaint/aircraftmaint.html', form=thisform)


@bp.route('/slotlist', methods=['GET', 'POST'])
@login_required
def slotlist():
    if not current_user.administrator:
        flash("Sorry, this is an admin only function")
        return render_template('index.html')
    if request.method == 'GET':
        list = Slot.query.order_by(Slot.slot_type, Slot.slot_key)
        return render_template('mastmaint/slotlist.html', list=list)


@bp.route('/slotmaint/<id>', methods=['GET', 'POST'])
@login_required
def slotmaint(id):
    if not current_user.administrator:
        flash("Sorry, this is an admin only function")
        return render_template('index.html')
    thisrec = Slot.query.get(id)
    if thisrec is None:
        thisrec = Slot()
    thisform = SlotForm(obj=thisrec)
    if thisform.validate_on_submit():
        if thisform.cancel.data:
            return redirect(url_for('mastmaint.slotlist'))
        if thisform.delete.data:
            db.session.delete(thisrec)
            db.session.commit()
            return redirect(url_for('mastmaint.slotlist'))
        thisform.populate_obj(thisrec)
        if thisrec.id is None:
            db.session.add(thisrec)
        db.session.commit()
        return redirect(url_for('mastmaint.slotlist'))
    return render_template('mastmaint/slotmaint.html', form=thisform)


@bp.route('/userverify', methods=['Get'])
@login_required
def userverify():
    if not current_user.administrator:
        flash("Sorry, this is an admin only function")
        return render_template('index.html')
    # see also logbook.py for an example of this code that uses parameters
    sql = sqltext("""
    -- Unapproved user
        SELECT
        id key, fullname name, 'Unapproved user' msg,
        1 priority,
        'URGENT' msgtype,
        'users' tbl
        FROM users
        WHERE approved = 0
    -- users not showing up in pilots file
        UNION
        SELECT id, fullname, 'User id missing from pilots',5,'Warning','users'
        FROM users
        WHERE id NOT IN (SELECT userid FROM pilots)
    -- pilots missing a customer code
        UNION
        SELECT id, fullname , 'No Customer code and payer is in the last 90 days',9,'Warning', 'pilots'
        FROM pilots
        WHERE (accts_cust_code IS NULL OR length(accts_cust_code) = 0)
        AND fullname IN (SELECT payer FROM flights WHERE julianday('now') - julianday(flt_date) < 90)
    -- pilots missing a gnz code
        UNION
        SELECT id, fullname, 'No GNZ Code',8,'Warning','pilots'
        FROM pilots
        WHERE (gnz_no IS NULL OR gnz_no = 0) and fullname not like 'ATC%' and fullname not like 'Trial%'
    -- missing gnz no in users
        union
        SELECT id, fullname, 'User missing GNZ Code',8,'Warning','users'
        FROM users
        WHERE gnz_no IS NULL OR gnz_no = 0
    -- GNZ code in users not in pilots
        UNION 
        SELECT id, fullname, 'User GNZ Code not in pilots table',8,'Warning','users'
        FROM users
        WHERE gnz_no NOT IN (SELECT gnz_no FROM pilots)
    -- flights in last 30 days where the pilot appears more than once but is not in the pilots table
        union
        SELECT 
        max(id),name,'Pilot has more than one flight in the last 90 days but not in pilots table',max(2),'ERROR','flights'
        FROM (
            SELECT id,'pic' 'type', pic 'name' 
                FROM flights 
                WHERE linetype = 'FL'
                AND julianday('now') - julianday(flt_date) < 90
            UNION
            SELECT id,'p2', p2 
                FROM flights 
                WHERE linetype = 'FL' 
                AND julianday('now') - julianday(flt_date) < 90
                AND (p2 IS NOT NULL and LENGTH(p2) > 0)
        ) AS t0
        WHERE name NOT IN (SELECT fullname FROM pilots)
        AND name NOT LIKE '%trial%'
        and name not like '%pax%'
        GROUP BY 2 HAVING count(*) > 1
    -- pilot has chargeable flight in last 30 days but not in pilots table
        UNION
        SELECT id,payer,'Payer has chargeable flight in last 30 days but not in pilots table',2,'ERROR','flights'
        FROM flights
        WHERE payer NOT IN (SELECT fullname FROM pilots)
        AND julianday('now') - julianday(flt_date) < 30
    -- GNZ no different between users and pilots
        union
        SELECT t0.id, t0.fullname, 'User gnz_no does not match pilots table',8,'ERROR','users'
        FROM users t0
        JOIN pilots t1 ON t1.fullname = t0.fullname
        WHERE t0.gnz_no != t1.gnz_no
    -- email different between users and pilots
        union
        SELECT t0.id, t0.fullname, 'User email does not match pilots table',8,'ERROR','users'
        FROM users t0
        JOIN pilots t1 ON t1.fullname = t0.fullname
        WHERE t0.email != t1.email
    -- sort
        ORDER BY priority
            """)
    sql = sql.columns(id=db.Integer,
                      name=db.String,
                      msg=db.String,
                      priority=db.Integer,
                      msgtype=db.String,
                      tbl=db.String)
    messages = db.engine.execute(sql).fetchall()
    return render_template('mastmaint/userverify.html', messages=messages)


@bp.route('/unpaidflights', methods=['GET', 'POST'])
@login_required
def unpaidflights():
    if not current_user.administrator:
        flash("Sorry, this is an admin only function")
        return render_template('index.html')
    if request.method == 'GET':
        sql = """
                      SELECT t0.id, t0.flt_date, t0.payer,
                        t1.email, 
                         t0.tow_charge + t0.glider_charge + t0.other_charge amount
                         FROM flights t0
                         join pilots t1 on t0.payer = t1.fullname
                      where paid = False
                      and payer != 'Trial Flight'
                      and linetype = 'FL'
                      order by t0.payer,t0.id
                    """
        sql_to_execute = sqlalchemy.sql.text(sql)
        sql_to_execute = sql_to_execute.columns(flt_date=db.Date, duration=db.Integer, release_height=db.Integer,
                                                amount=SqliteDecimal(10, 2))
        # list = db.engine.execute(sql_to_execute, startdate=thisform.start_date.data,
        #                              enddate=thisform.end_date.data).fetchall()
        list = db.engine.execute(sql_to_execute).fetchall()
        return render_template('mastmaint/unpaidflights.html', list=list)


@bp.route('/rosterlist', methods=['GET', 'POST'])
@login_required
def rosterlist():
    if not current_user.administrator:
        flash("Sorry, this is an admin only function")
        return render_template('index.html')
    if request.method == 'GET':
        list = Roster.query.order_by(Roster.roster_date.desc())
        return render_template('mastmaint/rosterlist.html', list=list)


@bp.route('/rosterimport', methods=['GET', 'POST'])
@login_required
def rosterimport():
    if not current_user.administrator:
        flash("Sorry, this is an admin only function")
        return render_template('index.html')
    form = RosterUploadForm()
    if form.cancel.data:
        return redirect(url_for('mastmaint.rosterlist'))
    if form.validate_on_submit():
        filename = secure_filename(form.roster_file.data.filename)
        full_path_to_file = os.path.join(app.instance_path, filename)
        # Upload file to instance folder:
        form.roster_file.data.save(full_path_to_file)
        # File processing goes here:
        # Establish the earliest and latest dates from this file
        with open(full_path_to_file) as rosterfile:
            thisreader = csv.DictReader(rosterfile, delimiter=",")
            mindate = datetime.date(2200, 12, 31)  # just a date long after I will be alive!
            maxdate = datetime.date(1900, 1, 1)  # before the advent of flying!
            for row in thisreader:
                thisdate = datetime.datetime.strptime(row['Date'], "%d/%m/%Y").date()
                if thisdate < mindate:
                    mindate = thisdate
                if thisdate > maxdate:
                    maxdate = thisdate
        # Now remove all of those records
        db.session.query(Roster).filter(Roster.roster_date >= mindate).filter(Roster.roster_date <= maxdate).delete()
        # db.session.commit()
        # Finally add the new ones
        with open(full_path_to_file) as rosterfile:
            thisreader = csv.DictReader(rosterfile, delimiter=",")
            for row in thisreader:
                r = Roster()
                r.roster_date = datetime.datetime.strptime(row['Date'], "%d/%m/%Y")
                r.roster_inst = convert_pilot(row['Instructor'])
                r.roster_tp = convert_pilot(row['Tow_Pilot'])
                r.roster_dp = convert_pilot(row['Duty_Pilot'])
                db.session.add(r)
                db.session.commit()
        return redirect(url_for('mastmaint.rosterlist'))
    return render_template('mastmaint/rosterupload.html', form=form)


@bp.route('/paidupload', methods=['GET', 'POST'])
@login_required
def paidupload():
    if not current_user.administrator:
        flash("Sorry, this is an admin only function")
        return render_template('index.html')
    form = PaidUploadForm()
    if form.cancel.data:
        return redirect(url_for('mastmaint.unpaidflights'))
    if form.validate_on_submit():
        filename = secure_filename(form.payments_file.data.filename)
        full_path_to_file = os.path.join(app.instance_path, filename)
        # Upload file to instance folder:
        form.payments_file.data.save(full_path_to_file)
        # File processing goes here:
        # Establish the earliest and latest dates from this file
        with open(full_path_to_file) as paymentsfile:
            thisreader = csv.DictReader(paymentsfile, delimiter=",")
            for row in thisreader:
                # extract flight number
                print(row)
                if float(row['outstanding_amt']) == 0:
                    fid = int(row['id'][4:])
                    try:
                        flight = db.session.query(Flight).get(fid)
                        flight.paid = True
                        db.session.commit()
                    except Exception as e:
                        print("Failed to find flights {}:{}".format(fid, str(e)))
                        pass
        # now remember the date
        thisday = datetime.date.today()
        db.session.merge(
            Slot(slot_type='SYSTEM', slot_key='LASTPAIDUPDATE', slot_desc='Date last time invoice data was uploaded',
                 slot_data=thisday.strftime('%d-%b-%Y')))
        db.session.commit()
        return redirect(url_for('mastmaint.unpaidflights'))
    return render_template('mastmaint/paidupload.html', form=form)


@bp.route('/unpaidemail', methods=['GET', 'POST'])
@login_required
def unpaidemail():
    if not current_user.administrator:
        flash("Sorry, this is an admin only function")
        return render_template('index.html')
    sql = """
                   SELECT t0.id, t0.flt_date, t0.payer,
                     t1.email, 
                      t0.tow_charge + t0.glider_charge + t0.other_charge amount
                      FROM flights t0
                      join pilots t1 on t0.payer = t1.fullname
                   where paid = False
                   and payer != 'Trial Flight'
                   and linetype = 'FL'
                   order by t0.payer,t0.id
                 """
    sql_to_execute = sqlalchemy.sql.text(sql)
    sql_to_execute = sql_to_execute.columns(flt_date=db.Date, duration=db.Integer, release_height=db.Integer,
                                            amount=SqliteDecimal(10, 2))
    list = db.engine.execute(sql_to_execute).fetchall()
    lastemail = ''
    tbl = None  # this is an important control (None or not) on how the loop works.
    total = 0
    counter = 0
    for index,l in enumerate(list):
        # If the mail changes or we reach the last item.....
        if l['email'] != lastemail:
            if tbl != '' and lastemail != '':
                send_debtor_email(tbl,lastemail,total)
                tbl = None
                total = 0
                counter += 1
            print('new email {}'.format(l['email']))
        if tbl is None:
            tbl = '<table border="1" style="border-collapse:collapse; border:1px solid blue" ><tr><th>id</th><th>Date</th><th align=right>Amount</th></tr>'
        tbl += '<tr><td>' + str(l['id']) + '</td><td>' + \
               l['flt_date'].strftime('%d-%b-%Y') + '</td><td align=right>' + \
               '${:,.2f}'.format(l['amount']) + '</td></tr>'
        total += l['amount']
        lastemail = l['email']
    # now deal with sending the lastt item at the end of the loop.
    send_debtor_email(tbl, lastemail, total)
    return redirect(url_for('mastmaint.index'))

def send_debtor_email(ptbl,pemail,ptotal):
    if ptbl is None:
        return # Nothing to do
    if not isinstance(ptbl,str):
        raise AttributeError("Table parameter is not a string")
    if pemail is None:
        raise AttributeError("Email address is none")
    if ptotal is None:
        raise AttributeError("Total value is none")
    if not isinstance(pemail,str):
        raise AttributeError("email parameter is not a string")
    print(type(ptotal))
    if not isinstance(ptotal,decimal.Decimal) and not isinstance(ptotal,int) and not isinstance(ptotal,float):
        raise AttributeError("total parameter is not a number")
    # Finish the table
    ptbl += "<tr><td>Total</td><td></td><td>" + '${:,.2f}'.format(ptotal) + '</td></tr>'
    ptbl += "</table>"
    # Creatte the mail
    dunningcc = db.session.query(Slot).filter_by(slot_type='SYSTEM', slot_key='DUNNINGCC').first()
    msg = ascmailer('Outstanding flights requiring payment.')
    msg.add_body('Our records currently show the following flights as outstanding.<br>')
    msg.add_body('For further information on individual flights, log into the club flight system.<br>')
    msg.add_body('If you believe payment has already been made please contact the club treasurer.<br>')
    msg.add_body(ptbl)
    msg.add_body('<br><br>')
    # check if we have a last date
    lastdate = db.session.query(Slot).filter_by(slot_type='SYSTEM').filter_by(slot_key='LASTPAIDUPDATE').first()
    if lastdate is not None:
        msg.add_body('<br>Paymemts received after {} have not yet been processed'.format(lastdate.slot_data))
        msg.add_body('<br>')
    # If we are not in debug mode
    if db.session.query(Slot).filter_by(slot_type='SYSTEM', slot_key='MAILDEBUG').first() is None:
        if dunningcc is not None:
            if len(dunningcc.slot_data) > 0:
                msg.cc = dunningcc.slot_data
        msg.add_recipient(pemail)
        msg.send()
        applog.info('Dunning email sent to {}'.format(pemail))
    # ELSE i.e. we are in DEBUG mode.....
    else:
        msg.add_body('<br> would have gone to: {}'.format(pemail))
        msg.add_body('<br> cc would have been {}'.format(dunningcc.slot_data))
        msg.add_recipient("ray@rayburns.nz")
        if dunningcc is not None:
            if len(dunningcc.slot_data) > 0:
                msg.cc = dunningcc.slot_data
        msg.send()



def convert_pilot(proster_name):
    # look in pilots table for match:
    # replace the space with a percent:
    likeqry = proster_name.replace(" ", "%").strip()
    thispilot = Pilot.query.filter(Pilot.fullname.ilike(likeqry)).first()
    if thispilot is None:
        return proster_name
    else:
        return thispilot.fullname
