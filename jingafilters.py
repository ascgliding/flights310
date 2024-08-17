from flask import Flask,session, g, current_app
import logging
import datetime
import dateutil
import re
import decimal

# --------------------------------------------------------------------
# Be careful here... in order to access current_app this module
# must be loaded within an application context (whatever thay may be).
# This is done __init__.py.  Look at the create_filters function
# to see how this is done.
# --------------------------------------------------------------------

app = current_app
applog = logging.getLogger('applog')

# This is how to define a jinja filter that can be used in a template
# as a formatter.
# You need to add the following line in the mainline:
#    app.jinja_env.filters['strdate'] = reformatstrdate
# and you use in the template like this"
# <legend>Flights for {{ thisdate|stddate }}</legend>


def displayfornone(pobj):
    if pobj is None:
        return '-'
    elif type(pobj) in [float,decimal.Decimal,int]:
        if pobj == 0:
            return "-"
        else:
            return pobj
    else:
        return pobj

def nameinitials(pstr):
    if pstr is None:
        return "-"
    else:
        initials = ''
        for names in pstr.split():
            initials += names[0]
        return initials

def strtimetotime(ptime):
    """
    This function is used to take a string in "HH:MM" format and
    return a time object.
    This is used when the request.form from a screen returns a string.
    It needs to be changed to a time sot aht the hrsmins template filter
    displays a time correctly.  This is most important when the same screen needs to be re dislayed after an error
    :param ptime:
    :return: time
    """
    if isinstance(ptime, str):
        # return datetime.datetime.strptime(ptime, "%H:%M").time()
        hrsmins = re.findall(r'(\d+)', ptime)
        return datetime.time(int(hrsmins[0]), int(hrsmins[1]))
    else:
        return None


def makedatetime(pdate):
    """
    This routine takes an ninput and returns a valid datetime to the nearest second
    :param pdate: Either a string or a datetime, or a date.  If  string then the format must YYYY-MM-DDTHH:MM
    or YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
    :return: Datetime object
    """
    thisdate = pdate
    if isinstance(thisdate, datetime.datetime):
        return thisdate
    if isinstance(thisdate, str):
        # then it has probably come from request.form and is now a string so needs setting back to a date
        try:
            if len(thisdate) == 16:
                thisdate = datetime.datetime.strptime(thisdate, "%Y-%m-%dT%H:%M")
            elif len(thisdate) == 10:
                thisdate = datetime.datetime.strptime(thisdate, '%Y-%m-%d')
            elif len(thisdate) == 23:
                thisdate = datetime.datetime.strptime(thisdate, "%Y-%m-%dT%H:%M:%S.SSS")
            else:
                thisdate = datetime.datetime.strptime(thisdate, "%Y-%m-%dT%H:%M:%S")
        except Exception as e:
            try:
                thisdate = dateutil.parser.parse(thisdate)
            except:
                applog.error(str(e))
                raise
    elif isinstance(thisdate, datetime.date):
        thisdate = datetime.datetime(pdate.year, pdate.month, pdate.day)
    else:
        raise Exception("Input to makedatetime is not valid.  Type:{} Value:{}".format(str(type(pdate)), pdate))
    try:
        thisdate.replace(microsecond=0)
    except Exception as e:
        applog.error("Could not convert:" + str(type(e)) + str(e))
        raise Exception(str(type(e)) + ":" + str(e))
    return thisdate


@app.template_filter()
def objvariable(k, v):
    """
    The purpose of this filter is to allow displaying of all the public variables in an object in Jinga.
    :param k: The name of a variable
    :param v: The contents of Variable
    :return: True or False depending on whether the variable should be displayed or not.
    """
    if k[0] == '_':
        return False
    if v is None:
        return True
    if isinstance(v, int):
        return True
    if isinstance(v, datetime.datetime):
        return True
    if isinstance(v, datetime.date):
        return True
    if isinstance(v, str):
        return True
    if isinstance(v, float):
        return True
    if isinstance(v, bool):
        return True
    return type(v)


@app.template_filter()
def reformatstddate(pdate):
    """
    Returns a string in the format dd/mm/yyyy from a valid date or datetime
    :param pdate: Must be a date or datetime object
    :return: a string in the format dd/mm/yyyy
    """
    if pdate is None:
        return None
    if not (isinstance(pdate, datetime.date) or isinstance(pdate, datetime.datetime)):
        applog.error("A call was made to reformatstddate with input that was not a date or datetime ({})".format(type(pdate)))
        raise Exception("The input to this function is not in the correct format:{}".format(type(pdate)))
    if isinstance(pdate, datetime.datetime):
        return pdate.date().strftime('%d/%m/%Y')
    else:
        return pdate.strftime('%d/%m/%Y')


