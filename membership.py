from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Flask, send_from_directory, current_app
)
from werkzeug.exceptions import abort

from flask_login import login_required, current_user
from asc import db
from asc.schema import Pilot, Member, Slot, MemberTrans
from sqlalchemy import text as sqltext
from sqlalchemy import or_, and_

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

bp = Blueprint('membership', __name__, url_prefix='/membership')
app = Flask(__name__)
applog = app.logger


class MemberForm(FlaskForm):
    id = IntegerField('ID', description='Primary Key')
    active = BooleanField('Active', description="Active members appear on the membership list")
    gnz_no = IntegerField('NZGA No', [validators.DataRequired(message='You cannot have a blank code')])
    type = RadioField('Member Type', render_kw={'title': 'Select the correct Membership Type'})
    surname = StringField('Surname', [validators.DataRequired(message='You cannot have a blank Surname')],
                          description="Members Surname", render_kw={'autocomplete': 'dont'})
    firstname = StringField('Firstname', [validators.DataRequired(message='You cannot have a blank Firstname')],
                            description="Members Firstname", render_kw={'autocomplete': 'dont'})
    rank = SelectField('Rank',
                       description="Select Suitable Rank")  # note that the choices are defined when the form is loaded with:
    # thisform.rank.choices = [(r.slot_key, r.slot_desc) for r in Slot.query.filter_by(slot_type = 'RANK')]
    note = TextAreaField('Note', render_kw={'rows': 5, 'cols': 50})
    email_address = EmailField('Email Addr', [Email(message='Invalid email address')], description="Email Address",
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
    committee = BooleanField('Committee Member')
    instructor = BooleanField('Instructor')
    tow_pilot = BooleanField('Tow Pilot')
    oo = BooleanField('OO')
    duty_pilot = BooleanField('Duty Pilot')
    nok_name = StringField('Next of Kin')
    nok_rship = StringField('Relationship', render_kw={'list': "nok_rship_datalist"})
    nok_phone = StringField('NOK Phone', description='Next of Kin Phone number')
    nok_mobile = StringField('NOK Mobile', description='Next of kin Mobile Number')
    glider = StringField('Glider', description='Registration of privately owned glider')
    # transactions = relationship("MemberTrans", backref='memberid')

    btnsubmit = MatButtonField('done', id='matdonebtn', icon='done', help="Confirm all Changes")
    cancel = MatButtonField('cancel', id='matcancelbtn', icon='cancel',
                            help="Press to exit and make no changes")  # , render_kw={'formnovalidate':''})
    print = MatButtonField('print', id='printbtn', icon='print', help='Press to print report')
    trans = TextButtonField('Transactions', id="transbtn", text='Transactions', help="View transactions for members")
    delete = MatButtonField('delete', id='matdeletebtn', icon='delete', help='Press to delete this record',
                            render_kw={'onclick': 'return ConfirmDelete()'})

    def validate_email_address(self, email_address):
        """Email validation."""
        if len(email_address.data) > 0:
            sqlstmt = sqltext("""SELECT id
                            FROM members 
                             where (email_address = :email and id != :thisid )
                             or (email_2 = :email and id != :thisid )""")
            cnt = db.engine.execute(sqlstmt, thisid=self.id.data, email=email_address.data).fetchall()
            if len(cnt) > 0:
                raise ValidationError("Email address already in use")



    def validate_email_2(self, email_2):
        """Email validation."""
        if len(email_2.data) > 0:
            sqlstmt = sqltext("""SELECT id
                            FROM members 
                             where (email_address = :email and id != :thisid )
                             or (email_2 = :email and id != :thisid )""")
            cnt = db.engine.execute(sqlstmt, thisid=self.id.data, email=email_2.data).fetchall()
            if len(cnt) > 0:
                raise ValidationError("Email address already in use")


class TransactionForm(Form):
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


@bp.route('/memberlist', methods=['GET', 'POST'])
@login_required
def memberlist():
    if request.method == 'GET':
        list = Member.query.order_by(Member.surname)
        return render_template('membership/memberlist.html', list=list)


@bp.route('/membermaint/<id>', methods=['GET', 'POST'])
@login_required
def membermaint(id):
    thismem = Member.query.get(id)
    # if thismem is None then we will be adding
    if thismem is None:
        thismem = Member()
    thisform = MemberForm(obj=thismem, name='Member Maintenance')
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
        if thismem.id is None:
            db.session.add(thismem)
        if thisform.delete.data:
            # Note that there is a cascading delete to remove trans
            db.session.delete(thismem)
        db.session.commit()
        return redirect(url_for('membership.memberlist'))
    return render_template('membership/membermaint.html', form=thisform, nokrs=nok_relationships)


@bp.route('/translist/<id>', methods=['GET', 'POST'])
@login_required
def translist(id):
    if request.method == 'GET':
        thismember = Member.query.get(id)
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
        """)
        sqlstmt = sqlstmt.columns(transdate=db.Date)
        list = db.engine.execute(sqlstmt, member=id)
        # list = MemberTrans.query.filter_by(memberid=id).order_by(MemberTrans.transdate)
        return render_template('membership/translist.html', list=list, member=thismember)


@bp.route('/transmaint/<id>/<member>', methods=['GET', 'POST'])
@login_required
def transmaint(id, member=None):
    thisrec = MemberTrans.query.get(id)
    # if thismem is None then we will be adding
    if thisrec is None:
        thisrec = MemberTrans(member)
    thisform = TransactionForm(obj=thisrec)
    if thisform.cancel.data:
        return redirect(url_for('membership.memberlist'))
    thisform.transtype.choices = [(r.slot_key, r.slot_desc) for r in Slot.query.filter_by(slot_type='TRANSTYPE')]
    thisform.transsubtype.choices = [(r.slot_key, r.slot_desc) for r in Slot.query.filter_by(slot_type='RATING')]
    thisform.transsubtype.choices.append(('', 'N/A'))
    # this is the line that does the work
    if request.method == 'POST' and thisform.validate():
        # Provided the field names are the same, this function updates all the fields
        # on the table.  If there are any that are different then each field needs to be
        # assigned manually.
        thisform.populate_obj(thisrec)
        if thisrec.id is None:
            db.session.add(thisrec)
        if thisform.delete.data:
            db.session.delete(thisrec)
        db.session.commit()
        return redirect(url_for('membership.memberlist'))
    return render_template('membership/transmaint.html', form=thisform)
