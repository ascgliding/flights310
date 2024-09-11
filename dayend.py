import os
import sys

sys.path.insert(0, os.path.abspath(".."))

# from asc.schema import *
# from decimal import Decimal
from asc import db, create_app
from asc.mailer import ascmailer
# # In order to trap errors from the engine
# import sqlalchemy.exc
# from sqlalchemy import text as sqltext, func
# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail,Attachment,FileContent,FileName,FileType,Disposition
# import datetime

from asc.common import *
import re
import os
import arrow
from ics import Calendar
import requests

app = create_app()
log = app.logger

try:
    del os.environ['PYTHONHOME']
except KeyError as e:
    print("Pythonhome is not set anyway")
    pass  # don't care if it's not there

print("sys.path is ".format(sys.path))
print("pwd is {}".format(os.getcwd()))
print("pythonpath (in create_app dayend)_ is {}".format(os.environ['PYTHONPATH']))


def testmailer():
    """
    Test application class
    :return:
    """
    print("*** Send Test Email ***")
    try:
        msg = ascmailer('Test Mailer Subject')
        msg.add_body("Here is the Test Email")
        msg.add_body("</br> It is now " + datetime.datetime.now().strftime('%A %d-%b-%Y %H:%M'))
        msg.add_body("See table below<br>")
        sql = sqltext("""
               select id,pic,landed
               from flights
               limit 5
               """)
        sql = sql.columns(Flight.id,
                          Flight.pic,
                          Flight.landed
                          )
        thisset = db.engine.execute(sql).fetchall()
        dictlist = [x._asdict() for x in thisset]
        print(dictlist)
        print(list(dictlist))
        print(type(dictlist[0]))
        dictlist.insert(0, ['ID', 'PIC', 'Landed'])
        msg.add_body_list(dictlist)
        msg.add_recipient('ray@rayburns.nz')
        msg.send()
        print("Send grid status {}".format(msg.response.status_code))
        print(msg.response.headers)
    except Exception as e:
        print("Error raised :{}".format(e))


def update_auto_readings():
    print("*** Update Auto Meter Readings ***")
    sql = sqltext("""
        select t1.regn 
        from acmeters t0
        join aircraft t1 on t1.id = t0.ac_id 
        where auto_update  = 1
        group by 1
        """)
    rows = db.engine.execute(sql).fetchall()
    common_set_log(log)
    for row in rows:
        create_readings_from_flights(row[0])


def send_one_maintenance_email(address, thelist):
    # print('TESTING: Email to {}'.format(address))
    # print('About to send:')
    # for t in thelist:
    #     print(t)
    # send the email here
    msg = ascmailer('ASC Aircraft tasks due')
    # msg.add_body("Email should have gone to {}".format(address))
    msg.add_body_list(thelist)
    msg.add_recipient(address)
    msg.send()
    # print(msg.body)


def send_maintenance_emails():
    print("*** Maintenance Emails ***")
    sql = sqltext("""
    select 
        t1.regn
        from actasks t0
            left outer join aircraft t1 on t1.id = t0.ac_id 
        where warning_days  is NOT NULL 
        and warning_email is not null
        group by 1
    """)
    ac_with_warnings = db.engine.execute(sql).fetchall()
    common_set_log(log)
    emails = []
    for ac in ac_with_warnings:
        # print('Processing {}'.format(ac.regn))
        thisac = ACMaint(ac[0])
        for t in thisac.tasks:
            # print('Task {}'.format(t.description))
            if t.warning_days is not None:
                if t.next_due_date - relativedelta(days=t.warning_days) <= datetime.date.today():
                    addresses = re.split(',|;| |\|', t.warning_email)
                    # print('Addresses: {}'.format(emails))
                    for addr in addresses:
                        if "@" in addr:  # looks like an email and deals with any empty list items.
                            emails.append({'addr': addr,
                                           'ac': ac[0],
                                           'due': t.next_due_date,
                                           'duemsg': t.next_due_message,
                                           'task': t.description, })
    # we now have a list of email messages to send that we want to sort into address
    # order so that we only send each person one email.
    sortedlist = sorted(emails, key=lambda d: (d['addr'], d['ac'], d['due']))
    for s in sortedlist:
        print(s)
    print('Now Processing Sorted list')
    lastaddr = None
    emailtext = []
    # emailtext.append({'ac':'Regn',
    #                   'task':'Task',
    #                   'due':'Due',
    #                   'duemsg': 'Due Message'
    #                     })
    emailtext.append(['Regn', 'Task', 'Due', 'Message'])
    for tasks in sortedlist:
        if lastaddr is not None and lastaddr != tasks['addr']:
            send_one_maintenance_email(lastaddr, emailtext)
            emailtext.clear()
            emailtext.append(['Regn', 'Task', 'Due', 'Message'])
        emailtext.append({'ac': tasks['ac'],
                          'task': tasks['task'],
                          'due': tasks['due'],
                          'duemsg': tasks['duemsg']
                          })
        lastaddr = tasks['addr']
    # send the last one
    if len(emailtext) > 1:
        send_one_maintenance_email(lastaddr, emailtext)


