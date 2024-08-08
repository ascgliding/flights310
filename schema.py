import decimal

import sqlalchemy.exc
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

from asc import db

# Decimal support:
from sqlalchemy import Integer, ForeignKey
from decimal import Decimal
from sqlalchemy.orm import relationship
import sqlalchemy.types as types
from decimal import *
import re


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
    cache_ok = False

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


class SqliteDecHrs(types.TypeDecorator):
    impl = Integer

    def __init__(self):
        types.TypeDecorator.__init__(self)

    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, datetime.timedelta):
                return value.total_seconds() / 60
            if isinstance(value, int):
                # The passed value is already a number of hours
                value = int(value * 60)
                return value
            if isinstance(value, float) or isinstance(value, Decimal):
                return round(value * 60)
            if isinstance(value, str):
                # see if we can convert it to a number:
                try:
                    dechrs = float(value)
                    return round(float(value) * 60)
                except Exception as e:
                    pass  # If the coversion fails then try converting from hrs:mins
                # IT can only contain numbers or ":"
                if re.match("[\d:\s]+$", value) is None:
                    # does not look like a valid time
                    # raise sqlalchemy.exc.DataError("Not a valid time")
                    # raise ValueError("Not a valid time")
                    return None
                # Now convert to a time
                bits = value.split(':')
                hrs = int(bits[0])
                if len(bits) > 1:  # Occasionally, only hrs iss specified
                    mins = int(bits[1])
                else:
                    mins = 0
                return (hrs * 60) + mins
        return value

    # def process_result_value(self, value, dialect):
    #     if value is not None:
    #         #value = datetime.timedelta(minutes=value)
    #         #value = value / 60
    #     return value


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True, comment='Name the user will login with')
    fullname = db.Column(db.String, comment='Users full name')
    email = db.Column(db.String, comment='Users email address')
    administrator = db.Column(db.Boolean, comment='Set if a sysadmin', default=False)
    authenticated = db.Column(db.Boolean, comment='True if user is logged in', default=False)
    gnz_no = db.Column(db.Integer, comment='GNZ No', default=False)
    password_hash = db.Column(db.String, comment="Hashed password")
    approved = db.Column(db.Boolean, comment='True if user has been approved', default=False)
    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return "(" + str(self.id) + ") " + self.name

    def __str(self):
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
    pic = db.Column(db.String, comment='Name of Pilot in charge')
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
        if key == 'ac_regn':
            if value.strip().upper()[0] != 'G' and value.strip().upper() != 'TUG ONLY':
                raise SchemaError('The Glider Regn must start with a "G". Do you mean TUG ONLY?')
        return value.strip().upper()

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

    def __repr__(self):
        return "(" + str(self.id) + ") Flight"

    def __str(self):
        return str(id)


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
    accts_cust_code = db.Column(db.String, comment='Customer code in accounting system')
    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    @db.validates('code')
    def convert_upper(self, key, value):
        return value.upper()

    def __repr__(self):
        return "(" + str(self.id) + ") " + self.fullname

    def __str(self):
        return self.fullname

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
    type = db.Column(db.String, comment="Type/Model e.g. Ka6CR")

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
    owner = db.Column(db.String, comment="Aircraft Owner")

    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    @db.validates('regn')
    def convert_upper(self, key, value):
        return value.upper()

    def __repr__(self):
        return "(" + str(self.id) + ") " + self.regn

    def __str(self):
        return self.regn


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

    def __repr__(self):
        return "(" + str(self.id) + ") " + self.firstname + " " + self.surname

    def __str(self):
        return self.firstname + " " + self.surname


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

    def __repr__(self):
        return self.transtype + '/' + self.transdate.strftime('%d-%m-%Y')


class Roster(db.Model):
    __tablename__ = "roster"

    id = db.Column(db.Integer, db.Sequence('roster_id_seq'), primary_key=True)
    roster_date = db.Column(db.Date, comment='The Roster date', default=datetime.date.today())
    roster_inst = db.Column(db.String, comment='Name of Duty Instructor')
    roster_tp = db.Column(db.String, comment='Name of Duty Tow Pilot')
    roster_dp = db.Column(db.String, comment='Name of Duty Pilot')

    def __str__(self):
        return 'Roster ' + datetime.date.strftime(self.roster_date, "%Y-%m-%d")

    def __repr__(self):
        return 'Roster ' + datetime.date.strftime(self.roster_date, "%Y-%m-%d")


#
# Maintenance Database
#


