import time

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Flask, send_from_directory, current_app, send_file,session
)
from flask_login import current_user
from asc import db
from sqlalchemy import not_
from asc.schema import Pilot,  Slot, MemberTrans, User
from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, validators, SubmitField, SelectField, BooleanField, RadioField, \
    TextAreaField
from wtforms.fields import EmailField, IntegerField, DateField
from asc.wtforms_ext import MatButtonField, TextButtonField
from asc.oMailerSmtp import MailerSmtp
import markdown



app = current_app
applog = app.logger
#bootstrap = Bootstrap5()

markdown_placeholder_text = """Enter the email text here.
Markdown is supported.  For example:
    
# Welcome
This is a **Markdown** example with a [link](https://example.com).

* Item 1
* Item 2

To send attachments: Load to the google drive and use a link as shown above.
"""

bp = Blueprint('bulkemail', __name__, url_prefix='/bulkemail')

class EmailContentForm(FlaskForm):
    subject = StringField('Subject', description='Subject', render_kw={'placeholder': 'Enter the Subject Text Here'})
    email_text = TextAreaField('Emailtext', description='The content of the email', render_kw={'rows': 10, 'cols': 50, 'placeholder': markdown_placeholder_text})
    btnsubmit = MatButtonField('done', id='matdonebtn', icon='email', help="Send the Email")
    cancel = MatButtonField('cancel', id='matcancelbtn', icon='cancel',
                            help="Press to exit and make no changes")  # , render_kw={'formnovalidate':''})

class Mailer(MailerSmtp):

    def __init__(self, subject=None):
        # super(MailerSmtp, self).__init__(subject)
        super().__init__(subject)
        # now get the values from the database
        smtpkeys = Slot.query.filter(Slot.slot_type == 'SMTP').all()
        for s in smtpkeys:
            print(f'{s.slot_key} / {s.slot_data}')
            if s.slot_key == 'SMTP_SERVER':
                self.smtp_server = s.slot_data
            elif s.slot_key == 'SMTP_PORT':
                self.smtp_port = int(s.slot_data)
            elif s.slot_key == 'SMTP_MAIL_ADDRESS':
                self.smtp_mail_address = s.slot_data
            elif s.slot_key == 'SMTP_PASSWORD':
                print(f'setting password to s.slot_data')
                self.smtp_mail_password = s.slot_data

@bp.route('/')
def index():
    if 'emaillist' in session:
        thislist = session['emaillist']
    else:
        session['emaillist']=[]
    return render_template('bulkemail/index.html', list=session['emaillist'])

@bp.route('test', methods=['GET', 'POST'])
def test():
    if 'emaillist' in session:
        thislist = session['emaillist']
    else:
        thislist = []
    if len(thislist) == 0:
        thislist.append({'email': 'ray.burns@velocityglobal.co.nz', 'firstname': 'CIO'})
        thislist.append({'email': 'cfi@ascgliding.org', 'firstname': 'CFI'})
        thislist.append({'email': 'maskthis-website@xtra.co.nz', 'firstname': 'Ray'})
    session['emaillist'] = thislist
    return render_template('bulkemail/index.html', list=session['emaillist'])

@bp.route('delitem/<email>', methods=['GET', 'POST'])
def delitem(email):
    if 'emaillist' in session:
        thislist = session['emaillist']
    else:
        thislist = []
    session['emaillist'] = [item for item in thislist if item['email'] != email]
    return render_template('bulkemail/index.html', list=session['emaillist'])

def __addfromqry(qrylist):
    if 'emaillist' in session:
        thislist = session['emaillist']
    else:
        thislist = []
    for i in qrylist:
        if i.email not in [ p['email'] for p in thislist]:
            thislist.append({'email': i.email, 'name':i.fullname, 'firstname': i.firstname})
    session['emaillist'] = thislist


@bp.route('addactivemembers', methods=['GET', 'POST'])
def addactivemembers():
    __addfromqry(db.session.query(Pilot).filter(Pilot.active).filter(Pilot.member).all())
    return render_template('bulkemail/index.html', list=session['emaillist'])

@bp.route('addtowpilots', methods=['GET', 'POST'])
def addtowpilots():
    __addfromqry(db.session.query(Pilot).filter(Pilot.active).filter(Pilot.member).filter(Pilot.towpilot).all())
    return render_template('bulkemail/index.html', list=session['emaillist'])

@bp.route('addcommittee', methods=['GET', 'POST'])
def addcommittee():
    __addfromqry(db.session.query(Pilot).filter(Pilot.active).filter(Pilot.member).filter(Pilot.committee).all())
    return render_template('bulkemail/index.html', list=session['emaillist'])

@bp.route('addinstructors', methods=['GET', 'POST'])
def addinstructors():
    __addfromqry(db.session.query(Pilot).filter(Pilot.active).filter(Pilot.member).filter(Pilot.instructor).all())
    return render_template('bulkemail/index.html', list=session['emaillist'])

@bp.route('clearlist', methods=['GET', 'POST'])
def clearlist():
    session['emaillist'] = []
    return render_template('bulkemail/index.html', list=session['emaillist'])

@bp.route('addstudents', methods=['GET', 'POST'])
def addstudents():
    if 'emaillist' in session:
        thislist = session['emaillist']
    else:
        thislist = []
    thesemembers = db.session.query(Pilot).filter(Pilot.active).filter(Pilot.member).filter(not_(Pilot.towpilot)).all()
    for m in thesemembers:
        isstudent = True
        for t in m.transactions:
            if t.transtype == 'RTG' and t.transsubtype == 'QGP':
                isstudent = False
        if isstudent:
            thislist.append({'email': m.email, 'name':m.fullname, 'firstname': m.firstname})
    session['emaillist'] = thislist
    return render_template('bulkemail/index.html', list=session['emaillist'])



@bp.route('/emailtext', methods=['GET'])
def emailtext():
    if 'emaillist' not in session:
        flash('You need to select recipients first')
        return render_template('bulkemail/index.html', list=[])
    thisform = EmailContentForm()
    return render_template('bulkemail/emailtext.html', form=thisform)


@bp.route('/sendemail', methods=['POST'])
def sendemail():
    if 'emaillist' not in session:
        flash('You need to select recipients first')
        return render_template('bulkemail/index.html', list=[])
    thisform = EmailContentForm()
    if thisform.subject.data == '':
        flash('You must Enter a subject')
    try:
        thismail = Mailer(thisform.subject.data)
        thismail.replyto = current_user.email
        for item in session['emaillist']:
            thismail.recipients = [item['email']]  # a list of one entry
            thismail.body = markdown.markdown(item['firstname'] + ",\n" + thisform.email_text.data)
            thismail.send()
        flash(f'The email was sent to {len(session["emaillist"])} recipients.', category='success')
    except Exception as e:
        flash(str(e),"error")
    return render_template('bulkemail/index.html', list=session['emaillist'])



