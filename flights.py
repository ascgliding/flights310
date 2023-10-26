from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Flask, send_from_directory, current_app,session
)
from werkzeug.exceptions import abort

from flask_login import login_required, current_user
from asc.schema import Flight, SchemaError, Aircraft, Pilot, Slot
from sqlalchemy import func, or_, and_
import datetime
from sqlalchemy import text as sqltext
from sqlalchemy.sql import func, select
# WTForms
from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, validators, SubmitField, SelectField, BooleanField, RadioField, \
    TextAreaField, TimeField
from wtforms.fields import EmailField, IntegerField, DateField, TimeField, DateTimeField, DecimalField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length

from asc.wtforms_ext import MatButtonField, TextButtonField
from decimal import *
from asc.common import *

try:
    # app = Flask(__name__)
    # from asc import create_app
    # app = create_app()
    app = current_app
except Exception as e:
    print("Failed to load app in flights.py: {}".format(e))



bp = Blueprint('flights', __name__, url_prefix='/flights')
applog = app.logger

constDAYDATE = 'daydate'
constDAYVIEW = 'dayview'

# TODO: Dayend to roll log if empty
# TODO: purge downloads folder
# TODO: ARE you sure for flights where either a start/tug down or landed is already recorded and the user presses that button.

class NewDayForm(FlaskForm):
    newdate = DateField('Date',
                     description="Today's Date",
                     default=datetime.date.today()
                     # validators=[validators.DataRequired()]
                    )
    instructor = StringField('Instructor',
                             description = "Instructor Name",
                             render_kw={'list': "instructors"})
    towpilot = StringField('Tow Pilot',
                             description = "Tow Pilot Name",
                             render_kw={'list': "towies"})
    dutypilot = StringField('Duty Pilot',
                             description = "Duty Pilot Name",
                             render_kw={'list': "dutypilots"})

class FlightForm(FlaskForm):
    id = IntegerField('ID',
                      description='Primary Key')
    pic = StringField('PIC',
                      [validators.DataRequired(message='You cannot have a blank code')],
                      description="Pilot in charge",
                      render_kw={'list': "activepilots"})
    p2 = StringField('P2',
                     description="Passenger or Student",
                     render_kw={'list': "activepilots"})
    flt_date = DateField('Date',
                         description='Flight Date',
                         render_kw={'class': 'mobile_port_supress mobile_land_supress'})
    ac_regn = StringField('Regn',
                          [validators.DataRequired(message='You cannot have a blank code')],
                          description='Last 3 characters of AC Registration',
                          render_kw={'list': "acregns"})
    takeoff = TimeField('Takeoff',
                        [validators.Optional()],
                        description="Takeoff Time",
                        render_kw={'step': "60"})
    tug_down = TimeField('Tug Down',
                         [validators.Optional()],
                         description="Time the Tow plane landed",
                         render_kw={'step': "60"})
    release_height = IntegerField('Release Height',
                                  [validators.Optional()],
                                  description='Release height in feet',
                                  render_kw={'Step': '500'})
    landed = TimeField('Landed',
                       [validators.Optional()],
                       description="Landing Time",
                       render_kw={'step': "60"})
    tow_pilot = StringField('Tow Pilot',
                            description="Tow Pilot",
                            render_kw={'list': "towies"})
    tug_regn = StringField('Tug Regn',
                           description="Tug Registration - Last Three Characters",
                           render_kw={'list': "towregnlist"})
    btnsubmit = MatButtonField('done',
                            id='matdonebtn',
                            icon='done',
                            help="Confirm all Changes")
    cancel = MatButtonField('cancel',
                            id='matcancelbtn',
                            icon='cancel',
                            help="Press to exit and make no changes")  # , render_kw={'formnovalidate':''})
    payment = MatButtonField('payment', id='matpaymentbtn', icon='attach_money',
                             help="Maintain cost and payment")  # , render_kw={'formnovalidate':''})
    note = MatButtonField('note', id='matnotebtn', icon='description',
                          help="Add a note to the flight")
    delete = MatButtonField('delete', id='matdeletebtn',
                            icon='delete',
                            help='Press to delete this record',
                            render_kw={'onclick': 'return ConfirmDelete()'})

