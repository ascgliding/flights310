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

class ACMaint:

    """
    This class contains three variables which are lists:
        tasks, meters and users.

    """

    class ACMaintError(Exception):
        pass

    class ACtask():

        def __init__(self,ptask):
            """ The object is instantiated with a ACTask item"""
            if ptask is not None:
                self.__id = ptask.id
                self.__ac_id = ptask.ac_id
                self.__last_done = ptask.last_done
                self.__last_done_reading = ptask.last_done_reading
                self.__warning_days = ptask.warning_days
                self.__warning_email = ptask.warning_email
                self.__stdtask = ptask.std_task_rec # Tasks.query.get(ptask.task_id)
                # applog.debug('creating task for {}'.format(self.__stdtask.task_description))
                self.__due_basis_date = ptask.due_basis_date
                self.__due_basis_reading = ptask.due_basis_reading
                self.__estimate_days = ptask.estimate_days
                self.__meter = None
                self.__meter = ptask.std_task_rec.std_meter_rec
                if self.__meter is None:
                    self.__contains_meter = False
                else:
                    self.__contains_meter = True
                self.__stdmeter = self.__stdtask.std_meter_rec
                self.__messages = []
                self.__last_meter_reading_date = None
                self.__last_meter_reading_value = None
                self.__validate_task()
                self.__set_last_reading()
                self.__daily_use = None
                self.__set_daily_use()
                self.__next_due_date = None
                self.__next_due_message = None
                self.__set_next_due()


        def __str__(self):
            if self.__stdtask.task_description is None:
                return "No description defined for task"
            else:
                return self.__stdtask.task_description

        @property
        def id(self):
            return self.__id

        @property
        def description(self):
            if self.__stdtask.task_description is None:
                return "No description defined for task"
            else:
                return self.__stdtask.task_description

        @property
        def recurrence_description(self):
            return self.__stdtask.recurrence_description

        @property
        def task_basis(self):
            return self.__stdtask.task_basis

        @property
        def task_id(self):
            return self.__stdtask.id

        @property
        def contains_meter(self):
            return self.__contains_meter

        @property
        def meter_id(self):
            if self.__meter is None:
                return None
            else:
                return self.__meter.id

        @property
        def meter_name(self):
            if self.__meter is None:
                return "Not applicable"
            else:
                return self.__meter.meter_name

        @property
        def last_meter_reading_date(self):
            return self.__last_meter_reading_date

        @property
        def last_meter_reading_value(self):
            return self.__last_meter_reading_value

        @property
        def next_due_date(self):
            return self.__next_due_date

        @property
        def days_to_go(self):
            return (self.__next_due_date - datetime.date.today()).days

        @property
        def next_due_message(self):
            return self.__next_due_message

        @property
        def daily_use(self):
            return self.__daily_use

        @property
        def last_done(self):
            return self.__last_done

        @property
        def last_done_reading(self):
            return self.__last_done_reading

        # days to use for the average day usage
        @property
        def estimate_days(self):
            return self.__estimate_days

        @property
        def messages(self):
            return self.__messages

        @property
        def due_basis_date(self):
            return self.__due_basis_date

        @property
        def due_basis_reading(self):
            return self.__due_basis_reading

        @property
        def warning_days(self):
            return self.__warning_days

        @property
        def warning_email(self):
            return self.__warning_email

        def __validate_task(self):
            if self.__stdtask.task_basis == 'Calendar':
                if self.__stdtask.task_calendar_uom not in ['Months', 'Years', 'Days']:
                    raise ACMaint.ACMaintError('Invalid UOM for calendar based task')
                if self.__stdtask.task_calendar_period is None:
                    raise ACMaint.ACMaintError('Calendar based task has invalid period')
                if self.__stdtask.task_calendar_period <= 0:
                    raise ACMaint.ACMaintError('Calendar based task has invalid period')
                if self.__stdtask.task_meter_id is not None:
                    if self.__meter is None:
                        raise ACMaint.ACMaintError('A task has a meter but that meter does not exist')
                # Calendar based task may have a meter.
            if self.__stdtask.task_basis == 'Meter':
                # A meter based task may NOT have a calendar
                if self.__stdtask.task_calendar_uom is not None:
                    raise ACMaint.ACMaintError('A standard task is meter based but has a calendar uom')
                if self.__stdtask.task_calendar_period is not None:
                    raise ACMaint.ACMaintError('A standard task is meter based but has a calendar period')
                if self.__meter is None:
                    raise ACMaint.ACMaintError('A meter based task has no associated meter')



        def __set_daily_use(self):
            if self.__meter is None:
                self.__messages.append('No Meter defined for this task')
                return None
            if self.__last_meter_reading_date is None:
                self.__messages.append('No Readings for this meter')
                return None
            sql = """
                select reading_date,meter_reading
                from meterreadings
                where reading_date >= :start_date
                and ac_id = :aircraft
                and meter_id = :meterid
                order by reading_date
                """
            sql_to_execute = sqlalchemy.sql.text(sql)
            # thisdate = datetime.date.today() - datetime.timedelta(days=90)

            thisdate = self.__last_meter_reading_date - datetime.timedelta(days=self.__estimate_days)
            sql_to_execute = sql_to_execute.columns(reading_date = db.Date,meter_reading = SqliteDecimal(10,2),ac_id = db.Integer)
            # sql_to_execute = sql_to_execute.columns(transdate=db.Date)
            # todo: What if the meter was reset during the period?  Need to check all readings...
            list = db.engine.execute(sql_to_execute, start_date=thisdate,
                                     aircraft = self.__ac_id,
                                     meterid = self.__stdmeter.id).fetchall()
            # list is a list of tuples.....
            if list is None:
                self.__messages.append('No meter readings')
                return None
            if len(list) < 2:
                self.__messages.append('Insufficient meter readings')
                return None
            daycount = (list[-1][0] - list[0][0]).days
            meterdiff = list[-1][1] - list[0][1]
            if meterdiff is None:
                self.__messages.append('Meter Delta is None')
                return None
            if daycount is None:
                self.__messages.append('Days Delta is None')
                return None
            if daycount <= 1:
                self.__messages.append('Insufficient Days')
                return None
            self.__daily_use =  float(meterdiff) / daycount

        def __set_last_reading(self):
            if self.__meter is None:
                self.__messages.append('No Meter defined for this task')
                return None
            sql = """
                select reading_date,meter_reading
                from meterreadings
                where ac_id = :aircraft
                and meter_id = :meterid
                order by reading_date desc
                limit 2
                """
            sql_to_execute = sqlalchemy.sql.text(sql)
            if self.__estimate_days is None:
                thisdate = datetime.date.today() - datetime.timedelta(days=90)
            elif self.__estimate_days < 30:
                thisdate = datetime.date.today() - datetime.timedelta(days=30)
            elif self.__estimate_days > 365:
                thisdate = datetime.date.today() - datetime.timedelta(days=365)
            else:
                thisdate = datetime.date.today() - datetime.timedelta(days=self.__estimate_days)
            sql_to_execute = sql_to_execute.columns(reading_date = db.Date,meter_reading = SqliteDecimal(10,2),ac_id = db.Integer)
            list = db.engine.execute(sql_to_execute,
                                     aircraft = self.__ac_id,
                                     meterid = self.__stdmeter.id).fetchall()
            # list is a list of tuples.....
            if list is None or len(list) == 0:
                self.__messages.append('No meter readings')
                self.__last_meter_reading_date = None
                self.__last_meter_reading_value = None
                return
            self.__last_meter_reading_date = list[0][0]
            self.__last_meter_reading_value = list[0][1]
            return

        def __add_period(self,pstartdate,pbasis,pquantum):
            '''
            This is a shorthand way of calculating a next date based on whether it is
            specified in days years or months.
            It is a separate function because we do it so often
            :param pstartdate:  The starting date
            :param pbasis: D,M or Y
            :param pquantum: The number of pbasii
            :return: The next date or None
            '''
            if pstartdate is None:
                return None
            if not isinstance(pbasis,str):
                return AttributeError('Basis must be a string.  Got {}'.format(type(pbasis)))
            if pbasis not in ['Days','Months','Years']:
                return AttributeError('Basis must be Days,Months,Years.  Got {}'.format(pbasis))
            if not isinstance(pquantum,int):
                return AttributeError('Quantum be an integer. Got {}'.format(type(pquantum)))
            if not isinstance(pstartdate,datetime.date):
                return AttributeError('Reference date must be a date.  Got {}'.format(
                    type(preference_date)))
            #
            if pbasis == 'Days':
                return pstartdate + relativedelta(days=pquantum)
            if pbasis == 'Months':
                return pstartdate + relativedelta(months=pquantum)
            if pbasis == 'Years':
                return pstartdate + relativedelta(years=pquantum)


        def __regenerate_from_date(self,plastdone,pbasis,pquantum,preference_date):
            '''
            Calculate the next due when the regeneration is at a specific date
            :param plastdone: Date task was last done
            :param pbasis: Either D,M,Y
            :param pquantum: The qty of pbasis
            :param preference_date: The starting reference Date
            :return: The calculated date or None if not applicaable
            '''
            if preference_date is None:
                return None
            if not isinstance(pbasis,str):
                return AttributeError('Basis must be a string.  Got {}'.format(type(pbasis)))
            if pbasis not in ['Days','Months','Years']:
                return AttributeError('Basis must be Days,Months,Years.  Got {}'.format(pbasis))
            if not isinstance(pquantum,int):
                return AttributeError('Quantum be an integer. Got {}'.format(type(pquantum)))
            if not isinstance(preference_date,datetime.date):
                return AttributeError('Reference date must be a date.  Got {}'.format(
                    type(preference_date)))
            if plastdone is not None:
                if not isinstance(plastdone,datetime.date):
                    return AttributeError('Last Done date must be a date.  Got {}'.format(
                            type(preference_date)
                    ))
            #
            # Now we know have a valid set of parameters
            #
            # starting at the reference date keep looking forward until we have a date that is
            # larger than the last done date.
            #
            # if it has never been done then add to the reference date.
            #
            if plastdone is None:
                return self.__add_period(preference_date,pbasis,pquantum)
            else:
                # it has been done so start at the reference date and keep adding quanta
                # until we get to a date greater than last done.
                nextdue = self.__add_period(preference_date,pbasis,pquantum)
                whilebrake = 0
                while nextdue < plastdone:
                    whilebrake += 1
                    if whilebrake > 5000:
                        raise ValueError('A while brake was exceeded')
                    nextdue = self.__add_period(nextdue, pbasis, pquantum)
                return nextdue

        def __regenerate_from_reading(self,plastdone,pregenerate_every,preference_reading):
            """
            Calculate a next due reading based on a reference reading.
            This is used when a task is regnerated from a nominal starting point.
            For example, 50 hours is done every 50 hours irrespective of the reading it was
            last done at.
            :param plastdone:  The Meter READING at which the task was last done
            :param pregenerate_every: The number of reading units for the task
            :param preference_reading: The starting point from which to calculate the next due
            :return: A date or none.
            """
            if plastdone is not None:
                if not isinstance(plastdone,decimal.Decimal) and not isinstance(plastdone,int):
                    raise AttributeError("Last done reading must be a decimal or integer.  Got {}".format(
                        type(plastdone)
                    ))
            if not isinstance(pregenerate_every,decimal.Decimal) and not isinstance(pregenerate_every,int):
                raise AttributeError("Regeneration must  decimal or integer.  Got {}".format(
                    type(pregenerate_every)
                ))
            if not isinstance(preference_reading,decimal.Decimal) and not isinstance(preference_reading,int):
                raise AttributeError("Reference reading must be a decimal or integer.  Got {}".format(
                    type(preference_reading)
                ))

            if plastdone is None:
                return pregenerate_every + preference_reading
            else:
                # applog.debug("plastdone {}".format(plastdone))
                # applog.debug("pregenerate_every {}".format(pregenerate_every))
                # applog.debug("preference_reading {}".format(preference_reading))
                if preference_reading < plastdone:
                    # Yes, I could do this one formula, but the loop is easier to follow.
                    nextduereading = preference_reading
                    while nextduereading <= plastdone:
                        nextduereading += pregenerate_every
                else:
                    # the reference reading is in front of the last done
                    nextduereading = preference_reading + pregenerate_every
                # applog.debug("nextduereading {}".format(nextduereading))
                return nextduereading


        def __set_next_due(self):
            # debugging trap:
            if self.__stdtask.task_description == 'test006':
                pass
            regenerate_from_exists = False
            next_date = datetime.date(1900,1,1)
            cnext_date = None
            vnext_date = None
            if self.__last_done is not None:
                next_date = self.__last_done
            #
            # ------------------  Calendar Readings -------------------------
            #
            if self.__stdtask.task_basis == 'Calendar':
                if self.__due_basis_date is not None:
                    # then we need to caluclate LAST as if it was from the regnerate point
                    cnext_date = self.__regenerate_from_date(next_date, self.__stdtask.task_calendar_uom,
                                                             self.__stdtask.task_calendar_period,
                                                             self.__due_basis_date)
                    regenerate_from_exists = True
                    self.__messages.append('Regneration from {}'.format(
                        datetime.date.strftime(self.__due_basis_date,"%d-%b-%Y")))

                else:
                    cnext_date = self.__add_period(next_date,self.__stdtask.task_calendar_uom,
                                                   self.__stdtask.task_calendar_period)
                    if cnext_date is None:
                        self.__next_due_date = None
                        self.__next_due_message = 'Task is Calendar Based but UOM is not valid'
                        return


                if cnext_date < datetime.date.today():
                    self.__next_due_date = cnext_date
                    self.__next_due_message = 'Calendar Based Task Expired'
                    # that's it - get out of here
                    if regenerate_from_exists:
                        self.__next_due_message += ' (R)'
                    self.__messages.append(self.__next_due_message)
                    return
            #
            # ---------------- Meter Readings ---------------------------
            #
            if self.__stdtask.task_basis == 'Meter' \
                    or self.__stdtask.task_meter_id is not None:
                    # or self.__meter is not None:
                due_at_next_reading = None
                if self.__due_basis_reading is not None and self.__due_basis_reading != 0:
                    regenerate_from_exists = True
                    self.__messages.append('A Meter based regeneration exists')
                    if self.__stdmeter.uom == 'Time':
                        due_at_next_reading = \
                            self.__regenerate_from_reading(self.__last_done_reading,
                                                         self.__stdtask.task_meter_period * 60,
                                                         self.__due_basis_reading)
                    if self.__stdmeter.uom == 'Qty':
                        due_at_next_reading = \
                            self.__regenerate_from_reading(self.__last_done_reading,
                                                         self.__stdtask.task_meter_period,
                                                         self.__due_basis_reading)
                if self.__last_done_reading is None:
                    vnext_date = None
                else:
                    if due_at_next_reading is None:
                        # No regenerate from was defined so determine next reading from last done.
                        if self.__stdmeter.uom == 'Time':
                            due_at_next_reading =  self.__last_done_reading + (self.__stdtask.task_meter_period * 60)
                        elif self.__stdmeter.uom == 'Qty':
                            due_at_next_reading = self.__last_done_reading + self.__stdtask.task_meter_period # - self.__last_meter_reading_value
                    # At this point due_at_next_reading contains the reading that the service is next due on
                    # irrespective of whether it had a regenerate_from override or not.
                    # if it as already gone past then it is due now
                    if self.__last_meter_reading_value is None:  # there are no readings
                        vnext_date = datetime.date.today()
                        self.__next_due_message = 'No meter readings in database'
                    if self.__daily_use is None:
                        vnext_date = datetime.date.today()
                        self.__next_due_message = 'Insufficient meter readings to determine an average'
                    else:  # IT has not expired so calculate when it is due.
                        if self.__stdmeter.uom == 'Time' :
                            if due_at_next_reading is None:
                                togo = self.__last_done_reading + (self.__stdtask.task_meter_period * 60) - self.__last_meter_reading_value
                            else:
                                togo = due_at_next_reading - self.__last_meter_reading_value
                        elif self.__stdmeter.uom == 'Qty' :
                            if due_at_next_reading is None:
                                togo = self.__last_done_reading + self.__stdtask.task_meter_period - self.__last_meter_reading_value
                            else:
                                togo = due_at_next_reading - self.__last_meter_reading_value
                        if togo <= 0:
                            self.__next_due_message = 'Meter Based Task Expired'
                        try:
                            if self.__daily_use == 0:
                                daystogo = 0
                            else:
                                daystogo = int(float(togo) / self.__daily_use)
                            vnext_date = datetime.date.today() + datetime.timedelta(days=daystogo)
                        except OverflowError as e:
                            vnext_date = None

            if cnext_date is None and vnext_date is None:
                self.__next_due_message  = 'Unable to determine Due Date'
                self.__next_due_date = next_date
            elif cnext_date is None:
                if self.__next_due_message is None:
                    self.__next_due_message  = 'Estimate Based on Meter'
                self.__next_due_date = vnext_date
            elif vnext_date is None:
                if self.__next_due_message is None:
                    self.__next_due_message  = 'Estimate Based on Calendar'
                self.__next_due_date = cnext_date
            elif cnext_date <= vnext_date:
                self.__next_due_message  = 'Calendar basis earlier than meter estimate'
                self.__next_due_date = cnext_date
            else:
                self.__next_due_message  = 'Meter estimate earlier than calendar date'
                self.__next_due_date = vnext_date
            if regenerate_from_exists:
                self.__next_due_message += ' (R)'
            self.__messages.append(self.__next_due_message)

    class ACMeter():

        def __init__(self,pacmeter):
            # class is instantiated with an acmeter object
            self.__id = pacmeter.id
            self.__ac_id = pacmeter.ac_id
            thisac = Aircraft.query.get(self.__ac_id)
            self.__regn  = thisac.regn
            self.__meter_id = pacmeter.meter_id
            thismeter = Meters.query.get(self.__meter_id)
            self.__meter_name = thismeter.meter_name
            self.__uom = thismeter.uom
            self.__entry_uom = pacmeter.entry_uom
            self.__entry_prompt = pacmeter.entry_prompt
            self.__entry_method = pacmeter.entry_method
            self.__meter_reset_date = pacmeter.meter_reset_date
            self.__meter_reset_value = pacmeter.meter_reset_value
            self.__auto_update = pacmeter.auto_update
            self.__last_reading_date = None
            self.__last_reading_value = None
            self.__last_reading_delta = None
            self.__last_reading_note = None
            sql = sqltext('''
            select reading_date,meter_reading,meter_delta,note
                from meterreadings
                where ac_id = :ac_id
                and meter_id = :meter_id
                and reading_date >= (select max(reading_date) 
                            from meterreadings 
                            where ac_id = :ac_id and meter_id = :meter_id)
                ''')
            sql = sql.columns(reading_date=db.Date, meter_reading=SqliteDecimal(10, 2),
                              meter_delta=SqliteDecimal(10, 2))
            list = db.engine.execute(sql, ac_id=self.__ac_id, meter_id=self.__meter_id).fetchall()
            if len(list) > 0:
                self.__last_reading_date = list[0]['reading_date']
                self.__last_reading_value = list[0]['meter_reading']
                self.__last_reading_delta = list[0]['meter_delta']
                self.__last_reading_note = list[0]['note']

        def __str__(self):
            if self.__meter_name is None:
                return "No name  defined for meter"
            else:
                return self.__regn + "/" + self.__meter_name

        def __repr__(self):
            return str(self)

        @property
        def id(self):
            return self.__id

        @property
        def meter_id(self):
            return self.__meter_id

        @property
        def meter_name(self):
            return self.__meter_name

        @property
        def uom(self):
            return self.__uom

        @property
        def entry_uom(self):
            return self.__entry_uom

        @property
        def entry_prompt(self):
            return self.__entry_prompt

        @property
        def entry_method(self):
            return self.__entry_method

        @property
        def auto_update(self):
            return self.__auto_update

        @property
        def meter_reset_date(self):
            return self.__meter_reset_date

        @property
        def meter_reset_value(self):
            return self.__meter_reset_value

        @property
        def last_reading_date(self):
            return self.__last_reading_date

        @property
        def last_meter_reading(self):
            return self.__last_reading_value

        @property
        def last_meter_reading_formatted(self):
            if self.__last_reading_value is None:
                return 'No Meter Readings'
            if self.__uom == 'Time':
                if self.__entry_uom == 'Hours:Minutes':
                    return str(int(self.__last_reading_value / 60)) + \
                        ':' + \
                           str(self.__last_reading_value % 60)
                else:
                    return round(self.__last_reading_value / 60, 2)
            else:
                return self.__last_reading_value

        @property
        def last_meter_delta(self):
            return self.__last_reading_delta

        @property
        def last_reading_note(self):
            return self.__last_reading_note

        @property
        def reading_errors(self):
            return self.__reading_errors()

        #
        # Public methods for a meter
        #

        def reset_delta(self):
            """
            Reset the delta's starting at the earliest reading
            :return: The number of changes that were made
            """
            readings = db.session.query(MeterReadings) \
                .filter(MeterReadings.ac_id == self.__ac_id) \
                .filter(MeterReadings.meter_id == self.__meter_id) \
                .order_by(MeterReadings.reading_date) \
                .all()
            change_count = 0
            if readings is not None:
                prev_reading = 0
                for r in readings:
                    if r.meter_delta != r.meter_reading - prev_reading :
                        r.meter_delta = r.meter_reading - prev_reading
                        change_count += 1
                    prev_reading = r.meter_reading
                if change_count > 0:
                    db.session.commit()
            return change_count

        def reset_readings(self):
            """
            Reset the readings based on the delta.
            The FIRST reading is not changed - it must be correct
            :return: The number of changes
            """
            readings = db.session.query(MeterReadings) \
                .filter(MeterReadings.ac_id == self.__ac_id) \
                .filter(MeterReadings.meter_id == self.__meter_id) \
                .order_by(MeterReadings.reading_date) \
                .all()
            change_count = 0
            if readings is not None:
                prev_reading = readings[0].meter_reading
                for r in readings[1:]:
                    if r.meter_reading != prev_reading + r.meter_delta :
                        r.meter_reading = prev_reading + r.meter_delta
                        change_count += 1
                    prev_reading = r.meter_reading
                if change_count > 0:
                    db.session.commit()
            return change_count

        def __reading_errors(self):
            readings = db.session.query(MeterReadings) \
                .filter(MeterReadings.ac_id == self.__ac_id) \
                .filter(MeterReadings.meter_id == self.__meter_id) \
                .order_by(MeterReadings.reading_date) \
                .all()
            ok = True
            messages = []
            if readings is not None:
                lastreading = readings[0].meter_reading
                for r in readings[1:]:
                    if r.meter_reading != lastreading + r.meter_delta:
                        ok = False
                        messages.append('Reading on {} is {}.  Should be {}'.format(r.reading_date, r.meter_reading,
                                                                                    lastreading + r.meter_delta))
                    lastreading = r.meter_reading
                    if len(messages) > 10:
                        return messages
            return messages




    class ACUser():

        def __init__(self, acmaintuser):
            self.__id = acmaintuser.id
            self.__user_id = acmaintuser.user_id
            self.__maint_level = acmaintuser.maint_level
            thisuser = User.query.get(self.__user_id)
            self.__fullname = thisuser.fullname

        @property
        def id(self):
            return self.__id

        @property
        def user_id(self):
            return self.__user_id

        @property
        def maint_level(self):
            return self.__maint_level

        @property
        def fullname(self):
            return self.__fullname

