from werkzeug.security import generate_password_hash, check_password_hash
import datetime

from asc import db

# Decimal support:
from sqlalchemy import Integer, ForeignKey
from decimal import Decimal
from sqlalchemy.orm import relationship
import sqlalchemy.types as types
from decimal import *


class SchemaError(Exception):
    pass


# Here are two approaches for dealing with decimals.
# the problem of the first one is that storing it in the db as a string will cause
# big problems with sorting and comparison.


# class SqliteNumeric(types.TypeDecorator):
#     impl = types.db.String
# 
#     def load_dialect_impl(self, dialect):
#         return dialect.type_descriptor(types.VARCHAR(100))
# 
#     def process_bind_param(self, value, dialect):
#         return str(value)
# 
#     def process_result_value(self, value, dialect):
#         return D(value)

# This approach stores all decimals in the db as integers and converts in the class
# this fixes the sorting and comparison issues.

class SqliteDecimal(types.TypeDecorator):
    # This TypeDecorator use Sqlalchemy Integer as impl. It converts Decimals
    # from Python to Integers which is later stored in Sqlite database.
    impl = Integer

    def __init__(self, precision, scale):
        # Precision is never used, but added just to keep consistency with
        # other decimal implementations.
        # It takes a 'scale' parameter, which specifies the number of digits
        # to the right of the decimal point of the number in the column.
        types.TypeDecorator.__init__(self)
        self.scale = scale
        self.multiplier_int = 10 ** self.scale

    def process_bind_param(self, value, dialect):
        # e.g. value = Column(SqliteDecimal(2)) means a value such as
        # Decimal('12.34') will be converted to 1234 in Sqlite
        if value is not None:
            value = int(Decimal(value) * self.multiplier_int)
        return value

    def process_result_value(self, value, dialect):
        # e.g. Integer 1234 in Sqlite will be converted to Decimal('12.34'),
        # when query takes place.
        if value is not None:
            value = Decimal(value) / self.multiplier_int
        return value


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True, comment='Name the user will login with')
    fullname = db.Column(db.String, comment='Users full name')
    email = db.Column(db.String, comment='Users email address')
    administrator = db.Column(db.Boolean, comment='Set if a sysadmin', default=False)
    authenticated = db.Column(db.Boolean, comment='True if user is logged in', default=False)
    gnz_no = db.Column(db.Integer, comment='GNZ No',default=False)
    password_hash = db.Column(db.String, comment="Hashed password")
    approved = db.Column(db.Boolean, comment='True if user has been approved', default=False)
    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return self.fullname

    def __init__(self, name=None):
        self.name = name
        self.fullname = None
        self.email = None
        self.authenticated = False
        self.administrator = False
        thisuser = User.query.filter_by(name=name).one_or_none()
        if thisuser is not None:
            self.name = thisuser.name
            self.fullname = thisuser.fullname
            self.email = thisuser.email
            self.administrator = thisuser.administrator
            self.authenticated = thisuser.authenticated

    def set_password(self, plaintext_password):
        self.password_hash = generate_password_hash(plaintext_password)

    def is_correct_password(self, plaintext_password):
        return check_password_hash(self.password_hash, plaintext_password)

    @property
    def is_authenticated(self):
        """Return True if the user is authenticated."""
        if self.approved:
            return self.authenticated
        else:
            return False

    @property
    def is_approved(self):
        return self.approved

    @property
    def is_active(self):
        # TODO: Need to check approved flag
        """Always True, as all users are active."""
        return True

    @property
    def is_anonymous(self):
        """Always False, as anonymous users aren't supported."""
        return False

    def get_id(self):
        """Return the id of a user to satisfy Flask-Login's requirements."""
        # return str(self.id)
        return str(self.name)


class Flight(db.Model):
    __tablename__ = "flights"

    id = db.Column(db.Integer, db.Sequence('flights_id_seq'), primary_key=True)
    flt_date = db.Column(db.Date, comment='The date of this flight', default=datetime.date.today())
    linetype = db.Column(db.String(2), comment="Type of Line - flight or comment.", default="FL")
    pic = db.Column(db.String,  comment='Name of Pilot in charge')
#    pic_gnz_no = db.Column(db.Integer, comment='GNZ No of PIC')
    p2 = db.Column(db.String, comment='Name of second pilot')