def validate_all_readings():
    print("*** Validating Readings ***")
    sql = sqltext("""
        select t1.regn
            from meterreadings t0
            left outer join aircraft t1 on t1.id = t0.ac_id
            group by 1
    """)
    ac_with_readings = db.engine.execute(sql).fetchall()
    for ac in ac_with_readings:
        thisac = ACMaint(ac[0])
        print('Checking {}'.format(thisac.regn))
        for m in thisac.meters:
            print('Checking meter {}'.format(m.meter_name))
            for e in m.reading_errors:
                print(e)


def send_db():
    print('sending Database')
    print(os.getcwd())
    msg = ascmailer('Database Backup')
    # msg.add_body("Email should have gone to {}".format(address))
    msg.add_body("<html>Here is the Database Backup")
    msg.add_body("</br> It is now " + datetime.datetime.now().strftime('%A %d-%b-%Y %H:%M'))
    msg.add_body("</html>")
    msg.add_recipient('ray@rayburns.nz')
    msg.add_attachment('../instance/asc.sqlite')
    msg.send()


def send_med_bfr_to_cfi():
    mems = Pilot.query.filter(Pilot.active == True).filter(Pilot.email_med_warning == True).order_by(Pilot.surname).all()
    thatlist = Pilot.query.filter(Pilot.active == True).filter(Pilot.email_bfr_warning == True).order_by(Pilot.surname).all()
    for m in thatlist:
        if m not in mems:
            mems.append(m)
    count = 0
    email_list = [{'name': 'Name', 'medical': 'Medical', 'bfr': 'BFR', 'message': 'Message'}]
    for m in mems:
        msgs = []
        if m.bfr_due is not None and m.bfr_due < datetime.date.today():
            msgs.append('BFR Expired')
        elif m.bfr_due is not None and m.bfr_due < datetime.date.today() - relativedelta(days=60):
            msgs.append('BFR Coming Up')
        if m.medical_due is not None and m.medical_due < datetime.date.today():
            msgs.append('Medical Expired')
        elif m.medical_due is not None and m.medical_due < datetime.date.today() - relativedelta(days=60):
            msgs.append('Medical Coming Up')
        if len(msgs) > 0:
            count += 1
            email_list.append(
                {'Name': m.fullname, 'Medical': m.medical_due, 'BFR': m.bfr_due, 'Message': ','.join(msgs)})
    if count > 0:
        msg = ascmailer('Medical and BFR Status')
        msg.add_body_list(email_list)
        msg.add_recipient('ray@rayburns.nz')
        msg.send()


