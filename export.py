from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Flask, send_from_directory, current_app,session,send_file
)
# from werkzeug.exceptions import abort

from flask_login import login_required, current_user
# from asc.schema import Flight, SchemaError, Aircraft, Pilot, Slot
# from sqlalchemy import func, or_, and_
import datetime
from sqlalchemy import text as sqltext
# from sqlalchemy.sql import func, select
# WTForms
from flask_wtf import FlaskForm
# from wtforms import Form, StringField, PasswordField, validators, SubmitField, SelectField, BooleanField, RadioField, \
#     TextAreaField, TimeField
# from wtforms.fields import EmailField, IntegerField, DateField, TimeField, DateTimeField, DecimalField
from wtforms.fields import BooleanField
from wtforms.fields import  DateField
# from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from asc.wtforms_ext import MatButtonField, TextButtonField
# from decimal import *
from asc.common import *
import os
import xlsxwriter
import csv
from asc import create_app

# app = Flask(__name__)
# app = create_app()
app = current_app
applog = app.logger

bp = Blueprint('export', __name__, url_prefix='/export')

# TODO :  General_note for flight + general_note record.

class ExcelPromptForm(FlaskForm):
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

class AcctsExportForm(FlaskForm):
    export_dates = BooleanField('Use exported date',
                              description='Ticked will check export dates and update export dates',
                              default=1)
    include_header = BooleanField('Include Header Record',
                                  description='Include the header record in the csv.  Leave unchecked for GNU',
                                default = 0)
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


@bp.route('/exportflt', methods=['GET', 'POST'])
@login_required
def exportflt():
    thisform = ExcelPromptForm(name='Export Flights to Excel')
    if thisform.cancel.data:
        return render_template('mastmaint/index.html')
    if request.method == 'GET':
        # Most likely we will want the previous Saturday.
        prevsat = datetime.date.today()
        while prevsat.weekday() != 5:
            prevsat = prevsat - datetime.timedelta(days=1)
        thisform.start_date.data = prevsat
        thisform.end_date.data = datetime.date.today()
        return render_template('export/exp_daterange.html', form=thisform, title='Export Flights')
    if request.method == 'POST':
        rflights = db.session.query(Flight).filter(Flight.linetype == 'FL').filter(
            Flight.flt_date >= thisform.start_date.data).filter(Flight.flt_date <= thisform.end_date.data).all()
        rflights = db.session.query(Flight).filter(Flight.flt_date >= thisform.start_date.data).filter(
            Flight.flt_date <= thisform.end_date.data).order_by(Flight.flt_date,Flight.id).all()
        if len(rflights) <= 0:
            flash("No Flights in this date range")
            return render_template('export/exp_daterange.html', form=thisform, title='Export Flights')
        return send_file(createfltsxlsx(rflights), as_attachment=True)
        return render_template('mastmaint/index.html')

@bp.route('/exportacsummary', methods=['GET', 'POST'])
@login_required
def exportacsummary():
    thisform = ExcelPromptForm(name='Export AC Summary')
    if thisform.cancel.data:
        return render_template('mastmaint/index.html')
    if request.method == 'GET':
        # Most likely we will want the previous Saturday.
        prevsat = datetime.date.today()
        while prevsat.weekday() != 5:
            prevsat = prevsat - datetime.timedelta(days=1)
        thisform.start_date.data = prevsat
        thisform.end_date.data = datetime.date.today()
        return render_template('export/exp_daterange.html', form=thisform, title="Export A/C Summary to Excel")
    if request.method == 'POST':
        sql = sqltext("""
                SELECT flt_date, ac_regn,  
                count(*) fltcount, 
                sum(round((julianday(landed) - julianday(takeoff)) * 1440,2)) totalmins
                FROM flights
                where flt_date >= :startdate
                and flt_date <= :enddate 
                and linetype = 'FL'
                GROUP BY flt_date,ac_regn
                order by ac_regn, flt_date
              """)
        fltsummary = db.engine.execute(sql, startdate=thisform.start_date.data, enddate=thisform.end_date.data).fetchall()
        if len(fltsummary) <= 0:
            flash("No Flights in this date range")
            return render_template('export/exp_daterange.html', form=thisform, title='Export A/C Summary to Excel')
        for w in fltsummary:
            f = datetime.datetime.strptime(w.flt_date,'%Y-%m-%d').date()
        return send_file(createsummsxlsx(fltsummary), as_attachment=True)
        return render_template('mastmaint/index.html')

