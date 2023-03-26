from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Flask, send_from_directory, current_app,session,send_file
)

from asc.schema import Flight, User, Pilot
from asc import db
from flask_login import login_required, current_user
from sqlalchemy import text as sqltext, or_, bindparam
# WTForms
from flask_wtf import FlaskForm
from wtforms.fields import  DateField
from asc.wtforms_ext import MatButtonField, TextButtonField
from asc.common import *
import os
import xlsxwriter

bp = Blueprint('logbook', __name__, url_prefix='/logbook')
app = Flask(__name__)
applog = app.logger

class PromptForm(FlaskForm):
    start_date = DateField('Start Date',
                         description='Start Date')
    end_date = DateField('End Date',
                         description='End Date')
    btnsubmit = MatButtonField('done',
                            id='matdonebtn',
                            icon='done',
                            help="Confirm all Changes")
    cancel = MatButtonField('cancel',
                            id='matcancelbtn',
                            icon='cancel',
                            help="Press to exit and make no changes")  # , render_kw={'formnovalidate':''})

@bp.route('/logbook', methods=['GET','POST'])
@login_required
def logbook():
    if request.method == "GET":
        if 'startdate' in session:
            startdate = datetime.datetime.strptime(session['startdate'],"%Y-%m-%d").date()
        else:
            startdate = datetime.date.today() - datetime.timedelta(days=datetime.date.today().day - 1)
            session['startdate'] = startdate.strftime("%Y-%m-%d")
        if 'enddate' in session:
            enddate = datetime.datetime.strptime(session['enddate'],"%Y-%m-%d").date()
        else:
            enddate = datetime.date.today()
            session['enddate'] = enddate.strftime("%Y-%m-%d")
        thisuser = db.session.query(Pilot).filter(Pilot.userid == current_user.id).first()
        if thisuser is None:
            flash("Your userid is not associated with a pilot.  Sorry about that...")
            return render_template("index.html")
        if thisuser.userid is None:
            flash("Your userid is not associated with a pilot.  Sorry about that...")
            return render_template("index.html")
        # Get this user:
        sql = sqltext("""
            SELECT
                t0.id,
                t0.flt_date,
                t0.pic,
                t0.p2,
                COALESCE(t1.TYPE,"Unknown") actype,
                CASE WHEN ac_regn = 'TUG ONLY'
                    THEN tug_regn
                    ELSE ac_regn
                END regn,
                time(takeoff) takeoff,
                time(landed) landed,
                coalesce(round((julianday(t0.landed) - julianday(t0.takeoff)) * 1440,0),0) totalmins,
                coalesce(t1.seat_count,0) seat_count,
                CASE WHEN t0.p2 = t2.fullname THEN 'P2'
                    WHEN t1.seat_count = 1 THEN 'P1'
                    WHEN t1.seat_count = 2 AND t0.p2 = '' THEN 'P1'
                    WHEN t1.seat_count = 2 AND t2.instructor = 1 THEN 'DI' 
                    ELSE 'P1'
                END crew_capacity
                FROM flights t0
                LEFT OUTER JOIN aircraft t1 ON t0.ac_regn = t1.regn
                LEFT OUTER JOIN pilots t2 ON t2.userid = :pilot
                WHERE (t2.fullname = t0.pic OR t2.fullname = t0.p2)
                and t0.flt_date >= :startdate
                and t0.flt_date <= :enddate 
                and t0.linetype = 'FL'
            """)
        sql = sql.columns(id=db.Integer,
                         flt_date=db.Date,
                         pic=db.String,
                         p2=db.String,
                         actype=db.String,
                         regn=db.String,
                         takeoff=db.Time,
                         landed=db.Time,
                         totalmins=db.Integer,
                         seat_count=db.Integer,
                         crew_capacity=db.String
                         )
        flights = db.engine.execute(sql, startdate=startdate, enddate=enddate, pilot=thisuser.userid).fetchall()
        return render_template('logbook/logbook.html', list=flights, startdate=startdate, enddate=enddate)
    if request.method == "POST":
        return url_for("logbook.logbook",sdate=None,edate=None)

@bp.route("daterange", methods=["GET","POST"])
def daterange():
    thisform = PromptForm(name='Select Date Range')
    if thisform.cancel.data:
        return render_template('logbook/logbook.html')
    if request.method == 'GET':
        if 'startdate' in session:
            startdate = datetime.datetime.strptime(session['startdate'], "%Y-%m-%d").date()
        else:
            # Most likely we will want the previous Saturday.
            prevsat = datetime.date.today()
            while prevsat.weekday() != 5:
                prevsat = prevsat - datetime.timedelta(days=1)
            startdate = prevsat
        if 'enddate' in session:
            enddate = datetime.datetime.strptime(session['enddate'], "%Y-%m-%d").date()
        else:
            enddate = datetime.date.today()
        thisform.start_date.data = startdate
        thisform.end_date.data = enddate
        return render_template('logbook/daterange.html', form=thisform, title='Select Date Range')
    if request.method == 'POST':
        # Store in a cookie so we can use with excel button
        session['startdate'] = thisform.start_date.data.strftime("%Y-%m-%d")
        session['enddate'] = thisform.end_date.data.strftime("%Y-%m-%d")
        return redirect(url_for('logbook.logbook'))

