from asc import db
import datetime
from dateutil.relativedelta import relativedelta

from asc.schema import MemberTrans, Pilot

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.fields import  DateField
from asc.wtforms_ext import MatButtonField

from flask import (flash, redirect, render_template, url_for, current_app as app)


class BasePass:

    class BasePassError(Exception):
        pass

    def __init__(self, memberid=None):
        self.__memberid = memberid
        if self.__memberid is not None:
            thismbr = db.session.get(Pilot,self.__memberid)
            if thismbr is None:
                raise self.BasePassError('Invalid member')
        self.__type = None
        self.__reference = None
        self.__issuedate = None
        self.__expirydate = None
        self.__transid = None
        last_pass = MemberTrans.query.filter(MemberTrans.memberid == self.__memberid). \
            filter(MemberTrans.transtype == 'BPASS'). \
            order_by(MemberTrans.inserted.desc()).first()
        if last_pass is None:
            # no record so set some defaults.
            self.__type = 'CLUB'
            self.__issuedate = datetime.date.today()
            self.__expirydate = self.__issuedate + relativedelta(years=2)
        else:
            # If the update or inserted date was quite recent then we will asssume they are changing
            # the record that exists, otherwise we will add a new row.
            # TODO:flesh out above rule.
            parts = last_pass.transnotes.split('/')
            self.__type = parts[0]
            self.__reference  = parts[1]
            self.__issuedate = last_pass.transdate
            self.__expirydate = datetime.datetime.strptime(parts[2],"%Y-%m-%d").date()
            self.__transid = last_pass.id

    @property
    def type(self):
        return self.__type

    @property
    def memberid(self):
        return self.__memberid

    # this does not really get executed....
    @memberid.setter
    def memberid(self, memberid):
        self.__memberid = memberid

    @type.setter
    def type(self, value):
        if value is None:
            raise self.BasePassError('Type must not be None ')
        if not isinstance(value, str):
            raise self.BasePassError('Type must be a string')
        if value not in ['CLUB','MD58','3389']:
            raise self.BasePassError('Type must be either 3389, CLUB or MD58')
        self.__type = value

    @property
    def reference(self):
        return self.__reference

    @reference.setter
    def reference(self,value):
        self.__reference = str(value)

    @property
    def issuedate(self):
        return self.__issuedate

    @issuedate.setter
    def issuedate(self,value):
        if value is None:
            raise self.BasePassError('Issue Date must not be None ')
        if not isinstance(value, datetime.date):
            raise self.BasePassError('Issue Date must be a Date')
        self.__issuedate = value


    @property
    def expirydate(self):
        return self.__expirydate

    @expirydate.setter
    def expirydate(self,value):
        if value is None:
            raise self.BasePassError('Expiry Date must not be None ')
        if not isinstance(value, datetime.date):
            raise self.BasePassError('Expiry Date must be a Date')
        self.__expirydate = value


    def __transnote(self):
        return self.__type + '/' + self.__reference + '/' + self.__expirydate.strftime("%Y-%m-%d")

    def updatetrans(self):
        thistrans = db.session.get(MemberTrans, self.__transid)
        if thistrans is not None:
            if thistrans.updated is None:
                addupd_date = thistrans.inserted.date()
            else:
                addupd_date = thistrans.updated.date()
            if addupd_date < datetime.date.today() - datetime.timedelta(days=30):
            # if addupd_date < datetime.date.today() - datetime.timedelta(days=30):
                # The pass has not been updated or created in the last 30 days so
                # we want to add new Transactions
                thistrans = None
        if thistrans is None:
            thistrans = MemberTrans(self.__memberid)
            thistrans.transtype = 'BPASS'
            thistrans.transdate = self.__issuedate
            thistrans.transnotes = self.__transnote()
            db.session.add(thistrans)
            db.session.commit()
            app.logger.info('Base Pass Added' + str(self.__memberid) + "/" + thistrans.transnotes)
        else:
            thistrans.transdate = self.__issuedate
            thistrans.transnotes = self.__transnote()
            app.logger.info('Base Pass Updated:' + str(self.__memberid) + "/" + thistrans.transnotes)


class BasePassMnt():

    # This is a separate class because we want to call this from multiple places:
    # Memberhsip maintenance and user profile maintenance

    # To call it the caller needs to create the template and then
    # use this code, changing "thispage" and "prevpage" as required.

    # @bp.route('/mntbasepass/<int:memberid>/', methods=['GET', 'POST'])
    # @login_required
    # def mntbasepass(memberid):
    #     try:
    #         mntform = BasePassMnt(memberid)
    #         mntform.thispage = 'membership.mntbasepass'
    #         mntform.prevpage = 'membership.membermaint'
    #         return mntform.theform()
    #     except Exception as e:
    #         flash(str(e), "error")
    #         return redirect(url_for('membership.membermaint', id=memberid))

    class BasePassMntError(Exception):
        pass

    class BasePassMntForm(FlaskForm):
        # id = IntegerField('ID', description='Primary Key', render_kw={'readonly': True, 'hidden':True})
        # memberid = IntegerField('Member', description='The id of the related member field', render_kw={'readonly': True, 'hidden':True})
        type = SelectField('Pass Type', description='The type of pass issued',
                           choices=[('none', 'None'), ('CLUB', 'Club Pass'), ('MD58', 'Military (MD58)'),
                                    ('3389', 'Cadet')])
        reference = StringField('Reference', description='Reference eg. Pass No or Service No.')
        issuedate = DateField('Issue Date', description='The date the pass was issued')
        expirydate = DateField('Expiry Date', description='The date the pass will expire')
        btnsubmit = MatButtonField('done', id='matdonebtn', icon='done', help="Confirm all Changes")
        cancel = MatButtonField('cancel', id='matcancelbtn', icon='cancel',
                                help="Press to exit and make no changes")  # , render_kw={'formnovalidate':''})
        delete = MatButtonField('delete', id='matdeletebtn', icon='delete',
                                help='Press to delete this record', render_kw={'onclick': 'return ConfirmDelete()'})

    def __init__(self, memberid):
        self.__memberid = memberid
        thismbr = db.session.get(Pilot,self.__memberid)
        if thismbr is None:
            raise self.BasePassMntError('Invalid member')
        self.__thispage = None
        self.__prevpage = None
        self.__thispage_template = None

    @property
    def thispage(self):
        return self.__thispage

    @thispage.setter
    def thispage(self,value):
        self.__thispage = value
        self.__thispage_template = self.thispage.replace(".","/")
        self.__thispage_template += ".html"

    @property
    def prevpage(self):
        return self.__prevpage

    @thispage.setter
    def prevpage(self, value):
        self.__prevpage = value

    def theform(self):
        if self.__thispage is None:
            raise self.BasePassMntError('This Page Not Set')
        if self.__prevpage is None:
            raise self.BasePassMntError('Previouse Page Not Set')
        try:
            thisrec = BasePass(self.__memberid)
            thisform = self.BasePassMntForm(obj=thisrec)
            if thisform.cancel.data:
                return redirect(url_for(self.__prevpage, id=self.__memberid))
            if thisform.validate_on_submit():
                # Provided the field names are the same, this function updates all the fields
                # on the table.  If there are any that are different then each field needs to be
                # assigned manually.
                thisform.populate_obj(thisrec)
                thisrec.updatetrans()
                return redirect(url_for(self.__prevpage, id=self.__memberid))
            return render_template(self.__thispage_template, form=thisform)
        except Exception as e:
            flash(str(e), "error")
            return redirect(url_for(self.__prevpage, id=self.__memberid))
