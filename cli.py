# import sqlite3
import os
import click
from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy import Column, Integer, Boolean, Date, String, Time, DateTime, Sequence
from sqlalchemy.orm import validates, sessionmaker
import sqlalchemy.exc
# import pwd
# import logging
# from logging.handlers import RotatingFileHandler
import datetime
from asc.schema import *
import decimal

import csv

from asc import db, create_app
from asc.common import *

# In order to trap errors from the engine
import sqlalchemy.exc

app = create_app()
log = app.logger

# This is a completely separate and nothing to do with flask or the web application.

# Base = declarative_base()
#
# class User(Base):
#
#     __tablename__ = 'users'
#
#     id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
#     name = Column(String, nullable=False, unique=True, comment='Name the user will login with')
#     fullname = Column(String, nullable=False, comment='Users full name')
#     email = Column(String, comment='Users email address')
#     administrator = Column(Boolean, comment='Set if a sysadmin')
#     inserted = Column(DateTime, default=datetime.datetime.now)
#     updated= Column(DateTime, onupdate=datetime.datetime.now)
#
#     def __repr__(self):
#         return self.fullname
#
#
# class Flight(Base):
#
#     __tablename__ = "flights"
#
#     id = Column(Integer, Sequence('flights_id_seq'), primary_key=True)
#     pic = Column(String, nullable=False, comment='Name of Pilot in charge')
#     p2 =  Column(String, comment='Name of send pilot')
#     ac_regn = Column(String, comment='Aircraft Registration')
#     tug_regn = Column(String, comment='Tug Registration')
#     takeoff = Column(DateTime, default=datetime.datetime.now, comment='Takeoff Time')
#     tug_down = Column(DateTime, comment='Tug Landing Time')
#
#     inserted = Column(DateTime, default=datetime.datetime.now)
#     updated= Column(DateTime, onupdate=datetime.datetime.now)
#
#
#     @validates('ac_regn', 'tug_regn')
#     def convert_upper(self, key, value):
#         return value.upper
#

# class UserIDFilter(logging.Filter):
#     """
#     This is a filter which injects contextual information into the log.
#     """
#     # The standard logger does not include an attribute for the user name.  This is done by adding this function
#     def filter(record):
#         record.user_id = pwd.getpwuid(os.getuid()).pw_name
#         return True



# def dict_factory(cursor, row):
#     d = {}
#     for idx, col in enumerate(cursor.description):
#         d[col[0]] = row[idx]
#     return d
#
#
# def get_db():
#     db = sqlite3.connect(
#             os.path.join(os.getcwd(),"instance/expenses.sqlite"),
#             detect_types=sqlite3.PARSE_DECLTYPES
#         )
#     db.row_factory = dict_factory
#     sqlite3.register_adapter(bool, int)
#     sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
#     return db


# def close_db(e=None):
#     db = g.pop('db', None)
#
#     if db is not None:
#         db.close()
#
# def establishlogging(logfile, loglevel='INFO', logclear=False):
#     logger = logging.getLogger('cli')
#     loghandler = RotatingFileHandler(logfile, maxBytes=1000000, backupCount=3)
#     if loglevel == 'CRITICAL':
#         loghandler.setLevel(logging.CRITICAL)
#     elif loglevel == 'ERROR':
#         loghandler.setLevel(logging.ERROR)
#     elif loglevel == 'WARNING':
#         loghandler.setLevel(logging.WARNING)
#     elif loglevel == 'INFO':
#         loghandler.setLevel(logging.INFO)
#     else:
#         loghandler.setLevel(logging.DEBUG)
#     fmt = '%(asctime)s|%(filename)s|%(funcName)s|%(levelname)s|%(user_id)s|%(message)s'
#     fmt_date = '%Y-%m-%d|%H:%M:%S'
#     loghandler.addFilter(UserIDFilter)
#     formatter = logging.Formatter(fmt, fmt_date)
#     loghandler.setFormatter(formatter)
#     if logclear:
#        loghandler.doRollover()
#     # now establish the logger
#     logger.addHandler(loghandler)



def test_001():
    """Prove the cli interface works"""
    click.echo('If the Cli is working correctly you should see a dump of the first 10 flights:')
    try:
        flights = Flight.query.limit(10).all()
        for f in flights:
            click.echo("{}\t{}\t{}".format(f.id, f.pic, f.takeoff))
        pilots = Pilot.query.limit(2).all()
        for p in pilots:
            click.echo("{}".format(p.fullname))
    except Exception as e:
        click.echo("Error raised (in test_001) :{}".format(e))
    click.echo("Test Complete")

