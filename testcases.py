import sendgrid
from flask_sqlalchemy import __version__
from flask import Flask
import logging
import inspect
from asc.schema import *
import unittest
import sys
from decimal import Decimal
from asc import db, create_app
from asc.mailer import ascmailer
#from csv import DictWriter,DictReader
import csv
# In order to trap errors from the engine
import sqlalchemy.exc
from sqlalchemy import text as sqltext, func

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail,Attachment,FileContent,FileName,FileType,Disposition
import base64

app = create_app()
log = app.logger


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class TestTbl(db.Model):
    """This is a test table cor check create and delete"""

    __tablename__ = "testtbl"

    id = db.Column(db.Integer, db.Sequence('test_id_seq'), primary_key=True)
    test_type = db.Column(db.String, comment="The type of record", nullable=False)
    test_key = db.Column(db.String, comment="The specific key for this type", nullable=False)
    test_desc = db.Column(db.String, comment="A generic Description")

    inserted = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    @db.validates('test_type', 'test_key')
    def convert_upper(self, key, value):
        return value.upper()


class FSqlalchemyTst(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        log.info("Set of tests on lists")
        log.info("Class Setup complete")
        log.info("test cases for flask sqlalchemy {}".format(__version__))
        cls.summary = []

    def setUp(self):
        log.info("Test ID:{}".format(self.id()))
        log.info("Test Description:{}".format(self.shortDescription()))

    def tearDown(self):
        statusmsg = 'Test Successul'
        log.info('Test Completed:{}'.format(self.id()))
        if hasattr(self, '_outcome'):
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
            if len(result.errors) > 0:
                log.error("There were errors in this test routine")
                self.logresults(result.errors)
                statusmsg = 'Test had a python error'
            if len(result.failures) > 0:
                log.error("This test failed")
                self.logresults(result.failures)
                statusmsg = 'Test Failed'
        self.summary.append({'id': self.id(), 'status': statusmsg})

    @classmethod
    def tearDownClass(cls):
        for s in cls.summary:
            cls.printout("Test: {} \t\t\tResult: {}".format(s['id'], s['status']))

    def logresults(self, txt):
        """
        txt is a list and the list can contain tuples and the tuble could be a long string delimtied by \n
        :param txt: a long string with line feeds delimiting the string
        :return: None
        """
        if len(txt) > 0:
            for listitem in txt:
                if isinstance(listitem, tuple):
                    for tupleitem in listitem:
                        if isinstance(tupleitem, str):
                            tuplelist = tupleitem.split('\n')
                            pass
                            for t in tuplelist:
                                log.info(t)

    @staticmethod
    def printout(message):
        if isinstance(message, str):
            sys.stderr.write('\n' + message + '\n')
        else:
            sys.stderr.write('\n' + str(message) + '\n')

    def logerror(self, e=None):
        """
        Where a an error is exepected to be raised, then this function should be called
        to add the error to the log file
        :param e: The error
        :return: None
        """
        caller = inspect.getouterframes(inspect.currentframe(), 2)[1][3]
        if e is None:
            log.info("test {} successful".format(caller))
        else:
            log.info("Test {} error raised".format(caller))
            if isinstance(e, str):
                log.info(e)
            if isinstance(e, sqlalchemy.exc.SQLAlchemyError):
                log.info(type(e))
                # log.info(e.statement)
                log.info(e.params)
                log.info(e.orig)
            else:
                self.printout(str(e))
                log.info(str(e))

    # def test000a(self):
    #     "test001a success"
    #     self.assertEquals(1, 1, msg="1 aint 1")
    #
    # def test000b(self):
    #     "test001a fail"
    #     self.assertEquals(1, 2, msg="1 aint 1")
    #
    # def test000c(self):
    #     "test001c forece fail"
    #     self.fail("test000c broke")
    #
    # def test000d(self):
    #     "untrapped error"
    #     ans = int('sdfd')

    def test001(self):
        """Can I access a flight"""
        try:
            flights = Flight.query.limit(10).all()
            self.assertEqual(len(flights), 10, "Ten records were not returned.")
        except Exception as e:
            self.logerror(e)
            self.fail("Error raised :{}".format(e))

    def test002(self):
        """Can I run direct sql"""
        try:
            # Note that there is a difference between the following statement with and without the ".fetchall"
            # at the end. fetchall returns a list object that you can perform a len() on whereas
            # without the fetchall you get a ResultProxy object which has no length
            recs = db.engine.execute("select id,pic,p2,ac_regn,takeoff,landed from flights limit 10;").fetchall()
            # print(recs)
            # for f in recs:
            #     print(f['pic'])
            self.assertEqual(len(recs), 10, "Ten records were not returned")
        except Exception as e:
            self.logerror(e)
            self.fail("Error raised :{}".format(e))

    def test003(self):
        """ Build the database """
        try:
            db.create_all()
        except Exception as e:
            self.fail(str(e))

    def test004(self):
        """ A user record is inserted"""
        # check if user exists
        try:
            if len(User.query.filter_by(name='testuser').all()) > 0:
                # get it
                testuser = User.query.filter_by(name='testuser').one()
                # delete it
                db.session.delete(testuser)
                # make sure you commit the change
                db.session.commit()
                self.printout("Deleted test user")
            # now create another
            oneuser = User(name='testuser')
            oneuser.fullname = 'Test User'
            oneuser.administrator = False
            # add and then commit
            db.session.add(oneuser)
            db.session.commit()
        except Exception as e:
            self.logerror(e)
            self.fail(str(e))

    ## So the rest of tests should follow a similar pattern as per testcase.py
    # all I needed to do was to replace self.ORM with "db.session"
    # and self.engine.execute with db.engine.execute.

    def test005(self):
        """An error is thrown if a duplicate is added"""
        try:
            # testuser was added by the previous and has a unqiue contstraint
            oneuser = User(name='testuser')
            oneuser.fullname = 'Test User'
            oneuser.administrator = False
            db.session.add(oneuser)
            db.session.commit()
            self.fail("No error detected n duplicate key")
        except sqlalchemy.exc.IntegrityError as e:
            # this is where we should end up.
            self.logerror(e)
            db.session.rollback()
            log.info('Correct error raised')
        # except sqlite3.IntegrityError as e:
        #     self.ORM.rollback()
        #     self.logerror(e)
        #     self.fail("Got the sqlite error instead of alchemy")
        except Exception as e:
            db.session.rollback()
            self.logerror(e)
            self.fail("Incorrect error raised :{}".format(e))

    def test006(self):
        """An update is successful"""
        try:
            if db.session.query(User).filter(User.name == 'testuser').count() > 0:
                # get it
                testuser = db.session.query(User).filter(User.name == 'testuser').one()
                # update it
                testuser.fullname = 'Joe Blow'
                db.session.commit()
                self.printout("Updated test user")
            else:
                self.fail('The record is not there....')
        except Exception as e:
            db.session.rollback()
            self.logerror(e)
            self.fail("An error occurred :{}".format(e))

    def test007(self):
        """A user cannot be added with a blank name"""
        try:
            oneuser = User(None)
            oneuser.administrator=False
            db.session.add(oneuser)
            db.session.commit()
            self.fail("No error detected n duplicate key")
        except sqlalchemy.exc.IntegrityError as e:
            # this is the correct result of the test
            db.session.rollback()
            self.logerror(e)
            log.info("Correct Error Received")
        except Exception as e:
            self.fail("Failed to trap correct error {}".format(e))

    def test008(self):
        """A users name cannot be changed to blank name"""
        try:
            testuser = db.session.query(User).filter(User.name == 'testuser').one()
            testuser.name = None
            db.session.commit()
            self.fail("No error was raised")
        except sqlalchemy.exc.IntegrityError as e:
            db.session.rollback()
            self.logerror(e)
            log.info("Correct Error Raised")

    def test009(self):
        """ a flight will change the regn to uppercase"""
        try:
            flt = Flight()
            flt.pic = 'Ray Burns'
            flt.tug_regn = 'rdw'
            flt.ac_regn = 'gmw'
            db.session.add(flt)
            db.session.commit()
            # the added record is automatically reloaded so:

            # what is the id of the record?
            log.info("The id of the inserted record is {}".format(flt.id))
            log.info("The new regn is {}".format(flt.ac_regn))
            self.assertEqual(flt.ac_regn, 'GMW', 'The case did not change')
        except sqlalchemy.exc.IntegrityError as e:
            self.printout(e.statement)
            self.printout(e.params)
            self.printout(e.orig)
            self.fail("Integrity errr raised: {}".format(e.orig))

    def test010(self):
        """ Verify direct sql"""
        anyerror = None
        try:
            dictlist = db.engine.execute("select * from users").fetchall()
            for r in dictlist:
                self.printout("name = {}, fullname = {}".format(r['name'], r['fullname']))
        except Exception as e:
            log.info(e)
            db.session.rollback()
            self.fail("error with simple select")
        try:
            # or using a shortcut
            dictlist = db.engine.execute("select * from flights where id > ? and takeoff < ?", 8274,
                                         datetime.datetime(2019, 3, 13, 14, 23))
            for r in dictlist:
                self.printout("id = {}, takeoff = {}".format(r['id'], r['takeoff']))
        except Exception as e:
            log.info(e)
            db.session.rollback()
            self.fail("error with select with parameters")
        try:
            # first col of first row:
            usercount = int(db.engine.scalar("select count(*) from users"))
            log.info("There are {} users".format(usercount))
        except Exception as e:
            log.info(e)
            db.session.rollback()
            self.fail("Error With count users via scalar")
        try:
            # updates are just as easy;
            db.engine.execute("Insert into users (name,fullname) values(?,?)", 'user{:06d}'.format(usercount + 1),
                              'Another user')  # note this autocommits
        except Exception as e:
            log.info(e)
            db.session.rollback()
            self.fail("Error With INSERT")
        try:
            # # multiple SQL is possible:
            conn = db.session.connection().connection
            cursor = conn.cursor()
            cursor.executescript("""
                select * from users;
                select * from slots;
                """)
            # """
            #  begin transaction;
            #     alter table user rename to _user;
            #     CREATE TABLE user (
            #           id INTEGER PRIMARY KEY AUTOINCREMENT,
            #           username TEXT UNIQUE NOT NULL,
            #           password TEXT NOT NULL,
            #           fullname TEXT,
            #           administrator boolean,
            #           email text
            #             );
            #
            #     insert into user (id, username, password, fullname, administrator)
            #         select id,username, password, fullname, administrator from _user;
            #
            #     drop table _user;
            #
            #     commit;
            #
            # """

        except Exception as e:
            log.info(e)
            db.session.rollback()
            self.fail("Error with multi sql")

    def test011(self):
        """Test valiations on records"""
        try:
            f = Flight()
            f.pic = "Ray"
            f.ac_regn = 'gmw'
            f.tug_regn = 'rdw'
            f.tow_pilot = "rc"
            f.linetype = 'XX'
            f.takeoff = datetime.datetime(2019, 3, 19, 10, 0).time()
            f.tug_down = datetime.datetime(2019, 3, 19, 10, 7).time()
            f.landed = datetime.datetime(2019, 3, 19, 11, 5).time()
            db.session.add(f)
            db.session.commit()
            self.fail("No Error Raised")
        except SchemaError as e:
            db.session.rollback
            log.info("Correct Schema Error Raised")
        except Exception as e:
            db.session.rollback
            self.logerror(e)
            self.fail("Invalid Error Raised")

    def test012(self):
        """Test Default Line Type"""
        try:
            f = Flight()
            f.pic = "Ray"
            f.ac_regn = 'gmw'
            f.tug_regn = 'rdw'
            f.tow_pilot = "rc"
            f.takeoff = datetime.datetime(2019, 3, 19, 10, 0)
            f.tug_down = datetime.datetime(2019, 3, 19, 10, 7)
            f.landed = datetime.datetime(2019, 3, 19, 11, 5)
            db.session.add(f)
            db.session.commit()
            self.assertEquals(f.linetype, "FL", "Default value for line type not correct")
        except Exception as e:
            db.session.rollback
            self.logerror(e)
            self.fail("Error Raised")

    def test013(self):
        """Test flight durations"""
        try:
            lastrec = int(db.engine.scalar("select max(id) from flights"))
            f = db.session.query(Flight).filter(Flight.id == lastrec).one()
            log.info("Last Glider time {}".format(f.glider_mins()))
            self.assertEquals(f.glider_mins(), 65, "Glider time incorrect")
            self.assertEquals(f.tow_mins(), 7, "Tug time incorrect")
        except Exception as e:
            raise (e)

    def test014(self):
        """Test Decimals work ok"""
        try:
            lastrec = int(db.engine.scalar("select max(id) from flights"))
            f = db.session.query(Flight).filter(Flight.id == lastrec).one()
            f.glider_charge = Decimal('23.54')
            # The problem here is that 23.54 like this is a float.
            f.other_charge = 16.50
            db.session.commit()
            log.info("Type of decimal is {}".format(type(f.glider_charge)))
            # Note that Decima('23.54') is not equal to Decimal(23.54)
            self.assertEquals(f.glider_charge, Decimal('23.54'), "Decimal Stored incorrect")
            self.assertEquals(f.glider_charge, Decimal(23.54).quantize(Decimal('.01')),
                              "Decimal Stored incorrect (quantize)")
        except Exception as e:
            raise e

    def test015(self):
        """Fail on create table that already exists"""
        try:
            TestTbl.__table__.create(db.engine)  # it will be created earlier by the create all.
        except sqlalchemy.exc.OperationalError as e:
            log.info("Correct error raised: {}".format(e))
        except Exception as e:
            self.fail("inError on drop table {}".format(e))

    def test016(self):
        """Drop a table that does not exist"""
        try:
            TestTbl.__table__.drop(db.engine)  # it will be created earlier by the create all.
            TestTbl.__table__.drop(db.engine)  # this should faile
        except sqlalchemy.exc.OperationalError as e:
            log.info("Correct error raised: {}".format(e))
        except Exception as e:
            self.fail("inError on drop table {}".format(e))

    def test017(self):
        """List all the tables in the db"""
        try:
            tbls = db.engine.table_names()
            self.assertGreater(len(tbls), 2, "There are less than two tables")
            self.assertIsInstance(tbls, list, "Tables is not a list")
            log.info(tbls)
        except Exception as e:
            self.fail(e)


    def test018(self):
        """Can I run direct sql, specifying parameters"""
        try:
            sqlstmt = """SELECT
                t0.id,
                t0.memberid,
                t0.transdate,
                t0.transtype,
                coalesce(t1.slot_desc, '') typedesc,
                t0.transsubtype,
                coalesce(t2.slot_desc, '') subtypedesc,
                t0.transnotes
                FROM membertrans AS t0 
                LEFT JOIN slots AS t1 
                    ON t1.slot_type = 'TRANSTYPE'  AND t1.slot_key = t0.transtype 
                LEFT JOIN slots AS t2 
                    ON t2.slot_type = t1.slot_desc  AND t2.slot_key = t0.transsubtype 
                WHERE t0.memberid = :member"""
            sql_to_execute = sqlalchemy.sql.text(sqlstmt)
            recs = db.engine.execute(sql_to_execute,member=8).fetchall()
            print(recs)
            for f in recs:
                print('{}\t{}\t{}'.format(f['transdate'], f['typedesc'], f['subtypedesc']))
            self.assertEqual(len(recs), 36, "36 records were not returned")
        except Exception as e:
            self.logerror(e)
            self.fail("Error raised :{}".format(str(e)))


    def test019(self):
        """Can I run joins, specifying parameters"""
        # The problem with the approach in test018, especially with respect to sqlite,
        # is that it does not data conversion, especially for dates.
        try:
            sqlstmt = """SELECT
                t0.id,
                t0.memberid,
                t0.transdate,
                t0.transtype,
                coalesce(t1.slot_desc, '') typedesc,
                t0.transsubtype,
                coalesce(t2.slot_desc, '') subtypedesc,
                t0.transnotes
                FROM membertrans AS t0 
                LEFT JOIN slots AS t1 
                    ON t1.slot_type = 'TRANSTYPE'  AND t1.slot_key = t0.transtype 
                LEFT JOIN slots AS t2 
                    ON t2.slot_type = t1.slot_desc  AND t2.slot_key = t0.transsubtype 
                WHERE t0.memberid = :member"""
            sql_to_execute = sqlalchemy.sql.text(sqlstmt)
            sql_to_execute = sql_to_execute.columns(transdate=db.Date)
            recs = db.engine.execute(sql_to_execute,member=8).fetchall()
            print(recs)
            for f in recs:
                print('{}\t{}\t{}'.format(f['transdate'], type(f['transdate']), f['subtypedesc']))
            self.assertEquals(len(recs), 36, "36 records were not returned")
        except Exception as e:
            self.logerror(e)
            self.fail("Error raised :{}".format(e))

    def test020(self):
        """ Verify data types"""
        f = db.session.query(Flight).get(8224)
        self.assertIsInstance(f.landed,datetime.datetime,'Landed is not a datetime')

    def test021(self):
        """ Using sql text but mapping to a class"""
        sql = sqltext("""
              select id,landed
              from flights
              where id = :pid
              """)
        sql = sql.columns(Flight.id,
                          Flight.landed
                          )
        thisset = db.session.query(Flight).from_statement(sql).params(pid=8224).all()
        self.assertIsInstance(thisset,list,'Query did not return  a list')
        f = thisset[0]
        self.assertIsInstance(f,Flight,'Query did not return  a Flight')
        self.assertIsInstance(f.landed,datetime.datetime, 'Landed is not a datetime')

    def test022(self):
        """ Using query to return datetime using mapper"""
        thisdate = datetime.date(2019,1,13)
        thisset = db.session.query(Flight).filter(func.date(Flight.takeoff)==thisdate).all()
        self.assertIsInstance(thisset, list, 'Query did not return  a list')
        f = thisset[0]
        self.assertIsInstance(f, Flight, 'Query did not return  a Flight')
        self.assertIsInstance(f.landed, datetime.datetime, 'Landed is not a datetime')

    def test023(self):
        """ Using scalar but checking type of datetime"""
        # lastdate = int(db.engine.scalar("select max(takeoff) from flights"))
        lastdate = db.session.query(func.max(Flight.takeoff).label("maxdate")).scalar()
        # for l in lastdate:
        #     print(l)
        print("{}:{}".format(lastdate,type(lastdate)))
        self.assertIsInstance(lastdate, datetime.datetime, 'takeoff is not a datetime')

    def test024(self):
        """ Using sql text but mapping to a class"""
        sql = sqltext("""
              select pic
              from flights
              where date(takeoff) = :date
              and pic <> ''
              union
              select p2
              from flights
              where date(takeoff) = :date
              and p2 <> ''
              """)
        thisset = [r[0] for r in (db.engine.execute(sql, date=datetime.date(2019,1,13)).fetchall())]
        for f in thisset:
            print(f)
        self.assertIsInstance(thisset, list, 'Query did not return  a list')

    def test025(self):
        """Test Null values for takeoff and landing"""
        try:
            f = Flight()
            f.pic = "Ray"
            f.ac_regn = 'gmw'
            f.tug_regn = 'rdw'
            f.tow_pilot = "rc"
            f.payment_note = 'test025'
            db.session.add(f)
            db.session.commit()
            print('takeoff is {}'.format(f.takeoff))
            self.fail("No Error Raised")
        except SchemaError as e:
            db.session.rollback
            log.info("Correct Schema Error Raised")
        except Exception as e:
            db.session.rollback
            self.logerror(e)
            self.fail("Invalid Error Raised")

class CSVTst(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        log.info("Set of tests on lists")
        log.info("Class Setup complete")
        log.info("test cases for csv {}".format(__version__))
        cls.summary = []

    def setUp(self):
        log.info("Test ID:{}".format(self.id()))
        log.info("Test Description:{}".format(self.shortDescription()))

    def tearDown(self):
        statusmsg = 'Test Successul'
        log.info('Test Completed:{}'.format(self.id()))
        if hasattr(self, '_outcome'):
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
            if len(result.errors) > 0:
                log.error("There were errors in this test routine")
                self.logresults(result.errors)
                statusmsg = 'Test had a python error'
            if len(result.failures) > 0:
                log.error("This test failed")
                self.logresults(result.failures)
                statusmsg = 'Test Failed'
        self.summary.append({'id': self.id(), 'status': statusmsg})

    @classmethod
    def tearDownClass(cls):
        for s in cls.summary:
            cls.printout("Test: {} \t\t\tResult: {}".format(s['id'], s['status']))

    def logresults(self, txt):
        """
        txt is a list and the list can contain tuples and the tuble could be a long string delimtied by \n
        :param txt: a long string with line feeds delimiting the string
        :return: None
        """
        if len(txt) > 0:
            for listitem in txt:
                if isinstance(listitem, tuple):
                    for tupleitem in listitem:
                        if isinstance(tupleitem, str):
                            tuplelist = tupleitem.split('\n')
                            pass
                            for t in tuplelist:
                                log.info(t)

    @staticmethod
    def printout(message):
        if isinstance(message, str):
            sys.stderr.write('\n' + message + '\n')
        else:
            sys.stderr.write('\n' + str(message) + '\n')

    def logerror(self, e=None):
        """
        Where a an error is exepected to be raised, then this function should be called
        to add the error to the log file
        :param e: The error
        :return: None
        """
        caller = inspect.getouterframes(inspect.currentframe(), 2)[1][3]
        if e is None:
            log.info("test {} successful".format(caller))
        else:
            log.info("Test {} error raised".format(caller))
            if isinstance(e, str):
                log.info(e)
            if isinstance(e, sqlalchemy.exc.SQLAlchemyError):
                log.info(type(e))
                log.info(e.statement)
                log.info(e.params)
                log.info(e.orig)
            else:
                self.printout(str(e))
                log.info(str(e))


    def test001(self):
        """Can I access a flight"""
        try:
            flights = Flight.query.limit(10).all()
            self.assertEquals(len(flights), 10, "Ten records were not returned.")
        except Exception as e:
            self.logerror(e)
            self.fail("Error raised :{}".format(e))

    def test002(self):
        """export csv"""
        try:
            flights = db.session.query(Flight).filter(Flight.pic == 'Ray Burns').all()
            print(len(flights))
            with open('gnutest.csv','w',newline=chr(10)) as csvf:
                fieldnames = ['id','date_opened','owner_id','billing_id','notes','date','desc','action','account','quantity',
                                'price','disc_type','disc_how','discount','taxable','taxincluded','tax_table','date_posted',
                                'due_date','account_posted','memo_posted','accu_splits']
                w = csv.DictWriter(csvf,fieldnames=fieldnames)
                w.writeheader()
                id = 1
                for f in flights:
#                    if f.glider_charge != 0 or f.other_charge != 0 or f.tow_charge != 0:
                    if f.tow_charge != 0:
                        thisrec = {}
                        thisrec['id'] = "FL-" + str(id).zfill(6)
                        thisrec['owner_id'] = '000006'
                        thisrec['desc'] = "Aerotow"
                        thisrec['notes'] = 'Flight {}'.format(f.id)
                        thisrec['account'] = 'Income:Flying Income:RDW Income:RDW Aerotows'
                        thisrec['quantity'] = '1'
                        thisrec['price'] = str(f.tow_charge)
                        thisrec['taxable'] =  'X'
                        thisrec['taxincluded'] = 'X'
                        w.writerow(thisrec)
                    if f.glider_charge != 0 and f.tow_charge != 0:
                        thisrec = {}
                        thisrec['desc'] = "Glider Time"
                        thisrec['notes'] = 'Flight {}'.format(f.id)
                        thisrec['account'] = 'Income:Flying Income:GNF Hire'
                        thisrec['quantity'] = '1'
                        thisrec['price'] = str(f.glider_charge)
                        thisrec['taxable'] = 'X'
                        thisrec['taxincluded'] = 'X'
                    w.writerow(thisrec)
                    id += 1
        except Exception as e:
            self.logerror(e)
            self.fail("Error raised :{}".format(e))

class sendgridtest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        log.info("Class Setup complete")
        log.info("test cases for sendgridmail {}".format(sendgrid.version.__version__))
        cls.summary = []

    def setUp(self):
        log.info("Test ID:{}".format(self.id()))
        log.info("Test Description:{}".format(self.shortDescription()))

    def tearDown(self):
        statusmsg = 'Test Successul'
        log.info('Test Completed:{}'.format(self.id()))
        if hasattr(self, '_outcome'):
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
            if len(result.errors) > 0:
                log.error("There were errors in this test routine")
                self.logresults(result.errors)
                statusmsg = 'Test had a python error'
            if len(result.failures) > 0:
                log.error("This test failed")
                self.logresults(result.failures)
                statusmsg = 'Test Failed'
        self.summary.append({'id': self.id(), 'status': statusmsg})

    @classmethod
    def tearDownClass(cls):
        for s in cls.summary:
            cls.printout("Test: {} \t\t\tResult: {}".format(s['id'], s['status']))

    def logresults(self, txt):
        """
        txt is a list and the list can contain tuples and the tuble could be a long string delimtied by \n
        :param txt: a long string with line feeds delimiting the string
        :return: None
        """
        if len(txt) > 0:
            for listitem in txt:
                if isinstance(listitem, tuple):
                    for tupleitem in listitem:
                        if isinstance(tupleitem, str):
                            tuplelist = tupleitem.split('\n')
                            pass
                            for t in tuplelist:
                                log.info(t)

    @staticmethod
    def printout(message):
        if isinstance(message, str):
            sys.stderr.write('\n' + message + '\n')
        else:
            sys.stderr.write('\n' + str(message) + '\n')

    def logerror(self, e=None):
        """
        Where a an error is exepected to be raised, then this function should be called
        to add the error to the log file
        :param e: The error
        :return: None
        """
        caller = inspect.getouterframes(inspect.currentframe(), 2)[1][3]
        if e is None:
            log.info("test {} successful".format(caller))
        else:
            log.info("Test {} error raised".format(caller))
            if isinstance(e, str):
                log.info(e)
            if isinstance(e, sqlalchemy.exc.SQLAlchemyError):
                log.info(type(e))
                log.info(e.statement)
                log.info(e.params)
                log.info(e.orig)
            else:
                self.printout(str(e))
                log.info(str(e))


    # def test001(self):
    #     """
    #     Send basic mail message
    #     :return:
    #     """
    #     try:
    #         print("api key is {}".format(app.config['SENDGRIDAPIKEY']))
    #         sg = sendgrid.SendGridAPIClient(api_key=app.config['SENDGRIDAPIKEY'])
    #         message = Mail(
    #             from_email = 'ascgliding@gmail.com',
    #             to_emails  = 'ray@rayburns.nz',
    #             subject  = 'Test Sendgrid email',
    #             html_content = '<B> Here </B> is my text'
    #             )
    #         response = sg.send(message)
    #         print(response.status_code, response.body, response.headers)
    #     except Exception as e:
    #         self.fail('Send grid failed with {}'.format(str(e)))
    #
    # def test002(self):
    #     """
    #     Send mail with attachment.
    #     :return:
    #     """
    #     try:
    #         print("api key is {}".format(app.config['SENDGRIDAPIKEY']))
    #         sg = sendgrid.SendGridAPIClient(api_key=app.config['SENDGRIDAPIKEY'])
    #         message = Mail(
    #             from_email = 'ascgliding@gmail.com',
    #             to_emails  = 'ray@rayburns.nz',
    #             subject  = 'Test Sendgrid attachment email',
    #             html_content = 'Please find attached the readme rst file.'
    #             )
    #
    #         with open('c:/users/rayb/pythonvenv/flask310/asc/README_USER.rst', 'rb') as f:
    #             data = f.read()
    #             f.close()
    #         encoded_data = base64.b64encode(data).decode()
    #
    #         attachedfile = Attachment(
    #             FileContent(encoded_data),
    #             FileName('README_USER.rst'),
    #             FileType('application/text'),
    #             Disposition('attachment')
    #         )
    #         message.attachment = attachedfile
    #
    #         response = sg.send(message)
    #         print(response.status_code, response.body, response.headers)
    #     except Exception as e:
    #         self.fail('Send grid failed with {}'.format(str(e)))

    def test003(self):
        """
        Test application class
        :return:
        """
        try:
            msg = ascmailer('Test Mailer Subject')
            # thisbody = "<table><tr><th>col1</th><th>col2</th></tr>"
            # thisbody = thisbody + "<tr><td>1</td><td>One</td></tr>"
            # thisbody = thisbody + "<tr><td>2</td><td>Two</td></tr>"
            # thisbody = thisbody + "<tr><td>3</td><td>Three</td></tr>"
            # thisbody = thisbody + "</table>"
            # msg.body = thisbody
            # msg.body = "Heree is the content"
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
            dictlist.insert(0,['ID','PIC','Landed'])
            msg.add_body_list(dictlist)
            msg.add_recipient('ray@rayburns.nz')
            msg.send()
            print(msg.response)
        except Exception as e:
            self.fail("Error raised :{}".format(e))

    # def test004(self):
    #     """Can I run direct sql, specifying parameters"""
    #     sql = sqltext("""
    #            select id,pic,landed
    #            from flights
    #            limit 5
    #            """)
    #     sql = sql.columns(Flight.id,
    #                       Flight.pic,
    #                       Flight.landed
    #                       )
    #     thisset = db.engine.execute(sql).fetchall()
    #     # turn into a dictionary
    #     dictlist = [[x._asdict() for x in thisset]]
    #     # This returns a list of tuples
    #     print(dictlist)
    #     self.assertIsInstance(dictlist, list, 'Query did not return  a list')
    #     f = dictlist[0]
    #     print(type(f))
    #     self.assertIsInstance(f, tuple, 'Query did not return  a tuple')

if __name__ == '__main__':
    case1 = unittest.TestLoader().loadTestsFromTestCase(FSqlalchemyTst)
    case2 = unittest.TestLoader().loadTestsFromTestCase(CSVTst)
    case3 = unittest.TestLoader().loadTestsFromTestCase(sendgridtest)
    # thissuite = unittest.TestSuite([case1])
    thissuite = unittest.TestSuite([case3])

    # The next line is critical tomae the rest work.....
    with app.app_context():
        unittest.TextTestRunner(verbosity=2).run(thissuite)