#    p2_gnz_no = db.Column(db.Integer, comment='GNZ No of P2')
    ac_regn = db.Column(db.String, comment='Aircraft Registration')
    tow_pilot = db.Column(db.String, comment='Tow Pilot')
    tug_regn = db.Column(db.String, comment='Tug Registration')
    takeoff = db.Column(db.Time, comment='Takeoff Time')
    tug_down = db.Column(db.Time, comment='Tug Landing Time')
    landed = db.Column(db.Time, comment='Landed Time')
    release_height = db.Column(db.Integer, comment='Altitude at Release')
    payer = db.Column(db.String, comment='Person Paying for flight')
    tow_charge = db.Column(SqliteDecimal(10, 2), nullable=False, default=0)
    glider_charge = db.Column(SqliteDecimal(10, 2), nullable=False, default=0)
    other_charge = db.Column(SqliteDecimal(10, 2), nullable=False, default=0)
    payment_note = db.Column(db.String, comment="Payment Note")
    general_note = db.Column(db.String, comment="General Note")
    accts_export_date = db.Column(db.Date, comment='The date this flight was exported')
    paid = db.Column(db.Boolean, comment='True indicates flight has been paid', default=False)

    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    # def get_pic_gnz_no(self):
    #     thispilot = Pilot.query.filter_by(fullname=self.pic).first()
    #     print(thispilot)
    #     print(type(thispilot))
    #     if thispilot is None:
    #         return None
    #     else:
    #         return thispilot.gnz_no
    #
    # def get_p2_gnz_no(self):
    #     thispilot = Pilot.query.filter_by(fullname=self.p2).first()
    #     if thispilot is None:
    #         return None
    #     else:
    #         return thispilot.gnz_no
    #
    # def get_payer_gnz_no(self):
    #     thispilot = Pilot.query.filter_by(fullname=self.payer).first()
    #     if thispilot is None:
    #         return None
    #     else:
    #         return thispilot.gnz_no

    def pic_rec(self):
        return Pilot.query.filter_by(fullname=self.pic).first()

    def p2_rec(self):
        return Pilot.query.filter_by(fullname=self.p2).first()

    def payer_rec(self):
        return Pilot.query.filter_by(fullname=self.payer).first()

    def aircraft_rec(self):
        return Aircraft.query.filter_by(regn=self.ac_regn).first()

    def tug_rec(self):
        return Aircraft.query.filter_by(regn=self.tug_regn).first()

    def total_charge(self):
        return self.tow_charge + self.glider_charge + self.other_charge

    def tow_mins(self) -> Decimal:
        if self.tug_down is None:
            return 0
        else:
            return Decimal((datetime.datetime.combine(self.flt_date, self.tug_down) -
                    datetime.datetime.combine(self.flt_date, self.takeoff)).seconds / 60)

    def glider_mins(self) -> Decimal:
        if self.landed is None:
            return 0
        else:
            return Decimal((datetime.datetime.combine(self.flt_date, self.landed) -
                    datetime.datetime.combine(self.flt_date, self.takeoff)).seconds / 60)

    @db.validates('ac_regn', 'tug_regn', "tow_pilot")
    def convert_upper(self, key, value):
        return value.upper()

    @db.validates('linetype')
    def validate_type(self, key, value):
        # this is better than a check contraint because if we want ot change it we do not need to rebuild the table
        if value not in ['FL', 'NT']:
            raise SchemaError("Invalid Line Type")
        return value

    @db.validates('tug_down', 'landed')
    def validate_type(self, key, value):
        # this is better than a check contraint because if we want ot change it we do not need to rebuild the table
        if value is not None:
            if self.takeoff is None:
                raise SchemaError("You cannot record a landing before a takeoff.")
            if self.takeoff > value:
                raise SchemaError("You cannot record a landing before a takeoff.")
        return value


class Pilot(db.Model):
    __tablename__ = "pilots"
    id = db.Column(db.Integer, db.Sequence('pilot_id_seq'), primary_key=True)
    code = db.Column(db.String, nullable=False, unique=True,
                     comment='GNZ Id')
    fullname = db.Column(db.String, nullable=False, comment='Users full name')
    email = db.Column(db.String, comment='Users email address')
    userid = db.Column(db.Integer, comment="If non null then a valid user id")
    towpilot = db.Column(db.Boolean, comment="Select to include in tow pilot list")
    instructor = db.Column(db.Boolean, comment="Select to mark as instructor")
    bscheme = db.Column(db.Boolean, comment='Set if Pilot participates in B Scheme', default=True)
    yg_member = db.Column(db.Boolean, comment='Set if Pilot is a Youth Glide member', default=True)
    gnz_no = db.Column(db.Integer, comment="GNZ Number")
    accts_cust_code = db.Column(db.String,comment='Customer code in accounting system')
    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    @db.validates('code')
    def convert_upper(self, key, value):
        return value.upper()


class Slot(db.Model):
    __tablename__ = "slots"

    id = db.Column(db.Integer, db.Sequence('slots_id_seq'), primary_key=True)
    userid = db.Column(db.Integer, comment="If non null then a valid user id")
    slot_type = db.Column(db.String, comment="The type of record", nullable=False)
    slot_key = db.Column(db.String, comment="The specific key for this type", nullable=False)
    slot_desc = db.Column(db.String, comment="A generic Description")
    slot_data = db.Column(db.String, comment="Any kind of data that is converted when used")

    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    @db.validates('slot_type', 'slot_key')
    def convert_upper(self, key, value):
        return value.upper()