class PaymentForm(FlaskForm):
    payer = StringField('Payer',
                        description='Person paying for this flight',
                        render_kw={'list': "pilots"})
    tow_charge = DecimalField('Launch',
                              description="Launch Charge",
                              places=2,
                              rounding=None)
    glider_charge = DecimalField('Glider',
                                 description="Glider Charge",
                                 places=2)
    other_charge = DecimalField('Other',
                                description="Other eg. Trial Flight Charge",
                                places=2)
    payment_note = StringField('Payment',
                               description = "Payment Method",
                               render_kw={'list': "paymentmethods"})
    paid = BooleanField('Paid',
                        description="Checked indicates this flight has been paid")
    btnsubmit = MatButtonField('done',
                            id='matdonebtn',
                            icon='done',
                            help="Confirm all Changes")
    cancel = MatButtonField('cancel',
                            id='matcancelbtn',
                            icon='cancel',
                            help="Press to exit and make no changes")  # , render_kw={'formnovalidate':''})
    # 22 Jan 23:  Removed the delete function
    # We don't want users to be able to delete a record on the payment screen
    # delete = MatButtonField('delete',
    #                         id='matdeletebtn',
    #                         icon='delete',
    #                         help='Press to delete this record',
    #                         render_kw={'onclick': 'return ConfirmDelete()'})
    calc = TextButtonField('Transactions',
                           id="calcbtn",
                           text='Calc',
                           help="Reset default charges")

class NoteForm(FlaskForm):
    flt_date = DateField('Date',
                         description='Flight Date',
                         )
    general_note = TextAreaField('Note',
                               description = "Any Notes for Lionel or yourself",
                                render_kw={'rows':'8'})
    btnsubmit = MatButtonField('done',
                            id='matdonebtn',
                            icon='done',
                            help="Confirm all Changes")
    cancel = MatButtonField('cancel',
                            id='matcancelbtn',
                            icon='cancel',
                            help="Press to exit and make no changes")  # , render_kw={'formnovalidate':''})
    delete = MatButtonField('delete', id='matdeletebtn',
                            icon='delete',
                            help='Press to delete this record',
                            render_kw={'onclick': 'return ConfirmDelete()'})



# TODO: Test Error Handling in Production environment.

@app.before_request
def before_request():
    applog.debug("In before_request")


@bp.route('/daysummary')
@login_required
def daysummary():
    # TODO: Add paging
    sql = sqltext("""
    SELECT
        flt_date,
        count(*) movements,
        max(id) last_id
        FROM flights 
        GROUP BY flt_date
        ORDER BY flt_date desc 
        """)
    sql = sql.columns(flt_date=db.Date)
    app.logger.info("Main Page accessed")
    try:
        summary = db.engine.execute(sql).fetchall()
        return render_template('flights/daysummary.html', summary=summary)
    except Exception as e:
        flash("An error occurred: {}".format(e))
        app.logger.info("An error occurred: {}".format(e))
        # return e
        abort(404, e)

@bp.route('/newday', methods=['GET','POST'])
@login_required
def newday():
    """
    Start a new day.  Get the roster details and so on.
    """
    if request.method == 'GET':
        instlist = [r.fullname for r in db.session.query(Pilot).filter(Pilot.instructor == True).all()]
        towielist = [r.fullname for r in db.session.query(Pilot).filter(Pilot.towpilot == True).all()]
        dplist = [r.fullname for r in db.session.query(Pilot).filter(Pilot.towpilot == False).filter(Pilot.instructor == False).all()]
        newdate = datetime.date.today()
        thisform = NewDayForm()
        todayroster = Roster.query.filter(Roster.roster_date >= newdate).first()
        if todayroster is None:
            thisform.newdate.data = datetime.date.today()
        else:
            thisform.newdate.data = todayroster.roster_date
            thisform.instructor.data = todayroster.roster_inst
            thisform.towpilot.data = todayroster.roster_tp
            thisform.dutypilot.data = todayroster.roster_dp
    if request.method == 'POST' :
        thisform = NewDayForm(request.form)
        # Add the note here
        notetext = "Instructor:{}, Tow Pilot:{}, Duty Pilot:{}".format(thisform.instructor.data,
                                                                       thisform.towpilot.data,
                                                                       thisform.dutypilot.data)
        daynote = Flight(flt_date=thisform.newdate.data,
                         linetype='NT',
                         general_note=notetext)
        db.session.add(daynote)
        db.session.commit()
        # print("post note: {} / {}".format(thisform.newdate.data,thisform.instructor.data))
        return redirect(url_for('flights.daysheet', date=thisform.newdate.data.strftime('%Y-%m-%d')))
    # if not post....
    return render_template('flights/newday.html', form=thisform, instlist=instlist, towielist=towielist,
                           dplist=dplist)