class Meters(db.Model):
    __tablename__ = "meters"

    id = db.Column(db.Integer, db.Sequence('meters_id_seq'), primary_key=True)
    meter_name = db.Column(db.String, comment='Meter Name', nullable=False, unique=True)
    # The uom has a big impact on how the meter readings are stored.
    # Note that Decimal hours is a qty.  Hours is stored as a total number of minutes
    uom = db.Column(db.Enum('Time', 'Qty'), default='Time', comment="Unit of Measure")

    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    def __str__(self):
        return self.meter_name

    def __repr__(self):
        return "(" + str(self.id) + ") "+ self.meter_name + "/" + self.uom


class Tasks(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, db.Sequence('tasks_id_seq'), primary_key=True)
    task_description = db.Column(db.String, comment='The description of the task', nullable=False,
                                 unique=True)

    task_basis = db.Column(db.Enum('Calendar', 'Meter'),
                           comment='Is this task Date based task or based on a meter reading')

    task_calendar_uom = db.Column(db.Enum('Years', 'Months', 'Days'),
                                  comment='Uom for calendar based tasks')
    task_calendar_period = db.Column(db.Integer,
                                     comment='The number of days, months or years as appropriate')

    task_meter_id = db.Column(db.Integer, ForeignKey(Meters.id), comment="Meter id")
    std_meter_rec = relationship("Meters")

    # Note that where a task is based on a meter that is time based then the increment
    # is ALWAYS in hours.  Not Minutes.
    task_meter_period = db.Column(db.Integer, comment='The Incremental value for the task')
    task_meter_note = db.Column(db.String, comment='Any note related to the meter reading.')

    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    def __str__(self):
        return self.task_description

    def __repr__(self):
        return "(" + str(self.id) + ") "+ self.task_description + "/" + self.task_basis

    @property
    def recurrence_description(self):  # -> str:
        rtnval = "No Recurrence"
        if self.task_basis == 'Calendar':
            rtnval = "Every " + str(self.task_calendar_period) + " " \
                     + (self.task_calendar_uom or 'No unit defined')
            if self.task_meter_id is not None:
                rtnval = rtnval + " or "
                # m = Meters.query.filter_by(id=self.task_meter_id).first()
                # rtnval = rtnval + "Every " + str(self.task_meter_period) + " " + m.meter_name + \
                #          "(" + m.uom + ")"
                rtnval = rtnval + "Every " + str(self.task_meter_period) + " " + str(self.std_meter_rec) + \
                         "(" + self.std_meter_rec.uom + ")"
        if self.task_basis == 'Meter':
            # m = Meters.query.filter_by(id=self.task_meter_id).first()
            # rtnval = "Every " + str(self.task_meter_period) + " " + m.meter_name + \
            #          " (" + m.uom + ")"
            m = Meters.query.filter_by(id=self.task_meter_id).first()
            rtnval = "Every " + str(self.task_meter_period) + " " + str(self.std_meter_rec) + \
                     " (" + self.std_meter_rec.uom + ")"
        return rtnval

    # @property
    # def std_meter_rec(self):
    #     return Meters.query.filter_by(id=self.task_meter_id).first()


class ACMeters(db.Model):
    __tablename__ = 'acmeters'

    id = db.Column(db.Integer, db.Sequence('acmeters_id_seq'), primary_key=True)
    ac_id = db.Column(db.Integer, ForeignKey(Aircraft.id), comment="Aircraft for this meter")
    aircraft_rec = relationship("Aircraft")
    meter_id = db.Column(db.Integer, ForeignKey(Meters.id), comment="Meter id")
    std_meter_rec = relationship("Meters")
    meter_reset_date = db.Column(db.Date, comment="The date the meter was changed or reset")
    meter_reset_value = db.Column(SqliteDecimal(10, 2),
                                  comment="The value of the new meter at replacement", default=0)
    # In some cases, at data entry we will want the user to enter the difference as with the
    # number of landings but in other cases we will want to enter the actual meter reading, as
    # with the tacho
    entry_prompt = db.Column(db.String, comment='Text to appear as data entry prompt',
                             default='Enter Value', )
    entry_method = db.Column(db.Enum('Reading', 'Delta'), default='Reading',
                             comment='Should the user enter the delta or the meter reading')
    entry_uom = db.Column(db.Enum('Decimal Hours', 'Hours:Minutes', 'Qty'))
    auto_update = db.Column(db.Boolean, comment='Automatically update from club flying records',
                            default=False)

    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    def __str__(self):
        return str(self.std_meter_rec.meter_name)

    def __repr__(self):
        return "(" + str(self.id) + ") "+ self.aircraft_rec.regn + "/" \
               + str(self.std_meter_rec)

    # @property
    # def meter_name(self):
    #     thismeter = Meters.query.filter_by(id=self.meter_id).first()
    #     return thismeter.meter_name

    @db.validates('entry_prompt')
    def convert_upper(self, key, value):
        if value is None:
            raise SchemaError('The entry prompt must not be empty')
        if len(value) == 0:
            raise SchemaError('The entry prompt must not be empty')
        return value