def send_stats_to_gnz(asat):
    """
    This is the text of the email from Max...
    The usual 6-monthy flight stats are now called for.  As a reminder of what is required (criteria), please see the attachment.
        To complete your return just reply to this message with the following information:
        1.    Number of aero-tow launches
        2.    Number of winch launches
        3.    Number of automobile launches
        4.    Number of self-launches
        5.    Total number of flights by club gliders (ie not private)
        -       Number of trial flights within this total
        -       Number of youth flights (under 26 years) within this total
        Number of First Solos – please also provide the names of your first-solos so we don’t double-count them!
    :return:
    """
    print('Sending Statistics')
    # Get the first solos....
    sql = sqltext('''
    select distinct t0.flt_date, t0.pic
        from flights t0
        join aircraft t1 on t0.ac_regn  = t1.regn 
        join pilots t2 on t0.pic = t2.fullname
        where t0.linetype  = 'FL'
        and t0.flt_date > DATETIME(:asat, '-6 month')
        -- the pic can't flown as pic before this flight date
        and t0.pic not in (select s0.pic from flights s0 where s0.pic  = t0.pic and s0.flt_date < t0.flt_date)
        -- double check the A Badge rating in case it is a member that has started flying after a long break
        and t0.pic in (
        select s1.fullname from membertrans s0
        join pilots s1 on s0.memberid = s1.id
        where s0.transtype = 'RTG'
        and s0.transsubtype  = 'AB'
        and s0.transdate > DATETIME(:asat, '-6 month'))
    ''')
    solos = db.engine.execute(sql, asat=asat.strftime('%Y-%m-%d')).fetchall()
    # get the other stats
    sql = sqltext('''
    select 'Number of flights by club gliders' stat,count(*) number
        from flights t0
        join aircraft t1 on t0.ac_regn  = t1.regn 
        where linetype = 'FL'
        and owner = 'ASC'
        and flt_date > DATETIME(:asat, '-6 month')
        union
        select 'Number of Aerotow Launches', count(*)
        from flights
        where linetype = 'FL'
        and tug_regn != 'SELF LAUNCH'
        and flt_date > DATETIME(:asat, '-6 month')
        union
        select 'Number of Self Launches', count(*)
        from flights
        where linetype = 'FL'
        and tug_regn = 'SELF LAUNCH'
        and flt_date > DATETIME(:asat, '-6 month')
        union
        select 'Number of flights by ATC gliders',count(*)
        from flights t0
        join aircraft t1 on t0.ac_regn  = t1.regn 
        where linetype = 'FL'
        and owner = 'ATC'
        and flt_date > DATETIME(:asat, '-6 month')
        Union
        select 'Number of flights in club gliders by Juniors',count(*)
        from flights t0
        join aircraft t1 on t0.ac_regn  = t1.regn 
        join pilots pic on pic.fullname = t0.pic 
        left outer join pilots p2 on p2.fullname = t0.p2
        where linetype = 'FL'
        and owner = 'ASC'
        and flt_date > DATETIME(:asat, '-6 month')
        and (strftime('%Y',:asat) -  strftime('%Y',pic.dob) < 26
        or strftime('%Y',:asat) -  strftime('%Y',p2.dob) < 26)
        UNION 
        select 'Number of Trial Flights',count(*)
        from flights t0
        join aircraft t1 on t0.ac_regn  = t1.regn 
        where linetype = 'FL'
        and owner = 'ASC'
        and flt_date > DATETIME(:asat, '-6 month')
        and ( upper(t0.payer) = 'TRIAL FLIGHT'
        or upper(t0.p2) like '%RIAL%')
    ''')
    stats = db.engine.execute(sql, asat=asat.strftime('%Y-%m-%d')).fetchall()
    # now email it
    msg = ascmailer('Statistics')
    msg.add_body('<html>For the period {} to {} <br>'.format(asat - relativedelta(months=6), asat))
    msg.add_body('<br>Here are the first solos<br>')
    # row one has to be titles
    msgdict = [x._asdict() for x in solos]
    msgdict.insert(0, ['Date of First Solo', 'Name'])
    msg.add_body_list(msgdict)
    msg.add_body('<br>')
    msg.add_body('Here are the other statistics')
    msgdict = [x._asdict() for x in stats]
    msgdict.insert(0, ['Statistic', 'Count'])
    msg.add_body_list(msgdict)
    msg.add_body('No winch Launching or Automobile Launches</html>')

    msg.add_recipient('ray@rayburns.nz')
    msg.add_recipient('lionelpnz@gmail.com')
    msg.send()