@bp.route('/daysheet/<date>')
@login_required
def daysheet(date):
    """
    Display flights on a day
    :param date: String.  Can be one of:
        "TODAY" - obvious
        "SESSION" - a date stored in the session cookie "DAYDATE"
        a string in dd-mmm-yyyy format
    :return:
    """
    if date == 'TODAY':
        thisdate = date.today()
    elif date == 'SESSION':
        thisdate = datetime.datetime.strptime(session[constDAYDATE],'%Y-%m-%d').date()
    else:
        thisdate = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    # Now remember it:
    session[constDAYDATE] = datetime.datetime.strftime(thisdate, '%Y-%m-%d')
    # Deal with the view
    if constDAYVIEW in session:
        view = session[constDAYVIEW]
    else:
        view = 'ALL'
    if view is None:
        view = 'ALL'
    if view == 'AIRBORNE':
        thisset = db.session.query(Flight).filter(Flight.linetype == 'FL').filter(Flight.flt_date == thisdate).filter(Flight.takeoff != None).filter(Flight.landed == None).all()
        title = "Airborne " + thisdate.strftime("%a %d %b")
    elif view == 'WAITING':
        thisset = db.session.query(Flight).filter(Flight.linetype == 'FL').filter(Flight.flt_date == thisdate).filter(Flight.takeoff == None).all()
        title = "Gridded " + thisdate.strftime("%a %d %b")
    elif view == 'LANDED':
        thisset = db.session.query(Flight).filter(Flight.linetype == 'FL').filter(Flight.flt_date == thisdate).filter(Flight.landed != None).all()
        title = "Landed " +  thisdate.strftime("%a %d %b")
    elif view == 'UNPAID':
        thisset = db.session.query(Flight).filter(Flight.linetype == 'FL').filter(Flight.flt_date == thisdate).filter(Flight.landed != None).filter(or_(Flight.payment_note == None, Flight.payment_note =='')).all()
        title = "Unpaid"
    else:
        thisset = db.session.query(Flight).filter(Flight.flt_date == thisdate).all()
        title  = "All Flights " + thisdate.strftime("%a %d %b")
    # see if it is possible to record tug down with one button.
    launched = db.session.query(Flight).filter(Flight.linetype == 'FL').filter(Flight.flt_date == thisdate).filter(Flight.takeoff != None).filter(Flight.tug_down == None).all()
    current_glider_under_tow = ''
    id_of_towed_aircraft = 0
    count_of_towed_aircraft = 0
    for l in launched:
        # check if slef launch
        thisaircraft = db.session.query(Aircraft).filter(Aircraft.regn == l.ac_regn).first()
        if thisaircraft is not None and thisaircraft.default_launch != constTOW_FOR_SELF_LAUNCH:
            id_of_towed_aircraft = l.id
            current_glider_under_tow = l.ac_regn
            count_of_towed_aircraft += 1
    if count_of_towed_aircraft > 1:
        flash("Seems we have > 1 aircraft under tow!!")
    try:
        return render_template('flights/daysheet.html', title=title,  flights=thisset ,
                               towcount=count_of_towed_aircraft,
                               towedregn=current_glider_under_tow,
                               towedid=id_of_towed_aircraft
                               )
    except Exception as e:
        flash("An error occurred: {}".format(e))
        app.logger.info("An error occurred: {}".format(e))
        return render_template('flights/daysummary.html')

@bp.route('/changeview', methods=['GET', 'POST'])
@login_required
def changeview():
    if request.method == 'GET':
        return render_template('flights/changeview.html')
    if request.method == 'POST':
        session[constDAYVIEW] = request.form['view']
    return redirect(url_for('flights.daysheet', date='SESSION'))