@bp.route('/exportaccts', methods=['GET', 'POST'])
@login_required
def exportaccts():
    if not current_user.administrator:
        flash("Sorry, this is an admin only function")
        return render_template('index.html')
    thisform = AcctsExportForm(name='Export Invoices')
    if thisform.cancel.data:
        return render_template('mastmaint/index.html')
    if request.method == 'GET':
        # Most likely we will want the previous Saturday.
        prevsat = datetime.date.today()
        while prevsat.weekday() != 5:
            prevsat = prevsat - datetime.timedelta(days=1)
        thisform.start_date.data = prevsat
        thisform.end_date.data = datetime.date.today()
        return render_template('export/exportaccts.html', form=thisform, title="Export to accounting system")
    if request.method == 'POST':
        if thisform.export_dates.data:
            sql = sqltext("""
                    SELECT id,flt_date 
                    FROM flights
                    where flt_date >= :startdate
                    and flt_date <= :enddate 
                    and linetype = 'FL'
                    and accts_export_date is null
                  """)
        else:
            sql = sqltext("""
                    SELECT id,flt_date  
                    FROM flights
                    where flt_date >= :startdate
                    and flt_date <= :enddate 
                    and linetype = 'FL'
                  """)
        flights = db.engine.execute(sql, startdate=thisform.start_date.data, enddate=thisform.end_date.data).fetchall()
        if len(flights) == 0:
            flash("There are no flights to export in this range","warning")
            return render_template('export/exportaccts.html', form=thisform, title="Export to Accts System")
        else:
            flash("There are {} flights to export in this range".format(len(flights)), "warning")
        #for w in fltsummary:
        #    f = datetime.datetime.strptime(w.flt_date,'%Y-%m-%d').date()
        try:
            rtndict = getacctsexport(flights,thisform.export_dates.data, thisform.include_header.data)
            return redirect(
                url_for('export.exportacctsmsgs', pstart=thisform.start_date.data, pend=thisform.end_date.data,
                        pheader=thisform.include_header.data, pexport_dates=thisform.export_dates.data))

            return render_template('export/exportacctsmsgs.html',  title="Export to Accts System", messages=rtndict['msgs'],filename=rtndict['filename'])
            return send_file(getacctsexport(flights,thisform.export_dates.data, thisform.include_header.data), as_attachment=True)
        except Exception as e:
            flash(str(e),"error")
            return render_template('export/exportaccts.html', form=thisform, title="Export to Accts System")

