# import sqlite3
import os
import click
from sqlalchemy import create_engine, text as sqltext
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

def initialise_maint_tables():
    """Drop and rebuild the maintenance database tables"""
    click.echo("Initialising Maintenance Database")
    Tasks.__table__.drop(db.engine)
    Meters.__table__.drop(db.engine)
    ACMeters.__table__.drop(db.engine)
    MeterReadings.__table__.drop(db.engine)
    ACTasks.__table__.drop(db.engine)
    ACMaintUser.__table__.drop(db.engine)
    ACMaintHistory.__table__.drop(db.engine)
    db.create_all()
    click.echo("Maintenance Database initialisation complete")

def load_maintenance():
    click.echo("Loading RDW maintenancce tables")
    thismeter = Meters(meter_name = 'Landings', uom='Qty')  #, entry_uom = 'Units')
    db.session.add(thismeter)
    thismeter = Meters(meter_name = 'Tachometer', uom='Time')  # , entry_uom = 'Hours:Minutes')
    db.session.add(thismeter)
    thismeter = Meters(meter_name = 'AirFrame', uom='Time')  #, entry_uom = 'Decimal Hours')
    db.session.add(thismeter)
    thismeter = Meters(meter_name = 'Motor Glider Engine Hrs', uom='Time')  #, entry_uom = 'Decimal Hours')
    db.session.add(thismeter)
    db.session.flush()
    db.session.commit()
    # tasks are referred to by name in more than one place so I have allocated them to their
    # own variable so no mistakes can be made with misspelling descriptions
    tskadhoc = 'Ad Hoc Maintenance'
    tsk50hr = '50 Hour Service'
    tsk100hr = '100 Hr Service'
    tsk200hr = '200 Hr Service'
    tsk500hr = '500 Hr Service'
    tsktransponder = 'Transponder Check'
    tskaltimeter = 'Altimeter Check'
    tskradio = 'Radio Check'
    tskelt = 'ELT'
    tskeltbatt = 'Replace ELT Battery'
    tskara = 'Biennial RA'
    tskbeambolts = 'Replace Undercarriage Beam Bolts'
    tskbrakefluid = 'Replace Brake Fluid'
    tskcarbflange = 'Replace Carburettor Flanges'
    tskairbox = 'Replace Air Box'
    tskvibe = 'Replace engine vibration dampers'
    tskbowden = 'Replace Carburettor Bowden Cables'
    tskelasto = 'Replace All rubber hoses for fuel, oil and cooling'
    tskbrs = 'BRS Service'
    tskengine = 'Replace Engine'
    tsknosehook = 'Nose Hook Replacement'
    tskbellyhook = 'Belly Hook Replacement'
    tsk3mth = '3 Monthly Glider Inspection'
    tskannual = 'Annual Glider Inspection'
    tskcompass = 'Compass Swing'
    tskbelts = 'Belts Replacement'
    tskplb = 'PLB Replacement'



    # Both of these are equivalent (once a flush operation has occurred.
    oTach = db.session.query(Meters).filter(Meters.meter_name == 'Tachometer').first()
    oAirframe = db.session.query(Meters).filter(Meters.meter_name == 'AirFrame').first()
    oLandings = db.session.query(Meters).filter(Meters.meter_name == 'Landings').first()
    thistask = Tasks(task_description = tskadhoc , task_basis='Calendar',
                     task_calendar_uom='Years', task_calendar_period=500)
    db.session.add(thistask)
    # Maintenenance Due Sheet
    thistask = Tasks(task_description = tsk50hr , task_basis='Meter',
                     task_meter_id=oAirframe.id, task_meter_period=50 )
    db.session.add(thistask)
    thistask = Tasks(task_description = tsk100hr , task_basis='Meter',
                     task_meter_id=oAirframe.id, task_meter_period=100 )
    db.session.add(thistask)
    thistask = Tasks(task_description = tsk200hr, task_basis='Meter',
                     task_meter_id=oAirframe.id, task_meter_period=200 )
    db.session.add(thistask)
    thistask = Tasks(task_description = tsk500hr, task_basis='Meter',
                     task_meter_id=oAirframe.id, task_meter_period=500 )
    db.session.add(thistask)
    thistask = Tasks(task_description = tsktransponder, task_basis='Calendar',
                     task_calendar_uom = 'Years', task_calendar_period=2 )
    db.session.add(thistask)
    thistask = Tasks(task_description = tskaltimeter, task_basis='Calendar',
                     task_calendar_uom = 'Years', task_calendar_period=2)
    db.session.add(thistask)
    thistask = Tasks(task_description=tskradio, task_basis='Calendar',
                     task_calendar_uom='Years', task_calendar_period=2)
    db.session.add(thistask)
    thistask = Tasks(task_description=tskelt, task_basis='Calendar',
                     task_calendar_uom='Years', task_calendar_period=2)
    db.session.add(thistask)
    thistask = Tasks(task_description=tskeltbatt, task_basis='Calendar',
                     task_calendar_uom='Years', task_calendar_period=5)
    db.session.add(thistask)
    thistask = Tasks(task_description = tskara, task_basis='Calendar',
                     task_calendar_uom = 'Years', task_calendar_period=2)
    db.session.add(thistask)

    # Lifed Items Sheet
    thistask = Tasks(task_description = tskbeambolts, task_basis='Meter',
                     task_meter_id=oLandings.id, task_meter_period=1000 )
    db.session.add(thistask)
    thistask = Tasks(task_description = tskbrakefluid, task_basis='Calendar',
                     task_calendar_uom = 'Years', task_calendar_period=4 )
    db.session.add(thistask)
    thistask = Tasks(task_description = tskcarbflange, task_basis='Meter',
                     task_meter_id=oAirframe.id, task_meter_period=200 )
    db.session.add(thistask)
    thistask = Tasks(task_description = tskairbox, task_basis='Meter',
                     task_meter_id=oAirframe.id, task_meter_period=200)
    db.session.add(thistask)
    thistask = Tasks(task_description = tskvibe,
                     task_calendar_uom='Years', task_calendar_period = 2,
                     task_basis='Calendar', task_meter_id=oAirframe.id, task_meter_period=200 )
    db.session.add(thistask)
    thistask = Tasks(task_description = tskbowden, task_basis='Meter',
                     task_meter_id=oAirframe.id, task_meter_period=400)
    db.session.add(thistask)
    thistask = Tasks(task_description = tskelasto,
                     task_basis='Calendar', task_calendar_uom = 'Years', task_calendar_period=5,
                     task_meter_id = oAirframe.id, task_meter_period = 500)
    db.session.add(thistask)
    thistask = Tasks(task_description = tskbrs, task_basis='Calendar',
                     task_calendar_uom='Years',
                     task_calendar_period=5)
    db.session.add(thistask)
    thistask = Tasks(task_description = tskengine, task_basis='Meter',
                     task_meter_id = oTach.id, task_meter_period=2000)
    db.session.add(thistask)
    thistask = Tasks(task_description = tsknosehook, task_basis='Meter',
                     task_meter_id = oLandings.id, task_meter_period=2000)
    db.session.add(thistask)
    thistask = Tasks(task_description = tskbellyhook, task_basis='Meter',
                     task_meter_id = oLandings.id, task_meter_period=2000)
    db.session.add(thistask)
    thistask = Tasks(task_description = tsk3mth, task_basis='Calendar',
                     task_calendar_uom = 'Months', task_calendar_period=3)
    db.session.add(thistask)
    thistask = Tasks(task_description = tskannual, task_basis='Calendar',
                     task_calendar_uom = 'Years', task_calendar_period=1)
    db.session.add(thistask)
    thistask = Tasks(task_description = tskcompass, task_basis='Calendar',
                     task_calendar_uom = 'Years', task_calendar_period=4)
    db.session.add(thistask)
    thistask = Tasks(task_description = tskbelts, task_basis='Calendar',
                     task_calendar_uom = 'Years', task_calendar_period=12)
    db.session.add(thistask)
    thistask = Tasks(task_description = tskplb, task_basis='Calendar',
                     task_calendar_uom = 'Years', task_calendar_period=4)
    db.session.add(thistask)
    db.session.flush
    db.session.commit()
    oAltimeter = db.session.query(Tasks).\
        filter(Tasks.task_description == tskaltimeter).first()
    oTransponder = db.session.query(Tasks).\
        filter(Tasks.task_description == tsktransponder).first()
    oVibedampers = db.session.query(Tasks).\
        filter(Tasks.task_description == tskvibe).first()
    oFiftyhr = db.session.query(Tasks).\
        filter(Tasks.task_description == tsk50hr).first()
    oBrakefluid = db.session.query(Tasks).\
        filter(Tasks.task_description == tskbrakefluid).first()
    oBeambolts = db.session.query(Tasks).\
        filter(Tasks.task_description == tskbeambolts).first()
    oElastometrics = db.session.query(Tasks).\
        filter(Tasks.task_description == tskelasto)\
        .first()
    oEngine = db.session.query(Tasks).filter(Tasks.task_description == tskengine).first()
    oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
    oGMP = db.session.query(Aircraft).filter(Aircraft.regn == 'GMP').first()
    oGNF = db.session.query(Aircraft).filter(Aircraft.regn == 'GNF').first()
    oGVF = db.session.query(Aircraft).filter(Aircraft.regn == 'GVF').first()
    oGON = db.session.query(Aircraft).filter(Aircraft.regn == 'GON').first()
    oGBU = db.session.query(Aircraft).filter(Aircraft.regn == 'GBU').first()
    oGKT = db.session.query(Aircraft).filter(Aircraft.regn == 'GKT').first()
    # A/C meters
    thisrow = ACMeters(ac_id = oRDW.id, meter_id = oAirframe.id, entry_uom="Decimal Hours",
                       entry_prompt="Enter the Additional Airframe DECIMAL  hours ",
                       entry_method="Delta")
    db.session.add(thisrow)
    thisrow = ACMeters(ac_id = oRDW.id, meter_id = oTach.id, entry_uom="Hours:Minutes",
                       entry_prompt="End Tacho Reading (h:mm)",
                       entry_method="Reading")
    db.session.add(thisrow)
    thisrow = ACMeters(ac_id = oRDW.id, meter_id = oLandings.id, entry_uom="Qty",
                       entry_prompt="Enter the number of landings for the day",
                       entry_method="Delta")
    db.session.add(thisrow)
    # Readings
    with open('instance/rdwhours.csv', 'r') as csvf:
        reader = csv.DictReader(csvf,delimiter='|',quoting=csv.QUOTE_NONE)
        count = 0
        last_tach_reading_mins = 0
        last_tach_delta_mins = 0
        last_landings_reading = 0
        last_landings_delta = 0
        last_af_reading_mins = 0
        last_af_delta_mins = 0
        for row in reader:
            if count < 5000:
                count += 1
                #  Airframe

                try:
                    # chckifnum = Decimal(row['Daily A/F Hours'])
                    if row['Daily A/F Hours'] != '' or row['Total A/F Hours'] != '':
                        thisreading = MeterReadings()
                        thisreading.ac_id = oRDW.id
                        thisreading.meter_id = oAirframe.id
                        thisreading.reading_date = datetime.datetime.strptime(row['Date'], "%Y-%m-%d")
                        # update both if they have been supplied:
                        if row['Daily A/F Hours'] != '':
                            meter_delta_mins = round(float(row['Daily A/F Hours']) * 60)
                        if row['Total A/F Hours'] != '':
                            meter_reading_mins = round(float(row['Total A/F Hours']) * 60)
                        # if either are missing then calculate...
                        if row['Daily A/F Hours'] == '':  # then we must have the meter reading
                            meter_delta_mins = meter_reading_mins  - last_af_reading_mins
                        if row['Total A/F Hours'] == '':  # then we must have the delta
                            meter_reading_mins = last_af_reading_mins + meter_delta_mins

                        thisreading.note = row['Tow Pilot']
                        thisreading.meter_delta = meter_delta_mins
                        thisreading.meter_reading = meter_reading_mins
                        last_af_delta_mins = meter_delta_mins
                        last_af_reading_mins = meter_reading_mins
                        if thisreading.meter_delta is not None and thisreading.meter_reading is not None:
                            db.session.add(thisreading)
                        else:
                            print('Null Meter reading for Air frame on {} {}/{}'.
                                  format(thisreading.reading_date, thisreading.meter_reading,
                                         thismeter.meter_delta))
                except Exception as e:
                    print('No Airframe {}'.format(str(e)))
                    pass

                # Tacho

                try:
                    if row['Tacho'] != '' or row['Daily Tacho Hours'] != '':
                        thisreading = MeterReadings()
                        thisreading.ac_id = oRDW.id
                        thisreading.meter_id = oTach.id
                        thisreading.reading_date = \
                            datetime.datetime.strptime(row['Date'], "%Y-%m-%d")
                        if row['Tacho'] != '':
                            try:
                                meter_reading_mins = int(row['Tacho']) * 60
                            except:
                                try:
                                    meter_readings_mins = float(row['Tacho']) * 60
                                except:
                                    bits = row['Tacho'].split(':')
                                    hrs = int(bits[0])
                                    if len(bits) > 1:  # Occasionally, only hrs iss specified
                                        mins = int(bits[1])
                                    else:
                                        mins = 0
                                    meter_reading_mins = Decimal((hrs * 60) + mins)
                        if row['Daily Tacho Hours'] != '':  # when specified this is in decimal hours
                            meter_delta_mins = round(float(row['Daily Tacho Hours']) * 60)
                        # missing values
                        if row['Tacho'] == '':   # then  we must have the delta
                            meter_reading_mins = last_tach_reading_mins + meter_delta_mins
                        if row['Daily Tacho Hours'] == '':  # then we must have the reading
                            meter_delta_mins = meter_reading_mins - last_tach_reading_mins
                        thisreading.note = row['Tow Pilot']
                        thisreading.meter_delta = meter_delta_mins
                        thisreading.meter_reading = meter_reading_mins
                        last_tach_delta_mins = meter_delta_mins
                        last_tach_reading_mins = meter_reading_mins
                        if thisreading.meter_delta is not None and thisreading.meter_reading is not None:
                            db.session.add(thisreading)
                        else:
                            print('Null Meter reading for Tach on {}: {}/{}'.
                                  format(thisreading.reading_date, thisreading.meter_reading,
                                         thisreading.meter_delta))
                except Exception as e:
                    print('No tach: {}, row number {}'.format(str(e), count))
                    pass

                # Landings

                try:
                    if row['Landings'] != '' or row['Total Landings'] != '':
                        thisreading = MeterReadings()
                        thisreading.ac_id = oRDW.id
                        thisreading.meter_id = oLandings.id
                        thisreading.reading_date = datetime.datetime.strptime(row['Date'], "%Y-%m-%d")
                        if row['Landings'] != '':
                            thisreading.meter_delta = Decimal(row['Landings'])
                        if row['Total Landings'] != '':
                            thisreading.meter_reading = Decimal(row['Total Landings'])
                        # complete any missing values
                        if row['Landings'] == '': # Then we must have the reading
                            thisreading.meter_delta = \
                                thisreading.meter_reading - last_landings_reading
                        if row['Total Landings'] == '':  #Then we must have the delta
                            thisreading.meter_reading = \
                                last_landings_reading + thisreading.meter_delta
                        thisreading.note = row['Tow Pilot']
                        last_landings_reading = thisreading.meter_reading
                        last_landings_delta = thisreading.meter_delta
                        if thisreading.meter_delta is not None \
                                and thisreading.meter_reading is not None:
                            db.session.add(thisreading)
                        else:
                            print('Null Meter reading for Landings on {}'.
                                  format(thisreading.reading_date))
                except Exception as e:
                    print('No landings: {} row {}'.format(str(e),count))
                    pass
        print('{} records added'.format(count))
    db.session.commit()
    #users
    me = User.query.filter_by(name='rayb').first()
    peter = User.query.filter_by(name='peebee89').first()
    craig = User.query.filter_by(name='craigbest').first()
    db.session.add(ACMaintUser(ac_id = oRDW.id, user_id = me.id, maint_level='All'))
    db.session.add(ACMaintUser(ac_id = oRDW.id, user_id = peter.id, maint_level='All'))
    db.session.add(ACMaintUser(ac_id=oGON.id, user_id=craig.id, maint_level='All'))
    for ac in [oGBU,oGKT]:
        db.session.add(ACMaintUser(ac_id=ac.id, user_id=me.id, maint_level='All'))
    for ac in [oGVF,oGMP,oGNF]:
        db.session.add(ACMaintUser(ac_id=ac.id, user_id=me.id, maint_level='All'))
        db.session.add(ACMaintUser(ac_id=ac.id, user_id=craig.id, maint_level='All'))
    db.session.commit()
    add_task_and_history(oRDW.id,tsk50hr,None,1456.33,None,1102,
                         [206.7,306.7,350.61,403.73,470.04,519.22,567.51,623.24,
                         661.31,710.08,760.78,802,859.1,896.28,949.8,992.78,1045.53,1095.93,
                         1102,1148.72,1210.2,1242.94,1300.49,1347.88,1407,1459.33])
    add_task_and_history(oRDW.id,tsk100hr,None,1407,None,1202,
                         [250.75,301.91,399.83,470.04,567.51,661.31,760.78,
                         859.1,949.8,1102,1210.2,1300.49,1407])
    add_task_and_history(oRDW.id,tsk200hr,None,1407,None,1202,
                         [470.04,670.04,661.31,881.31,859.1,1059.1,1102,1210.2,1407])
    add_task_and_history(oRDW.id,tsk500hr,None,1102,None,1202,
                         [])
    add_task_and_history(oRDW.id,tsktransponder,datetime.date(2023,10,17),None,None,None,
                         [datetime.date(2017,7,28),
                          datetime.date(2019, 5, 3),
                          datetime.date(2021, 6, 3),
                          datetime.date(2023, 10, 17)
                          ])
    add_task_and_history(oRDW.id,tskaltimeter,datetime.date(2023,10,17),None,None,None,
                         [datetime.date(2017, 7, 28),
                          datetime.date(2019, 5, 3),
                          datetime.date(2021, 6, 3),
                          datetime.date(2023, 10, 17)
                          ])
    add_task_and_history(oRDW.id,tskelt,datetime.date(2023,10,17),None,None,None,
                         [datetime.date(2017, 7, 28),
                          datetime.date(2019, 5, 3),
                          datetime.date(2021, 6, 3),
                          datetime.date(2023, 10, 17)
                          ])
    add_task_and_history(oRDW.id,tskeltbatt,datetime.date(2021,6,28),None,None,None,
                         [datetime.date(2012, 8, 1)
                          ])
    add_task_and_history(oRDW.id,tskara,datetime.date(2023,11,18),None,None,None,
                         [datetime.date(2011, 2, 9),
                          datetime.date(2012, 2, 29),
                          datetime.date(2012, 10, 12),
                          datetime.date(2023, 10, 15),
                          datetime.date(2017, 10, 16),
                          datetime.date(2019, 12, 6),
                          datetime.date(2021, 12, 6),
                          datetime.date(2023, 11, 18)
                          ])
    add_task_and_history(oRDW.id,tskbeambolts,None,10093,None,None,
                         [1120,2071,2468,3623,4289,5080,6328,7272,8181,9075,10093])
    add_task_and_history(oRDW.id,tskbrakefluid,datetime.date(2023,7,1),None,None,None,
                         [datetime.date(2012, 5, 1),
                          datetime.date(2014, 11, 1),
                          datetime.date(2018, 11, 1),
                          datetime.date(2020, 12, 1),
                          datetime.date(2023, 7, 1)
                          ])
    add_task_and_history(oRDW.id,tskcarbflange,None,1407.02,None,None,
                         [270,949.98,1189.04,1407.02])
    add_task_and_history(oRDW.id,tskairbox,None,1,None,None,[])
    add_task_and_history(oRDW.id, tskvibe, datetime.date(2023,5,13), 1346.33, None, None, [250,403.73,567.51,760.78,949.8,1346.33])
    add_task_and_history(oRDW.id, tskbowden, None, 1300.49, None, None, [470.04,894.88,1300.49])
    add_task_and_history(oRDW.id,tskelasto, datetime.date(2023,6,5), 1347.88, None, None, [470.04,949.8,1347.88])
    add_task_and_history(oRDW.id,tskbrs, datetime.date(2020,12,22), None, None, None, [])


