from asc.schema import *
from asc.oMaint import *

# Named constants
constREGN_FOR_TUG_ONLY = 'TUG ONLY'
constREGN_FOR_WINCH = 'WINCH'
constTOW_FOR_SELF_LAUNCH = 'SELF LAUNCH'
constTRIAL_FLIGHT_CUST = 'TRIAL FLIGHT'
constOTHER_CLUB_MEMBER = 'OTHER CLUB MEMBER'

global_log = None

def common_set_log(logger):
    global global_log
    global_log = logger

def addupdslot(pslottype,pslotkey,pslotdata=None,puser=None,pslotdesc=None):
    """
    Add or update a slot value
    ************************************************
    *   NO  COMMIT !!!   made in caller            *
    ************************************************
    :param pslottype:
    :param pslotkey:
    :param pslotdata:
    :param puser:
    :param pslotdesc:
    :return:
    """
    thisrec = db.session.query(Slot).filter_by(userid=puser).filter_by(slot_type=pslottype).filter_by(slot_key=pslotkey).first()
    if thisrec is None:
        thisrec = Slot()
        thisrec.slot_type = pslottype
        thisrec.slot_key = pslotkey
        thisrec.slot_data = pslotdata
        thisrec.slot_desc = pslotdesc
        db.session.add(thisrec)
    else:
        thisrec.slot_data = pslotdata
        thisrec.slot_desc = pslotdesc

def toDate(dateString):
    return datetime.datetime.strptime(dateString, "%Y-%m-%d").date()

#
#########################################################################
# Routines for dealing with Meter Readings
#########################################################################
#



def flight_summary_for_day(pac_regn, pdate):
    """
    Calculate the total number of flights and the total number of minuutes
    For a specified a/c (either Glider or Tug) and return both as a dictionary
    :param pac_regn: Short registration (e.g. RDW, GNF) for the A/C
    :param pdate: Date in question
    :return: Dictionary of Movements and minutes ( {"count":count, "minutes":mins}  )
    """
    if pac_regn is None:
        raise AttributeError("Aircraft registration is none")
    if not isinstance(pac_regn,str):
        raise AttributeError("Aircraft registration is not a string")
    __thisac = db.session.query(Aircraft).filter(Aircraft.regn==pac_regn).first()
    if __thisac is None:
        raise AttributeError("{} is not on the aircraft table".format(pac_regn))
    # Check date
    if pdate is None:
        raise AttributeError("Date cannot be none")
    if not isinstance(pdate,datetime.date):
        raise AttributeError("Passed date is not a date {}".format(type(pdate)))
    # Processing
    # print("Processing Readings for {} on {}".format(pac_regn, pdate))
    flts = db.session.query(Flight).filter(Flight.ac_regn==pac_regn).filter(Flight.flt_date==pdate)
    count=0
    mins=0
    for f in flts:
        count += 1
        mins += f.glider_mins()
    flts = db.session.query(Flight).filter(Flight.tug_regn==pac_regn).filter(Flight.flt_date==pdate)
    for f in flts:
        count += 1
        mins += f.tow_mins()
    return {"count":count, "minutes":mins}

def list_of_dates_for_flights(p_start_date=None, p_end_date=None):
    """
    Function simply returns a list of all the dates for which there are flight records
    between two dates
    :param p_start_date:
    :param p_end_date:
    :return: list of dates
    """
    if p_start_date is not None:
        if not isinstance(p_start_date,datetime.date):
            raise AttributeError("Passed date is not a date {}".format(type(p_start_date)))
    else:
        p_start_date = datetime.date(1900,1,1)
    if p_end_date is not None:
        if not isinstance(p_end_date,datetime.date):
            raise AttributeError("Passed date is not a date {}".format(type(p_end_date)))
    else:
        p_end_date = datetime.date.today()
    rows = db.session.query(
        Flight.flt_date,
         ).filter(Flight.linetype=='FL'
         ).filter(Flight.flt_date >= p_start_date
         ).filter(Flight.flt_date <= p_end_date
         ).group_by(Flight.flt_date
                   ).all()
    return [f.flt_date for f in rows]

def create_readings_from_flights(p_ac_regn,p_start_date=None,p_end_date=None, p_meter_id=None):
    """
    Create readings for ac between two dates.
    All this does is insert readings into the readings file
    Note that there are separate routines to reset the end reading dates
    :param p_ac_regn: The a/c Registration
    :param p_start_date: If not specified then 1/1/1900
    :param p_end_date: If not specified then today
    :param p_meter_id: If not specified then all auto update meters used.
    :return
    """
    # get the Aircraft
    thisac = ACMaint(p_ac_regn)
    if thisac is None:
        raise AttributeError('A/c Regn invalid')
    if p_start_date is not None:
        if not isinstance(p_start_date,datetime.date):
            raise AttributeError('Start Date must be a valid date')
    if p_end_date is not None:
        if not isinstance(p_end_date,datetime.date):
            raise AttributeError('End Date must be a valid date')
    # Processing
    if p_meter_id is None:
        meters_to_update = [m for m in thisac.meters if m.auto_update]
    else:
        meters_to_update = [m for m in thisac.meters if m.meter_id == p_meter_id]
    listofdates = list_of_dates_for_flights(p_start_date,p_end_date)
    rowsadded = 0
    for day in listofdates:
        deltas = flight_summary_for_day(thisac.regn,day)
        if deltas['count'] != 0:
            for m in meters_to_update:
                if m.last_reading_date is None or day > m.last_reading_date:
                    if m.uom == 'Qty':
                        # print("Qty updating  {} for {}".format(m,day))
                        reading = MeterReadings(ac_id=thisac.id,meter_id=m.meter_id,
                                                reading_date = day,
                                                meter_reading=0,
                                                meter_delta=deltas['count'],
                                                note='Auto Inserted')
                        db.session.add(reading)
                        rowsadded += 1
                        db.session.flush
        if deltas['minutes'] != 0:
            for m in meters_to_update:
                if m.last_reading_date is None or day > m.last_reading_date:
                    if m.uom == 'Time':
                        # print("timne updating  {}".format(m))
                        reading = MeterReadings(ac_id=thisac.id,meter_id=m.meter_id,
                                                reading_date = day,
                                                meter_reading=0,
                                                meter_delta=deltas['minutes'],
                                                note='Auto Inserted')
                        db.session.add(reading)
                        rowsadded += 1
                        db.session.flush
        db.session.commit()
    for m in meters_to_update:
        reset_readings_from_start(p_ac_regn,m.meter_id)
    return rowsadded