@bp.route('/changeflight/<id>', methods=['GET', 'POST'])
@login_required
def changeflight(id):
    # --------------------------------------------------------------------------------------------
    # Preparation - get default values, poplulate lists
    # --------------------------------------------------------------------------------------------
    thisrec = Flight.query.get(id)
    # if thisrec is None then we will be adding
    if thisrec is None:
        thisrec = Flight()
        thisrec.flt_date = db.session.query(func.max(Flight.flt_date).label("maxdate")).scalar()
        lastflt = db.session.query(Flight).filter(Flight.linetype == 'FL').order_by(Flight.id.desc()).first()
        # Determine the TUG:
        if lastflt is not None:
            thisrec.tow_pilot = lastflt.tow_pilot
            applog.debug("New rec tow pilot set to {} at point A. LAst flit id is {}".format(lastflt.tow_pilot, lastflt.id))
            thisrec.tug_regn = lastflt.tug_regn
        # on a mobile platform the flight date is always the current date.  On windows or linux it will be prompted.
        # is todays date equal to the flight date?
        applog.info("User Agent:{}".format(request.user_agent.platform))
        if request.user_agent.platform is not None and request.user_agent.platform not in ['windows', 'linux']:
            thisrec.flt_date = datetime.date.today()
    else:
        lastdate = thisrec.flt_date
    #
    thisform = FlightForm(obj=thisrec, name='Flight Maintenance')
    if thisform.cancel.data:
        return redirect(url_for('flights.daysheet', date=thisrec.flt_date.strftime('%Y-%m-%d')))
    # Pilot list
    # Populate the choices list for pilots and
    sql = sqltext("""
          select pic
          from flights
          where flt_date > :date
          and pic <> ''
          and linetype = 'FL'
          union
          select p2
          from flights
          where flt_date > :date
          and p2 <> ''
          and linetype = 'FL'
          union
          select fullname
          from pilots
          """)
    if thisrec.flt_date is not None:
        activepilotdate = thisrec.flt_date - datetime.timedelta(days=180)
    else:
        activepilotdate = datetime.date.today()
    pilotlist = [r[0] for r in db.engine.execute(sql, date=activepilotdate).fetchall()]
    # A/C List
    sql = sqltext("""
        select distinct ac_regn
        from flights
        where flt_date > :date
        and linetype = 'FL'
       union
        select regn
        from aircraft
        order by ac_regn
        """)
    if thisrec.flt_date is not None:
        activeacdate = thisrec.flt_date - datetime.timedelta(days=90)
    else:
        activeacdate = datetime.date.today()
    acregnlist = [r[0] for r in db.engine.execute(sql, date=activeacdate).fetchall()]
    # Add the Tug only if it not already there..(i.e. used in last 90 days) ...
    if constREGN_FOR_TUG_ONLY not in acregnlist:
        acregnlist.append(constREGN_FOR_TUG_ONLY)
    # Towie list
    towielist = [r.fullname for r in db.session.query(Pilot).filter(Pilot.towpilot == True).all()]
    sql = sqltext("""
        select distinct regn
        from aircraft 
        where launch = 1
    """)
    towregnlist = [r.regn for r in db.engine.execute(sql).fetchall()]
    towregnlist.append(constTOW_FOR_SELF_LAUNCH)


    # --------------------------------------------------------------------------------------------
    # Processing
    # --------------------------------------------------------------------------------------------
    if request.method == 'POST' and thisform.validate():
        # Provided the field names are the same, this function updates all the fields
        # on the table.  If there are any that are different then each field needs to be
        # assigned manually.
        try:
            thisform.populate_obj(thisrec)
            if thisrec.id is None:
                # thisrec.pic_gnz_no = thisrec.get_pic_gnz_no()
                # thisrec.p2_gnz_no = thisrec.get_p2_gnz_no()
                db.session.add(thisrec)
                applog.info('New Flight added: {}'.format(thisrec.id))
            elif thisform.delete.data:
                db.session.delete(thisrec)
                applog.info('Flight {} deleted'.format(id))
            else:
                # if this a tug only flight make sure that tug down and landed are the same
                # thisrec.pic_gnz_no = thisrec.get_pic_gnz_no()
                # thisrec.p2_gnz_no = thisrec.get_p2_gnz_no()
                if thisrec.ac_regn == constREGN_FOR_TUG_ONLY or thisrec.tug_regn == constTOW_FOR_SELF_LAUNCH:
                    if thisrec.tug_down == None and thisrec.landed != None:
                        thisrec.tug_down = thisrec.landed
                    elif thisrec.tug_down != None and thisrec.landed == None:
                        thisrec.landed = thisrec.tug_down
                applog.info('Flight {} changed'.format(id))
            if thisrec.tug_regn != constTOW_FOR_SELF_LAUNCH and thisrec.ac_regn != constREGN_FOR_TUG_ONLY:
                addupdslot('DEFAULT','LASTTOWIE',thisrec.tow_pilot)
                addupdslot('DEFAULT','LASTTUG',thisrec.tug_regn)
            applog.debug('Just before commit: towie is {}'.format(thisrec.tow_pilot))
            db.session.commit()
            if thisform.note.data:
                return redirect(url_for('flights.flightnote', id=thisrec.id))
            if thisform.payment.data:
                return redirect(url_for('flights.payment', id=thisrec.id))
        except SchemaError as e:
            flash(e)
            return render_template('flights/changeflight.html', form=thisform, pilots=pilotlist, ac=acregnlist, towielist=towielist)
        return redirect(url_for('flights.daysheet', date=thisrec.flt_date.strftime('%Y-%m-%d')))
    applog.debug('About to render changefligt at b with id {}'.format(thisform.id.data))
    return render_template('flights/changeflight.html', form=thisform, pilots=pilotlist, ac=acregnlist, towielist=towielist, towregnlist=towregnlist)