def add_task_and_history(pac_id,ptask_desc,plast_done,plast_done_reading,
                         pdue_basis_date,pdue_basis_reading
                         ,phistory):
    '''

    :param ptask_desc:
    :param plast_done:
    :param plast_done_reading:
    :param pdue_basis_date:
    :param pdue_basis_reading:
    :param phistory: a list of either dates or readings
    :return:
    '''
    # get te id
    thistask = db.session.query(Tasks).filter(Tasks.task_description==ptask_desc).first()
    if thistask.std_meter_rec is not None:
        if thistask.std_meter_rec.uom == 'Time':
            if plast_done_reading is not None:
                plast_done_reading *= 60
            if pdue_basis_reading is not None:
                pdue_basis_reading *= 60

    thisactask = ACTasks(ac_id=pac_id, task_id=thistask.id, last_done=plast_done,
                     last_done_reading=plast_done_reading,
                     due_basis_date=pdue_basis_date,
                     due_basis_reading=pdue_basis_reading,
                     note='Inserted via import')
    db.session.add(thisactask)
    db.session.commit()
    # now get the id
    thisactask = db.session.query(ACTasks).filter(ACTasks.ac_id==pac_id).\
        filter(ACTasks.task_id==thistask.id).first()
    for h in phistory:
        histrow=ACMaintHistory(ac_id=pac_id,task_id=thisactask.id,
                               task_description=thistask.task_description,
                               )
        if isinstance(h,datetime.date):
            histrow.history_date = h
        else:
            # what kind of meter is this?
            if thistask.std_meter_rec.uom == 'Time':
                histrow.meter_reading = round(h * 60,2)
                nearest_reading = db.session.query(MeterReadings).filter(MeterReadings.ac_id == pac_id) \
                    .filter(MeterReadings.meter_id == thistask.std_meter_rec.id) \
                    .filter(MeterReadings.meter_reading >= (h * 60)) \
                    .order_by(MeterReadings.meter_reading).first()
            else:
                histrow.meter_reading = h
                nearest_reading = db.session.query(MeterReadings).filter(MeterReadings.ac_id==pac_id) \
                    .filter(MeterReadings.meter_id==thistask.std_meter_rec.id) \
                    .filter(MeterReadings.meter_reading>= h) \
                    .order_by(MeterReadings.meter_reading).first()
            # If we have a meter reading then we need to try and work out when
            # the task might have occurred based on the meter readings
            if nearest_reading is None:
                histrow.history_date = datetime.date.today()
                histrow.task_description += " (Could not determine date)"
            else:
                histrow.history_date = nearest_reading.reading_date
                histrow.task_description += " (Date estimated from meter readings)"
        db.session.add(histrow)
    db.session.commit()

@click.command()
@click.option('--test', default=False, is_flag=True, help='run click test')
@click.option('--init', default=False, is_flag=True, help='delete all tables, create database and build new tables')
@click.option('--loadcsv', default=False, is_flag=True, help='Load data from CSV file')
@click.option('--demodata', default=False, is_flag=True, help='Load demo data ')
@click.option('--loadmbr', default=False, is_flag=True, help='Load memberdata')
@click.option('--updmbr', default=False, is_flag=True, help='Update member and pilot data')
@click.option('--maintinit', default=False, is_flag=True, help='Initialise the maintenance Tables')
@click.option('--maintload', default=False, is_flag=True, help='Load the maintenance Tables')
def cli(test, init, loadcsv, demodata, loadmbr, updmbr, maintinit,maintload):
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
    if maintinit:
        log.info("cli called with --maintinit")
        initialise_maint_tables()
    if maintload:
        log.info("cli called with --maintlog")
        load_maintenance()


if __name__ == '__main__':
    # establishlogging('logs/cli.log','DEBUG',True)
    # log = logging.getLogger('cli')
    # log.error('about this')
    with app.app_context():
        log.info("cli started")
        print("app instance path (in __main__ cli.py)_ is {}".format(app.instance_path))
        cli()
