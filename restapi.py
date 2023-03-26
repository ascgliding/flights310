from flask import (
    Blueprint, render_template, jsonify, request, Flask
)
from asc.schema import Aircraft, Flight, Slot
from decimal import Decimal
import datetime
from asc.common import *

bp = Blueprint('restapi', __name__)
app = Flask(__name__)
applog = app.logger

# ------------------------------------------------------------------------------------------------------
# Supporting functions
# ------------------------------------------------------------------------------------------------------

def sqlalchemy2json(sobj):
    """
    This routine takes an sqlalchmey object and converts it into a dictionary of data items that
    are supported by Json.  Data types not supported by JSON are just dropped.
    :param sobj:
    :return:
    """
    rtndict = {}
    if sobj is None:
        return rtndict
    try:
        thisdict = sobj.__dict__
        for k,v in thisdict.items():
            if isinstance(v,Decimal):
                rtndict[k] = float(v)
            elif type(v) in [str,bool,int,float]:
                rtndict[k] = v
            # The rest we can ignore
    except Exception as e:
        pass
    return rtndict


# ------------------------------------------------------------------------------------------------------
# APIS
# ------------------------------------------------------------------------------------------------------

@bp.route('/getdefaults')
def getdefaults():
    ac = request.args.get('ac')
    flt_date = request.args.get('flt_date')
    try:
        thisdate = datetime.datetime.strptime(flt_date,"%Y-%m-%d")
    except Exception as e:
        thisdate = datetime.date.today()
    # Get the ac details to determine seat count, default launch method and default pilot
    thisdict = {}
    thisac = Aircraft.query.filter_by(regn=ac).first()
    # unknown Ac
    if thisac is None:
        thisslot = Slot.query.filter_by(slot_type='DEFAULT').filter_by(slot_key="LASTTUG").first()
        if thisslot is not None:
            thisdict['tug'] = thisslot.slot_data
        thisslot = Slot.query.filter_by(slot_type='DEFAULT').filter_by(slot_key="LASTTOWIE").first()
        if thisslot is not None:
            thisdict['towie'] = thisslot.slot_data
    else:
        # convert that data into a standard dictionary.
        thisdict = sqlalchemy2json(thisac)
        # add the default launch method.
        if thisac.default_launch != None:
            thisdict['tug'] = thisac.default_launch
            thisdict['towie'] = None
        thisslot = Slot.query.filter_by(slot_type='DEFAULT').filter_by(slot_key="LASTTUG").first()
        if thisslot is not None:
            thisdict['tug'] = thisslot.slot_data
        thisslot = Slot.query.filter_by(slot_type='DEFAULT').filter_by(slot_key="LASTTOWIE").first()
        if thisslot is not None:
            thisdict['towie'] = thisslot.slot_data
    return jsonify(thisdict,[],True)

@bp.route('/setscreendim')
def setscreendim():
    '''
    Set screen dimensions.
    Get the screen size via ajax and save in session cookie.
    :return: None
    '''
    width = request.args.get('width')
    height = request.args.get('height')
    session['SCRWIDTH'] = width
    session['SCRHEIGHT'] = height