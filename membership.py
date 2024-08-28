from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Flask, send_from_directory, current_app, send_file
)
import datetime
import xlsxwriter
from dateutil.relativedelta import *
from werkzeug.exceptions import abort

from flask_login import login_required, current_user
from asc import db,create_app
from asc.schema import Pilot,  Slot, MemberTrans
from sqlalchemy import text as sqltext
from sqlalchemy import or_, and_
import os
# WTforms
from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, validators, SubmitField, SelectField, BooleanField, RadioField, \
    TextAreaField
from wtforms.fields import EmailField, IntegerField, DateField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length

from asc.wtforms_ext import MatButtonField, TextButtonField

# direct from the db defintion
from flask_wtf import Form
import email_validator
import email_validator
##from wtforms.ext.sqlalchemy.orm import model_form

from asc.oPerson import *

# app = Flask(__name__)
# app = create_app()
app = current_app
applog = app.logger

bp = Blueprint('membership', __name__, url_prefix='/membership')


class PilotForm(FlaskForm):
    id = IntegerField('ID', description='Primary Key')
    active = BooleanField('Active', description="Active members appear on the membership list")
    gnz_no = IntegerField('NZGA No', description='Add the members GNZ no when known.')
    type = RadioField('Member Type', render_kw={'title': 'Select the correct Membership Type'})
    fullname = StringField('Fullname', [validators.DataRequired(message='You cannot have a blank name')],
                          description="Members Name", render_kw={'autocomplete': 'dont','size':'50'})
    #
    # surname = StringField('Surname', [validators.DataRequired(message='You cannot have a blank Surname')],
    #                       description="Members Surname", render_kw={'autocomplete': 'dont'})
    # firstname = StringField('Firstname', [validators.DataRequired(message='You cannot have a blank Firstname')],
    #                         description="Members Firstname", render_kw={'autocomplete': 'dont'})
    rank = SelectField('Rank',
                       description="Select Suitable Rank")  # note that the choices are defined when the form is loaded with:
    # thisform.rank.choices = [(r.slot_key, r.slot_desc) for r in Slot.query.filter_by(slot_type = 'RANK')]
    note = TextAreaField('Note', render_kw={'rows': 2, 'cols': 50})
    email = EmailField('Email Addr', [Email(message='Invalid email address')], description="Email Address",
                               render_kw={'size': '50', 'autocomplete': 'dont'})
    dob = DateField('Date of Birth')
    phone = StringField('Phone', render_kw={'autocomplete': 'dont'})
    mobile = StringField('Mobile', render_kw={'autocomplete': 'dont'})
    address_1 = StringField('Address 1', render_kw={'autocomplete': 'dont'})
    address_2 = StringField('Address 2')
    address_3 = StringField('Address 3')
    service = BooleanField('Service', description='Tick if a current service member')
    roster = SelectField('Roster', description='Which rosters?', choices=[('I', 'Instructor'),
                                                                          ('T', 'TowPilot'),
                                                                          ('IT', 'Both Instructor and Tow Pilot'),
                                                                          ('N', 'No Roster'),
                                                                          ('D', 'Duty Pilot')]
                         )
    email_2 = StringField('Email 2', description="Add any send email address",
                          render_kw={'size': '50', 'autocomplete': 'dont'})
    phone2 = StringField('Phone 2', description="Any second phone number", render_kw={'autocomplete': 'dont'})
    mobile2 = StringField('Mobile 2', description="Add any second emobile number", render_kw={'autocomplete': 'dont'})
    committee = BooleanField('Committee Member', render_kw={'class': 'intable'})
    instructor = BooleanField('Instructor', render_kw={'class': 'intable'})
    tow_pilot = BooleanField('Tow Pilot', render_kw={'class': 'intable'})
    oo = BooleanField('OO', render_kw={'class': 'intable'})
    duty_pilot = BooleanField('Duty Pilot', render_kw={'class': 'intable'})
    nok_name = StringField('Next of Kin')
    nok_rship = StringField('Relationship', render_kw={'list': "nok_rship_datalist"})
    nok_phone = StringField('NOK Phone', description='Next of Kin Phone number')
    nok_mobile = StringField('NOK Mobile', description='Next of kin Mobile Number')
    # glider = StringField('Glider', description='Registration of privately owned glider')
    # email_bfr_med = BooleanField('Email BFR and Med Warnings', description='Auto email when BFR''s and Emails are soon to expire')
    email_bfr_warning = BooleanField('BFR', description='Auto email when BFR''s  soon to expire', render_kw={'class': 'intable'})
    email_med_warning = BooleanField('Med', description='Auto email when Medicals are soon to expire', render_kw={'class': 'intable'})
    email_mbrfrm_warning = BooleanField('Membership Form', description='Auto email when BFR''s and Emails are soon to expire', render_kw={'class': 'intable'})
    user_id = SelectField('User key',description = "Key to the User Table")
    # transactions = relationship("MemberTrans", backref='memberid')

    btnsubmit = MatButtonField('done', id='matdonebtn', icon='done', help="Confirm all Changes")
    cancel = MatButtonField('cancel', id='matcancelbtn', icon='cancel',
                            help="Press to exit and make no changes")  # , render_kw={'formnovalidate':''})
    print = MatButtonField('print', id='printbtn', icon='print', help='Press to print report')
    trans = TextButtonField('Transactions', id="transbtn", text='Transactions', help="View transactions for members")
    delete = MatButtonField('delete', id='matdeletebtn', icon='delete', help='Press to delete this record',
                            render_kw={'onclick': 'return ConfirmDelete()'})
    cancel = SubmitField('cancel', id='cancelbtn')
    delete = SubmitField('delete', id='deletebtn', render_kw={"OnClick": "ConfirmDelete()"})

    # I don't believe it matters if the email address is used more than once.
    # This may well occur if we have two juniors from the same family and they both use a parents email addres.

    # def validate_email_address(self, email_address):
    #     """Email validation."""
    #     if len(email_address.data) > 0:
    #         sqlstmt = sqltext("""SELECT id
    #                         FROM pilots
    #                          where (email = :email and id != :thisid )
    #                          or (email_2 = :email and id != :thisid )""")
    #         cnt = db.engine.execute(sqlstmt, thisid=self.id.data, email=email_address.data).fetchall()
    #         if len(cnt) > 0:
    #             raise ValidationError("Email address already in use")
    #
    #
    #
    # def validate_email_2(self, email_2):
    #     """Email validation."""
    #     if len(email_2.data) > 0:
    #         sqlstmt = sqltext("""SELECT id
    #                         FROM members
    #                          where (email_address = :email and id != :thisid )
    #                          or (email_2 = :email and id != :thisid )""")
    #         cnt = db.engine.execute(sqlstmt, thisid=self.id.data, email=email_2.data).fetchall()
    #         if len(cnt) > 0:
    #             raise ValidationError("Email address already in use")


