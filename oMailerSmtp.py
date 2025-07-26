import os
from flask import current_app
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

app = current_app

class MailerSmtp:

    # this is so simple with gmail.
    #   Log in to your account
    #   From the three-dot menu select "Manage Your Account"
    #   Select Security
    #   2 Factor Authenticaion MUST be enabled
    #   Go to the 2FA screen - at the bottom is a section called "App Passwords"
    #   Create an app password.  It will be a string of four groups of four characters
    #   When using the server.login method the email address is your gmail account address
    #   And the password is the four character password.
    #  Set all of this in config.py:

    # SMTP_MAIL_ADDRESS="ray.burns.ggl@gmail.com"
    # SMTP_MAIL_PASSWORD = "xxxx xxxx xxxx xxxx"
    # SMTP_SERVER = "smtp.gmail.com"
    # SMTP_PORT = 587

    # Limits.
    # Note that there is a limit.  You can send 500 emails per 24 hour period.
    # each TO, CC or BCC is considered a single email.  Therefore if you have
    # one email being sent to one person with 5 CC entries, this will count
    # as 6 emails.

    class mailerError(Exception):
        pass


    def __init__(self,subject=None):
        # Before anything verify the following variables are defined:

        for v in ['SMTP_SERVER','SMTP_PORT','SMTP_MAIL_ADDRESS','SMTP_MAIL_PASSWORD']:
            if v not in app.config.keys():
                raise self.mailerError(f'Variable {v} is missing from config.py')
            if v == 'SMTP_PORT':
                if not isinstance(app.config[v],int):
                    raise self.mailerError(f'Variable {v} in config.py is not a valid integer')
            else:
                if not isinstance(app.config[v],str):
                    raise self.mailerError(f'Variable {v} in config.py is not a valid string')

        self.__subject = ''
        if subject is not None:
            if not isinstance(subject,str):
                raise AttributeError("Subject line must be a string")
        self.__subject = subject
        self.__attachments = [] # list of filenames
        self.__bodyhtml = ''
        self.__description = 'Mail message'
        self.__recipients = [] # list of email addresses to send to
        self.__response = None
        self.__cc = []
        self.__replyto = None
        app.logger.info('Mail item created.  Subject: ' + subject)


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

    @property
    def replyto(self):
        return self.__replyto

    @replyto.setter
    def replyto(self, value):
        if value is None:
            raise AttributeError("Reply to cannot be set to None")
        if not isinstance(value, str):
            raise AttributeError("reply to is not a string variable")
        self.__replyto = value


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

    def add_cc(self,value):
        if value is None:
            raise AttributeError("cc cannot be set to None")
        if not isinstance(value, str):
            raise AttributeError("cc is not a string variable")
        self.__cc.append(value)


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
        thismsg = MIMEMultipart()
        if self.__recipients is None:
            raise self.mailerError("Recipient list is None")
        if len(self.__recipients) == 0:
            raise self.mailerError("No recipients specified")
        if self.__subject == '':
            raise self.mailerError("The subject cannot be empty")
        # Create the mail
        thismsg['Subject'] = self.__subject
        thismsg.attach(MIMEText(self.__bodyhtml,'html'))
        # Recipients
        recipient_string = ",".join(self.__recipients)
        thismsg['To']   = recipient_string
        thismsg['Cc']   = ",".join(self.__cc)
        thismsg['From']   = app.config['SMTP_MAIL_ADDRESS']
        if self.__replyto is not None and isinstance(self.__replyto,str):
            thismsg.add_header('reply-to',self.__replyto)

        for f in self.__attachments or []:
            with open(f,"rb") as file:
                part = MIMEApplication(file.read(),name=os.path.basename(f))
            part['Content-Disposition'] = f'attachment; filename={os.path.basename(f)}'
            thismsg.attach(part)

        # send it
        try:
            app.logger.info('About to send to Mail Recipients : {}'.format(",".join(self.__recipients)))

            with smtplib.SMTP(app.config['SMTP_SERVER'], app.config['SMTP_PORT']) as server:
                server.starttls()
                server.login(app.config['SMTP_MAIL_ADDRESS'],app.config['SMTP_MAIL_PASSWORD'])
                server.sendmail(app.config['SMTP_MAIL_ADDRESS'],recipient_string, thismsg.as_string())
            app.logger.info('Mail sent successfully')
        except Exception as e:
            app.logger.error('Error sending mail : {}'.format(str(e)))
            raise self.mailerError(str(e))


