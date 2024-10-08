#
# This files ccontains a few functions that I want available to everyone so they are
# unsecured.
#
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Flask, send_from_directory, current_app, send_file
)
#import datetime
import xlsxwriter
#from dateutil.relativedelta import *
from werkzeug.exceptions import abort

from flask_login import login_required, current_user
from asc import db,create_app
from asc.schema import *
from sqlalchemy import text as sqltext
#from sqlalchemy import or_, and_
import os
# WTforms
#from flask_wtf import FlaskForm
#from wtforms import Form, StringField, PasswordField, validators, SubmitField, SelectField, BooleanField, RadioField, \
#    TextAreaField
#from wtforms.fields import EmailField, IntegerField, DateField
#from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length

#from asc.wtforms_ext import MatButtonField, TextButtonField
#from asc.role_decorators import *

# direct from the db defintion
from flask_wtf import Form
import email_validator
import email_validator
##from wtforms.ext.sqlalchemy.orm import model_form

# app = Flask(__name__)
# app = create_app()
app = current_app
applog = app.logger
from asc.common import *
from asc.oMetservice import MetService
from asc.ochart import Chart

from flask_wtf import FlaskForm
from wtforms import  SelectField


bp = Blueprint('misc', __name__, url_prefix='/misc')

class MetChartForm(FlaskForm):
    measure = SelectField('Measure', description='Measure', render_kw={"onchange": 'this.form.submit()'})

@bp.route('/contactlist', methods=['GET', 'POST'])
@login_required
def contactlist():
    if request.method == 'GET':
        list = Pilot.query.filter(Pilot.member).filter(Pilot.active).order_by(Pilot.surname)
        return render_template('misc/contactlist.html', list=list)

@bp.route('/instrcontactlist', methods=['GET', 'POST'])
@login_required
def instrcontactlist():
    if request.method == 'GET':
        list = Pilot.query.filter(Pilot.member).filter(Pilot.active).order_by(Pilot.surname)
        return render_template('misc/instrcontactlist.html', list=list)

@bp.route('/currencydtl/<id>', methods=['GET', 'POST'])
@login_required
def currencydtl(id):
    if request.method == 'GET':
        thispilot = db.session.get(Pilot,id)
        if thispilot is None:
            flash('Could not access Pilot currency')
            return render_template('misc/instrcontactlist.html', list=list)
        if not current_user.is_member_of('INSTRUCTOR') and current_user.id != thispilot.user_id:
            flash('You can only access your own details')
            return render_template('index.html')
        currency = currency_dict(id)
        sql = sqltext('''
        select flt_date, ac_regn, pic, p2,
                    round(((julianday(t0.landed) - julianday(t0.takeoff)) * 1440),0) mins
            from flights t0
            where linetype = 'FL'
            and ac_regn <> 'TUG ONLY'
            and (p2=:name or pic=:name)
            order by flt_date desc
            limit 10
        ''')
        sql = sql.columns(flt_date=db.Date)
        last20 = db.engine.execute(sql, name = thispilot.fullname).fetchall()
        # below is for barometer
        return render_template('misc/currencydtl.html', list=currency, pilot=thispilot, last20=last20, today=datetime.date.today() )


@bp.route('/barometer/<pilot_id>', methods=['GET', 'POST'])
@bp.route('/barometer', methods=['GET', 'POST'])
@login_required
def barometer(pilot_id=None):
    if pilot_id is None:
        pilot_id = current_user.pilot_id
    if current_user.pilot_id is None:
        flash('Your userid is not associated with a pilot.  Ask the sysadmin',"error")
        return render_template('index.html')
    if current_user.pilot_id != pilot_id and not current_user.is_member_of('INSTRUCTOR'):
        flash('You can only view your own barometer',"error")
        return render_template('index.html')
    #
    if request.method == 'GET':
        thispilot = db.session.get(Pilot,pilot_id)
        if thispilot is None:
            flash('Could not access Pilot currency')
            return render_template('misc/instrcontactlist.html', list=list)
        currency = currency_dict(pilot_id)
        # below is for barometer
        msg = None
        gliderflights = [x for x in currency if x['summary_type'] == 'Glider Flights']
        if len(gliderflights) > 0:
            last12_launches = gliderflights[0]['last12_launches']
            last12_hrs = gliderflights[0]['last12_hrs']
        else:
            last12_launches = 0
            last12_hrs = 0
        # make them percentages.....
        if last12_hrs > 32:
            if thispilot.currency_barometer < 100:
                msg = 'Hours are off scale (' + str(last12_hrs) + ')'
            last12_hrs = 1
        elif last12_hrs <= 0:
            last12_hrs = 0
        else:
            last12_hrs /= 32
        if last12_launches > 41:
            if thispilot.currency_barometer < 100:
                if msg is None:
                    msg = 'Launches are off scale (' + str(last12_launches) + ')'
                else:
                    msg += 'Launches are off scale (' + str(last12_launches) + ')'
            last12_launches = 1
        elif last12_launches <= 0:
            last12_launches = 0
        else:
            last12_launches /= 41
        # but the graph is "upside down...." so subtract from 1
        last12_hrs = 1 - last12_hrs
        last12_launches =  1 - last12_launches
        return render_template('misc/barometer.html', pilot=thispilot, last12_launches=last12_launches, last12_hrs=last12_hrs,msg=msg )