def txt2boolean(text):
    if text == 'Y':
        return True
    else:
        return False

def addslot(slottuple, type='RANK'):
    # inpput is a tuble of code and description.
    s = Slot()
    s.slot_type = type
    s.slot_key = slottuple[0]
    s.slot_desc = slottuple[1]
    db.session.add(s)
    db.session.commit()

def periodic_mbr_update():
    click.echo("Updating Member Data")
    if not os.path.exists("membershipdb_members.csv"):
        print("membershipdb_members.csv missing.  Load into parent of instance folder.")
        return
    with open("membershipdb_members.csv", "r", encoding='Latin-1') as d:
        reader = csv.reader(d, delimiter="|")
        readcount = 0
        insertcount = 0
        updatecount = 0
        failedcount = 0
        epinsert = 0
        epupdate = 0
        for r in reader:
            print("Processing GNZ: {} Name {} {}".format(r[1], r[4] , r[3]))
            log.info("Reading {} {} from csv file".format(r[4],r[3]))
            try:
                readcount += 1
                if r[0] == 'Active':  # we have a header record.
                    continue  # skip to next record.
                # We either update or add
                existingmbr = db.session.query(Member).filter(Member.gnz_no == r[1]).all()
                if len(existingmbr) > 0:
                    print(existingmbr[0])
                    print("Member found - update mode")
                    # These are from the membership db spreadsheet columns B-AD.  Without headings.
                    existingmbr[0].active = txt2boolean(r[0])
                    existingmbr[0].type = r[2].upper()
                    existingmbr[0].surname = r[3]
                    existingmbr[0].firstname = r[4]
                    existingmbr[0].rank = r[5].upper()
                    if existingmbr[0].rank == 'ATC':
                        existingmbr[0].rank = 'CDT'
                    existingmbr[0].note = r[6]
                    existingmbr[0].email_address = r[7]
                    if r[8] != '':
                        existingmbr[0].dob = datetime.datetime.strptime(r[8], "%d-%m-%Y").date()
                    existingmbr[0].phone = r[9]
                    existingmbr[0].mobile = r[10]
                    existingmbr[0].address_1 = r[11]
                    existingmbr[0].address_2 = r[12]
                    existingmbr[0].address_3 = r[13]
                    existingmbr[0].service = txt2boolean(r[14])
                    if r[15] in ['I', 'IT', 'D', 'T']:
                        existingmbr[0].roster = r[15]
                    else:
                        existingmbr[0].roster = 'N'
                    existingmbr[0].email_2 = r[16]
                    existingmbr[0].phone2 = r[17]
                    existingmbr[0].mobile2 = r[18]
                    existingmbr[0].committee = txt2boolean(r[19])
                    existingmbr[0].instructor = txt2boolean(r[20])
                    existingmbr[0].tow_pilot = txt2boolean(r[21])
                    existingmbr[0].oo = txt2boolean(r[22])
                    existingmbr[0].duty_pilot = txt2boolean(r[23])
                    existingmbr[0].nok_name = r[24]
                    existingmbr[0].nok_rship = r[25]
                    existingmbr[0].nok_phone = r[26]
                    existingmbr[0].nok_mobile = r[27]
                    existingmbr[0].glider = r[28]
                    db.session.commit()
                    updatecount += 1
                    log.info("Updated Member {} {} ".format(r[4], r[3]))
                else:
                    print("New Member - add mode")
                    m = Member()
                    # These are from the membership db spreadsheet columns B-AD.  Without headings.
                    m.active = txt2boolean(r[0])
                    m.gnz_no = r[1]
                    m.type = r[2].upper()
                    m.surname = r[3]
                    m.firstname = r[4]
                    m.rank = r[5].upper()
                    if m.rank == 'ATC':
                        m.rank = 'CDT'
                    m.note = r[6]
                    m.email_address = r[7]
                    if r[8] != '':
                        m.dob = datetime.datetime.strptime(r[8], "%d-%m-%Y").date()
                    m.phone = r[9]
                    m.mobile = r[10]
                    m.address_1 = r[11]
                    m.address_2 = r[12]
                    m.address_3 = r[13]
                    m.service = txt2boolean(r[14])
                    if r[15] in ['I', 'IT', 'D', 'T']:
                        m.roster = r[15]
                    else:
                        m.roster = 'N'
                    m.email_2 = r[16]
                    m.phone2 = r[17]
                    m.mobile2 = r[18]
                    m.committee = txt2boolean(r[19])
                    m.instructor = txt2boolean(r[20])
                    m.tow_pilot = txt2boolean(r[21])
                    m.oo = txt2boolean(r[22])
                    m.duty_pilot = txt2boolean(r[23])
                    m.nok_name = r[24]
                    m.nok_rship = r[25]
                    m.nok_phone = r[26]
                    m.nok_mobile = r[27]
                    m.glider = r[28]
                    db.session.add(m)
                    db.session.commit()
                    insertcount += 1
                    log.info("New Member Added {} {}".format(r[4], r[3]))
                # Now update the pilots file for NEW pilots only - don't update existing details
                existingpilot = db.session.query(Pilot).filter(Pilot.code == r[1]).all()
                if len(existingpilot) > 0:
                    # check only tow pilot and instructor
                    print("Existing Pilot - update mode")
                    existingpilot[0].instructor = txt2boolean(r[20])
                    existingpilot[0].tow_pilot = txt2boolean(r[21])
                    existingpilot[0].bscheme = txt2boolean(r[0])
                    existingpilot[0].email = r[7]
                    db.session.commit()
                    epupdate += 1
                    log.info("Existing Pilot Updated {} {}".format(r[4], r[3]))
                else:
                    # new pilot
                    print("New Pilot - add mode")
                    np = Pilot()
                    np.code = r[1]
                    np.fullname = r[4] + " " + r[3]
                    np.email = r[7]
                    np.instructor = txt2boolean(r[20])
                    np.tow_pilot = txt2boolean(r[21])
                    np.bscheme = txt2boolean(r[0])
                    db.session.add(np)
                    db.session.commit()
                    epinsert += 1
                    log.info("New Pilot Added {} {} ".format(r[4], r[3]))
            except Exception as e:
                db.session.rollback()
                log.error("Problem occurred with {} {} : {} ".format(r[4], r[3],str(e)))
                print(str(e))
                print(r)
                failedcount += 1
    print(' ')
    print('Member:Read {} Inserted {} Updated {} Failed {}'.format(readcount, insertcount, updatecount, failedcount))
    print('Pilot:Read {} Inserted {} Updated {} Failed {}'.format(readcount, epinsert, epupdate, failedcount))