# NOTELINE is a line of type NT that is NOT a flight!
@bp.route('/linenote/<id>', methods=['GET', 'POST'])
@login_required
def linenote(id):
    if constDAYDATE in session:
        thisdate = datetime.datetime.strptime(session[constDAYDATE], '%Y-%m-%d').date()
    else:
        thisdate = datetime.date.today()
    thisrec = Flight.query.get(id)
    if thisrec is None:
        thisrec = Flight()
        thisrec.flt_date = db.session.query(func.max(Flight.flt_date).label("maxdate")).scalar()
        # lastflt = db.session.query(Flight).order_by(Flight.id.desc()).first()
        thisrec.linetype = 'NT'
    thisform = NoteForm(obj=thisrec, name='Notes for Flight')
    if request.method == 'GET':
        # if thisrec is None then we will be adding
        return render_template('flights/changenote.html', form=thisform, line=thisrec)
    if request.method == 'POST' and thisform.validate():
        # Provided the field names are the same, this function updates all the fields
        # on the table.  If there are any that are different then each field needs to be
        # assigned manually.
        try:
            thisform.populate_obj(thisrec)
            if thisrec.id is None:
                db.session.add(thisrec)
                applog.info('New Note added: {}'.format(thisrec.id))
            elif thisform.delete.data:
                db.session.delete(thisrec)
                applog.info('Note {} deleted'.format(id))
            else:
                applog.info('Note {} note details updated'.format(id))
            db.session.commit()
            return redirect(url_for('flights.daysheet', date=thisdate.strftime('%Y-%m-%d')))
        except SchemaError as e:
            flash(e)
            return render_template('flights/changenote.html', form=thisform)
        except Exception as e:
            flash(e)
            return render_template('flights/changenote.html', form=thisform)
        return redirect(url_for('flights.daysheet', date=thisdate.strftime('%Y-%m-%d')))
    return redirect(url_for('flights.daysheet', date=thisdate.strftime('%Y-%m-%d')))