@bp.route('/metforecast', methods=['GET', 'POST'])
@login_required
def metforecast():
    wxfile = os.path.join(app.instance_path,'wx.json')
    thiswx = MetService()
    try:
        if os.path.isfile(wxfile):
            thiswx.get_current_file(wxfile)
        else:
            thiswx.get_current(174.6131, -36.7928, savefilename=wxfile, reading_count=12)  # Whenuapai
    except Exception as e:
        flash(str(e))
        return render_template('index.html')
    thischart = Chart('Met Service Forecast')
    thisform = MetChartForm()
    # get the first forecast time
    determinationdate = thiswx.ForecastTimeLocal[0]
    thisform.measure.choices = [thiswx.human_name(m) for m in thiswx.CurrentValues.keys()]
    # if request.method == 'GET':
    #     print("first in {}".format(thisform.measure.data))
    #     for i,v in enumerate(thiswx.qnh):
    #         thischart.AddDataPoint('QNH',i,v)
    #         thischart.SetCategoryValue(i,thiswx.ForecastTimeLocal[i].strftime('%d %H:%M'))
    # if request.method == 'POST':
    #     print(thisform.measure.data)
    #     for i,v in enumerate(thiswx.CurrentValues[thisform.measure.data]):
    #         thischart.AddDataPoint(thisform.measure.data,i,v)
    #         thischart.SetCategoryValue(i,thiswx.ForecastTimeLocal[i].strftime('%d %H:%M'))
    # build chart for selected measure
    if thisform.measure.data is None:
        # use the first one:
        selected_measure = next(iter(thiswx.CurrentValues.keys()))
    else:
        selected_measure = thiswx.api_name(thisform.measure.data)
    print(selected_measure)
    thischart.SetAxisLabel("y",thiswx.uom(selected_measure))
    thischart.SetAxisLabel("x","Time")
    #thischart.SetAxisTickRotate("x",270)
    thischart.SetAxisTickCulling("x",True)
    thischart.SetSeriesShowDataPoint("data",False)
    thischart.HideLegend=True
    for i, v in enumerate(thiswx.CurrentValues[selected_measure]):
        thischart.AddDataPoint("data", i, v)
        thischart.SetCategoryValue(i, thiswx.ForecastTimeLocal[i].strftime('%H:00'))
    thischart.SetSeriesChartType("data","spline")
    return render_template('misc/metforecast.html', form=thisform, chart0data=thischart.ChartJson)

@bp.route('/conctactspreadsheet>', methods=['GET', 'POST'])
@login_required
def contactspreadsheet():
    return send_file(createmshipxlsx(),
                     as_attachment=True)


def createmshipxlsx():
    """
    Creates a spreadsheet ready for download for flights between two dates.
    :param self:
    :param flights:  List of flights to write
    :return: Name of excel file.
    """
    # setup workbook:
    filename = os.path.join(app.instance_path,
                            "downloads/Members" + ".xlsx")
    workbook = xlsxwriter.Workbook(filename)
    borderdict = {'border': 1}
    noborderdict = {'border': 0}
    datedict = {'num_format': 'dd-mmm-yy'}
    timedict = {'num_format': 'h:mm'}
    dollardict = {'num_format': '$#, ##0.00'}
    title_merge_format = workbook.add_format(
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
    sub_heading_merge_format = workbook.add_format(
        {
            "bold": 1,
            "border": 1,
            "align": "center",
            "valign": "vcenter",
        }
    )
    col_head_fmt = workbook.add_format({'border': 1, 'text_wrap': 1,
                                        'bold': 1})
    border_fmt = workbook.add_format({'border': 1, 'text_wrap': 1})
    # title_merge_format = workbook.add_format({'align': 'center', 'border': 1})
    date_fmt = workbook.add_format(dict(datedict, **borderdict))
    dollar_fmt = workbook.add_format(dict(dollardict, **borderdict))
    time_fmt = workbook.add_format(dict(timedict, **borderdict))
    hrsmins_fmt = workbook.add_format({'num_format': '[h]:mm'})
    #
    #  Add the members Sheet
    #
    ssdata = Pilot.query.filter(Pilot.member).filter(Pilot.active).order_by(Pilot.surname).all()
    if len(ssdata) == 0:
        return
    ws = workbook.add_worksheet("Members")
    try:
        row = 2
        ws.write(row, 0, "Surname", col_head_fmt)
        ws.write(row, 1, "First Name", col_head_fmt)
        ws.write(row, 2, "Rank", col_head_fmt)
        ws.write(row, 3, "Note", col_head_fmt)
        ws.write(row, 4, "Address", col_head_fmt)
        ws.write(row, 6, "Email", col_head_fmt)
        ws.write(row, 7, "Home", col_head_fmt)
        ws.write(row, 8, "Mobile", col_head_fmt)
        ws.write(row, 9, "Class", col_head_fmt)
        ws.merge_range("E3:F3", "Address",col_head_fmt)
        row += 1
        for m in ssdata:
            ws.write(row, 0, m.surname, border_fmt)
            ws.write(row, 1, m.firstname, border_fmt)
            ws.write(row, 2, m.rank, border_fmt)
            ws.write(row, 3, m.note, border_fmt)
            ws.write(row, 4, m.address_1, border_fmt)
            ws.write(row, 5, m.address_2, border_fmt)
            ws.write(row, 6, m.email, border_fmt)
            ws.write(row, 7, m.phone, border_fmt)
            ws.write(row, 8, m.mobile, border_fmt)
            ws.write(row, 9, m.type, border_fmt)
            row += 1
        # col widths
        ws.autofit()
        # autfit overrides
        # ws.set_column(0, 0, 12)
        col = 1
        # Put in the title last so that the autofit works nicely
        ws.merge_range("A1:J1", "ASC Membership " + datetime.date.today().strftime("%d-%m-%Y"), title_merge_format)
    except Exception as e:
        applog.error("An error ocurred during spreadsheet create:{}".format(str(e)))
        applog.debug("Row was:{}".format(row))
        raise
    workbook.close()
    return filename