def add_mbr_data():
    db.create_all()
    click.echo('Loading Mbr Data.')
    Member.__table__.drop(db.engine)
    MemberTrans.__table__.drop(db.engine)
    Member.__table__.create(db.engine)
    MemberTrans.__table__.create(db.engine)
    # Load Ranks
    print("Adding Ranks")
    Slot.query.filter_by(slot_type = 'RANK').delete()
    addslot(('AM', 'Air Marshal'))
    addslot(('GPCAPT', 'Group Captain'))
    addslot(('WGCDR', 'Wing Commander'))
    addslot(('SQNLDR', 'Squandron Leader'))
    addslot(('FLTLT', 'Flight Lietuenant'))
    addslot(('FGOFF', 'Flying Officer'))
    addslot(('PLTOFF', 'Pilot Officer'))
    addslot(('OCDT', 'Officer Cadet'))
    addslot(('WOFF', 'Warrant Officer'))
    addslot(('FSGT', 'Flight Sergeant'))
    addslot(('SGT', 'Sergeant'))
    addslot(('CPL', 'Corporal'))
    addslot(('A/CPL', 'Acting Corporal'))
    addslot(('LAC', 'Leading Aircraftman'))
    addslot(('ACM', 'Airman'))
    addslot(('CIV', 'Civilian'))
    addslot(('JUNIOR', 'Junior Civilian'))
    Slot.query.filter_by(slot_type = 'MEMBERTYPE').delete()
    addslot(('Flying', 'Flying'), 'MEMBERTYPE')
    addslot(('VFP Bulk', 'VFP Bulk'), 'MEMBERTYPE')
    addslot(('Junior', 'Junior'), 'MEMBERTYPE')
    addslot(('Social', 'Social'), 'MEMBERTYPE')
    Slot.query.filter_by(slot_type = 'TRANSTYPE').delete()
    addslot(('BFR', 'BFR'), 'TRANSTYPE')
    addslot(('DCG', 'Date Commenced Gliding'), 'TRANSTYPE')
    addslot(('ICR', 'Instructor Competency Review'), 'TRANSTYPE')
    addslot(('IR', 'Incident Report'), 'TRANSTYPE')
    addslot(('MD', 'Medical'), 'TRANSTYPE')
    addslot(('MF', 'Membership Form'), 'TRANSTYPE')
    addslot(('NOT', 'General Note'), 'TRANSTYPE')
    addslot(('RTG', 'RATING'), 'TRANSTYPE')
    Slot.query.filter_by(slot_type = 'RATING').delete()
    addslot(('AB', 'A Badge'), 'RATING')
    addslot(('BB', 'B Badge'), 'RATING')
    addslot(('BCAT', 'B CAT Instructor'), 'RATING')
    addslot(('CCAT', 'C CAT Instructor'), 'RATING')
    addslot(('FRTO', 'FRTO'), 'RATING')
    addslot(('GC', 'Gold C'), 'RATING')
    addslot(('MG', 'Motor Glider'), 'RATING')
    addslot(('OO', 'OO'), 'RATING')
    addslot(('PAX', 'Passenger'), 'RATING')
    addslot(('QGP', 'QGP'), 'RATING')
    addslot(('SC', 'Silver C'), 'RATING')
    addslot(('SOLO', 'SOLO'), 'RATING')
    addslot(('TP', 'Tow Pilot'), 'RATING')
    addslot(('XC', 'Cross Country'), 'RATING')

    with open("membershipdb_members.csv", "r", encoding='Latin-1') as d:
        reader = csv.reader(d, delimiter="|")
        readcount = 0
        insertcount = 0
        failedcount = 0
        for r in reader:
            try:
                readcount += 1
                m = Member()
                # These are from the membership db spreadsheet columns B-AD.  Without headings.
                m.active = txt2boolean(r[0])
                m.gnz_no = r[1]
                m.type = r[2].upper()
                m.surname = r[3]
                m.firstname = r[4]
                m.rank = r[5].upper()
                if m.rank == 'ATC':
                    m.rank = 'CDT'
                m.note = r[6]
                m.email_address = r[7]
                if r[8] != '':
                    m.dob = datetime.datetime.strptime(r[8], "%d-%m-%Y").date()
                m.phone = r[9]
                m.mobile = r[10]
                m.address_1 = r[11]
                m.address_2 = r[12]
                m.address_3 = r[13]
                m.service = txt2boolean(r[14])
                if r[15] in ['I', 'IT', 'D', 'T']:
                    m.roster = r[15]
                else:
                    m.roster = 'N'
                m.email_2 = r[16]
                m.phone2 = r[17]
                m.mobile2 = r[18]
                m.committee = txt2boolean(r[19])
                m.instructor = txt2boolean(r[20])
                m.tow_pilot = txt2boolean(r[21])
                m.oo = txt2boolean(r[22])
                m.duty_pilot = txt2boolean(r[23])
                m.nok_name = r[24]
                m.nok_rship = r[25]
                m.nok_phone = r[26]
                m.nok_mobile = r[27]
                m.glider = r[28]
                db.session.add(m)
                db.session.commit()
                insertcount += 1
            except Exception as e:
                db.session.rollback()
                print(str(e))
                print(r)
                failedcount += 1
    print(' ')
    print('Read {} Inserted {} Failed {}'.format(readcount,insertcount,failedcount))
    print(' ')
    with open("membershipdb_transactions.csv", "r", encoding='Latin-1') as d:
        reader = csv.reader(d, delimiter="|")
        readcount = 0
        insertcount = 0
        failedcount = 0
        currentmember = 0 # to force first read./
        thismember = None
        for r in reader:
            try:
                readcount += 1
                # get the id
                # if thismember.id != currentmember or readcount == 0:
                thismember = Member.query.filter_by(gnz_no = r[1]).first()
                if thismember is None:
                    print('Unable to find {}'.format(r[1]))
                    failedcount += 1
                else:
                    t = MemberTrans(thismember.id)
