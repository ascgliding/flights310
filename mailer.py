import base64

from sendgrid import SendGridAPIClient,Mail
from sendgrid.helpers.mail import Mail,Attachment,FileContent,FileName,FileType,Disposition,Content,To
import os
from flask import current_app
from asc.schema import  Slot

app = current_app

class ascmailer:

    class mailerError(Exception):
        pass


    def __init__(self,subject=None):
        self.__subject = ''
        if subject is not None:
            if not isinstance(subject,str):
                raise AttributeError("Subject line must be a string")
            self.__subject = subject
        self.__apikey = Slot.query.filter_by(slot_type='SYSTEM').filter_by(slot_key='SENDGRIDAPIKEY').first()
        if self.__apikey is None:
            raise ValueError("API Key for Sendgrid not defined in datbase.")
        # self.__sg = SendGridAPIClient(api_key=app.config['SENDGRIDAPIKEY'])
        self.__sg = SendGridAPIClient(api_key=self.__apikey.slot_data)
        self.__message = Mail(from_email='ascgliding@gmail.com')
        self.__attachments = [] # list of filenames
        self.__bodyhtml = ''
        self.__description = 'Mail message'
        self.__recipients = [] # list of email addresses to send to
        self.__response = None
        self.__cc = ''
        app.logger.info('Mail item created ' + subject)


    def __str__(self):
        return self.__description

    @property
    def description(self):
        return self.__description

    @description.setter
    def description(self, value):
        if value is None:
            raise AttributeError("Description cannot be set to None")
        if not isinstance(value, str):
            raise AttributeError("Description is not a string variable")
        self.__description = value

    @property
    def subject(self):
        return self.__subject

    @subject.setter
    def subject(self, value):
        if value is None:
            raise AttributeError("Subject cannot be set to None")
        if not isinstance(value, str):
            raise AttributeError("Subject is not a string variable")
        self.__subject = value

    @property
    def body(self):
        return self.__bodyhtml

    @body.setter
    def body(self, value):
        if value is None:
            raise AttributeError("Body cannot be set to None")
        if not isinstance(value, str):
            raise AttributeError("Body is not a string variable")
        self.__bodyhtml = value

    @property
    def response(self):
        return self.__response

    @property
    def cc(self):
        return self.__cc

    @cc.setter
    def cc(self,value):
        if value is None:
            raise AttributeError("CC cannot be none")
        if not isinstance(value,str):
            raise AttributeError("CC must be a string")
        self.__cc = value



    # -----------------------------------------------------------------------------------------
    # Public Methods
    # -----------------------------------------------------------------------------------------

    def add_body(self,phtml):
        """
        Simply adds html to the body.  Call as many times as you like.
        :param phtml:
        :return:
        """
        if phtml is None:
            raise AttributeError("Parameter is None.")
        if isinstance(phtml, str):
            self.__bodyhtml += phtml
        else:
            raise AttributeError("Parameter is neither a string or a list.")

    def add_body_list(self,plist):
        """
        Plist should be a list of dictionaries
        First row is considered headings.

        From sqlalchemy this can be returned using:
        thisset = db.engine.execute(sql).fetchall()
        # turn into a dictionary
        dictlist = [[x._asdict() for x in thisset]]

        Add column headings with something like:

        dictlist.insert(0,['ID','PIC','Landed'])


        The intention of this is it is easy to add a table to the html directly
        from an sqlalchemy sql statement.

        :param plist:
        :return:
        """
        if plist is None:
            raise AttributeError("Parameter is None")
        if not isinstance(plist,list):
            raise AttributeError("Parameter must be a list")
        for p in plist:
            if not isinstance(p,dict) and not isinstance(p,list):
                raise AttributeError("Parameter list item is not a dictionary ({}:{})".format(type(p),p))
        # keyvalues = list(plist[0].keys())
        htmltable = "<table style='border-spacing:10px'><tr>"
        if isinstance(plist[0],dict):
            thislist = plist[0].keys()
        else:
            thislist = plist[0]
        for fld in thislist:
            htmltable += '<th>' + fld + '</th>'
        htmltable += '</tr>'
        for r in plist[1:]:
            htmltable += "<tr>"
            if isinstance(r,dict):
                thislist = list(r.values())
            else:
                thislist = r
            for fld in thislist:
                htmltable += "<td>" + str(fld) + "</td>"
            htmltable += '</tr>'
        htmltable += '</table>'
        self.__bodyhtml += htmltable


    def add_recipient(self,value):
        if value is None:
            raise AttributeError("Recipient cannot be set to None")
        if not isinstance(value, str):
            raise AttributeError("Recipient is not a string variable")
        self.__recipients.append(value)

    def add_attachment(self,value):
        if value is None:
            raise AttributeError("Attachment cannot be set to None")
        if not isinstance(value, str):
            raise AttributeError("Attachment is not a string variable")
        # Check if attachment is available
        if not os.path.isfile(value):
            raise FileExistsError("Attachment is not a file on the system")
        self.__attachments.append(value)

    def send(self):
        if self.__recipients is None:
            raise self.mailerError("Recipient list is None")
        if len(self.__recipients) == 0:
            raise self.mailerError("No recipients specified")
        if self.__subject == '':
            raise self.mailerError("The subject cannot be empty")
        # Create the mail
        self.__message.subject = self.__subject
        self.__message.content = Content("text/html",self.__bodyhtml)
        tolist = []
        for addr in self.__recipients:
            tolist.append(To(addr))
        self.__message.to = tolist
        if self.cc != '':
            self.__message.cc = self.__cc
        # Deal with attachements
        for attachment in self.__attachments:
            print('Attaching {}'.format(attachment))
            with open(attachment,'rb') as f:
                data = f.read()
                f.close
            encoded_file = base64.b64encode(data).decode()
            thisfile = Attachment(
                FileContent(encoded_file),
                FileName(os.path.basename(attachment)),
                FileType('application/octet-stream'),
                Disposition('attachment')
            )
            self.__message.attachment = thisfile
        # send it
        try:
            self.__response = self.__sg.send(self.__message)
            app.logger.info('Mail Recipients : {}'.format(",".join(self.__recipients)))
            app.logger.info('Mail sent successfully with status {}'.format(self.__response.status_code))
            # the correct status code is 202.  I don't want other conditions to be an error because
            # who knows what sendgrid may do in the future, but I do want to log non-202 status codes.
            if self.__response.status_code != 202:
                app.logger.error('Mail returned an non-202 status code.  This looks odd.')
            # it may also be usefult to know self.__response.headers and self.__response.body
        except Exception as e:
            app.logger.error('Error sending mail {}'.format(str(e)))
            raise self.mailerError(str(e))