class ACTasks(db.Model):
    __tablename__ = 'actasks'

    id = db.Column(db.Integer, db.Sequence('maintschedule_id_seq'), primary_key=True)
    ac_id = db.Column(db.Integer, ForeignKey(Aircraft.id), comment="Aircraft for this meter")
    aircraft_rec = relationship("Aircraft")
    task_id = db.Column(db.Integer, ForeignKey(Tasks.id), comment="Required Task")
    std_task_rec = relationship("Tasks")
    last_done = db.Column(db.Date)
    last_done_reading = db.Column(SqliteDecimal(10, 2),
                                  comment='The meter reading when this task was last done')
    estimate_days = db.Column(db.Integer, comment='The number of days to use for an average',
                              default=90)
    due_basis_date = db.Column(db.Date, default=None,
                            comment="Override due basis if NOT based on the last done date")
    due_basis_reading =  db.Column(SqliteDecimal(10,2), default=None,
                            comment="Override due basis if NOT based on the last done reading")

    warning_days = db.Column(db.Integer,
        comment="The number of days before the due date in which a warning will be emailed")
    warning_email = db.Column(db.String,
        comment=" space delimited list of email addresses that a warning will be sent to")
    note = db.Column(db.String, comment="Any Note related to this task")

    # For the purposes of having a separate counter in the logbook:
    logbook_include = db.Column(db.Boolean, default=False,
                                comment='Include as Logbook Column')
    logbook_column_title = db.Column(db.String,
                                     comment='The column title to appear in the logbook')
    #  People will not have all the readings so there needs to be a starting reference date and value
    # The date must be a date for which there is at least one reading
    logbook_start_date = db.Column(db.Date,
                                   comment='A reference date for the starting value')
    logbook_start_value = db.Column(SqliteDecimal(10,2),
                                    comment='The starting value')

    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    def __str__(self):
        return str(self.std_task_rec)  # which will return the __str__ of that record.

    def __repr__(self):
        return "(" + str(self.id) + ") "+ self.aircraft_rec.regn + "/" \
               + str(self.std_task_rec) + ' Last Done:' + str(self.last_done)

    @property
    def ac_meter_rec(self):
        # thistask = Tasks.query.get(self.task_id)
        # if thistask is None:
        #     raise AttributeError('Invalid task on AC Task')
        # if thistask.task_meter_id is not None:
        #     thismeter = Meters.query.get(thistask.task_meter_id)
        #     return ACMeters.query.filter_by(ac_id=self.ac_id).filter_by(meter_id=thismeter.id).first()
        # else:
        #     return None
        thistask = self.std_task_rec
        if thistask is None:
            raise AttributeError('Invalid task on AC Task')
        if thistask.task_meter_id is not None:
            thismeter = thistask.std_meter_rec
            return ACMeters.query.filter_by(ac_id=self.ac_id).filter_by(meter_id=thismeter.id).first()
        else:
            return None


    # @property
    # def std_task_rec(self):
    #     return Tasks.query.get(self.task_id)


