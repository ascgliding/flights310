
import os
import sys
sys.path.insert(0,os.path.abspath(".."))

from asc.schema import *
from decimal import Decimal
from asc import db, create_app
from asc.mailer import ascmailer
# In order to trap errors from the engine
import sqlalchemy.exc
from sqlalchemy import text as sqltext, func
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail,Attachment,FileContent,FileName,FileType,Disposition
import datetime

# from pydrive2.auth import GoogleAuth
# from pydrive2.drive import GoogleDrive
#
# from google.oauth2 import service_account
# from googleapiclient.discovery import build
# from googleapiclient.http import MediaFileUpload
# from googleapiclient.errors import HttpError
from asc.common import *
import re
import os

# import google.auth

app = create_app()
log = app.logger

# SCOPES = ['https://www.googleapis.com/auth/drive.metadata', 'https://www.googleapis.com/auth/drive']



try:
    del os.environ['PYTHONHOME']
except KeyError as e:
    print("Pythonhome is not set anyway")
    pass # don't care if it's not there

print("sys.path is ".format(sys.path))
print("pwd is {}".format(os.getcwd()))
print("pythonpath (in create_app dayend)_ is {}".format(os.environ['PYTHONPATH']))

# def google_credentials():
#     # reuturn a credentials object from the key downloaded from the google api console
#     pass
   

# def update_google():
#     # from google drive I navidated to my temp folder and grabbed this from the url:
#     mytempid = '1FoSoFYlcNplPH0-ReLuPLw1mqAzYh9RT'
#     service_account_id = 'ascbackup@api-project-1047925931133.iam.gserviceaccount.com'
#     # gauth = GoogleAuth()
#     # drive = GoogleDrive(gauth)
#     # upload_file_list = ['1.jpg', '2.jpg']
#     # for upload_file in upload_file_list:
#     #     gfile = drive.CreateFile({'parents': [{'id': mytempid}]}) # Read file and set it as the content of this instance.
#     #     gfile.SetContentFile(upload_file)
#     #     gfile.Upload() # Upload the file.
#     credentials, project_id = google.auth.default(scopes=SCOPES)
#
#     service = build('drive', 'v3', credentials=credentials)
#
#     # Call the Drive v3 API
#     results = service.files().list(
#         # q=f"'1YJ6gMgACOqVVbcgKviJKtVa5ITgsI1yP' in parents",
#         q=f"'1FoSoFYlcNplPH0-ReLuPLw1mqAzYh9RT' in parents",
#         pageSize=10, fields="nextPageToken, files(id, name, owners, parents)").execute()
#     items = results.get('files', [])
#
#     if not items:
#         print('No files found.')
#     else:
#         # print(items[0])
#
#         print('Files:')
#         for item in items:
#             # print (item)
#             print(u'{0}   {1}   {2}'.format(item['name'], item['owners'], item['parents']))
#
# def quickstart_authentication():
#     gauth = GoogleAuth()
#     gauth.LocalWebserverAuth()

def testmailer():
    """
    Test application class
    :return:
    """
    print("*** Send Test Email ***")
    try:
        msg = ascmailer('Test Mailer Subject')
        # thisbody = "<table><tr><th>col1</th><th>col2</th></tr>"
        # thisbody = thisbody + "<tr><td>1</td><td>One</td></tr>"
        # thisbody = thisbody + "<tr><td>2</td><td>Two</td></tr>"
        # thisbody = thisbody + "<tr><td>3</td><td>Three</td></tr>"
        # thisbody = thisbody + "</table>"
        # msg.body = thisbody
        # msg.body = "Here is the content"
        msg.add_body("Here is the Test Email")
        msg.add_body("</br> It is now " + datetime.datetime.now().strftime('%A %d-%b-%Y %H:%M'))
        msg.add_body("See table below<br>")
        sql = sqltext("""
               select id,pic,landed
               from flights
               limit 5
               """)
        sql = sql.columns(Flight.id,
                          Flight.pic,
                          Flight.landed
                          )
        thisset = db.engine.execute(sql).fetchall()
        dictlist = [x._asdict() for x in thisset]
        print(dictlist)
        print(list(dictlist))
        print(type(dictlist[0]))
        dictlist.insert(0, ['ID', 'PIC', 'Landed'])
        msg.add_body_list(dictlist)
        msg.add_recipient('ray@rayburns.nz')
        msg.send()
        print("Send grid status {}".format(msg.response.status_code))
        print(msg.response.headers)
    except Exception as e:
        self.fail("Error raised :{}".format(e))

def update_auto_readings():
    print("*** Update Auto Meter Readings ***")
    sql = sqltext("""
        select t1.regn 
        from acmeters t0
        join aircraft t1 on t1.id = t0.ac_id 
        where auto_update  = 1
        group by 1
        """)
    rows = db.engine.execute(sql).fetchall()
    common_set_log(log)
    for row in rows:
        create_readings_from_flights(row[0])

def send_one_maintenance_email(address,thelist):
    # print('TESTING: Email to {}'.format(address))
    # print('About to send:')
    # for t in thelist:
    #     print(t)
    # send the email here
    msg = ascmailer('ASC Aircraft tasks due')
    # msg.add_body("Email should have gone to {}".format(address))
    msg.add_body_list(thelist)
    msg.add_recipient(address)
    msg.send()
    # print(msg.body)