class Aircraft(db.Model):
    __tablename__ = "aircraft"

    id = db.Column(db.Integer, db.Sequence('aircraft_id_seq'), primary_key=True)
    regn = db.Column(db.String, comment="Aircraft Regsiration")
    type = db.Column(db.String, comment="Type")


    launch = db.Column(db.Boolean, comment='Set if Regn is a launch method', default=False)
    # each of the following rates are calculated and the TOTAL returned
    rate_per_hour = db.Column(SqliteDecimal(10, 2), nullable=False, default=0)
    #  flat_rate_per_launch could be used for winch launches
    flat_charge_per_launch = db.Column(SqliteDecimal(10, 2), nullable=False, default=0)
    # rate for height based charging
    rate_per_height = db.Column(SqliteDecimal(10, 2), nullable=False, default=0)
    # height used for rate based charging
    per_height_basis = db.Column(SqliteDecimal(10, 2), nullable=False, default=0)
    # Tug only per hour
    rate_per_hour_tug_only = db.Column(SqliteDecimal(10, 2), nullable=False, default=0)
    bscheme = db.Column(db.Boolean, comment='Set if a/c participates in B Scheme', default=True)
    default_launch = db.Column(db.String, comment="Default Launch Method")
    default_pilot = db.Column(db.String, comment="Default Pilot")
    seat_count = db.Column(db.Integer, comment="Seat Count")
    accts_income_acct = db.Column(db.String, comment="GL income account")
    accts_income_tow = db.Column(db.String, comment="GL income account - aerotow")
    owner = db.Column(db.String,comment = "Aircraft Owner")

    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)


    @db.validates('regn')
    def convert_upper(self, key, value):
        return value.upper()


class Member(db.Model):
    __tablename__ = "members"

    id = db.Column(db.Integer, db.Sequence('member_id_seq'), primary_key=True)
    active = db.Column(db.Boolean, comment="Active members appear on the membership list")
    gnz_no = db.Column(db.Integer)
    type = db.Column(db.Enum('FLYING', 'JUNIOR', 'VFP BULK', 'SOCIAL'), comment="Membership Type")
    surname = db.Column(db.String, comment="Members Surname")
    firstname = db.Column(db.String, comment="Members Firstname")
    rank = db.Column(db.String, comment="To be checked against slots")
    note = db.Column(db.Text)
    email_address = db.Column(db.String, comment="Email Address")
    dob = db.Column(db.Date)
    phone = db.Column(db.String)
    mobile = db.Column(db.String)
    address_1 = db.Column(db.String)
    address_2 = db.Column(db.String)
    address_3 = db.Column(db.String)
    service = db.Column(db.Boolean)
    roster = db.Column(db.Enum('D', 'T', "I", "IT", 'D', 'N'))
    email_2 = db.Column(db.String)
    phone2 = db.Column(db.String)
    mobile2 = db.Column(db.String)
    committee = db.Column(db.Boolean)
    instructor = db.Column(db.Boolean)
    tow_pilot = db.Column(db.Boolean)
    oo = db.Column(db.Boolean)
    duty_pilot = db.Column(db.Boolean)
    nok_name = db.Column(db.String)
    nok_rship = db.Column(db.String)
    nok_phone = db.Column(db.String)
    nok_mobile = db.Column(db.String)
    glider = db.Column(db.String)
    transactions = relationship("MemberTrans", cascade="all,delete-orphan")

    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)


class MemberTrans(db.Model):
    __tablename__ = "membertrans"

    id = db.Column(db.Integer, db.Sequence('member_id_seq'), primary_key=True)
    memberid = db.Column(db.Integer, ForeignKey('members.id'), comment="Must match member id")
    transdate = db.Column(db.Date, comment="Effect Date of Transaction")
    transtype = db.Column(db.Enum('IR', 'MF', 'DCG', 'MD', 'ICR', 'RTG', 'BFR', 'NOT'),
                          comment="to match against slots")
    transsubtype = db.Column(db.String, comment="to match against slots")
    transnotes = db.Column(db.Text)

    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    def __init__(self, member):
        """ This is only called for a new transaction"""
        self.memberid = member
        self.transdate = datetime.date.today()
        self.transsubtype = ''

class Roster(db.Model):
    __tablename__ = "roster"

    id = db.Column(db.Integer, db.Sequence('roster_id_seq'), primary_key=True)
    roster_date = db.Column(db.Date, comment='The Roster dat', default=datetime.date.today())
    roster_inst = db.Column(db.String,  comment='Name of Duty Instructor')
    roster_tp = db.Column(db.String,  comment='Name of Duty Tow Pilot')
    roster_dp = db.Column(db.String,  comment='Name of Duty Pilot')
