import sendgrid
from flask_sqlalchemy import __version__,model
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
from sqlalchemy.sql import select

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail,Attachment,FileContent,FileName,FileType,Disposition

from asc.oMaint import *

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
            print("Send grid status {}".format(msg.response.status_code))
            print(msg.response.headers)
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

class maintenance_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('in setup class')
        cls.initialise_maintenance_tables()
        cls.summary = []

    @classmethod
    def initialise_maintenance_tables(cls):
        print('Initialising ...')
        Tasks.__table__.drop(db.engine)
        Meters.__table__.drop(db.engine)
        ACMeters.__table__.drop(db.engine)
        MeterReadings.__table__.drop(db.engine)
        ACTasks.__table__.drop(db.engine)
        ACMaintUser.__table__.drop(db.engine)
        db.create_all()
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
        # Both of these are equivalent (once a flush operation has occurred.
        oTach = db.session.query(Meters).filter(Meters.meter_name == 'Tachometer').first()
        oAirframe = db.session.query(Meters).filter(Meters.meter_name == 'AirFrame').first()
        oLandings = db.session.query(Meters).filter(Meters.meter_name == 'Landings').first()
        # TODO:  add delete cascades to the database
        thistask = Tasks(task_description = '50 Hour Service', task_basis='Meter', task_meter_id=oAirframe.id, task_meter_period=50 )
        db.session.add(thistask)
        thistask = Tasks(task_description = '100 Hr Service', task_basis='Meter', task_meter_id=oAirframe.id, task_meter_period=100 )
        db.session.add(thistask)
        thistask = Tasks(task_description = '200 Hr Service', task_basis='Meter', task_meter_id=oAirframe.id, task_meter_period=200 )
        db.session.add(thistask)
        thistask = Tasks(task_description = '500 Hr Service', task_basis='Meter', task_meter_id=oAirframe.id, task_meter_period=500 )
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Replace Undercarriage Beam Bolts', task_basis='Meter', task_meter_id=oLandings.id, task_meter_period=1000 )
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Replace engine vibration dampers',
                         task_calendar_uom='Years', task_calendar_period = 2,
                         task_basis='Meter', task_meter_id=oAirframe.id, task_meter_period=50 )
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Replace Brake Fluid', task_basis='Calendar', task_calendar_uom = 'Years', task_calendar_period=4 )
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Transponder Check', task_basis='Calendar', task_calendar_uom = 'Years', task_calendar_period=2 )
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Altimeter Check', task_basis='Calendar', task_calendar_uom = 'Years', task_calendar_period=2)
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Replace Carburettor Flanges', task_basis='Meter', task_meter_id=oLandings.id, task_meter_period=200 )
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Replace Air Box', task_basis='Meter', task_meter_id=oLandings.id, task_meter_period=200)
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Replace Carburettor Bowden Cables', task_basis='Meter', task_meter_id=oLandings.id, task_meter_period=400)
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Replace All rubber hoses for fuel, oil and cooling', task_basis='Calendar', task_calendar_uom = 'Years', task_calendar_period=5,
                         task_meter_id = oAirframe.id, task_meter_period = 500)
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Radio Check', task_basis='Calendar', task_calendar_uom = 'Years', task_calendar_period=2)
        db.session.add(thistask)
        thistask = Tasks(task_description = 'ELT', task_basis='Calendar', task_calendar_uom = 'Years', task_calendar_period=2)
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Replace ELT Battery', task_basis='Calendar', task_calendar_uom = 'Years', task_calendar_period=5)
        db.session.add(thistask)
        thistask = Tasks(task_description = 'BRS Service')
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Biennial RA', task_basis='Calendar', task_calendar_uom = 'Years', task_calendar_period=2)
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Replace Engine', task_basis='Meter', task_meter_id = oTach.id, task_meter_period=2000)
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Nose Hook Replacement', task_basis='Meter', task_meter_id = oLandings.id, task_meter_period=2000)
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Belly Hook Replacement', task_basis='Meter', task_meter_id = oLandings.id, task_meter_period=2000)
        db.session.add(thistask)
        thistask = Tasks(task_description = '3 Monthly Glider Inspection', task_basis='Calendar', task_calendar_uom = 'Months', task_calendar_period=3)
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Annual Glider Inspection', task_basis='Calendar', task_calendar_uom = 'Years', task_calendar_period=1)
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Compass Swing', task_basis='Calendar', task_calendar_uom = 'Years', task_calendar_period=4)
        db.session.add(thistask)
        thistask = Tasks(task_description = 'Belts Replacement', task_basis='Calendar', task_calendar_uom = 'Years', task_calendar_period=12)
        db.session.add(thistask)
        thistask = Tasks(task_description = 'PLB Replacement', task_basis='Calendar', task_calendar_uom = 'Years', task_calendar_period=4)
        db.session.add(thistask)
        db.session.flush
        db.session.commit()
        # altimeterid = db.session.query(Tasks.id).filter(Tasks.task_description == 'Altimeter Check').scalar()
        # transponderid = db.session.query(Tasks.id).filter(Tasks.task_description == 'Transponder Check').scalar()
        # vibedampersid = db.session.query(Tasks.id).filter(Tasks.task_description == 'Replace engine vibration dampers').scalar()
        # fiftyhrid = db.session.query(Tasks.id).filter(Tasks.task_description == '50 Hour Service').scalar()
        # brakefluidid = db.session.query(Tasks.id).filter(Tasks.task_description == 'Replace Brake Fluid').scalar()
        oAltimeter = db.session.query(Tasks).filter(Tasks.task_description == 'Altimeter Check').first()
        oTransponder = db.session.query(Tasks).filter(Tasks.task_description == 'Transponder Check').first()
        oVibedampers = db.session.query(Tasks).filter(Tasks.task_description == 'Replace engine vibration dampers').first()
        oFiftyhr = db.session.query(Tasks).filter(Tasks.task_description == '50 Hour Service').first()
        oBrakefluid = db.session.query(Tasks).filter(Tasks.task_description == 'Replace Brake Fluid').first()
        oBeambolts = db.session.query(Tasks).filter(Tasks.task_description == 'Replace Undercarriage Beam Bolts').first()
        oElastometrics = db.session.query(Tasks).filter(Tasks.task_description == 'Replace All rubber hoses for fuel, oil and cooling').first()
        oEngine = db.session.query(Tasks).filter(Tasks.task_description == 'Replace Engine').first()
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        # A/C meters
        thisrow = ACMeters(ac_id = oRDW.id, meter_id = oAirframe.id, entry_uom="Decimal Hours", entry_prompt="Enter the incremental hours for the event")
        db.session.add(thisrow)
        thisrow = ACMeters(ac_id = oRDW.id, meter_id = oTach.id, entry_uom="Hours:Minutes", entry_prompt="Enter the final Meter Reading")
        db.session.add(thisrow)
        thisrow = ACMeters(ac_id = oRDW.id, meter_id = oLandings.id, entry_uom="Qty", entry_prompt="Enter the number of landings for the day")
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
                    # if count < 90:
                    #     continue
                    # if count > 125:
                    #     break
                    # print(row)

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
                                print('Null Meter reading for Air frame on {} {}/{}'.format(thisreading.reading_date, thisreading.meter_reading, thismeter.meter_delta))
                    except Exception as e:
                        print('No Airframe {}'.format(str(e)))
                        pass

                    # Tacho

                    try:
                        #TODO: Duplicate meter readings on same day....
                        # see 19 Feb 2022
                        if row['Tacho'] != '' or row['Daily Tacho Hours'] != '':
                            thisreading = MeterReadings()
                            thisreading.ac_id = oRDW.id
                            thisreading.meter_id = oTach.id
                            thisreading.reading_date = datetime.datetime.strptime(row['Date'], "%Y-%m-%d")
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
                                print('Null Meter reading for Tach on {}: {}/{}'.format(thisreading.reading_date, thisreading.meter_reading, thisreading.meter_delta))
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
                                thisreading.meter_delta = thisreading.meter_reading - last_landings_reading
                            if row['Total Landings'] == '':  #Then we must have the delta
                                thisreading.meter_reading = last_landings_reading + thisreading.meter_delta
                            thisreading.note = row['Tow Pilot']
                            last_landings_reading = thisreading.meter_reading
                            last_landings_delta = thisreading.meter_delta
                            if thisreading.meter_delta is not None and thisreading.meter_reading is not None:
                                db.session.add(thisreading)
                            else:
                                print('Null Meter reading for Landings on {}'.format(thisreading.reading_date))
                    except Exception as e:
                        print('No landings: {} row {}'.format(str(e),count))
                        pass
            print('{} records added'.format(count))
        # Maintenance Schedule

        # 50 hour service
        thissched = ACTasks()
        thissched.ac_id = oRDW.id
        thissched.task_id = oFiftyhr.id
        thissched.meter_id = oAirframe.id
        thissched.last_done_reading = 1502
        db.session.add(thissched)

        thissched = ACTasks()
        thissched.ac_id = oRDW.id
        thissched.task_id = oBeambolts.id
        thissched.meter_id = oLandings.id
        thissched.last_done_reading = 9075
        thissched.estimate_days = 180
        db.session.add(thissched)
        db.session.flush()

        thissched = ACTasks()
        thissched.ac_id = oRDW.id
        thissched.task_id = oEngine.id
        thissched.meter_id = oTach.id
        thissched.last_done_reading = 548 * 60 + 42
        thissched.estimate_days = 365
        db.session.add(thissched)
        db.session.flush()


        thissched = ACTasks()
        thissched.ac_id = oRDW.id
        thissched.task_id = oBrakefluid.id
        thissched.meter_id = None
        thissched.estimate_days = 365
        thissched.last_done = datetime.date(2023,7,1)
        db.session.add(thissched)

        thissched = ACTasks()
        thissched.ac_id = oRDW.id
        thissched.task_id = oElastometrics.id
        thissched.meter_id = oAirframe.id
        # thissched.meter_reading_next_due_value = (1847.88 * 60)
        # thissched.meter_reading_next_due_date = datetime.date(2028,6,5)
        thissched.estimate_days = 365
        thissched.last_done = datetime.date(2023,6,5)
        thissched.last_done_reading = round(1347.8 * 60)
        db.session.add(thissched)


        # history
        db.session.commit()  # must be committed for use of con.execute
        with db.engine.connect() as con:

            stmt = sqltext('''
                        insert into mainthistory (ac_id,task_id,task_description,meter_id,meter_reading,history_date)
                        values(:ac_id,:task_id,:task_description,:meter_id,:meter_reading,:history_date)
                    ''')

            history=[]
            history.append({'ac_id': oRDW.id, 'task_id':oBeambolts.id, 'task_description':'Undercarriage Beam Bolts', 'meter_id':2, 'meter_readings':[1120,2071,2468,3623,4289,5080,6328,7272,8181,9075], 'history_date':None})
            history.append({'ac_id': oRDW.id, 'task_id':oFiftyhr.id, 'task_description':'50 Hour', 'meter_id':4, 'meter_readings':[206.7,306.7,350.61,403.73,470.04,519.22,567.51,623.54,661.31,710.08,760.78,802,859.1,896.28,949.8,992.78,1045.53,1095.93,1102,1148.72,1210.2,1242.94,1300.49,1347.88,1407,1456.33], 'history_date':None})
            history.append({'ac_id': oRDW.id, 'task_id':oVibedampers.id, 'task_description':'Replace vibration Dampers', 'meter_id':4, 'meter_readings':[250,403.75,567.51,760.78,949.8,1346.33], 'history_date':None})
            history.append({'ac_id': oRDW.id, 'task_id':oBrakefluid.id, 'task_description':'Brake Fluid change', 'meter_id':1, 'meter_readings':[41030,41944,43405,44166,45137], 'history_date':None})
            history.append({'ac_id': oRDW.id, 'task_id':oTransponder.id, 'task_description':'Transponder Check', 'meter_id':1, 'meter_readings':[41264,41964,92944,43588,44350,45216], 'history_date':None})
            for h in history:
                data = []
                for r in h['meter_readings']:
                    data.append({'ac_id': h['ac_id'], 'task_id':h['task_id'], 'task_description':h['task_description'], 'meter_id':h['meter_id'], 'meter_reading':r * 100, 'history_date':None})
                for line in data:
                    con.execute(stmt, **line)



        db.session.flush()
        thishist = MaintHistory()
        thishist.ac_id = oRDW.id
        thishist.task_id = oFiftyhr.id
        thishist.task_description = "50Hr Oil Change"


        db.session.commit()

        #users
        me = User.query.filter_by(name='rayb').first()
        peter = User.query.filter_by(name='peebee89').first()
        oGHU = Aircraft.query.filter_by(regn='GHU').first()

        db.session.add(ACMaintUser(ac_id = oRDW.id, user_id = me.id, maint_level='All'))
        db.session.add(ACMaintUser(ac_id = oGHU.id, user_id = me.id, maint_level='Readings'))
        db.session.add(ACMaintUser(ac_id = oRDW.id, user_id = peter.id, maint_level='All'))

        db.session.commit()


    @classmethod
    def string_to_duration(cls,timestr):
        print('timestr {}'.format(timestr))
        if not isinstance(timestr,str):
            return 0
        bits = timestr.split(':')
        hrs = int(bits[0])
        mins = int(bits[1])
        print("hrs: {}, mins: {}".format(hrs,mins))
        return hrs + ((mins / 60)/ 100)


    def test001(self):
        print('here')
        self.assertTrue(True,'here i am')