def send_maintenance_emails():
    print("*** Maintenance Emails ***")
    sql = sqltext("""
    select 
        t1.regn
        from actasks t0
            left outer join aircraft t1 on t1.id = t0.ac_id 
        where warning_days  is NOT NULL 
        and warning_email is not null
        group by 1
    """)
    ac_with_warnings = db.engine.execute(sql).fetchall()
    common_set_log(log)
    emails = []
    for ac in ac_with_warnings:
        # print('Processing {}'.format(ac.regn))
        thisac = ACMaint(ac[0])
        for t in thisac.tasks:
            # print('Task {}'.format(t.description))
            if t.warning_days is not None:
                if t.next_due_date - relativedelta(days=t.warning_days) <= datetime.date.today():
                    addresses = re.split(',|;| |\|',t.warning_email)
                    # print('Addresses: {}'.format(emails))
                    for addr in addresses:
                        if "@" in addr :  # looks like an email and deals with any empty list items.
                            emails.append({'addr':addr,
                                           'ac':ac[0],
                                           'due': t.next_due_date,
                                           'duemsg': t.next_due_message,
                                           'task': t.description,})
    # we now have a list of email messages to send that we want to sort into address
    # order so that we only send each person one email.
    sortedlist = sorted(emails, key=lambda d: (d['addr'],d['ac'],d['due']) )
    for s in sortedlist:
        print(s)
    print('Now Processing Sorted list')
    lastaddr = None
    emailtext = []
    # emailtext.append({'ac':'Regn',
    #                   'task':'Task',
    #                   'due':'Due',
    #                   'duemsg': 'Due Message'
    #                     })
    emailtext.append(['Regn','Task','Due','Message'])
    for tasks in sortedlist:
        if lastaddr is not None and lastaddr != tasks['addr']:
            send_one_maintenance_email(lastaddr,emailtext)
            emailtext.clear()
            emailtext.append(['Regn', 'Task', 'Due', 'Message'])
        emailtext.append({'ac': tasks['ac'],
                          'task': tasks['task'],
                          'due': tasks['due'],
                          'duemsg': tasks['duemsg']
                          })
        lastaddr = tasks['addr']
    # send the last one
    if len(emailtext) > 1:
        send_one_maintenance_email(lastaddr, emailtext)

def validate_all_readings():
    print("*** Validating Readings ***")
    sql = sqltext("""
        select t1.regn
            from meterreadings t0
            left outer join aircraft t1 on t1.id = t0.ac_id
            group by 1
    """)
    ac_with_readings = db.engine.execute(sql).fetchall()
    for ac in ac_with_readings:
        thisac = ACMaint(ac[0])
        print('Checking {}'.format(thisac.regn))
        for m in thisac.meters:
            print('Checking meter {}'.format(m.meter_name))
            for e  in m.reading_errors:
                print(e)

def send_db():
    print('sending Database')
    print(os.getcwd())
    msg = ascmailer('Database Backup')
    # msg.add_body("Email should have gone to {}".format(address))
    msgbody
    msg.add_body("<html>Here is the Database Backup")
    msg.add_body("</br> It is now " + datetime.datetime.now().strftime('%A %d-%b-%Y %H:%M'))
    msg.add_body("</html>")
    msg.add_recipient('ray@rayburns.nz')
    msg.add_attachment('../instance/asc.sqlite')
    msg.send()

def send_med_bfr_to_cfi():
    mems = Member.query.filter(Member.active==True).filter(Member.email_bfr_med==True).order_by(Member.surname)
    count = 0
    email_list = [{'name':'Name','medical':'Medical','bfr':'BFR','message':'Message'}]
    email_list = []
    for m in mems:
        msgs = []
        if m.bfr_due is not None and m.bfr_due < datetime.date.today():
            msgs.append('BFR Expired')
        elif m.bfr_due is not None and m.bfr_due < datetime.date.today() - relativedelta(days=60):
            msgs.append('BFR Coming Up')
        if m.medical_due is not None and m.medical_due < datetime.date.today():
            msgs.append('Medical Expired')
        elif m.medical_due is not None and m.medical_due < datetime.date.today() - relativedelta(days=60):
            msgs.append('Medical Coming Up')
        if len(msgs) > 0:
            count += 1
            email_list.append({'Name':m.fullname, 'Medical': m.medical_due, 'BFR': m.bfr_due, 'Message':','.join(msgs) })
    if count > 0:
        msg = ascmailer('Medical and BFR Status')
        msg.add_body_list(email_list)
        msg.add_recipient('ray@rayburns.nz')
        msg.send()



def send_stats_to_gnz():
    """
    This is the text of the email from Max...
    The usual 6-monthy flight stats are now called for.  As a reminder of what is required (criteria), please see the attachment.
        To complete your return just reply to this message with the following information:
        1.    Number of aero-tow launches
        2.    Number of winch launches
        3.    Number of automobile launches
        4.    Number of self-launches
        5.    Total number of flights by club gliders (ie not private)
        -       Number of trial flights within this total
        -       Number of youth flights (under 26 years) within this total
        Number of First Solos – please also provide the names of your first-solos so we don’t double-count them!
    :return:
    """
    pass


if __name__ == '__main__':
    with app.app_context():
        # The execution time is 0400.
        log.info("Dayend started")
        # testmailer()
        update_auto_readings()
        send_maintenance_emails()
        #validate_all_readings()
        # send me the database on Saturdays and Sundays.
        if datetime.datetime.today().weekday() in [ 6,0 ]:
            log.info("Database Emailed during Dayend")
            send_db()
        # send me medical and BFR data on Friday Mornings.
        if datetime.datetime.today().weekday() in [ 1,4 ]:
            send_med_bfr_to_cfi()
        print("it ran")
