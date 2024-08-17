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

bp = Blueprint('misc', __name__, url_prefix='/misc')


@bp.route('/contactlist', methods=['GET', 'POST'])
@login_required
def contactlist():
    if request.method == 'GET':
        list = Member.query.filter(Member.active).order_by(Member.surname)
        return render_template('misc/contactlist.html', list=list)

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
    ssdata = Member.query.filter(Member.active).order_by(Member.surname).all()
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
            ws.write(row, 6, m.email_address, border_fmt)
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

