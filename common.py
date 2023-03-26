from asc.schema import *

# Named constants
constREGN_FOR_TUG_ONLY = 'TUG ONLY'
constREGN_FOR_WINCH = 'WINCH'
constTOW_FOR_SELF_LAUNCH = 'SELF LAUNCH'
constTRIAL_FLIGHT_CUST = 'TRIAL FLIGHT'


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
