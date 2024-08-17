import datetime
from dateutil.relativedelta import *
from asc.schema import *
from decimal import Decimal
from asc import db
from sqlalchemy import text as sqltext, delete, select
from flask import current_app


# TODO:  why can I not use this when using testcases?
# app = current_app
# applog = app.logger

class OneMember:

    """
    This class contains three variables which are lists:
        tasks, meters and users.

    """

    class MemberError(Exception):
        pass

    def __init__(self,pidentifier):
        # allow either the regn or id.
        self.__mbr_row = None
        try:
            self.__mbr_row = self.__get_mbr_record(pidentifier)
        except:
             raise self.MemberError('No Such Member')
        if self.__mbr_row is None:
            raise self.MemberError('No Such Member')
        self.__fullname = self.__mbr_row.fullname
        self.__user_id = None
        self.__pilot_id = None
        self.__build_instance()

    def __get_mbr_record(self,pidentifier):
        '''
        The class cal be instantiated with any of id, fullname or gnzno
        :param para:
        :return: A member record
        '''
        thismbr = Member.query.filter(Member.id == int(pidentifier)).first()
        if thismbr is None:
            thismbr = Member.query.filter(Member.gnz_no == int(pidentifier)).first()
        if thismbr is None:
            thismbr = Member.query.filter(Member.fullname == int(pidentifier)).first()
        return thismbr

    def __str__(self):
        return self.__regn

    @property
    def id(self):
        return self.__mbr_row.id

    @property
    def fullname(self):
        return self.__mbr_row.firstname + ' ' + self.__mbr_row.surname

    @property
    def email_address(self):
        return self.__mbr_row.email_address

    @property
    def phone(self):
        return self.__mbr_row.phone

    @property
    def mobile(self):
        return self.__mbr_row.mobile

    @property
    def gnz_no(self):
        return self.__mbr_row.gnz_no

    @property
    def pilot_id(self):
        return self.__pilot_id

    @property
    def user_id(self):
        return self.__user_id

    @property
    def bfr_due(self):
        return self.__bfr_due()

    @property
    def medical_due(self):
        return self.__medical_due()

    @property
    def currency_dict(self):
        return self.__currency_dict()

    @property
    def login_id(self):
        user = User.query.get(self.__user_id)
        if user is None:
            return 'Not registered'
        else:
            return user.name

    @property
    def customer_code(self):
        pilot = Pilot.query.get(self.__pilot_id)
        if pilot is None:
            return 'No pilot record'
        else:
            return pilot.accts_cust_code


    def __build_instance(self):
        # Find the link to the users
        thisuser = User.query.filter(User.gnz_no == self.gnz_no).first()
        if thisuser is None:
            thisuser = User.query.filter(User.fullname==self.fullname).first()
        if thisuser is not None:
            self.__user_id = thisuser.id
        # Find the link to pilots
        thispilot = Pilot.query.filter(Pilot.gnz_no==self.gnz_no).first()
        if thispilot is None:
            thispilot = Pilot.query.filter(Pilot.fullname==self.fullname).first()
        if thispilot is not None:
            self.__pilot_id = thispilot.id

    def __medical_due(self):
        # ONe is required only if QGP and wanting to carry passengers.
        QGP = MemberTrans.query.filter(MemberTrans.memberid==self.id). \
                    filter(MemberTrans.transtype=='RTG'). \
                    filter(MemberTrans.transsubtype=='QGP').first()
        if QGP is None:
            return None
        last_medical = MemberTrans.query.filter(MemberTrans.memberid == self.id). \
            filter(MemberTrans.transtype == 'MD'). \
            order_by(MemberTrans.transdate.desc()).first()
        if last_medical is None:
            return datetime.date.today()
        else:
            age = relativedelta(datetime.date.today(), self.__mbr_row.dob).years
            if age > 39:
                return last_medical.transdate + relativedelta(years=2)
            else:
                return last_medical.transdate + relativedelta(years=5)

    def __bfr_due(self):
        # todo: handle those who have not yet had one.
        bfr = MemberTrans.query.filter(MemberTrans.memberid==self.id). \
                    filter(MemberTrans.transtype=='BFR').\
                    order_by(MemberTrans.transdate.desc()).first()
        icr = MemberTrans.query.filter(MemberTrans.memberid==self.id). \
                    filter(MemberTrans.transtype=='ICR').\
                    order_by(MemberTrans.transdate.desc()).first()
        if icr is None:
            return bfr.transdate
        if bfr.transdate > icr.transdate:
            return bfr.transdate + relativedelta(years=2)
        else:
            return icr.transdate + relativedelta(years=2)

    def __currency_dict(self):
        rtndict = {'totalmins':0,
                   'totalflts':0,
                   'last90mins':0,
                   'last90flts':0,
                   'last12mins':0,
                   'last12flts':0,
                   'instmins':0,
                   'instflts':0,
                   'inst12mins':0,
                   'inst12flts':0}
        flts = Flight.query.filter((Flight.pic == self.fullname)| (Flight.p2 == self.fullname)).all()
        for f in flts:
            rtndict["totalmins"] += f.glider_mins()
            rtndict["totalflts"] += 1
            if f.flt_date + relativedelta(days=90) >= datetime.date.today():
                rtndict["last90mins"] += f.glider_mins()
                rtndict["last90flts"] += 1
            if f.flt_date + relativedelta(months=12) >= datetime.date.today():
                rtndict["last12mins"] += f.glider_mins()
                rtndict["last12flts"] += 1
            if self.__mbr_row.instructor:
                thisac = Aircraft.query.filter(Aircraft.regn==f.ac_regn).first()
                if thisac is not None:
                    if thisac.seat_count == 2 and f.pic == self.fullname:
                        rtndict["instmins"] += f.glider_mins()
                        rtndict["instflts"] += 1
                        if f.flt_date + relativedelta(months=12) >= datetime.date.today():
                            rtndict["inst12mins"] += f.glider_mins()
                            rtndict["inst12flts"] += 1
        return rtndict