@bp.route('/flightnote/<id>', methods=['GET', 'POST'])
@login_required
def flightnote(id):
    if constDAYDATE in session:
        thisdate = datetime.datetime.strptime(session[constDAYDATE], '%Y-%m-%d').date()
    else:
        thisdate = datetime.date.today()
    thisrec = Flight.query.get(id)
    if thisrec is None:
        flash("Unable to locate record")
        return redirect(url_for('flights.daysheet', date=thisdate.strftime('%Y-%m-%d')))
    # otherwise we have a good record
    thisform = NoteForm(obj=thisrec, name='Notes for Flight')
    if request.method == 'GET':
        return render_template('flights/changenote.html', form=thisform, line=thisrec)
    if request.method == 'POST' and thisform.validate():
        # Provided the field names are the same, this function updates all the fields
        # on the table.  If there are any that are different then each field needs to be
        # assigned manually.
        try:
            thisform.populate_obj(thisrec)
            if thisrec.id is None:
                flash("Unable to locate record")
                return redirect(url_for('flights.daysheet', date=thisdate.strftime('%Y-%m-%d')))
            else:
                applog.info('Flight {} note details updated'.format(id))
            db.session.commit()
        except SchemaError as e:
            flash(e)
            return render_template('flights/changenote.html', form=thisform)
        return redirect(url_for('flights.daysheet', date=thisdate.strftime('%Y-%m-%d')))
    return redirect(url_for('flights.daysheet', date=thisdate.strftime('%Y-%m-%d')))


@bp.route('/tuglanded/<id>')
@login_required
def tuglanded(id):
    if constDAYDATE in session:
        thisdate = datetime.datetime.strptime(session[constDAYDATE], '%Y-%m-%d').date()
    else:
        thisdate = datetime.date.today()
    try:
        thisflight = Flight.query.get(id)
        if thisflight.linetype != 'FL':
            flash("This line is not a flight")
            return redirect(url_for('flights.daysheet', date=thisdate.strftime('%Y-%m-%d')))
        down = datetime.datetime.now()
        # now round to the nearest minute
        if down.second > 30:
            # remove the seconds
            down -= datetime.timedelta(seconds=down.second, microseconds=down.microsecond)
            # Add one minute
            down += datetime.timedelta(minutes=1)
        else:
            # jsut remove the seconds
            down -= datetime.timedelta(seconds = down.second, microseconds=down.microsecond)
        thisflight.tug_down = down.time()
        if thisflight.ac_regn == constREGN_FOR_TUG_ONLY or thisflight.tug_regn == constTOW_FOR_SELF_LAUNCH:
            if thisflight.tug_down == None and thisflight.landed != None:
                thisflight.tug_down = thisflight.landed
            elif thisflight.tug_down != None and thisflight.landed == None:
                thisflight.landed = thisflight.tug_down
        db.session.commit()
    except Exception as e:
        applog.debug("Error updating tug down :{}".format(e))
        flash("Unable to update.  Record via Flight id")
    return redirect(url_for('flights.daysheet', date=thisdate.strftime('%Y-%m-%d')))

@bp.route('/payment/<id>', methods=['GET', 'POST'])
@login_required
def payment(id):
    thisrec = Flight.query.get(id)
    # if thisrec is None then we have an error
    if thisrec is None:
        flash("Cannot locate flight")
        return redirect(url_for('flights.daysummary'))
    thisform = PaymentForm(obj=thisrec, name='Payment Maintenance')
    if thisform.cancel.data:
        return redirect(url_for('flights.changeflight', id=id))
    if thisform.calc.data:
        if not calc_charges(id):
            flash("There was a problem setting the default charges")
        return redirect(url_for('flights.payment', id=id))
    if request.method == 'POST' and thisform.validate():
        # Provided the field names are the same, this function updates all the fields
        # on the table.  If there are any that are different then each field needs to be
        # assigned manually.
        try:
            thisform.populate_obj(thisrec)
            if thisrec.id is None:
                db.session.add(thisrec)
                applog.info('New payment details Added')
            # 22 Jan 23 - do not allow delete on the payment form.
            # elif thisform.delete.data:
            #     db.session.delete(thisrec)
            #     applog.info('Flight {} payment details deleted'.format(id))
            else:
                applog.info('Flight {} payment details updated'.format(id))
            db.session.commit()
        except SchemaError as e:
            flash(e)
            return render_template('flights/payment.html', form=thisform, glider_time = thisrec.glider_mins())
        return redirect(url_for('flights.daysheet', date=thisrec.flt_date.strftime('%Y-%m-%d')))
    # if we are here then we are getting the data for display
    sql = sqltext("""
             select fullname
             from pilots
             """)
    pilotlist = [r[0] for r in db.engine.execute(sql).fetchall()]
    return render_template('flights/payment.html', form=thisform,pilots=pilotlist)