#                    t.memberid = thismember.id
                    if r[2] != '':
                        t.transdate = datetime.datetime.strptime(r[2], "%d-%m-%Y").date()
                    t.transtype = r[3]
                    t.transsubtype = r[4]
                    t.transnotes = r[5]
                    db.session.add(t)
                    db.session.commit()
                    insertcount += 1
            except Exception as e:
                print(str(e))
                print(r)
                db.session.rollback()
                failedcount += 1
    print(' ')
    print('Read {} Inserted {} Failed {}'.format(readcount,insertcount,failedcount))
    print(' ')


def csvload():
    db.create_all()
    click.echo('Opened the database.')
    Flight.__table__.drop(db.engine)
    Flight.__table__.create(db.engine)
#    with open("/home/rayb/PycharmProjects/flask31/asc/utilisation_flat_data.csv", "r", encoding='Latin-1') as d:
    with open("utilisation_flat_data.csv", "r", encoding='Latin-1') as d:
        reader = csv.reader(d, delimiter="|")
        readcount = 0
        insertcount = 0
        failedcount = 0
        for r in reader:
            try:
                if readcount % 1000 == 0:
                    print("{} records read".format(readcount))
                readcount += 1
                # if readcount > 500:
                #     break
                # print(r)
                f = Flight()
                f.flt_date = datetime.datetime.strptime(r[0],'%Y-%m-%d').date()
                f.pic = r[1]
                f.p2 = r[2]
                f.takeoff = datetime.datetime.strptime(r[0],'%Y-%m-%d')
                f.takeoff +=  datetime.timedelta(12)
                f.tug_down = f.takeoff + datetime.timedelta(minutes=1)
                f.landed = f.takeoff + datetime.timedelta(minutes=int(r[5]))
                f.takeoff = f.takeoff.time()
                f.tug_down = f.tug_down.time()
                f.landed = f.landed.time()
                f.release_height = r[3]
                f.ac_regn = r[4]
                f.tug_regn = 'IMP'
                f.payment_note = 'Imported'
                try:
                    f.other_charge = decimal.Decimal(r[6])
                except decimal.InvalidOperation:
                    f.other_charge = 0
                db.session.add(f)
                db.session.commit()
                insertcount += 1
            except Exception as e:
                print(str(e))
                print(r)
                failedcount += 1


        print("{} records read, {} inserted, {} failed".format(readcount, insertcount, failedcount))