class TransactionForm(FlaskForm):
    id = IntegerField('ID', description='Primary Key')
    memberid = IntegerField('Member', description='The id of the related member field')
    transdate = DateField('Transaction Date', description='The date of the transaction')
    transtype = SelectField('Transaction Type', description='The type of transaction - from slots')
    transsubtype = SelectField('Sub Type', description='Subtype of Transaction (such as rating)')
    transnotes = TextAreaField('Notes', description='Any related Notes', render_kw={'rows': 5, 'cols': 50})

    btnsubmit = MatButtonField('done', id='matdonebtn', icon='done', help="Confirm all Changes")
    cancel = MatButtonField('cancel', id='matcancelbtn', icon='cancel',
                            help="Press to exit and make no changes")  # , render_kw={'formnovalidate':''})
    delete = MatButtonField('delete', id='matdeletebtn', icon='delete',
                            help='Press to delete this record', render_kw={'onclick':'return ConfirmDelete()'})


@bp.route('/memberlist/', defaults={'active':'ACTIVE'}, methods=['GET', 'POST'])
@bp.route('/memberlist/<active>', methods=['GET', 'POST'])
@login_required
def memberlist(active='ACTIVE'):
    if request.method == 'GET':
        if active=='ACTIVE':
            list = Pilot.query.filter(Pilot.member).filter(Pilot.active).order_by(Pilot.fullname)
        else:
            list = Pilot.query.filter(Pilot.member).order_by(Pilot.fullname)
        return render_template('membership/memberlist.html', list=list, active=active, today=datetime.date.today(),
                               twomonths=datetime.date.today() - relativedelta(months=-2))