@bp.route('/exportacctsmsgs/<pstart>/<pend>/<pheader>/<pexport_dates>', methods=['GET', 'POST'])
@login_required
def exportacctsmsgs(pstart,pend,pheader,pexport_dates):
    # Parameters are string so convert as necessary
    start = datetime.datetime.strptime(pstart,"%Y-%m-%d").date()
    end = datetime.datetime.strptime(pend,"%Y-%m-%d").date()
    header = False
    if pheader == 'True':
        header = True
    export_dates = False
    if pexport_dates == 'True':
        export_dates = True
    if request.method == 'GET':
        if export_dates:
            sql = sqltext("""
                    SELECT id,flt_date 
                    FROM flights
                    where flt_date >= :startdate
                    and flt_date <= :enddate 
                    and linetype = 'FL'
                    and accts_export_date is null
                  """)
        else:
            sql = sqltext("""
                    SELECT id,flt_date  
                    FROM flights
                    where flt_date >= :startdate
                    and flt_date <= :enddate 
                    and linetype = 'FL'
                  """)
        flights = db.engine.execute(sql, startdate=start, enddate=end).fetchall()
        # if len(flights) == 0:
        #     flash("There are no flights to export in this range","warning")
        #     return render_template('export/exportacctsmsgs.html',  title="Export to Accts System")
        # else:
        #     flash("There are {} flights to export in this range".format(len(flights)), "warning")
        # Now get the file.
        rtndict = getacctsexport(flights, export_dates, header)
        session['EXPORTFILE'] = rtndict['filename']
        # for any messages add other field elements to make it easy to see the problem on the screen
        for m in rtndict['msgs']:
            f = Flight.query.get(m['flt'])
            m['flt_date'] = f.flt_date
            m['ac_regn'] = f.ac_regn
            m['pic'] = f.pic
            m['p2'] = f.p2
            m['payer'] = f.p2
            m['tow_charge'] = f.tow_charge
            m['glider_charge'] = f.glider_charge
            m['general_note'] = f.general_note

        return render_template('export/exportacctsmsgs.html', title="Export to Accts System", messages=rtndict['msgs'],
                               filename=rtndict['filename'])
    # if request.method == 'POST':
    #     print('in post')
    #     print(request.form['matdownload'])
    #     if export_dates:
    #         sql = sqltext("""
    #                 SELECT id,flt_date
    #                 FROM flights
    #                 where flt_date >= :startdate
    #                 and flt_date <= :enddate
    #                 and linetype = 'FL'
    #                 and accts_export_date is null
    #               """)
    #     else:
    #         sql = sqltext("""
    #                 SELECT id,flt_date
    #                 FROM flights
    #                 where flt_date >= :startdate
    #                 and flt_date <= :enddate
    #                 and linetype = 'FL'
    #               """)
    #     flights = db.engine.execute(sql, startdate=start, enddate=end).fetchall()
    #     if len(flights) == 0:
    #         flash("There are no flights to export in this range","warning")
    #         return render_template('export/exportacctsmsgs.html',  title="Export to Accts System")
    #     else:
    #         flash("There are {} flights to export in this range".format(len(flights)), "warning")
    #     # Now get the file.
    #     rtndict = getacctsexport(flights, export_dates, header)
    #     request.send(getacctsexport(flights, export_dates, header),as_attachment=True)

@bp.route('/exportdownload', methods=['GET','POST'])
@login_required
def exportdownload():
    filename = session.get('EXPORTFILE',"file_missing")
    if not os.path.exists(filename):
        return 'Big Failure - the filename in the session cookie is missing {} - tell ray'.format(filename)
    else:
        return send_file(session['EXPORTFILE'], as_attachment=True)