@app.template_filter()
def tsdateformat(pdate):
    """
    Convert a datetime into a Day dd/mm/yyyy HH:MM format
    Although this can be done directly on the page by calling strftime, this routine provides
    a single point of change if a new format is required across the site.
    :param pdate: a datetime variable
    :return: A string in the format shown above
    """
    if not isinstance(pdate, datetime.datetime):
        raise Exception("The input is not a datetime")
    return pdate.strftime('%a %d/%m/%Y %H:%M')


@app.template_filter()
def datetimehtml(pdate):
    """
    The primary purpose of this function is to display datetimes in a format that
    is supported by the datetime-local html input type
    :param pdate: date, datetime or string objcect in correct format
    :return: a string in the format YYYY-MM-DDTHH:MM:SS
    """
    if pdate is None:
        return ""
    if not (isinstance(pdate, datetime.datetime) or isinstance(pdate, str)):
        err = "Input can only have datetimes or strings. got {}".format(str(type(pdate)))
        applog.error(err)
        raise Exception(err)
    thisdate = makedatetime(pdate)
    if not isinstance(pdate, datetime.datetime):
        applog.debug(thisdate, str(type(thisdate)))
        raise Exception("converted input is not a datetime")
    try:
        thisdate.replace(microsecond=0)
        return thisdate.strftime('%Y-%m-%dT%H:%M:%S')
    except Exception as e:
        applog.error("Error {} of type {} occurred".format(str(e), type(e)))
        applog.debug("Thisdate:{}".format(thisdate))
        raise

@app.template_filter()
def hrsminsfromtime(ptime):
    if ptime is None:
        return ""
    if not (isinstance(ptime,datetime.time)):
        return None
    return ptime.strftime("%H:%M")


@app.template_filter()
def hrsmins(pmins):
    """
    This function returns a string in the format HH:MM or H:MM or HHH:mm
    This is used in the flights subsystem
    :param pmins: An integer number of minutes
    :return: A string in the format above.
    """
    if pmins is None:
        return "0:00"
    if isinstance(pmins,float) or isinstance(pmins,decimal.Decimal):
        try:
            if int(pmins) != pmins:
                raise ValueError('Cannot convert parameter to integer')
            pmins = int(pmins)
        except Exception as e:
            raise ValueError('Unable to change float/decimal to int ({})({})'.format(pmins,type(pmins)))
    if not (isinstance(pmins, int) or isinstance(pmins, int)):
        applog.debug("A call to hrsmins was passed type {} value {}".format(str(type(pmins)), pmins))
        raise Exception("Parameter to hrsmins is not an integer ({})".format(pmins))

    if pmins:
        hrs = int(pmins/60)
        mins = pmins - (hrs * 60)
        if hrs > 0:
            return str(hrs) + ':' + "%02d" % mins
        else:
            return '0:' + str(mins)
    else:
        return ""


@app.template_filter()
def hhmmss(pdatetime):
    """
    Returns the time part of a datetime string
    :param pdatetime: any dattime object
    :return:
    """
    if pdatetime is None:
        return "00:00:00"
    if not isinstance(pdatetime,datetime.datetime):
        applog.debug("A call was made to hhmmss and was passed type {} value {}".format(str(type(pdatetime)), pdatetime))
        return "00:00:00"
    return pdatetime.strftime("%H:%M:%S")

@app.template_filter()
def hrsdec(pmins):
    """
    This function returns a string in the format HH.HH.
    It is the number of minutes converted to decimal hours - for use in the power logbook
    This is used in the flights subsystem
    :param pmins: An integer number of minutes
    :return: A string in the format above.
    """
    if pmins is None:
        return "0:00"
    if isinstance(pmins, decimal.Decimal):
        pmins = int(pmins)
    if not (isinstance(pmins, int) or isinstance(pmins, decimal.Decimal)):
        applog.debug("A call to hrsdec was passed type {} value {}".format(str(type(pmins)), pmins))
        raise Exception("Parameter to hrsdec is not an integer ({})".format(pmins))
    if pmins:
        return round(decimal.Decimal(pmins)/ decimal.Decimal(60),2)
    else:
        return ""

@app.template_filter()
def currency(pvalue):
    """
    Returns the time part of a datetime string
    :param pvalue: any float or integer
    :return:
    """
    applog.debug("in currency with {}".format(pvalue))
    if pvalue is None:
        return "$0"
    applog.debug("{}, ${:,.2f}".format(pvalue,pvalue))
    return "${:,.2f}".format(pvalue)