def calc_charges(id):
    """
    For a given id calculate the charges and update the record.
    :param id: The ID of the record
    :return: Boolean to say if all was ok or not
    """
    try:
        thisrec = Flight.query.get(id)
        if thisrec is None:
            return False
        # Launch fee
        tug = Aircraft.query.filter_by(regn=thisrec.tug_regn).first()
        if tug is None and thisrec.tug_regn != constTOW_FOR_SELF_LAUNCH:
            return False
        if thisrec.ac_regn == constREGN_FOR_TUG_ONLY:
            if thisrec.tow_mins() <= 0:
                flash('Insufficient flight data to calculate default charges')
                return False
        elif thisrec.tug_regn == constTOW_FOR_SELF_LAUNCH:
            pass # there are no checks.
        else:  # Not tug only.
            if thisrec.tow_mins is None \
                or (thisrec.release_height is None and thisrec.tug_regn != constTOW_FOR_SELF_LAUNCH) \
                or thisrec.glider_mins() == 0:
                flash('Insufficient flight data to calculate default charges')
                return False
            if thisrec.tow_mins() <= 0 or thisrec.glider_mins() <= 0:
                flash('Incorrect flight data.  Cannot calculate default charges')
                return False
        # Flight fee
        thisac = Aircraft.query.filter_by(regn=thisrec.ac_regn).first()
        if thisac is None:
            # this could be valid.  Could be a visiting a/c
            thisrec.glider_charge = 0
        # BIG IF-ELIF that determins the rates
        # Start with trial flights
        if thisrec.p2.upper() == constTRIAL_FLIGHT_CUST:
            SlotForRate = Slot.query.filter_by(slot_type='DEFAULT').filter_by(slot_key='TRIALFLIGHTPRICE').first()
            if SlotForRate is None:
                thisrec.tow_charge = 100
            else:
                thisrec.tow_charge = SlotForRate.slot_data
            thisrec.payer = thisrec.p2
        # REGN_FOR_TUG_ONLY appears in the Glider Regn field.
        elif thisrec.ac_regn == constREGN_FOR_TUG_ONLY:
            thisrec.glider_charge = 0
            thisrec.tow_charge = Decimal(thisrec.tow_mins() * (tug.rate_per_hour_tug_only / 60))
            thisrec.payer = thisrec.pic_rec().fullname
            # Nothing else to do if the tug is flown on it's own.
        elif thisrec.tug_regn == constTOW_FOR_SELF_LAUNCH:
            thisrec.tow_charge = 0
            thisrec.glider_charge = Decimal(thisrec.glider_mins()) * (thisac.rate_per_hour / 60)
            if thisrec.p2 is not None:
                payer = Pilot.query.filter_by(fullname=thisrec.p2).first()
            if payer is None:
                payer = Pilot.query.filter_by(fullname=thisrec.pic).first()
            if payer is not None:
                if payer.bscheme and thisac.bscheme:
                    thisrec.glider_charge = 0
            if payer is not None:
                thisrec.payer = payer.fullname
        else: # Normal Launch
            # Calculate the tow / launch costs
            thisrec.tow_charge = 0
            if tug.rate_per_height != 0:
                thisrec.tow_charge += Decimal((thisrec.release_height / tug.per_height_basis) * tug.rate_per_height)
            if tug.rate_per_hour != 0:
                thisrec.tow_charge += Decimal(thisrec.tow_mins() * (tug.rate_per_hour / 60))
            if tug.flat_charge_per_launch != 0:
                thisrec.tow_charge += tug.flat_charge_per_launch
            # Calculate the glider charge
            thisrec.glider_charge = Decimal(thisrec.glider_mins()) * (thisac.rate_per_hour / 60)
            if thisrec.p2 is not None:
                payer = Pilot.query.filter_by(fullname=thisrec.p2).first()
            if payer is None:
                payer = Pilot.query.filter_by(fullname=thisrec.pic).first()
            if payer is not None:
                if payer.bscheme and thisac.bscheme:
                    thisrec.glider_charge = 0
            if payer is not None:
                thisrec.payer = payer.fullname
        db.session.commit()
    except Exception as e:
        flash(str(e))
        return False
    return True

