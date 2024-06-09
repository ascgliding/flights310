import datetime
from dateutil.relativedelta import *
from asc.schema import *
from decimal import Decimal
from asc import db
from sqlalchemy import text as sqltext, delete, select

class ACMaint:

    class ACMaintError(Exception):
        pass

    class ACtask():

        def __init__(self,ptask):
            """ The object is instantiated with a MaintShedule item"""
            if ptask is not None:
                self.__id = ptask.id
                self.__ac_id = ptask.ac_id
                self.__last_done = ptask.last_done
                self.__last_done_reading = ptask.last_done_reading
                self.__stdtask = Tasks.query.get(ptask.task_id)
                self.__estimate_days = ptask.estimate_days
                self.__meter = None
                if ptask.meter_id is not None:
                    self.__meter = Meters.query.get(ptask.meter_id)
                self.__messages = []
                self.__last_meter_reading_date = None
                self.__last_meter_reading_value = None
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
            return self.__stdtask.recurrence_description()

        @property
        def task_basis(self):
            return self.__stdtask.task_basis

        @property
        def task_id(self):
            return self.__stdtask.id

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
                                     meterid = self.__meter.id).fetchall()
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
                                     meterid = self.__meter.id).fetchall()
            # list is a list of tuples.....
            if list is None or len(list) == 0:
                self.__messages.append('No meter readings')
                self.__last_meter_reading_date = None
                self.__last_meter_reading_value = None
                return
            self.__last_meter_reading_date = list[0][0]
            self.__last_meter_reading_value = list[0][1]
            return

        def __set_next_due(self):
            next_date = datetime.date(1900,1,1)
            cnext_date = None
            vnext_date = None
            if self.__last_done is not None:
                next_date = self.__last_done
            if self.__stdtask.task_basis == 'Calendar':
                # Start with last date
                if self.__stdtask.task_calendar_uom == 'Days':
                    cnext_date = next_date + datetime.timedelta(days=self.__stdtask.task_calendar_period)
                elif self.__stdtask.task_calendar_uom == 'Months':
                    cnext_date = next_date + relativedelta(months=self.__stdtask.task_calendar_period)
                elif self.__stdtask.task_calendar_uom == 'Years':
                    cnext_date = next_date + relativedelta(years=self.__stdtask.task_calendar_period)
                else:
                    self.__next_due_date = None
                    self.__next_due_message = 'Task is Calendar Based but UOM is not valid'
                    return
                if cnext_date < datetime.date.today():
                    self.__next_due_date = cnext_date
                    self.__next_due_message = 'Calendar Based Task already expired'
                    # that's it - get out of here
                    return
            if self.__stdtask.task_basis == 'Meter' or self.__stdtask.task_meter_id is not None:
                if self.__last_done_reading is None:
                    vnext_date = None
                else:
                    if self.__meter.uom == 'Time':
                        due_at_next_reading =  self.__last_done_reading + (self.__stdtask.task_meter_period * 60)
                    elif self.__meter.uom == 'Qty':
                        due_at_next_reading = self.__last_done_reading + self.__stdtask.task_meter_period # - self.__last_meter_reading_value
                    # if it as already gone past then it is due now
                    if self.__last_meter_reading_value is None:  # there are no readings
                        vnext_date = datetime.date.today()
                        self.__next_due_message = 'No meter readings in database'
                    if self.__daily_use is None:
                        vnext_date = datetime.date.today()
                        self.__next_due_message = 'Insufficient meter readings to determine an average'
                    elif due_at_next_reading < self.__last_meter_reading_value:
                        vnext_date = datetime.date.today()
                        self.__next_due_message = 'Meter based trigger already expired'
                    else:
                        if self.__meter.uom == 'Time' :
                            togo = self.__last_done_reading + (self.__stdtask.task_meter_period * 60) - self.__last_meter_reading_value
                        elif self.__meter.uom == 'Qty' :
                            togo = self.__last_done_reading + self.__stdtask.task_meter_period - self.__last_meter_reading_value
                        if togo <= 0:
                            self.__next_due_date = datetime.date.today()
                            self.__next_due_message = 'Meter based trigger already expired'
                            # That's it folks - we need to get on with it.
                            return
                        # how many days is that?
                        try:
                            daystogo = int(float(togo) / self.__daily_use)
                            vnext_date = datetime.date.today() + datetime.timedelta(days=daystogo)
                        except OverflowError as e:
                            vnext_date = None

            if cnext_date is None and vnext_date is None:
                self.__next_due_message  = 'Unable to determine Due Date'
                self.__next_due_date = next_date
            elif cnext_date is None:
                if self.__next_due_message is None:
                    self.__next_due_message  = 'Estimate based on Meter'
                self.__next_due_date = vnext_date
            elif vnext_date is None:
                self.__next_due_message  = 'Calendar based Task'
                self.__next_due_date = cnext_date
            elif cnext_date <= vnext_date:
                self.__next_due_message  = 'Calendar basis earlier than Meter estimate'
                self.__next_due_date = cnext_date
            else:
                self.__next_due_message  = 'Meter estimate earlier than calendar date'
                self.__next_due_date = vnext_date

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

    def __build_instance(self):
        # The sequence is important.  The meters must be built before the tasks
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

