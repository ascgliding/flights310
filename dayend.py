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



app = create_app()
log = app.logger




try:
    del os.environ['PYTHONHOME']
except KeyError as e:
    print("Pythonhome is not set anyway")
    pass # don't care if it's not there

print("sys.path is ".format(sys.path))
print("pwd is {}".format(os.getcwd()))
print("pythonpath (in create_app dayend)_ is {}".format(os.environ['PYTHONPATH']))

# print("app instance path (in create_app dayend.py)_ is {}".format(app.instance_path))

# from  asc.mailer import ascmailer

# def test():
#     thismailer = ascmailer('testmail')
#     thismailer.body = 'here is mail from the dayend'
#     thismailer.add_recipient('ray@rayburns.nz')

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
        testmailer()
        print("it ran")
        # thismail = ascmailer("Test mail from ASC dayend")
        # thismail.body = "Test Mail"
        # thismail.add_recipient("ray@rayburns.nz")
        # thismail.send()