#
#  Definition of ACMaint Starts Here
#

    def __init__(self,pidentifier):
        self.__tasks = [] # list of task objects
        self.__meters = []  # list of installed meters
        self.__users = [] # list of user access
        # allow either the regn or id.
        thisac = None
        try:
            thisac = db.session.query(Aircraft).filter(Aircraft.id == int(pidentifier)).first()
        except:
            thisac = db.session.query(Aircraft).filter(Aircraft.regn == pidentifier).first()
        if thisac is None:
            raise self.ACMaintError('No Such Aircraft')
        # applog.debug('Instantiating ACMaint for {}'.format(thisac.regn))
        self.__id = thisac.id
        self.__regn = thisac.regn
        self.__build_instance()

    def __str__(self):
        return self.__regn

    @property
    def id(self):
        return self.__id

    @property
    def regn(self):
        return self.__regn

    @property
    def tasks(self):
        return self.__tasks

    @property
    def meters(self):
        return self.__meters

    @property
    def users(self):
        return self.__users

    @property
    def currentreadings(self):
        thisstr = ''
        for m in self.__meters:
            if thisstr != '':
                thisstr += ","
            thisstr += m.meter_name + ":"
            if m.last_reading_date is None:
                thisstr += "No Readings"
            else:
                thisstr += str(m.last_meter_reading_formatted) + \
                       " (" + m.last_reading_date.strftime('%d-%m-%y') + ')'
        return thisstr

    def __build_instance(self):
        # The sequence is important.  The meters must be built before the tasks
        try:
            self.__meters = []
            for m in db.session.query(ACMeters).filter(ACMeters.ac_id==self.__id):
                thismeter = self.ACMeter(m)
                self.__meters.append(thismeter)
            self.__tasks = []
            # thesetasks = db.session.query(MaintSchedule).filter(MaintSchedule.ac_id==self.__id)
            for t in db.session.query(ACTasks).filter(ACTasks.ac_id == self.__id):
                thistask = self.ACtask(t)
                self.__tasks.append(thistask)
            self.__users = []
            for u in db.session.query(ACMaintUser).filter(ACMaintUser.ac_id==self.__id):
                thisuser = self.ACUser(u)
                self.__users.append(thisuser)
        except Exception as e:
            raise ACMaint.ACMaintError('Error in maintenance object build for {} ({})'.format(
                self.__regn,
                str(e)))

    def get_security_level(self,puser_id):
        thisuser = [u for u in self.__users if u.user_id == puser_id]
        if len(thisuser) == 0:
            return None
        else:
            return thisuser[0].maint_level

    def add_new_task(self,pstdtaskid):
        if pstdtaskid is None:
            raise ValueError('The new task id must be number')
        if not isinstance(pstdtaskid,int):
            raise ValueError('The new task id must be an integer')
        stdtask = Tasks.query.get(pstdtaskid)
        if stdtask is None:
            raise ValueError('The new task id is not a standard task')
        print([a.task_id for a in self.__tasks])
        if pstdtaskid in [a.task_id for a in self.__tasks]:
            raise ValueError('This id is already a task for this aircraft')
        if stdtask.task_meter_id is not None:
            if stdtask.task_meter_id not in [m.meter_id for m in self.__meters]:
                raise ValueError('This task is for a meter that is not installed on this a/c')
        # All well so add
        thistask = ACTasks(ac_id=self.__id, task_id=pstdtaskid)
        if stdtask.task_meter_id is not None:
            thistask.meter_id = stdtask.task_meter_id
        if stdtask.task_basis == 'Meter':
            thistask.last_done_reading =  0
        if stdtask.task_basis == 'Calendar':
            thistask.last_done = datetime.date(1900,1,1)
        db.session.add(thistask)
        db.session.commit()
        self.__build_instance()

    def add_new_meter(self,pstdmeterid):
        if pstdmeterid is None:
            raise ValueError('The new meter id must be number')
        if not isinstance(pstdmeterid,int):
            raise ValueError('The new meter id must be an integer')
        stdmeter = Meters.query.get(pstdmeterid)
        if stdmeter is None:
            raise ValueError('The new meter id is not a standard meter')
        if pstdmeterid in [a.meter_id for a in self.__meters]:
            raise ValueError('This id is already a meter for this aircraft')
        # All well so add
        thismeter = ACMeters(ac_id=self.__id, meter_id=pstdmeterid)
        thismeter.entry_uom = 'Qty'
        thismeter.entry_method = 'Delta'
        thismeter.entry_prompt = 'Enter Change for ' + stdmeter.meter_name
        if stdmeter.uom == 'Time':
            thismeter.entry_uom = 'Decimal Hours'
            thismeter.entry_method = 'Reading'
            thismeter.entry_prompt = 'Enter final reading for ' + stdmeter.meter_name
        db.session.add(thismeter)
        db.session.commit()
        self.__build_instance()