def reset_readings_from_start(p_ac_regn,p_meter_id,p_initial_value=None):
    """
    Use this procedure to recalculate the meter readings from the delta
    using the either p_initial_value (if supplied) or the first reading recorded.
    :param p_ac_regn: A/C regn string
    :param p_meter_id: The meter_id as per meters
    :param p_initial_value: A starting Value in either qty or mins as an integer
    :return: The number of changes.
    """
    # validate parameters
    thisac = ACMaint(p_ac_regn)
    if thisac is None:
        raise AttributeError("Invalid A/c Registration")
    try:
        meter = [m for m in thisac.meters if m.meter_id == p_meter_id][0]
    except Exception as e:
        raise AttributeError("Invalid Meter {}/{}".format(thisac.regn,p_meter_id))
    # print(meter)
    if meter is None:
        raise AttributeError("Invalid Meter")
    if p_initial_value is not None:
        if type(p_initial_value) not in [ int, float, decimal.Decimal]:
            raise AttributeError("Initial Value must be an integer")
    #
    if global_log is not None:
        global_log.info('Meter readings for {}/{} reset from start'.format(thisac.regn,meter.meter_name))
    #
    readings = db.session.query(MeterReadings).filter(MeterReadings.ac_id == thisac.id)\
        .filter(MeterReadings.meter_id == p_meter_id)\
        .order_by(MeterReadings.reading_date)\
        .all()
    if readings is None:
        return 0
    if len(readings) < 2:
        return 0
    changecount = 0
    if p_initial_value is not None:
        readings[0].meter_reading = p_initial_value
        last_reading = p_initial_value
        changecount += 1
    else:
        if readings[0].meter_reading == 0:
            readings[0].meter_reading = readings[0].meter_delta
        last_reading = readings[0].meter_reading
    db.session.commit()
    for r in readings[1:]:
        last_reading += r.meter_delta
        r.meter_reading = last_reading
        changecount += 1
        db.session.flush()
    db.session.commit()
    if global_log is not None:
        global_log.info('{} Values changed'.format(changecount))
    return changecount

def reset_readings_from_end(p_ac_regn,p_meter_id,p_latest_value=None):
    """
    Use this procedure to recalculate the meter readings from the delta
    using the either p_initial_value (if supplied) or the first reading recorded.
    :param p_ac_regn: A/C regn string
    :param p_meter_id: The meter_id as per meters
    :param p_latest_value: A starting Value in either qty or mins as an integer
    :return: The number of changes.
    """
    # validate parameters
    thisac = ACMaint(p_ac_regn)
    if thisac is None:
        raise AttributeError("Invalid A/c Registration")
    try:
        meter = [m for m in thisac.meters if m.meter_id == p_meter_id][0]
    except Exception as e:
        raise AttributeError("Invalid Meter {}/{}".format(thisac.regn,p_meter_id))
    if meter is None:
        raise AttributeError("Invalid Meter")
    if p_latest_value is not None:
        if type(p_latest_value) not in [int, float, decimal.Decimal]:
            raise AttributeError("Latest Value must be an integer")
    #
    if global_log is not None:
        global_log.info('Meter readins for reset from end using {}'.format(str(meter), p_latest_value or 0))
    #
    readings = db.session.query(MeterReadings).filter(MeterReadings.ac_id == thisac.id)\
        .filter(MeterReadings.meter_id == p_meter_id)\
        .order_by(MeterReadings.reading_date.desc())\
        .all()
    if readings is None:
        return 0
    if len(readings) < 2:
        return 0
    changecount = 0
    if p_latest_value is not None:
        readings[0].meter_reading = p_latest_value
        last_reading = p_latest_value
        changecount += 1
    else:
        if readings[0].meter_reading == 0:
            if global_log is not None:
                global_log.error('Negative value at start of change')
            raise OverflowError("The latest reading is zero.  Cannot have negative values")
        last_reading = readings[0].meter_reading
    db.session.flush()
    for r in readings[1:]:
        last_reading -= r.meter_delta
        if last_reading < 0:
            if global_log is not None:
                global_log.error('Negative value middle of change - rollback')
            db.session.rollback()
            raise OverflowError("A reading in the range went negative.  Cannot have negative readings")
        r.meter_reading = last_reading
        changecount += 1
        db.session.flush()
    db.session.commit()
    if global_log is not None:
        global_log.info('{} Values changed'.format(changecount))
    return changecount

def user_agent_os_extract(uastring):
    # find the content between the first two characters
    mo = re.search("\(.*?\)",uastring)
    if mo is None:
        return None
    # return a list of the values in the first brackets of the user agent.
    return mo[0][1:-1].split(";")

def user_agent_os_match(uastring,matchstring):
    # find the content between the first two characters
    mo = re.search("\(.*?\)",uastring)
    if mo is None:
        return False
    for os in mo[0][1:-1].split(";"):
        if matchstring in os:
            return True
    # If we get to here then it wasn't found
    return False




