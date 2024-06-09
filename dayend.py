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

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

import google.auth

app = create_app()
log = app.logger

SCOPES = ['https://www.googleapis.com/auth/drive.metadata', 'https://www.googleapis.com/auth/drive']



try:
    del os.environ['PYTHONHOME']
except KeyError as e:
    print("Pythonhome is not set anyway")
    pass # don't care if it's not there

print("sys.path is ".format(sys.path))
print("pwd is {}".format(os.getcwd()))
print("pythonpath (in create_app dayend)_ is {}".format(os.environ['PYTHONPATH']))

def google_credentials():
    # reuturn a credentials object from the key downloaded from the google api console
   

def update_google():
    # from google drive I navidated to my temp folder and grabbed this from the url:
    mytempid = '1FoSoFYlcNplPH0-ReLuPLw1mqAzYh9RT'
    service_account_id = 'ascbackup@api-project-1047925931133.iam.gserviceaccount.com'
    # gauth = GoogleAuth()
    # drive = GoogleDrive(gauth)
    # upload_file_list = ['1.jpg', '2.jpg']
    # for upload_file in upload_file_list:
    #     gfile = drive.CreateFile({'parents': [{'id': mytempid}]}) # Read file and set it as the content of this instance.
    #     gfile.SetContentFile(upload_file)
    #     gfile.Upload() # Upload the file.
    credentials, project_id = google.auth.default(scopes=SCOPES)

    service = build('drive', 'v3', credentials=credentials)

    # Call the Drive v3 API
    results = service.files().list(
        # q=f"'1YJ6gMgACOqVVbcgKviJKtVa5ITgsI1yP' in parents",
        q=f"'1FoSoFYlcNplPH0-ReLuPLw1mqAzYh9RT' in parents",
        pageSize=10, fields="nextPageToken, files(id, name, owners, parents)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        # print(items[0])

        print('Files:')
        for item in items:
            # print (item)
            print(u'{0}   {1}   {2}'.format(item['name'], item['owners'], item['parents']))

def quickstart_authentication():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()

def testmailer():
    """
    Test application class
    :return:
    """
    try:
        msg = ascmailer('Test Mailer Subject')
        # thisbody = "<table><tr><th>col1</th><th>col2</th></tr>"
        # thisbody = thisbody + "<tr><td>1</td><td>One</td></tr>"
        # thisbody = thisbody + "<tr><td>2</td><td>Two</td></tr>"
        # thisbody = thisbody + "<tr><td>3</td><td>Three</td></tr>"
        # thisbody = thisbody + "</table>"
        # msg.body = thisbody
        # msg.body = "Heree is the content"
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



if __name__ == '__main__':
    with app.app_context():
        log.info("Dayend started")
        # quickstart_authentication()
        # testmailer()
        update_google()
        print("it ran")
        # thismail = ascmailer("Test mail from ASC dayend")
        # thismail.body = "Test Mail"
        # thismail.add_recipient("ray@rayburns.nz")
        # thismail.send()