@bp.route('/membermaint/<id>', methods=['GET', 'POST'])
@login_required
def membermaint(id):
    thismem = Pilot.query.get(id)
    # if thismem is None then we will be adding
    if thismem is None:
        thismem = Pilot()
        thismem.member = True
        thismem.active = True
        thismem.type = 'FLYING'
        thismem.email_mbrfrm_warning = True
        thismem.email_bfr_warning = True
        thismem.email_med_warning = True
        thismem.gnz_no = 0
    if not thismem.rank:
        thismem.rank = 'CIV'
    thisform = PilotForm(obj=thismem, name='Member Maintenance')
    thisform.user_id.choices = [(None, 'No User')]
    thisform.user_id.choices.extend([(u.id, u.fullname) for u in User.query.order_by(User.fullname).all()])
    # check the cancel button before anything else.
    # This will avoid all validations.
    if thisform.cancel.data:
        return redirect(url_for('membership.memberlist'))
    if thisform.trans.data:
        return redirect(url_for('membership.translist', id=id))
    thisform.rank.choices = [(r.slot_key, r.slot_desc) for r in Slot.query.filter_by(slot_type='RANK')]
    thisform.type.choices = [(r.slot_key, r.slot_desc) for r in Slot.query.filter_by(slot_type='MEMBERTYPE')]
    nok_relationships = ['Father', 'Mother', 'Wife', 'Partner', 'Son', 'Daughter']
    # this is the line that does the work
    if thisform.validate_on_submit():
        if thisform.print.data:
            flash('The print button was pressed')
        # Provided the field names are the same, this function updates all the fields
        # on the table.  If there are any that are different then each field needs to be
        # assigned manually.
        thisform.populate_obj(thismem)
        if thisform.delete.data:
            # Note that there is a cascading delete to remove trans
            db.session.delete(thismem)
        else:
            if thismem.id is None:
                db.session.add(thismem)
            names = thismem.fullname.split(' ')
            if len(names) == 0:
                flash("You must provide and name.", "error")
                return render_template('mastmaint/pilotmaint.html', form=thisform, usernames=usernames)
            thismem.firstname = names[0]
            thismem.surname = names[-1]
            thismem.member = True  # if maintaining via this screen then it is definitely a member.
            if thismem.id is None:
                db.session.add(thismem)
            if thismem.user_tbl:
                thismem.user_tbl.email = thismem.email
                thismem.user_tbl.gnz_no = thismem.gnz_no
                thismem.user_tbl.pilot_id = thismem.id
        user = db.session.get(User,thismem.user_id)
        if user is not None:
            user.email = thismem.email
        db.session.commit()
        # sync = PersonSync(thismem)
        return redirect(url_for('membership.memberlist'))
    return render_template('membership/membermaint.html', form=thisform, nokrs=nok_relationships)


@bp.route('/translist/<id>', methods=['GET', 'POST'])
@login_required
def translist(id):
    if request.method == 'GET':
        # thismember = Pilot.query.get(id)
        thismember = db.session.get(Pilot,id)
        sqlstmt = sqltext("""SELECT
            t0.id,
            t0.memberid,
            t0.transdate,
            t0.transtype,
            coalesce(t1.slot_desc, '') typedesc,
            t0.transsubtype,
            coalesce(t2.slot_desc, '') subtypedesc,
            t0.transnotes
            FROM membertrans AS t0 
            LEFT JOIN slots AS t1 
                ON t1.slot_type = 'TRANSTYPE'  AND t1.slot_key = t0.transtype 
            LEFT JOIN slots AS t2 
                ON t2.slot_type = t1.slot_desc  AND t2.slot_key = t0.transsubtype 
            WHERE t0.memberid = :member
            order by t0.transdate desc
        """)
        sqlstmt = sqlstmt.columns(transdate=db.Date)
        list = db.engine.execute(sqlstmt, member=id)
        # list = MemberTrans.query.filter_by(memberid=id).order_by(MemberTrans.transdate)
        return render_template('membership/translist.html', list=list, member=thismember)