class maintenance_test_ac_obj(unittest.TestCase):


    def test001(self):
        """ Instantiage object by id"""
        try:
            thismnt = ACMaint(2)
        except Exception as e:
            self.fail("could not get object {}".format(str(e)))

    def test002(self):
        """ Instantiage object by id - failure"""
        try:
            thismnt = ACMaint(87676)
        except Exception as e:
            pass
        self.assertRaises(ACMaint.ACMaintError)

    def test003(self):
        """ Instantiate object by regn"""
        try:
            thismnt = ACMaint('RDW')
        except Exception as e:
            self.fail("could not get object {}".format(str(e)))

    def test004(self):
        """ Instantiage object by regn - failure"""
        try:
            thismnt = ACMaint('ERAD')
        except Exception as e:
            pass
        self.assertRaises(ACMaint.ACMaintError)

    def test005(self):
        """ Correct Regn"""
        thismnt = ACMaint('RDW')
        self.assertEqual(thismnt.regn,"RDW","Wrong Regn")

    def test006(self):
        """ Count of tasks"""
        thismnt = ACMaint('RDW')
        self.assertGreater(len(thismnt.tasks), 2, "there should be more than two tasks defined")

    def test007(self):
        """ lsit of tasks"""
        thismnt = ACMaint('RDW')
        for t in thismnt.tasks:
            print("{} : {}".format(t.id,t.description))
            # print("------------------------")
            # for a in [a for a in dir(t) if not a.startswith('_')]:
            #     print("{} : {} : {}".format(t,a,getattr(t,a)))
        self.assertGreater(len(thismnt.tasks), 2, "there should be more than two tasks defined")

    # def test008(self):
    #     """ next due beam bolts"""
    #     thismnt = ACMaint('RDW')
    #     for t in thismnt.tasks:
    #         print("------------------------")
    #         print(t.messages)
    #     self.assertGreater(len(thismnt.tasks), 2, "there should be more than two tasks defined")

    def test009(self):
        """ lsit attributes of one task"""
        thismnt = ACMaint('RDW')
        for t in [x for x in thismnt.tasks if x.id == 3]:
            print("------------------------")
            print(dir(t))
            for a in [a for a in dir(t) if not a.startswith('_')]:
                print("{} : {} : {}".format(t,a,getattr(t,a)))
        self.assertGreater(len(thismnt.tasks), 2, "there should be more than two tasks defined")

    def test010(self):
        """ Add a new task with incorrect None parameter """
        thisac  = ACMaint('RDW')
        with self.assertRaises(ValueError):
            thisac.add_new_task(None)

    def test011(self):
        """ Add a new task with incorrect invalid number parameter """
        thisac  = ACMaint('RDW')
        with self.assertRaises(ValueError):
            thisac.add_new_task('not a number')

    def test012(self):
        """ Add a new task with incorrect not a task parameter """
        thisac  = ACMaint('RDW')
        with self.assertRaises(ValueError):
            thisac.add_new_task(6567)

    def test013(self):
        """ Add a new task with incorrect task already there parameter """
        thisac  = ACMaint('RDW')
        with self.assertRaises(ValueError):
            thisac.add_new_task(1)

    def test014(self):
        """ Add a new task with valid parameter """
        thisac  = ACMaint('RDW')
        # This test can only be performed once after that data is loaded
        if 20  in [a.task_id for a in thisac.tasks]:
            print('Test 14 skipped')
            return
        thisac.add_new_task(20)
        if 20  not in [a.task_id for a in thisac.tasks]:
            self.fail('Newly added task missing')


    def test025(self):
        """ Count of meters"""
        thismnt = ACMaint('RDW')
        self.assertGreater(len(thismnt.meters), 2, "there should be more than two meters defined")

    def test026(self):
        """ lsit of meters"""
        thismnt = ACMaint('RDW')
        # for t in thismnt.meters:
            # print("{} : {}".format(t.id,t.meter_name))
        self.assertGreater(len(thismnt.tasks), 2, "there should be more than two meters defined")

    def test027(self):
        """ Add a new meter with valid parameter """
        thisac  = ACMaint('GHU')
        # This test can only be performed once after that data is loaded
        if 2  in [a.meter_id for a in thisac.meters]:
            self.skipTest('Skipped dur meter already existing')
        # otherwise
        thisac.add_new_meter(2)
        if 2  not in [a.meter_id for a in thisac.meters]:
            self.fail('Newly added meter missing')

    def test029(self):
        """List Meters"""
        thisac = ACMaint('RDW')
        for t in [x for x in thisac.meters if x.meter_id == 3]:
            print("------------------------")
            print(dir(t))
            for a in [a for a in dir(t) if not a.startswith('_')]:
                print("{} : {} : {}".format(t,a,getattr(t,a)))

    def test030(self):
        """Test that an existing reading has correct last reading date"""
        thisac = ACMaint('RDW')
        airframe = [m for m in thisac.meters if m.meter_name == 'AirFrame'][0]
        self.assertEqual(airframe.last_reading_date, datetime.date(2024,4,6), 'Incorrect Last reading date')

    def test031(self):
        """Test that an existing reading has correct last reading value"""
        thisac = ACMaint('RDW')
        airframe = [m for m in thisac.meters if m.meter_name == 'AirFrame'][0]
        self.assertEqual(airframe.last_meter_reading, 87923, "Incorrect last meter value")

    def test031(self):
        """Test that an existing reading has correct last reading delta"""
        thisac = ACMaint('RDW')
        airframe = [m for m in thisac.meters if m.meter_name == 'AirFrame'][0]
        self.assertEqual(airframe.last_meter_delta, 20, "Incorrect last meter delta")

    def test032(self):
        """ Test that last task avg days correct for 365 days"""
        thisac = ACMaint('RDW')
        ReplaceEngine = [t for t in thisac.tasks if str(t) == 'Replace All rubber hoses for fuel, oil and cooling'][0]
        self.assertEqual(round(ReplaceEngine.daily_use,3), 20.468, "Incorrect last meter delta")

    def test033(self):
        """ Test that last task avg days correct for 90 days"""
        thisac = ACMaint('RDW')
        hr50 = [t for t in thisac.tasks if str(t) == '50 Hour Service'][0]
        self.assertEqual(round(hr50.daily_use,3), 20.489, "Incorrect last meter delta")



    def test040(self):
        """ Test users"""
        thisac = ACMaint('RDW')
        for u in thisac.users:
            print(u.maint_level,u.fullname)
        me = User.query.filter_by(name='rayb').one_or_none()
        print(thisac.get_security_level(me.id))

    def test041(self):
        """ Test Meter based task"""
        thisac = ACMaint('RDW')
        thistask = [ t for t in thisac.tasks if str(t) == 'Replace Undercarriage Beam Bolts' ][0]
        # set the last done value
        dbrec = ACTasks.query.get(thistask.id)
        thetask = Tasks.query.get(thistask.task_id)
        print(dbrec.id)
        print(thetask.task_description)
        dbrec.last_done = datetime.date(2024,6,1)
        dbrec.last_done_reading = 10000
        db.session.commit()
        thisac = ACMaint('RDW')
        thistask = [ t for t in thisac.tasks if str(t) == 'Replace Undercarriage Beam Bolts' ][0]
        print("Avg Daily use {}".format(thistask.daily_use))
        daysaway = (thistask.next_due_date - datetime.date.today()).days
        print(daysaway)
        print(thistask.next_due_date)
        self.assertLess(daysaway,3650,"Target meter value incorrect")

    def test042(self):
        """
        Object with no tests and no meters
        :return:
        """
        try:
            ac = ACMaint('RDW')
            for t in ac.tasks:
                print(t.description)
                print(t.next_due_date)
                print(t.days_to_go)
        except Exception as e:
            self.fail('Did not load:{}'.format(str(e)))