def add_payers():
    flts = Flight.query.Filter_by(id > 42).all()
    for f in flts:
        if f.payer is None:
            # Tug only - pic pays
            if f.ac_regn == constREGN_FOR_TUG_ONLY:
                f.payer = f.pic
            # no p2 - pic pays
            elif f.p2 is None:
                f.payer = f.pic
            # p2 exists but no rec (e.g. pax) pic pays
            elif f.p2_rec() is None:
                f.payer = f.pic
            # p2 exists but pic is not an instructor - pic pays
            elif not f.p2_rec().instructor:
                f.payer = f.pic
            # must be instructional
            else:
                f.payer = f.p2
            db.session.commit()



def add_demo_data():
    click.echo("Adding Demo Data")
    init_db()
    # for t in db.engine.table_names():
    ray = User('rayb')
    ray.fullname = 'Ray Burns'
    ray.email = "ray@rayburns.nz"
    ray.approved = True
    ray.administrator = True
    ray.set_password("zkgbu")
    db.session.add(ray)
    db.session.commit()
    # Default Tow Plane
    tug = Slot()
    tug.slot_type = "DEFAULT"
    tug.slot_key = "TUG"
    tug.slot_data = "RDW"
    db.session.add(tug)
    db.session.commit()
    # Load aircraft from CSV file
    with open("asc/aircraft.csv", "r", encoding='Latin-1') as d:
        reader = csv.reader(d, delimiter="|")
        readcount = 0
        insertcount = 0
        failedcount = 0
        for r in reader:
            try:
                readcount += 1
                if readcount == 1:
                    # Skip the header record.
                    continue
                f = Aircraft()
                f.regn = r[0]
                f.type = r[1]
                f.rate_per_hour = r[2]
                f.flat_charge_per_launch = r[3]
                f.rate_per_height = r[4]
                f.per_height_basis = r[5]
                f.rate_per_hour_tug_only = r[6]
                f.launch = False
                if r[7] == 'Y':
                    f.launch = True
                f.bscheme = False
                if r[8] == 'Y':
                    f.bscheme = True
                f.default_launch = r[9]
                f.seat_count = r[10]
                f.default_pilot = r[11]
                db.session.add(f)
                db.session.commit()
                insertcount += 1
            except Exception as e:
                print(str(e))
                print(r)
                failedcount += 1
        print("Aircraft: {} records read, {} inserted, {} failed".format(readcount, insertcount, failedcount))
    # Load Pilots from CSV file
    with open("asc/pilots.csv", "r", encoding='Latin-1') as d:
        reader = csv.reader(d, delimiter="|")
        readcount = 0
        insertcount = 0
        failedcount = 0
        for r in reader:
            try:
                readcount += 1
                if readcount == 1:
                    # Skip the header record.
                    continue
                f = Pilot()
                f.code = r[0]
                f.fullname = r[1]
                f.email = r[2]
                if r[3] == 'Y':
                    f.towpilot = True
                else:
                    f.towpilot = False
                if r[4] == 'Y':
                    f.instructor = True
                else:
                    f.instructor = False
                if r[5] == 'Y':
                    f.bscheme = True
                else:
                    f.bscheme = False
                db.session.add(f)
                db.session.commit()
                insertcount += 1
            except Exception as e:
                print(str(e))
                print(r)
                failedcount += 1
        readcount -= 1 # remove the header record
        print("Pilots: {} records read, {} inserted, {} failed".format(readcount, insertcount, failedcount))
    # Create some Flights
    with open("asc/flights.csv", "r", encoding='Latin-1') as d:
        reader = csv.reader(d, delimiter="|")
        readcount = 0
        insertcount = 0
        failedcount = 0
        for r in reader:
            try:
                readcount += 1
                if readcount == 1:
                    # skip the header record
                    continue
                f = Flight()
                f.flt_date  = datetime.date.today()
                f.linetype = 'FL'
                f.pic = r[1]
                f.p2 = r[2]
                f.ac_regn = r[0]
                f.tow_pilot = 'Gus Cabre'
                f.tug_regn = 'RDW'
                if f.ac_regn == 'GNW':
                    f.tug_regn = 'SELF LAUNCH'
                f.takeoff = str2time(r[3])
                f.tug_down = str2time(r[4])
                f.landed = str2time(r[5])
                db.session.add(f)
                db.session.commit()
                insertcount += 1
            except Exception as e:
                print(str(e))
                print(r)
                failedcount += 1
        readcount -= 1 # remove the header record
        print("flights: {} records read, {} inserted, {} failed".format(readcount, insertcount, failedcount))
    click.echo('Demo data created.')