@bp.route('/transmaint/<id>/<member>', methods=['GET', 'POST'])
@login_required
def transmaint(id, member=None):
    # thisrec = MemberTrans.query.get(id)
    thisrec = db.session.query(MemberTrans).get(id)
    # if thismem is None then we will be adding
    if thisrec is None:
        thisrec = MemberTrans(member)
    thisform = TransactionForm(obj=thisrec)
    if thisform.cancel.data:
        return redirect(url_for('membership.translist',id=member))
    thisform.transtype.choices = [(r.slot_key, r.slot_desc) for r in Slot.query.filter_by(slot_type='TRANSTYPE')]
    thisform.transsubtype.choices = [(r.slot_key, r.slot_desc) for r in Slot.query.filter_by(slot_type='RATING')]
    thisform.transsubtype.choices.append(('', 'N/A'))
    # this is the line that does the work
    # if request.method == 'POST' and thisform.validate():
    if thisform.validate_on_submit():
        # Provided the field names are the same, this function updates all the fields
        # on the table.  If there are any that are different then each field needs to be
        # assigned manually.
        thisform.populate_obj(thisrec)
        if thisrec.id is None:
            thisrec.memberid = member
            db.session.add(thisrec)
        if thisform.delete.data:
            db.session.delete(thisrec)
        db.session.commit()
        return redirect(url_for('membership.translist',id=member))
    return render_template('membership/transmaint.html', form=thisform)

@bp.route('/spreadsheet>', methods=['GET', 'POST'])
@login_required
def spreadsheet():
    return send_file(createmshipxlsx(True,True,True),
                     as_attachment=True)