class maintenance_time_values(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('in setup class')
        cls.initialise_maintenance_tables()
        cls.summary = []

    @classmethod
    def initialise_maintenance_tables(cls):
        print('Initialising ...')
        MeterReadings.__table__.drop(db.engine)
        db.create_all()

    def test001(self):
        # thisrdg = MeterReadings(ac_id = 2, meter_id = 2, reading_date = datetime.date.today(),meter_reading = '23.45')
        thisrdg = MeterReadings(ac_id = 2, meter_id = 2, meter_reading = 10, note='Integer hours')
        db.session.add(thisrdg)
        thisrdg = MeterReadings(ac_id = 2, meter_id = 2, meter_reading = 10.3, note='float')
        db.session.add(thisrdg)
        thisrdg = MeterReadings(ac_id = 2, meter_id = 2, meter_reading = "5:30", note='string in hrs mins')
        db.session.add(thisrdg)
        thisrdg = MeterReadings(ac_id = 2, meter_id = 2, meter_reading = "5.75", note='string in decimal hours')
        db.session.add(thisrdg)
        thisrdg = MeterReadings(ac_id = 2, meter_id = 2, meter_reading = datetime.timedelta(hours=3,minutes=14), note='timedelta')
        db.session.add(thisrdg)
        thisrdg = MeterReadings(ac_id = 2, meter_id = 2, meter_reading = 0.83, note='should be 50 mins')
        db.session.add(thisrdg)
        thisrdg = MeterReadings(ac_id = 2, meter_id = 2, meter_reading = 0.81, note='should be 49 mins')
        db.session.add(thisrdg)
        thisrdg = MeterReadings()
        thisrdg.ac_id = 2
        thisrdg.meter_id = 2
        thisrdg.meter_reading = "1:30"
        thisrdg.note = "What is the value now?"
        print(thisrdg.meter_reading)
        db.session.add(thisrdg)
        db.session.commit()

    def test002(self):
        # thisrdg = MeterReadings(ac_id = 2, meter_id = 2, reading_date = datetime.date.today(),meter_reading = '23.45')
        try:
            thisrdg = MeterReadings(ac_id = 2, meter_id = 2, meter_reading = "5:3rap", note='Error in string in hrs mins')
            db.session.add(thisrdg)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)

    def test003(self):
        # thisrdg = MeterReadings(ac_id = 2, meter_id = 2, reading_date = datetime.date.today(),meter_reading = '23.45')
        try:
            thisrdg = MeterReadings(ac_id = 2, meter_id = 2, meter_reading = "", note='Empty String')
            db.session.add(thisrdg)
            db.session.commit()
        except Exception as e:
            print('ERror in #3 {}'.format(e))


    def test010(self):
        list = MeterReadings.query.all()
        for l in list:
            print(l.id, l.meter_reading, l.Hours(),l.HrsMins())