@bp.route('/export', methods=['GET', 'POST'])
@login_required
def export():
    if 'startdate' in session:
        startdate = datetime.datetime.strptime(session['startdate'], "%Y-%m-%d").date()
    else:
        startdate = datetime.date.today() - datetime.timedelta(days=datetime.date.today().day - 1)
        session['startdate'] = startdate.strftime("%Y-%m-%d")
    if 'enddate' in session:
        enddate = datetime.datetime.strptime(session['enddate'], "%Y-%m-%d").date()
    else:
        enddate = datetime.date.today()
        session['enddate'] = startdate.strftime("%Y-%m-%d")
    thisuser = db.session.query(Pilot).filter(Pilot.userid == current_user.id).first()
    if thisuser is None:
        flash("Your userid is not associated with a pilot.  Sorry about that...")
        render_template("index.html")
    # Get this user:
    sql = sqltext("""
        SELECT
            t0.id,
            t0.flt_date,
            t0.pic,
            t0.p2,
            COALESCE(t1.TYPE,"Unknown") actype,
            CASE WHEN ac_regn = 'TUG ONLY'
                THEN tug_regn
                ELSE ac_regn
            END regn,
            time(takeoff) takeoff,
            time(landed) landed,
            coalesce(round((julianday(t0.landed) - julianday(t0.takeoff)) * 1440,0),0) totalmins,
            coalesce(t1.seat_count,0) seat_count,
            CASE WHEN t0.p2 = t2.fullname THEN 'P2'
                WHEN t1.seat_count = 1 THEN 'P1'
                WHEN t1.seat_count = 2 AND t0.p2 = '' THEN 'P1'
                WHEN t1.seat_count = 2 AND t2.instructor = 1 THEN 'DI' 
                ELSE 'P1'
            END crew_capacity
            FROM flights t0
            LEFT OUTER JOIN aircraft t1 ON t0.ac_regn = t1.regn
            LEFT OUTER JOIN pilots t2 ON t2.userid = :pilot
            WHERE (t2.fullname = t0.pic OR t2.fullname = t0.p2)
            and t0.flt_date >= :startdate
            and t0.flt_date <= :enddate 
            and t0.linetype = 'FL'
        """)
    sql = sql.columns(id=db.Integer,
                      flt_date=db.Date,
                      pic=db.String,
                      p2=db.String,
                      actype=db.String,
                      regn=db.String,
                      takeoff=db.Time,
                      landed=db.Time,
                      totalmins=db.Integer,
                      seat_count=db.Integer,
                      crew_capacity=db.String
                      )
    flights = db.engine.execute(sql, startdate=startdate, enddate=enddate, pilot=thisuser.userid).fetchall()
    return send_file(createxlsx(flights,thisuser.fullname), as_attachment=True)
    return render_template('logbook/logbook.html')

def createxlsx(flights,user):
    """
    Creates a spreadsheet ready for download for flights between two dates.
    :param self:
    :param flights:  List of flights to write
    :return: Name of excel file.
    """
    row = 0
    try:
        filename = os.path.join(app.instance_path,
                                "downloads/LOGBOOK_" + user.replace(" ","_") + ".xlsx")
        workbook = xlsxwriter.Workbook(filename)
        ws = workbook.add_worksheet()
        borderdict = {'border': 1}
        datedict = {'num_format': 'dd-mmm-yy'}
        timedict = {'num_format': 'h:mm'}
        dollardict = {'num_format': '$#, ##0.00'}
        border_fmt = workbook.add_format({'border': 1})
        merge_format = workbook.add_format({'align': 'center', 'border': 1})
        date_format = workbook.add_format(dict(datedict, **borderdict))
        dollar_fmt = workbook.add_format(dict(dollardict, **borderdict))
        time_fmt = workbook.add_format(dict(timedict, **borderdict))
        ws.write("A3", "Id", border_fmt)
        ws.write("B3", "Date", border_fmt)
        ws.write("C3", "Type", border_fmt)
        ws.write("D3", "Glider Reg", border_fmt)
        ws.write("E3", "PIC", border_fmt)
        ws.write("F3", "P2", border_fmt)
        ws.write("G3", "Take Off", border_fmt)
        ws.write("H3", "Landed", border_fmt)
        ws.write("I3", "Crew Cap", border_fmt)
        ws.write("J3", "Mins", border_fmt)
        row = 3
        for f in flights:
            ws.write(row, 0, f.id, border_fmt)
            ws.write(row, 1, f.flt_date.strftime("%d/%m/%Y"), border_fmt)
            ws.write(row, 2, f.actype, border_fmt )
            ws.write(row, 3, f.regn, border_fmt )
            ws.write(row, 4, f.pic, border_fmt)
            ws.write(row, 5, f.p2, border_fmt )
            ws.write(row, 6, f.takeoff, time_fmt )
            ws.write(row, 7, f.landed, time_fmt )
            ws.write(row, 8, f.crew_capacity, border_fmt )
            ws.write(row, 9, f.totalmins, border_fmt )
            row += 1
        ws.write(row + 1, 1, "Totals:", border_fmt)
        ws.write_formula(row + 1, 9, "sum(J4:J" + str(row) + ")", border_fmt)
        # col widths
        for i,v in enumerate([3,12,20,20,10,20,12,9,9,9,9,9,12,9,12,12,12,20]):
            ws.set_column(i,i,v)
    except Exception as e:
        applog.error("An error ocurred during spreadsheet create:{}".format(str(e)))
        applog.debug("Row was:{}".format(row))
        raise
    workbook.close()
    return filename