def createmshipxlsx(include_currency=False,include_incident=False, include_nok=False):
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
    ssdata = Pilot.query.filter(Pilot.active).order_by(Pilot.surname).all()
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
        # for i in range(len(installed_meters)):
        #     ws.set_column(col, col, 12)
        #     ws.set_column(col + 1, col + 1, 12)
        #     col += 2
        # Put in the title last so that the autofit works nicely
        ws.merge_range("A1:J1", "ASC Membership " + datetime.date.today().strftime("%d-%m-%Y"), title_merge_format)
    except Exception as e:
        applog.error("An error ocurred during spreadsheet create:{}".format(str(e)))
        applog.debug("Row was:{}".format(row))
        raise
    #
    #  Currency Spreadsheet
    #
    if include_currency:
        ws = workbook.add_worksheet("Currency")
        try:
            row = 2
            ws.write(row, 0, "Name", col_head_fmt)
            ws.write(row,1, "Last Medical", col_head_fmt)
            ws.write(row,2, "DOB", col_head_fmt)
            ws.write(row,3, "Age", col_head_fmt)
            ws.write(row,4, "Medical Due", col_head_fmt)
            ws.write(row,5, "BFR/ICR Due", col_head_fmt)
            ws.write(row,6, "Ratings", col_head_fmt)
            ws.write(row, 7, "Last Mem Form", col_head_fmt)
            ws.write(row,8, "Currency", col_head_fmt)
            ws.write(row,9, "Hrs 12 Mths", col_head_fmt)
            row += 1
            for m in ssdata:
                ws.write(row, 0, m.fullname, border_fmt)
                ws.write(row, 1, m.last_medical, date_fmt)
                ws.write(row, 2, m.dob, date_fmt)
                ws.write(row, 3, m.age, border_fmt)
                ws.write(row, 4, m.medical_due, date_fmt)
                # this_fmt = date_fmt
                # this_fmt.set_bg_color('White')
                # if m.bfr_due is not None and m.bfr_due <= datetime.date.today():
                #     this_fmt.set_bg_color('red')
                #     this_fmt.set_fg_color('white')
                # if m.bfr_due is None:
                #     ws.write(row,5,datetime.date(2022,3,2))
                # else:
                ws.write(row, 5, m.bfr_due, date_fmt)
                ws.write(row, 6, m.ratings_string, border_fmt)
                ws.write(row, 7, m.last_mem_form, date_fmt)
                currency_string = ''
                if m.currency_dict['last90flts'] != 0:
                    currency_string += str(m.currency_dict['last90flts'])
                    currency_string += "/"
                    currency_string += str(round(m.currency_dict['last90mins'] / 60,1))
                    currency_string += " : "
                currency_string += str(m.currency_dict['last12flts'])
                currency_string += "/"
                currency_string += str(round(m.currency_dict['last12mins'] / 60,1))
                ws.write(row, 8, currency_string, border_fmt)
                ws.write(row,9,round(m.currency_dict['last12mins'] / 60,1), border_fmt)
                row += 1
            ws.autofit()
            ws.merge_range("A1:J1", "ASC Curency " + datetime.date.today().strftime("%d-%m-%Y"), title_merge_format)
            theseicons = []
            # In order to use conditional formatting, the formatting values require the julian number of dates
            # not a python object.  I'm not quite sure why I needed to add two days, but I checked the values
            # in excel with what I could get in python and this is the numbers I needed.
            green = ((datetime.date.today() + relativedelta(days=90)) - datetime.date(1900,1,1)).days + 2
            orange = ((datetime.date.today() + relativedelta(days=1)) - datetime.date(1900,1,1,)).days + 2
            theseicons.append({'criteria': '>=', 'type':'number', 'value': green})
            theseicons.append({'criteria': '<', 'type':'number', 'value': orange})
            ws.conditional_format(
                'A1:D1',
                {'type': 'icon_set',
                 'icon_style': '4_red_to_black',
                 'icons': [{'criteria': '>=', 'type': 'number', 'value': 90},
                           {'criteria': '<', 'type': 'percentile', 'value': 50},
                           {'criteria': '<=', 'type': 'percent', 'value': 25}]}
            )
            ws.conditional_format(3,4,row -1,5,
                                  {'type':'icon_set',
                                            'icon_style': '3_traffic_lights',
                                            'icons':theseicons
                                            })
            start = datetime.date(datetime.date.today().year,10,1)
            if datetime.date.today().month < 10:
                start -= relativedelta(years=1)
            red_date = workbook.add_format({'num_format':'dd-mmm-yy',
                                           'font_color': 'red',
                                           'border':1})
            ws.conditional_format(3,7,row - 1,7,
                                  {'type':'date',
                                            'criteria': 'less than',
                                            'value': start - relativedelta(months=1),
                                            'format':red_date
                                   }
                                  )
        except Exception as e:
            applog.error("An error ocurred during currency spreadsheet create:{}".format(str(e)))
            applog.debug("Row was:{}".format(row))
            raise
        #
        # Incidents
        #
        if include_incident:
            ws = workbook.add_worksheet("Incidents")
            try:
                sql = sqltext("""
                    select 
                    t1.surname,
                    t1.firstname,
                    t0.transdate,
                    t0.transnotes
                    from membertrans t0
                    join pilots t1 on t0.memberid = t1.id 
                    where t0.transtype = 'IR'
                    and t0.transdate >= :startdate
                    order by t0.transdate
                 """)
                sql = sql.columns(transdate=db.Date)
                incidents = db.engine.execute(sql, startdate=datetime.date.today() - relativedelta(months=12)).fetchall()
                row = 2
                ws.write(row, 0, "Name", col_head_fmt)
                ws.write(row,1, "Date", col_head_fmt)
                ws.write(row,2, "Notes", col_head_fmt)
                row += 1
                for ir in incidents:
                    ws.write(row, 0, ir.firstname + ' ' + ir.surname, border_fmt)
                    ws.write(row, 1, ir.transdate , date_fmt)
                    ws.write(row, 2, ir.transnotes , border_fmt)
                    row += 1
                ws.autofit()
                ws.merge_range("A1:C1", "12 Month Incident Summary " + datetime.date.today().strftime("%d-%m-%Y"), title_merge_format)

            except Exception as e:
                applog.error("An error ocurred during currency spreadsheet create:{}".format(str(e)))
                applog.debug("Row was:{}".format(row))
                raise
    #
    #  NOK Spreadsheet
    #
    if include_currency:
        ws = workbook.add_worksheet("NoK")
        try:
            ssdata = Pilot.query.filter(Pilot.active).order_by(Pilot.surname).all()
            row = 2
            ws.write(row, 0, "Name", col_head_fmt)
            ws.write(row,1, "Address", col_head_fmt)
            ws.write(row,2, "Nok Name", col_head_fmt)
            ws.write(row,3, "Nok R/Ship", col_head_fmt)
            ws.write(row,4, "Nok Contact", col_head_fmt)
            row += 1
            for m in ssdata:
                ws.write(row, 0, m.fullname, border_fmt)
                ws.write(row, 1, m.address_1 +',' + m.address_2, date_fmt)
                ws.write(row, 2, m.nok_name, border_fmt)
                ws.write(row, 3, m.nok_rship, border_fmt)
                if m.nok_phone is None or len(m.nok_phone) < 2:
                    ws.write(row, 4, m.nok_mobile, border_fmt)
                else:
                    ws.write(row, 4, m.nok_phone + ' / ' + m.nok_mobile, border_fmt)
                row += 1
            ws.autofit()
            ws.merge_range("A1:E1", "ASC Next of Kin List " + datetime.date.today().strftime("%d-%m-%Y"), title_merge_format)
        except Exception as e:
            applog.error("An error ocurred during currency spreadsheet create:{}".format(str(e)))
            applog.debug("Row was:{}".format(row))
            raise

    workbook.close()
    return filename