def getpilot(somename):
    names = somename.split(' ')
    if names[1] is not None:
        # print(names[1])
        thispilot = Pilot.query.filter(Pilot.member).filter(Pilot.active).filter(
            Pilot.fullname.ilike('%' + names[1] + '%')).first()
        if not thispilot:
            log.error('failed to find person {}'.format(somename))
            return None
        else:
            # print('{} found'.format(thispilot.email))
            return thispilot


def send_instr_email(thisdate, dayevents, instructor, tp, dp):
    """    :param events: a list of calendar event objects
    :param instructor: A Pilot object for the instructor
    :return:
    """
    if len(dayevents) != 0:
        # here is what we do with it.
        log.info('Event email being sent to {}'.format(instructor.fullname))
        msg = ascmailer('Events for this coming weekend')
        msg.add_body('<html>')
        msg.add_body('Events for {}'.format(thisdate))
        msg.add_body('<br>')
        if instructor is None:
            print('Date with no instructor {}'.format(thisdate))
        else:
            msg.add_body('Should have been emailed to {}'.format(instructor.email))
            msg.add_body('<br>')
            if tp:
                msg.add_body('Tow Pilot is {}'.format(tp.fullname))
                msg.add_body('<br>')
            if dp:
                msg.add_body('Duty Pilot is {}'.format(dp.fullname))
                msg.add_body('<br>')
            msg.add_body('<br>')
            msg.add_body('<B>Events to be aware of:</B>')
            msg.add_body('<br>')
            for de in dayevents:
                msg.add_body(de.name)
                msg.add_body('<br>')
            msg.add_body('<br>')
            msg.add_body('Please check the club calendar for extra details including contact numbers.')
            msg.add_body('You will need to contact effected individuals or groups if flying is cancelled for any reason.')
            msg.add_body('<br>')
            msg.add_body('<br>')
            msg.add_recipient('ray@rayburns.nz')
            msg.add_body('</html>')
            msg.send()


def update_roster(rdate, instr, tp, dp):
    """
    Update the roster table from the calendar
    :param date: The day in question
    :param instr: A pilot object for the instructor
    :param tp: A pilot object for the towie
    :param dp: A pilot object for the duty pilot
    :return:
    """
    thisroster = Roster.query.filter(Roster.roster_date == rdate).first()
    if not thisroster:
        newroster = Roster(roster_date=rdate)
        if instr is not None:
            newroster.roster_inst=instr.fullname,
        if tp is not None:
            newroster.roster_tp=tp.fullname
        if dp is not None:
            newroster.roster_dp=dp.fullname
        db.session.add(newroster)
    else:
        if instr is not None:
            thisroster.roster_inst = instr.fullname
        if tp is not None:
            thisroster.roster_tp = tp.fullname
        if dp is not None:
            thisroster.roster_dp = dp.fullname
    db.session.commit()


def geteventlist(file, startdate, enddate,prefix=None):
    if file.startswith('http'):
        icsfile = requests.get(file).text
        thiscal = Calendar(icsfile)
    else:
        with open(file, "r") as f:
            thiscal = Calendar(f.read())
    if thiscal is None:
        return []
    rtnlist = []
    for e in thiscal.timeline.included(arrow.get(startdate), arrow.get(enddate)):
        if prefix is not None:
            e.name = prefix + e.name
        rtnlist.append(e)
    return rtnlist