def str2time(pstr):
    if pstr == '':
        return None
    try:
        fstr = float(pstr)
        hours = int(fstr)
        mins = int((fstr - hours) * 100)
        thistime = datetime.time(hour=hours,minute=mins)
        return thistime
    except Exception as e:
        print("{}:{}".format(pstr,e))

def init_db():
    """Clear the existing data and create new tables."""
    # This is not strictly necessary because this is executed each time the app is started
    click.echo("Starting Initialisation")
    # for t in db.engine.table_names():
    db.drop_all()
    db.create_all()
    db.session.commit()
    click.echo('Initialized the database.')



@click.command()
@click.option('--test', default=False, is_flag=True, help='run click test')
@click.option('--init', default=False, is_flag=True, help='delete all tables, create database and build new tables')
@click.option('--loadcsv', default=False, is_flag=True, help='Load data from CSV file')
@click.option('--demodata', default=False, is_flag=True, help='Load demo data ')
@click.option('--loadmbr', default=False, is_flag=True, help='Load memberdata')
@click.option('--updmbr', default=False, is_flag=True, help='Update member and pilot data')
def cli(test, init, loadcsv, demodata, loadmbr, updmbr):
    print("Your current working directory should be the parent of the instance folder")
    if test:
        log.info("cli called with --test")
        test_001()
    if init:
        log.info("cli called with --init")
        init_db()
    if loadcsv:
        log.info("cli called with --loadcsv")
        csvload()
    if demodata:
        log.info("cli called with --demodata")
        add_demo_data()
    if loadmbr:
        log.info("cli called with --loadmbr")
        add_mbr_data()
    if updmbr:
        log.info("cli called with --updmbr")
        periodic_mbr_update()


if __name__ == '__main__':
    # establishlogging('logs/cli.log','DEBUG',True)
    # log = logging.getLogger('cli')
    # log.error('about this')
    with app.app_context():
        log.info("cli started")
        print("app instance path (in __main__ cli.py)_ is {}".format(app.instance_path))
        cli()