class meter_process(unittest.TestCase):

    def test001(self):
        ''' Check Integer create'''
        m = MeterProcess(234,'Units')
        self.assertEqual(234,m.value,'Values not the same')

    def test002(self):
        ''' Check Float create'''
        m = MeterProcess(234.65498, 'Units')
        self.assertEqual(234.65, m.value, 'Values not the same')

    def test003(self):
        ''' Check decimal create'''
        m = MeterProcess(Decimal(234.65), 'Units')
        self.assertEqual(234.65, m.value, 'Values not the same')

    def test004(self):
        ''' Check String create'''
        m = MeterProcess('344', 'Units')
        self.assertEqual(344, m.value, 'Values not the same')

    def test005(self):
        ''' Check String create'''
        m = MeterProcess('1465.65', 'Decimal Hours')
        self.assertEqual(87939, m.value, 'Values not the same')

    def test006(self):
        ''' Check String create'''
        m = MeterProcess('1465:39', 'Hours:Minutes')
        self.assertEqual(87939, m.value, 'Values not the same')

    #TODO: Add a few test to check rounding

    def test031(self):
        ''' Check Integer create'''
        m = MeterProcess(234,'Units')
        self.assertEqual(234,m.units,'Values not the same')

    def test032(self):
        ''' Check Float create'''
        m = MeterProcess(234.65498, 'Units')
        self.assertEqual(234.65, m.units, 'Values not the same')

    def test033(self):
        ''' Check decimal create'''
        m = MeterProcess(Decimal(234.65), 'Units')
        self.assertEqual(234.65, m.units, 'Values not the same')

    def test034(self):
        ''' Check String create'''
        m = MeterProcess('344', 'Units')
        self.assertEqual(344, m.units, 'Values not the same')

    def test035(self):
        ''' Check String create'''
        m = MeterProcess('1465.65', 'Decimal Hours')
        self.assertEqual(1465.65, m.dechrs, 'Values not the same')

    def test036(self):
        ''' Check String create'''
        m = MeterProcess('1465:39', 'Hours:Minutes')
        self.assertEqual('1465:39', m.hrsmins, 'Values not the same')

    def test037(self):
        ''' Check String create'''
        m = MeterProcess('1465.65', 'Decimal Hours')
        self.assertEqual('1465:39', m.hrsmins, 'Values not the same')

    def test036(self):
        ''' Check String create'''
        m = MeterProcess('1465:39', 'Hours:Minutes')
        self.assertEqual(87939, m.minutes, 'Values not the same')



    # self.assertEqual('234.00',str(m), 'not equal')


if __name__ == '__main__':
    case1 = unittest.TestLoader().loadTestsFromTestCase(FSqlalchemyTst)
    case2 = unittest.TestLoader().loadTestsFromTestCase(CSVTst)
    case3 = unittest.TestLoader().loadTestsFromTestCase(sendgridtest)
    case4 = unittest.TestLoader().loadTestsFromTestCase(maintenance_test)
    case5 = unittest.TestLoader().loadTestsFromTestCase(maintenance_test_ac_obj)
    case6 = unittest.TestLoader().loadTestsFromTestCase(maintenance_time_values)
    case7 = unittest.TestLoader().loadTestsFromTestCase(meter_process)
    # thissuite = unittest.TestSuite([case1])
    # thissuite = unittest.TestSuite([case4,case5])

    # I don't know why but the following will work in debug mode but not if you just run it.
    thissuite = unittest.TestLoader().loadTestsFromName('__main__.maintenance_test_ac_obj.test042')
    #

    # The next line is critical tomae the rest work.....
    with app.app_context():
        # thissuite = unittest.TestLoader().loadTestsFromName('__main__.maintenance_test_ac_obj.test042')
        unittest.TextTestRunner(verbosity=2).run(thissuite)
        # for e in thissuite.errors:
        #     print(e)