class MeterReadings(db.Model):
    __tablename__ = 'meterreadings'

    id = db.Column(db.Integer, db.Sequence('meterreadings_id_seq'), primary_key=True)
    ac_id = db.Column(db.Integer, ForeignKey(Aircraft.id), comment="Aircraft for this meter")
    aircraft_rec = relationship("Aircraft")
    meter_id = db.Column(db.Integer, ForeignKey(Meters.id), comment="Meter id")
    std_meter_rec = relationship("Meters")
    reading_date = db.Column(db.Date, comment='The time this meter reading was recorded',
                             default=datetime.datetime.now)
    # Where the uom is Qty, then this is the count (e.g. Landings)
    # Where the uom is Hours then this is the number of MINUTES.
    meter_reading = db.Column(SqliteDecimal(10, 2), comment='The meter reading at the time',
                              nullable=False)
    meter_delta = db.Column(SqliteDecimal(10, 2),
                            comment='The difference between this and the last reading')
    note = db.Column(db.String, comment="Any Note related to this reading, or this date.")

    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    def __repr__(self):
        if self.std_meter_rec is not None:
            return self.std_meter_rec.uom  + \
                ":" + str(datetime.date.strftime(self.reading_date,"%a %d %b %Y")) + \
                ":" + str(self.meter_reading)
        else:
            return ''


    def __str__(self):
        if self.std_meter_rec.uom == 'Qty':
            return datetime.date.strftime(self.reading_date,"%a %d %b %Y") \
                   + " : " + str(self.meter_reading) \
                   + " (" + str(self.std_meter_rec) + ")"
        else: # Must be time
            return datetime.date.strftime(self.reading_date, "%a %d %b %Y") \
                   + " : " + str(Decimal(self.meter_reading / 60).quantize(Decimal('.01'))) \
                   + " (" + str(self.std_meter_rec) + ")"

    # You will need to cognizant that the reading is in hours
    @property
    def Hours(self) -> Decimal:
        if self.std_meter_rec.uom == 'Qty':
            return None
        if self.meter_reading is None:
            return 0
        else:
            return Decimal(self.meter_reading / 60).quantize(Decimal('.01'))

    @property
    def HrsMinsTD(self) -> datetime.timedelta:
        if self.std_meter_rec.uom == 'Qty':
            return None
        if self.meter_reading is None:
            return datetime.timedelta(minutes=0)
        else:
            return datetime.timedelta(minutes=int(self.meter_reading))
        
    @property
    def HrsMins(self) -> str:
        if self.std_meter_rec.uom == 'Qty':
            return None
        if self.meter_reading is None:
            return "0"
        hrs = int(self.meter_reading / 60)
        mins = int(self.meter_reading - (hrs * 60))
        return str(hrs) + ':' + str(mins).zfill(2)

    @property
    def formatted_meter_reading(self) -> str:
        rtnstr = ''
        if self.meter_reading is None:
            return ''
        try:
            thisacmeter = db.session.query(ACMeters) \
                .filter(ACMeters.ac_id==self.ac_id) \
                .filter(ACMeters.meter_id==self.meter_id) \
                .first()
            if thisacmeter.entry_uom == 'Qty':
                return str(self.meter_reading)
            elif thisacmeter.entry_uom == 'Hours:Minutes':
                return str(int(self.meter_reading / 60)) + ":"  + str(int(self.meter_reading % 60))
            else:
                return str(Decimal(self.meter_reading/60).quantize(Decimal('.01')))
        except Exception as e:
            return str(self.meter_reading) + "(err)" + str(e)

class ACMaintHistory(db.Model):
    __tablename__ = 'acmainthistory'

    id = db.Column(db.Integer, db.Sequence('mainthistory_id_seq'), primary_key=True)
    ac_id = db.Column(db.Integer, ForeignKey(Aircraft.id), comment="Aircraft for this record")
    aircraft_rec = relationship("Aircraft")
    # There should be a standard task called AdHoc Work
    task_id = db.Column(db.Integer, ForeignKey(ACTasks.id), comment="Required Task")
    actask_rec = relationship("ACTasks")
    #  Note that the task description need not be a specfic task
    task_description = db.Column(db.String, comment="Description of the work undertaken")
    meter_reading = db.Column(SqliteDecimal(10, 2), comment="Meter reading at time of event")
    history_date = db.Column(db.Date, comment='The time this event occurred',
                             default=datetime.datetime.now)

    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    def __str__(self):
        return task_description[1:60]

    def __repr__(self):
        # return "(" + str(self.id) + ") " + (self.aircraft_rec.regn or 'None') + "/" \
        return "(" + str(self.id) + ") " \
               + self.task_description[1:60]

    @property
    def formatted_meter_reading(self) -> str:
        rtnstr = ''
        if self.meter_reading is None:
            return ''
        try:
            thisacmeter = db.session.query(ACMeters) \
                .filter(ACMeters.ac_id==self.ac_id) \
                .filter(ACMeters.meter_id==self.actask_rec.std_task_rec.task_meter_id) \
                .first()
            if thisacmeter.entry_uom == 'Qty':
                return str(self.meter_reading)
            elif thisacmeter.entry_uom == 'Hours:Minutes':
                return str(int(self.meter_reading / 60)) + ":"  + str(int(self.meter_reading % 60))
            else:
                return str(Decimal(self.meter_reading / 60).quantize(Decimal('.01')))
        except Exception as e:
            return str(self.meter_reading) + "(err)" + str(e)

class ACMaintUser(db.Model):
    __tablename__ = 'acmaintuser'

    id = db.Column(db.Integer, db.Sequence('mainthistory_id_seq'), primary_key=True)
    ac_id = db.Column(db.Integer, ForeignKey(Aircraft.id), comment="Aircraft for this record")
    aircraft_rec = relationship("Aircraft")
    user_id = db.Column(db.Integer, ForeignKey(User.id), comment="User who can maintain")
    user_rec = relationship("User")
    # all - includes standard tasks and meters
    # aircraft - anything to do with this aircraft
    # readings - just enter readings.
    maint_level = db.Column(db.Enum('All', 'Aircraft', 'Readings'), default='Readings',
                            comment='Level of detail allowed')

    def __str__(self):
        return user_rec.name

    def __repr__(self):
        return "(" + str(self.id or 0) + ") "+ str(self.user_rec or self.user_id) + "/" \
                   + str(self.aircraft_rec or self.ac_id)