def createfltsxlsx(flights):
    """
    Creates a spreadsheet ready for download for flights between two dates.
    :param self:
    :param flights:  List of flights to write
    :return: Name of excel file.
    """
    row = 0
    if len(flights) == 0:
        raise ValueError("No Flights in this range")
    try:
        filename = os.path.join(app.instance_path,
                                "downloads/FLTS_" + flights[0].flt_date.strftime("%Y-%m-%d") + ".xlsx")
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
        ws.write("C3", "PIC", border_fmt)
        ws.write("D3", "P2", border_fmt)
        ws.write("E3", "Glider Reg", border_fmt)
        ws.write("F3", "Tug Pilot", border_fmt)
        ws.write("G3", "Tug Regn", border_fmt)
        ws.write("H3", "Take Off", border_fmt)
        ws.write("I3", "Tug Down", border_fmt)
        ws.write("J3", "Glider Down", border_fmt)
        ws.write("K3", "Release", border_fmt)
        ws.write("L3", "Tug Time", border_fmt)
        ws.write("M3", "Tug Charge", border_fmt)
        ws.write("N3", "Glider Time", border_fmt)
        ws.write("O3", "Glider Charge", border_fmt)
        ws.write("P3", "Other Charge", border_fmt)
        ws.write("Q3", "Total", border_fmt)
        ws.write("R3", "Payment", border_fmt)
        ws.write("S3", "Payer", border_fmt)
        ws.write("T3", "Note", border_fmt)
        ws.write("U3", "Export Date", border_fmt)
        row = 3
        for f in flights:
            ws.write(row, 0, f.id, border_fmt)
            if f.linetype == 'FL':
                ws.write(row, 1, f.flt_date.strftime("%d/%m/%Y"), border_fmt)
                ws.write(row, 2, f.pic, border_fmt)
                ws.write(row, 3, f.p2, border_fmt )
                ws.write(row, 4, f.ac_regn, border_fmt )
                ws.write(row, 5, f.tow_pilot, border_fmt )
                ws.write(row, 6, f.tug_regn, border_fmt )
                ws.write(row, 7, f.takeoff, time_fmt )
                ws.write(row, 8, f.tug_down, time_fmt )
                ws.write(row, 9, f.landed, time_fmt )
                ws.write(row, 10, f.release_height, border_fmt )
                ws.write(row, 11, f.tow_mins(), border_fmt )
                ws.write(row, 12, f.tow_charge, border_fmt )
                ws.write(row, 13, f.glider_mins(), border_fmt )
                ws.write(row, 14, f.glider_charge, dollar_fmt )
                ws.write(row, 15, f.other_charge, dollar_fmt )
                ws.write(row, 16, f.tow_charge + f.glider_charge + f.other_charge, dollar_fmt )
                ws.write(row, 17, f.payment_note, border_fmt )
                ws.write(row, 18, f.payer, border_fmt )
                ws.write(row, 19, f.general_note, border_fmt )
                if f.accts_export_date is not None:
                    ws.write(row, 20, f.accts_export_date.strftime("%d/%m/%Y"), border_fmt )
            else:
                ws.write(row, 1, f.flt_date.strftime("%d/%m/%Y"), border_fmt)
                ws.write(row, 2, f.general_note)
            row += 1
        ws.write(row + 1, 1, "Totals:", border_fmt)
        ws.write_formula(row + 1, 11, "sum(L4:L" + str(row) + ")", border_fmt)
        ws.write_formula(row + 1, 12, "sum(M4:M" + str(row) + ")", dollar_fmt)
        ws.write_formula(row + 1, 13, "sum(N4:N" + str(row) + ")", border_fmt)
        ws.write_formula(row + 1, 14, "sum(O4:O" + str(row) + ")", dollar_fmt)
        ws.write_formula(row + 1, 15, "sum(P4:P" + str(row) + ")", dollar_fmt)
        ws.write_formula(row + 1, 16, "sum(Q4:Q" + str(row) + ")", dollar_fmt)
        # col widths
        for i,v in enumerate([3,12,20,20,10,20,12,9,9,9,9,9,12,9,12,12,12,20,20,40,15]):
            ws.set_column(i,i,v)
    except Exception as e:
        applog.error("An error ocurred during spreadsheet create:{}".format(str(e)))
        applog.debug("Row was:{}".format(row))
        raise
    workbook.close()
    return filename

def createsummsxlsx(summary):
    """
    Creates a spreadsheet ready for download for flights between two dates.
    :param self:
    :param summary:  Results of sql
    :return: Name of excel file.
    """
    row = 0
    try:
        filename = os.path.join(app.instance_path,
                                "downloads/Summ_" + summary[0].flt_date + ".xlsx")
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
        ws.write("A3", "Date", border_fmt)
        ws.write("B3", "Glider Reg", border_fmt)
        ws.write("C3", "Flight Count", border_fmt)
        ws.write("D3", "Total Mins", border_fmt)
        row = 3
        for s in summary:
            ws.write(row, 0, datetime.datetime.strptime(s.flt_date,"%Y-%m-%d").date().strftime("%d/%m/%Y"), border_fmt)
            ws.write(row, 1, s.ac_regn, border_fmt )
            ws.write(row, 2, s.fltcount, border_fmt )
            ws.write(row, 3, s.totalmins, border_fmt )
            row += 1
        # col widths
        for i,v in enumerate([12,9,9,9]):
            ws.set_column(i,i,v)
    except Exception as e:
        applog.error("An error ocurred during spreadsheet create:{}".format(str(e)))
        applog.debug("Row was:{}".format(row))
        raise
    workbook.close()
    return filename