def processcalendar(startdate, enddate):
    # print(icalendar.__version__)

    print('processing roster between {} and {}'.format(startdate, enddate))

    # ray - private
    myurl = "https://calendar.google.com/calendar/ical/kc802pkua73iejv9oho665ae0k%40group.calendar.google.com/private-28220b1eeb53d8a34830f66b4ae92040/basic.ics"
    # asc - public calendar format
    ascurl = "https://calendar.google.com/calendar/ical/ascgliding%40gmail.com/public/basic.ics"
    # Atc
    atcurl = "https://calendar.google.com/calendar/ical/pegasus.flying.trust%40gmail.com/public/basic.ics"
    # This works fine:
    # with urlopen(myurl) as calendar:
    #     for line in calendar:
    #         print(line.decode('iso-8859-1'))

    # using icalendar
    # This is what we want live:
    # icsfile = requests.get(myurl).text
    # thiscal = Calendar(icsfile)
    # for testing:
    # with open("instance/basic.ics","r") as f:
    #     thiscal = Calendar(f.read())
    lastdate = None
    dayevents = []
    # There may be some events in the calendar that are not related to the roster
    # such as committee meetings and so on.  We don't want to process those
    date_has_roster = False
    # eventlist = geteventlist("../instance/basic.ics", startdate,enddate)
    # eventlist.extend(geteventlist("../instance/atc.ics", startdate,enddate, "GNW:"))
    eventlist = geteventlist(ascurl, startdate,enddate)
    eventlist.extend(geteventlist(atcurl, startdate,enddate, "GNW:"))
    # need to ensure everything is date order after appending the ATC items
    eventlist.sort(key=lambda x: x.begin)
    # print('Herer are all the events')
    # for e in eventlist:
    #     print("{} : {}".format(e.begin.to('local'), e.name))
    for event in eventlist:  # thiscal.timeline.included(arrow.get(startdate),arrow.get(enddate)):
        # print('Processing {} on {}'.format(event.name, event.begin.to('local').date()))
        # build a  list of all items on this date....
        if lastdate is None or event.begin.to('local').date() != lastdate:
            if date_has_roster and len(dayevents) != 0:
                send_instr_email(lastdate, dayevents, thisinstr, thistp, thisdp)
            # now get ready for the next day
            dayevents = []
            thisinstr = None
            date_has_roster = False
        # look for the duty items but don't add that to the day events
        thismatch = re.search("(^INS:)(.*)(TP:)(.*)(DP:)(.*)", event.name)
        if thismatch:
            # print(event.begin.to('local'), event.name, thismatch.group(2))
            thisinstr = getpilot(thismatch.group(2))
            thistp = getpilot(thismatch.group(4))
            thisdp = getpilot(thismatch.group(6))
            date_has_roster = True
            update_roster(event.begin.to('local').date(), thisinstr, thistp, thisdp)
        else:
            # it's not the duty event so add it to theseevents.
            dayevents.append(event)
        lastdate = event.begin.to('local').date()
    # End of loop - do last record
    if len(dayevents) != 0 and date_has_roster:
        # here is what we do with it.
        send_instr_email(lastdate, dayevents, thisinstr, thistp, thisdp)


if __name__ == '__main__':
    with app.app_context():
        # The execution time is 0400.
        log.info("Dayend started")
        # print("starting in test")
        # send_med_bfr_to_cfi()
        # print("finished med and bfr")
        # exit()
        # send updates on Fridays:
        if datetime.date.today().weekday() in [4]:  # Friday is 4.
            sdate = datetime.date.today()
            edate = sdate + relativedelta(days=7)
            log.info("Sending Event Emails")
            processcalendar(sdate, edate)
        # Send statistics on the first of the month
        if datetime.date.today().day == 1:
            log.info("Sending Statistic Emails")
            send_stats_to_gnz(datetime.date.today() - relativedelta(days=1))
        # testmailer()
        log.info("Updating Readings")
        update_auto_readings()
        log.info("Sending Maintenance Emails")
        send_maintenance_emails()
        # send me the database on Saturdays and Sundays.
        if datetime.datetime.today().weekday() in [6, 0]:
            log.info("Database Emailed during Dayend")
            send_db()
        # send me medical and BFR data on Friday Mornings.
        if datetime.datetime.today().weekday() in [4]:
            log.info("Sending Medical and BFR details")
            send_med_bfr_to_cfi()
        print("it ran")