def getacctsexport(fltlist,pexport_date,pheader):
    applog.info("Accounts export started")
    filename = os.path.join(app.instance_path,
                            "downloads/accts" + fltlist[0].flt_date + ".csv")
    with open(filename, 'w', newline=chr(10)) as csvf:
        other_club_member_slot = Slot.query.filter_by(slot_type='DEFAULT').filter_by(slot_key='OTHERCUSTOMER').first()
        if other_club_member_slot is None:
            raise ValueError("Other Club Member slot missing")
        if other_club_member_slot.slot_data is None:
            raise ValueError("Other Club Member valu is not set")
        fieldnames = ['id', 'date_opened', 'owner_id', 'billing_id', 'notes', 'date', 'desc', 'action',
                      'account', 'quantity', 'price', 'disc_type', 'disc_how', 'discount', 'taxable', 'taxincluded',
                      'tax_table', 'date_posted', 'due_date', 'account_posted', 'memo_posted', 'accu_splits']
        w = csv.DictWriter(csvf, fieldnames=fieldnames)
        rtndict = {}
        rtndict['filename'] = filename
        rtndict['msgs'] = []
        if pheader:
            w.writeheader()
        for f in fltlist:
            # get the flight
            oneflt = Flight.query.get(f.id)
            #check if the export date flag has been set
            if pexport_date:
                if oneflt.accts_export_date is not None:
                    continue
            # A flight may give rise to more than one line.
            rows_added = 0
            # check that tug only records have the correct fees
            if oneflt.ac_regn == constREGN_FOR_TUG_ONLY:
                if oneflt.payer is None:
                    rtndict['msgs'].append({'flt': f.id, 'type': 'Error', 'msg': 'Tug only but there is no payer'})
                if oneflt.tow_charge == 0:
                    rtndict['msgs'].append({'flt': f.id, 'type': 'Warning', 'msg': 'Tug only but there is no Charge'})
                if oneflt.glider_charge != 0:
                    rtndict['msgs'].append({'flt': f.id, 'type': 'Warning', 'msg': 'Tug only but there is a glider Charge'})
            if oneflt.aircraft_rec() is not None:
                if oneflt.aircraft_rec().default_launch != constTOW_FOR_SELF_LAUNCH:
                    if oneflt.payer is None:
                        rtndict['msgs'].append(
                            {'flt': f.id, 'type': 'Warning', 'msg': 'No Payer'})
                    if oneflt.tow_charge == 0:
                        rtndict['msgs'].append(
                            {'flt': f.id, 'type': 'Warning', 'msg': 'No Tow Charge'})
                if oneflt.payer_rec() is None:
                    if oneflt.aircraft_rec().rate_per_hour != 0 and oneflt.glider_charge == 0:
                        rtndict['msgs'].append(
                            {'flt': f.id, 'type': 'Warning', 'msg': 'No Glider Charge'})
                else:  #there is a payer record
                    if oneflt.aircraft_rec().rate_per_hour != 0 and oneflt.glider_charge == 0 and not oneflt.payer_rec().bscheme:
                        rtndict['msgs'].append(
                            {'flt': f.id, 'type': 'Warning', 'msg': 'No Glider Charge'})
            # Process Aerotow
            if oneflt.tow_charge is not None:
                if oneflt.tug_rec() is None:
                    rtndict['msgs'].append(
                        {'flt': f.id, 'type': 'Error', 'msg': 'No Tug Regn'})
                elif oneflt.ac_regn != constREGN_FOR_TUG_ONLY and oneflt.tug_rec().accts_income_tow is None:
                    rtndict['msgs'].append(
                        {'flt': f.id, 'type': 'Error', 'msg': 'Income Account missing for Tow'})
                elif oneflt.ac_regn == constREGN_FOR_TUG_ONLY and oneflt.tug_rec().accts_income_acct is None:
                    rtndict['msgs'].append(
                        {'flt': f.id, 'type': 'Error', 'msg': 'Income Account missing for Private Hire'})
                else:
                    if oneflt.tow_charge > 0:
                        thisrec = {}
                        if rows_added == 0:
                            thisrec['id'] = "FL-" + str(f.id).zfill(6)
                            thisrec['notes'] = 'Paid by {}'.format(oneflt.payment_note)
                            if oneflt.general_note is not None:
                                thisrec['notes'] = thisrec['notes'] + ' ' + oneflt.general_note.replace('\n',' ')
                                rtndict['msgs'].append(
                                    {'flt': f.id, 'type': 'Warning', 'msg': 'There is a general note'})
                        if oneflt.payer_rec() is None:
                            thisrec['owner_id'] = other_club_member_slot.slot_data
                            rtndict['msgs'].append(
                                {'flt': f.id, 'type': 'Warning', 'msg': 'Posting to Other Club Member'})
                        else:
                            thisrec['owner_id'] = oneflt.payer_rec().accts_cust_code
                        thisrec['desc']  = 'Aerotow'
                        thisrec['quantity'] = 1
                        thisrec['price'] = oneflt.tow_charge
                        thisrec['taxable'] = 'X'
                        thisrec['date'] = oneflt.flt_date.strftime("%d/%m/%y")
                        thisrec['taxincluded'] = 'X'
                        if oneflt.ac_regn == constREGN_FOR_TUG_ONLY:
                            thisrec['account'] = oneflt.tug_rec().accts_income_acct
                        else:
                            thisrec['account'] = oneflt.tug_rec().accts_income_tow
                        w.writerow(thisrec)
                        rows_added += 1
            if oneflt.glider_charge > 0:
                if oneflt.aircraft_rec() is None:
                    rtndict['msgs'].append(
                        {'flt': f.id, 'type': 'Error', 'msg': 'No Glider Regn'})
                elif oneflt.aircraft_rec().accts_income_acct is None:
                    rtndict['msgs'].append(
                        {'flt': f.id, 'type': 'Error', 'msg': 'There is a glider charge but no income account defined'})
                else:
                    thisrec = {}
                    if rows_added == 0:
                        thisrec['id'] = "FL-" + str(f.id).zfill(6)
                        thisrec['notes'] = 'Paid by {}'.format(oneflt.payment_note)
                        if oneflt.general_note is not None:
                            thisrec['notes'] = thisrec['notes'] + ' ' + oneflt.general_note.replace('\n', ' ')
                            rtndict['msgs'].append(
                                {'flt': f.id, 'type': 'Warning',
                                 'msg': 'There is a general note on the flight'})
                    if oneflt.payer_rec() is None:
                        thisrec['owner_id'] = other_club_member_slot.slot_data
                        rtndict['msgs'].append(
                            {'flt': f.id, 'type': 'Warning', 'msg': 'Posting to Other Club Member'})
                    else:
                        thisrec['owner_id'] = oneflt.payer_rec().accts_cust_code
                    thisrec['desc'] = 'Aerotow'
                    thisrec['quantity'] = 1
                    thisrec['price'] = oneflt.glider_charge
                    thisrec['taxable'] = 'X'
                    thisrec['date'] = oneflt.flt_date.strftime("%d/%m/%y")
                    thisrec['taxincluded'] = 'X'
                    thisrec['account'] = oneflt.aircraft_rec().accts_income_acct
                    w.writerow(thisrec)
            if pexport_date:
                oneflt.accts_export_date = datetime.date.today()
                db.session.commit()
        if pexport_date:
            applog.info("{} Flights exported with export date option".format(len(fltlist)))
        else:
            applog.info("{} Flights exported without export date option".format(len(fltlist)))
        return rtndict



