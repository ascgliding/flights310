import sendgrid
from flask_sqlalchemy import __version__ as fsqa_version,model
from flask_login import __version__ as flogin_version
from flask import __version__ as flask_version
from flask_wtf import __version__ as flaskwtf_version
from wtforms import __version__ as wft_version
from sqlalchemy import __version__ as sqa_version


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
from sqlalchemy import text as sqltext, func, __version__
from sqlalchemy.sql import select
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail,Attachment,FileContent,FileName,FileType,Disposition
from dateutil.relativedelta import relativedelta

from asc.oMaint import ACMaint

import base64

print('about to create app')
app = create_app()
print('defining logger')
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
        print('Flask Version:{}'.format(flask_version))
        print("Python Version {}".format(sys.version))
        print("WTForms Version {}".format(wft_version))
        print("Flask WTForms Version {}".format(flaskwtf_version))
        print("Flask Login Version {}".format(flogin_version))
        print("Flask SQLAlchemy version {}".format(fsqa_version))
        print("SQL Alchemy version {}".format(sqa_version))



        Tasks.__table__.drop(db.engine)
        Meters.__table__.drop(db.engine)
        ACMeters.__table__.drop(db.engine)
        MeterReadings.__table__.drop(db.engine)
        ACTasks.__table__.drop(db.engine)
        ACMaintUser.__table__.drop(db.engine)
        # MaintHistory.__table__.drop(db.engine)
        ACMaintHistory.__table__.drop(db.engine)
        db.create_all()
        print('adding meters')
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
        print('establishing meter objects')
        oTach = db.session.query(Meters).filter(Meters.meter_name == 'Tachometer').first()
        oAirframe = db.session.query(Meters).filter(Meters.meter_name == 'AirFrame').first()
        oLandings = db.session.query(Meters).filter(Meters.meter_name == 'Landings').first()

        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        # A/C meters
        thisrow = ACMeters(ac_id = oRDW.id, meter_id = oAirframe.id, entry_uom="Decimal Hours", entry_prompt="Enter the incremental hours for the event")
        db.session.add(thisrow)
        thisrow = ACMeters(ac_id = oRDW.id, meter_id = oTach.id, entry_uom="Hours:Minutes", entry_prompt="Enter the final Meter Reading")
        db.session.add(thisrow)
        thisrow = ACMeters(ac_id = oRDW.id, meter_id = oLandings.id, entry_uom="Qty", entry_prompt="Enter the number of landings for the day")
        db.session.add(thisrow)
        oGBU = db.session.query(Aircraft).filter(Aircraft.regn == 'GBU').first()
        thisrow = ACMeters(ac_id = oGBU.id, meter_id = oAirframe.id, entry_uom="Hours:Minutes", entry_prompt="Enter the final Meter Reading")
        db.session.add(thisrow)
        thisrow = ACMeters(ac_id = oGBU.id, meter_id = oLandings.id, entry_uom="Qty", entry_prompt="Enter the number of landings for the day")
        db.session.add(thisrow)
        db.session.flush()
        oRDWTach = db.session.query(ACMeters).filter(ACMeters.meter_id == oTach.id).filter(ACMeters.ac_id == oRDW.id).first()
        oRDWAirframe = db.session.query(ACMeters).filter(ACMeters.meter_id == oTach.id).filter(ACMeters.ac_id == oRDW.id).first()
        oRDWTach = db.session.query(ACMeters).filter(ACMeters.meter_id == oTach.id).filter(ACMeters.ac_id == oRDW.id).first()
        # Readings

        # These need to be able to be relateive to today and create both 90 day and 465 day equivalents.
        # 3mth avg = ((3 * 40)/90 = 1.3333, 12 mth = ((3*40)+(9*80)) / (12*30)  = 2.333
        # 6 mth avg = ((3*40)+(3*80)) / (6*30)  = 2.000
        cls.add_meter_readings(oRDW.id,oLandings.id,40,80)
        # 3mth avg = ((3 * 200)/90 = 6.666hrs, 400 mins, 12 mth = ((3*200)+(9*20)) / (12*30)  = 2.166hr, 130min
        cls.add_meter_readings(oRDW.id,oAirframe.id,12000,1200)
        # 3mth avg = ((3 * 100)/90 = 3.3333hrs, 200 mins, 12 mth = ((3*200)+(9*20)) / (12*30)  = 1.083333hr, 65min
        cls.add_meter_readings(oRDW.id,oTach.id,6000,600)
        # Create some tasks here and assign them to GBU so that the general test cases for RDW
        # will not have the same ACTask.id as Task.id
        oGBU = db.session.query(Aircraft).filter(Aircraft.regn == 'GBU').first()
        oAirframe = db.session.query(Meters).filter(Meters.meter_name == 'AirFrame').first()
        oLandings = db.session.query(Meters).filter(Meters.meter_name == 'Landings').first()
        oACMeter = db.session.query(ACMeters).filter(ACMeters.meter_id == oAirframe.id).first()
        oLandings = db.session.query(Meters).filter(Meters.meter_name == 'Landings').first()
        thistask = Tasks(task_description = 'test001', task_basis='Calendar',
                         task_calendar_uom = 'Years', task_calendar_period=2)
        db.session.add(thistask)
        thistask = Tasks(task_description = 'test002', task_basis='Calendar',
                         task_calendar_uom = 'Years', task_calendar_period=1)
        db.session.add(thistask)
        thistask = Tasks(task_description = 'test003', task_basis='Meter',
                         task_meter_id=oAirframe.id, task_meter_period=50 )
        db.session.add(thistask)
        thistask = Tasks(task_description = 'test004', task_basis='Meter',
                         task_meter_id=oAirframe.id, task_meter_period=50 )
        db.session.add(thistask)
        db.session.commit()
        test001 = db.session.query(Tasks).filter(Tasks.task_description == 'test001').first()
        test002 = db.session.query(Tasks).filter(Tasks.task_description == 'test002').first()
        test003 = db.session.query(Tasks).filter(Tasks.task_description == 'test003').first()
        test004 = db.session.query(Tasks).filter(Tasks.task_description == 'test004').first()
        lastdone = datetime.date.today() - relativedelta(months=6)
        thisactask = ACTasks(ac_id=oGBU.id, task_id=test001.id, estimate_days=365,last_done=lastdone,
                             note='Tasks to ensure ACTask.id is not the same as Task.id for RDW tests')
        db.session.add(thisactask)
        thisactask = ACTasks(ac_id=oGBU.id, task_id=test002.id, estimate_days=365,last_done=lastdone,
                             note='Tasks to ensure ACTask.id is not the same as Task.id for RDW tests')
        db.session.add(thisactask)
        thisactask = ACTasks(ac_id=oGBU.id, task_id=test003.id, estimate_days=90,last_done_reading=150 * 60,
                             note='Tasks to ensure ACTask.id is not the same as Task.id for RDW tests')
        db.session.add(thisactask)
        thisactask = ACTasks(ac_id=oGBU.id, task_id=test004.id, estimate_days=90,last_done_reading=9100,
                             note='Tasks to ensure ACTask.id is not the same as Task.id for RDW tests')
        db.session.add(thisactask)
        db.session.commit()
        # Landings = 90 day avg = 12/90=0.1333, 360 = 12+9*5 = 57/360 = 0.15833333
        cls.add_meter_readings(oGBU.id,oLandings.id,4,5)
        # Airframe - 90 day avg = 36/90=0.4, 360 day = 36+9*8=0.3
        cls.add_meter_readings(oGBU.id,oAirframe.id,12,8)


        #users
        me = User.query.filter_by(name='rayb').first()
        peter = User.query.filter_by(name='peebee89').first()
        oGHU = Aircraft.query.filter_by(regn='GHU').first()

        db.session.add(ACMaintUser(ac_id = oGBU.id, user_id = me.id, maint_level='All'))
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

    @classmethod
    def add_meter_readings(cls,pac_id,pmeter_id,avg90,avg365):
        daysbetweenreadings = 30
        periods = 18
        thisreadingdate = datetime.date.today() - relativedelta(days=(daysbetweenreadings * periods)) # must be a multiple of 30
        this_meter_reading = 10000
        prev_reading = 0
        while thisreadingdate <= datetime.date.today() :
            #add readng
            thisreading = MeterReadings()
            thisreading.ac_id = pac_id
            thisreading.meter_id = pmeter_id
            thisreading.reading_date = thisreadingdate
            thisreading.meter_reading = this_meter_reading
            thisreading.meter_delta =  this_meter_reading - prev_reading
            thisreading.note = 'Test Data'
            db.session.add(thisreading)
            prev_reading = this_meter_reading
            if thisreadingdate < (datetime.date.today() - relativedelta(days=100)):
                this_meter_reading += avg365
            else:
                this_meter_reading += avg90
            # go fwd 20 days
            thisreadingdate = thisreadingdate + relativedelta(days=daysbetweenreadings)
        db.session.commit()

    def test001(self):
        ''' Calendar Based Task'''
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test001').first()
        lastdone=datetime.date.today() - relativedelta(months=6)
        expected_due = datetime.date.today() - relativedelta(months=6) + relativedelta(years=2)
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id, estimate_days=365,last_done=lastdone,
                             note='Plain unexpired calendar task')
        db.session.add(thisactask)
        # get the object
        omaint = ACMaint(oRDW.id)
        otask = [t for t in omaint.tasks if t.task_id==otest.id][0]
        print("test001:{} Last Done :{} Falls due:{} ({})  Expected {}".format(
            otask.recurrence_description, lastdone,
            otask.next_due_date, otask.next_due_message,expected_due))
        self.assertEqual(expected_due,otask.next_due_date,"Calendar based task incorrect date")
        self.assertEqual("Estimate Based on Calendar",otask.next_due_message,"Incorrect Message")
        self.assertEqual(thisactask.std_task_rec.recurrence_description, "Every 2 Years",
                         "Invalid Recurrence Description")

    def test002(self):
        ''' Calendar Based Task expired'''
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test002').first()
        lastdone=datetime.date.today() - relativedelta(months=15)
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id,
                             estimate_days=365,last_done=lastdone,
                             note='plain expired calendar task')
        db.session.add(thisactask)
        db.session.commit()
        expected_due = lastdone + relativedelta(years=1)
        # get the object
        omaint = ACMaint(oRDW.id)
        otask = [t for t in omaint.tasks if t.task_id==otest.id][0]
        print("test002:{} Last Done :{} Falls due:{} ({})  Expected {}".format(
            otask.recurrence_description, lastdone, otask.next_due_date,
            otask.next_due_message,expected_due))
        self.assertEqual(expected_due,otask.next_due_date,"Calendar based task incorrect date")
        self.assertEqual("Calendar Based Task Expired",
                         otask.next_due_message,"Calendar based task incorrect date")

    def test003(self):
        '''Meter Based Task - Time'''
        oAirframe = db.session.query(Meters).filter(Meters.meter_name == 'AirFrame').first()
        oACMeter = db.session.query(ACMeters).filter(ACMeters.meter_id == oAirframe.id).first()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test003').first()
        #
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        lastdone=1040 * 60
        # Annual Airframe avg 2.166hr /day
        expected_due = datetime.date.today() + relativedelta(days=int((1090-1066.6666)/2.16666))  # 10.7 days
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id,
                             estimate_days=365,last_done_reading=lastdone,
                             note="Unexpired Meter Based Task")
        db.session.add(thisactask)
        db.session.commit()
        # get the object
        try:
            omaint = ACMaint(oRDW.id)
        except Exception as e:
            self.assertFalse(str(e))

        otask = [t for t in omaint.tasks if t.task_id==otest.id][0]
        print("test003:{} Last Done :{} Falls due:{} ({})  Expected {} Average {} Togo {}".
              format(otask.recurrence_description, lastdone,
                     otask.next_due_date, otask.next_due_message,expected_due,
                     otask.daily_use,otask.days_to_go))
        self.assertEqual(expected_due,otask.next_due_date,"Meter based task incorrect date")
        self.assertEqual('Estimate Based on Meter', otask.next_due_message,
                         'Incorrect Message')
        self.assertEqual(thisactask.std_task_rec.recurrence_description, "Every 50 AirFrame (Time)",
                         "Invalid Recurrence Description")

    def test004(self):
        '''Meter Based Task Expired'''
        oAirframe = db.session.query(Meters).filter(Meters.meter_name == 'AirFrame').first()
        oACMeter = db.session.query(ACMeters).filter(ACMeters.meter_id == oAirframe.id).first()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test004').first()
        #
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        lastdone=500 * 60 # 30000 Minutes
        # Annual Airframe avg 2.166hr /day
        current_reading = 64000 # minutes
        expected_done = lastdone + (50 * 60) # 50 hours * 60 minutes
        # how many days?
        expected_days = int((current_reading - expected_done) / 130)
        expected_due = datetime.date.today() - relativedelta(days=expected_days)
        # therefore expected due is today
        # expected_due = datetime.date.today()
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id,
                             estimate_days=365,last_done_reading=lastdone,
                             note="Expired Meter Based Task")
        db.session.add(thisactask)
        db.session.commit()
        # get the object
        try:
            omaint = ACMaint(oRDW.id)
        except Exception as e:
            self.assertFalse(str(e))

        otask = [t for t in omaint.tasks if t.task_id==otest.id][0]
        print("test004:{} Last Done :{} Falls due:{} ({})  Expected {} Average {} Togo {}".
              format(otask.recurrence_description, lastdone,
                     otask.next_due_date, otask.next_due_message,expected_due,
                     otask.daily_use,otask.days_to_go))
        self.assertEqual(expected_due,otask.next_due_date,"Meter based task incorrect date")
        self.assertEqual("Meter Based Task Expired",
                         otask.next_due_message,"Incorrect Message")


    def test005(self):
        '''Calendar and Meter - Calendar wins not yet due '''
        oAirframe = db.session.query(Meters).filter(Meters.meter_name == 'AirFrame').first()
        oACMeter = db.session.query(ACMeters).filter(ACMeters.meter_id == oAirframe.id).first()
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        thistask = Tasks(task_description = 'test005', task_basis='Calendar',
                         task_calendar_uom = 'Months', task_calendar_period=3,
                         task_meter_id = oAirframe.id, task_meter_period = (500))
        db.session.add(thistask)
        db.session.commit()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test005').first()
        lastdone=datetime.date.today() - relativedelta(months=2)
        expected_due = lastdone + relativedelta(months=3)
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id,
                             estimate_days=90,
                             last_done=lastdone,last_done_reading=64000,
                             note="Calendar based task with Meter, Calendar date wins")
        db.session.add(thisactask)
        db.session.commit()
        # get the object
        omaint = ACMaint(oRDW.id)
        otask = [t for t in omaint.tasks if t.task_id==otest.id][0]
        print("tes005: {} Last Done :{} Falls due:{} ({})  Expected {}".format(
            otask.recurrence_description, lastdone, otask.next_due_date,
            otask.next_due_message,expected_due))
        self.assertEqual(expected_due,otask.next_due_date,"Incorrect Date")
        self.assertEqual("Calendar basis earlier than meter estimate",
                         otask.next_due_message,"Calendar based task incorrect date")
        self.assertEqual(thisactask.std_task_rec.recurrence_description,
                         "Every 3 Months or Every 500 AirFrame(Time)",
                         "Invalid Recurrence Description")

    def test006(self):
        '''Calendar and Meter - Meter wins not yet due '''
        oAirframe = db.session.query(Meters).filter(Meters.meter_name == 'AirFrame').first()
        oACMeter = db.session.query(ACMeters).filter(ACMeters.meter_id == oAirframe.id).first()
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        thistask = Tasks(task_description = 'test006', task_basis='Calendar',
                         task_calendar_uom = 'Years', task_calendar_period=1,
                         task_meter_id = oAirframe.id, task_meter_period = (50))
        db.session.add(thistask)
        db.session.commit()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test006').first()
        lastdone=datetime.date.today() - relativedelta(months=1)
        # 90 day average: 6.666 hrs = 400 mins
        # 1066:40 = 64000 mins
        # 50 hour check at 400 mins / day comes up every 7.5 days.
        # make last done reading the max reading (64000) less (2.5*400) = 1000 s.b. 5days away
        expected_due = datetime.date.today() + relativedelta(days = 5)
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id,
                             estimate_days=90,
                             last_done=lastdone,last_done_reading=63000,
                             note="Calendar based task with Meter, Meter date wins")
        db.session.add(thisactask)
        db.session.commit()
        # get the object
        omaint = ACMaint(oRDW.id)
        otask = [t for t in omaint.tasks if t.task_id==otest.id][0]
        print("tes006: {} Last Done :{} Falls due:{} ({})  Expected {} togo {} Avg {}" .format(
            otask.recurrence_description,
            lastdone, otask.next_due_date,
            otask.next_due_message,expected_due,
            otask.days_to_go, otask.daily_use))
        print("tes006: Last Done Reading:{} ".format(otask.last_done_reading))
        self.assertEqual(expected_due,otask.next_due_date,'Incorrect due date')
        self.assertEqual("Meter estimate earlier than calendar date",
                         otask.next_due_message,"Meter estimate earlier than calendar date")

    def test007(self):
        ''' Meter based - qty '''
        oLandings = db.session.query(Meters).filter(Meters.meter_name == 'Landings').first()
        oACMeter = db.session.query(ACMeters).filter(ACMeters.meter_id == oLandings.id).first()
        thistask = Tasks(task_description = 'test007', task_basis='Meter',
                         task_meter_id=oLandings.id, task_meter_period=100 )
        db.session.add(thistask)
        db.session.commit()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test007').first()
        #
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        lastdone=11300
        # Annual Airframe avg 2.333 /day
        # s.b. due at 11400, last reading is 11320. Therfore 80 to go.
        # 80 / 2.33 = 34.33 days
        expected_due = datetime.date.today() + relativedelta(days=34)
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id,
                             estimate_days=365,last_done_reading=lastdone,
                             note="Unexpired Meter Based Task - not time")
        db.session.add(thisactask)
        db.session.commit()
        # get the object
        try:
            omaint = ACMaint(oRDW.id)
        except Exception as e:
            self.assertFalse(str(e))

        otask = [t for t in omaint.tasks if t.task_id==otest.id][0]
        print("Test007:{} Last Done :{} Falls due:{} ({})  Expected {} Average {} Togo {}".
              format(otask.recurrence_description, lastdone,
                     otask.next_due_date, otask.next_due_message,expected_due,
                     otask.daily_use,otask.days_to_go))
        self.assertEqual(expected_due,otask.next_due_date,"Meter based task incorrect date")
        self.assertEqual('Estimate Based on Meter', otask.next_due_message,
                         'Incorrect Message')


    def test008(self):
        ''' Meter based - qty - Expired '''
        oLandings = db.session.query(Meters).filter(Meters.meter_name == 'Landings').first()
        oACMeter = db.session.query(ACMeters).filter(ACMeters.meter_id == oLandings.id).first()
        thistask = Tasks(task_description = 'test008', task_basis='Meter',
                         task_meter_id=oLandings.id, task_meter_period=100 )
        db.session.add(thistask)
        db.session.commit()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test008').first()
        #
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        lastdone=10300
        # Annual Airframe avg 2.333 /day
        # s.b. due at 10400, last reading is 11320. Therfore 10400 - 11320 = -920
        # -920 / 2.33 = 394 days late
        expected_due = datetime.date.today() - relativedelta(days=394)
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id,
                             estimate_days=365,last_done_reading=lastdone,
                             note="expired Meter Based Task - not time")
        db.session.add(thisactask)
        db.session.commit()
        # get the object
        try:
            omaint = ACMaint(oRDW.id)
        except Exception as e:
            self.assertFalse(str(e))

        otask = [t for t in omaint.tasks if t.task_id==otest.id][0]
        print("Test008:{} Last Done :{} Falls due:{} ({})  Expected {} Average {} Togo {}".
              format(otask.recurrence_description, lastdone,
                     otask.next_due_date, otask.next_due_message,expected_due,
                     otask.daily_use,otask.days_to_go))
        self.assertEqual(expected_due,otask.next_due_date,"Meter based task incorrect date")
        self.assertEqual('Meter Based Task Expired', otask.next_due_message,
                         'Incorrect Message')

    def test009(self):
        '''Validate the Four GBU test cases'''
        GBU=ACMaint('GBU')
        for t in GBU.tasks:
            if str(t) == 'test001':
                expected = datetime.date.today() - relativedelta(months=6) + relativedelta(years=2)
                self.assertEqual(t.next_due_date,expected,"task test001 Invalid Due Date")
            if str(t) == 'test002':
                expected = datetime.date.today() - relativedelta(months=6) + relativedelta(years=1)
                self.assertEqual(t.next_due_date,expected,"task test002 Invalid Due Date")
            if str(t) == 'test003':
                # last done : 150 hrs, Avg 0.4, last reading = 169:16 10,140 mins, 169.26666 hrs
                # last reading is today
                expected = datetime.date.today() + relativedelta(days=((((150 + 50) - 169.26666) * 60 ) / 0.4))
                self.assertEqual(t.next_due_date, expected, "task test003 Invalid Due Date")
            if str(t) == 'test004':
                # last done : 151:40 hrs, Avg 0.4, last reading = 169:16 10,140 mins, 169.26666 hrs
                # last reading is today
                expected = datetime.date.today() + relativedelta(days=((((151.666666 + 50) - 169.26666) * 60 ) / 0.4))
                self.assertEqual(t.next_due_date, expected, "task test004 Invalid Due Date")


    def test020(self):
        '''Test Regeneration function - 0 on Calendar Based Task'''
        thistask = Tasks(task_description = 'test020', task_basis='Calendar',
                         task_calendar_uom = 'Years', task_calendar_period=2)
        db.session.add(thistask)
        db.session.commit()
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test020').first()
        lastdone=datetime.date.today()
        expected_due = datetime.date(2020,1,1)
        while expected_due < lastdone:
            expected_due += relativedelta(years=2)
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id, estimate_days=365,last_done=lastdone,
                             due_basis_date=datetime.date(2020,1,1),
                             note='Task with calendar regeneration basis unexpired ')
        db.session.add(thisactask)
        # get the object
        omaint = ACMaint(oRDW.id)
        otask = [t for t in omaint.tasks if t.task_id==otest.id][0]
        print("test020:{} Last Done :{} Falls due:{} ({})  Expected {}".format(
            otask.recurrence_description, lastdone,
            otask.next_due_date, otask.next_due_message,expected_due))
        for m in otask.messages:
            print("test020: {}".format(m))
        self.assertEqual(expected_due,otask.next_due_date,"Calendar based task incorrect date")
        self.assertEqual("Estimate Based on Calendar (R)",otask.next_due_message,"Incorrect Message")

    def test021(self):
        '''Test Regeneration function Calendar Based Task - Expired'''
        thistask = Tasks(task_description = 'test021', task_basis='Calendar',
                         task_calendar_uom = 'Years', task_calendar_period=2)
        db.session.add(thistask)
        db.session.commit()
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test021').first()
        lastdone=datetime.date.today() - relativedelta(years=3)
        expected_due = datetime.date(2020,1,1)
        while expected_due < lastdone:
            expected_due += relativedelta(years=2)
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id, estimate_days=365,last_done=lastdone,
                             due_basis_date=datetime.date(2020,1,1),
                             note='Task with calendar regeneration basis unexpired ')
        db.session.add(thisactask)
        # get the object
        omaint = ACMaint(oRDW.id)
        otask = [t for t in omaint.tasks if t.task_id==otest.id][0]
        print("test021:{} Last Done :{} Falls due:{} ({})  Expected {}".format(
            otask.recurrence_description, lastdone,
            otask.next_due_date, otask.next_due_message,expected_due))
        for m in otask.messages:
            print("test021: {}".format(m))
        self.assertEqual(expected_due,otask.next_due_date,"Calendar based task incorrect date")
        self.assertEqual("Calendar Based Task Expired (R)",otask.next_due_message,"Incorrect Message")

    def test022(self):
        '''Meter Based Task - Time'''
        oAirframe = db.session.query(Meters).filter(Meters.meter_name == 'AirFrame').first()
        oACMeter = db.session.query(ACMeters).filter(ACMeters.meter_id == oAirframe.id).first()
        thistask = Tasks(task_description = 'test022', task_basis='Meter',
                         task_meter_id=oAirframe.id, task_meter_period=50 )
        db.session.add(thistask)
        db.session.commit()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test022').first()
        #
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        lastdone=1055 * 60
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id,
                             estimate_days=365,last_done_reading=lastdone,
                             due_basis_reading=(500 * 60),
                             note="Unexpired Meter Based Task with regneration from")
        db.session.add(thisactask)
        db.session.commit()
        # Annual Airframe avg 2.166hr /day
        expected_due = datetime.date.today() + relativedelta(days=int((1100-1066.6666)/2.16666))  # 15.3 days
        # get the object
        try:
            omaint = ACMaint(oRDW.id)
        except Exception as e:
            self.assertFalse(str(e))

        otask = [t for t in omaint.tasks if t.task_id==otest.id][0]
        print("test022:{} Last Done :{} Falls due:{} ({})  Expected {} Average {} Togo {}".
              format(otask.recurrence_description, lastdone,
                     otask.next_due_date, otask.next_due_message,expected_due,
                     otask.daily_use,otask.days_to_go))
        for m in otask.messages:
            print('test022:{}'.format(m))
        self.assertEqual(expected_due,otask.next_due_date,"Meter based task incorrect date")
        self.assertEqual('Estimate Based on Meter (R)', otask.next_due_message,
                         'Incorrect Message')

    def test022(self):
        '''Meter Based Task - Time - with regneration'''
        oAirframe = db.session.query(Meters).filter(Meters.meter_name == 'AirFrame').first()
        oACMeter = db.session.query(ACMeters).filter(ACMeters.meter_id == oAirframe.id).first()
        thistask = Tasks(task_description = 'test022', task_basis='Meter',
                         task_meter_id=oAirframe.id, task_meter_period=50 )
        db.session.add(thistask)
        db.session.commit()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test022').first()
        #
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        lastdone=1055 * 60
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id,
                             estimate_days=365,last_done_reading=lastdone,
                             due_basis_reading=(500 * 60),
                             note="Unexpired Meter Based Task with regneration from")
        db.session.add(thisactask)
        db.session.commit()
        # Annual Airframe avg 2.166hr /day
        expected_due = datetime.date.today() + relativedelta(days=int((1100-1066.6666)/2.16666))  # 15.3 days
        # get the object
        try:
            omaint = ACMaint(oRDW.id)
        except Exception as e:
            self.assertFalse(str(e))

        otask = [t for t in omaint.tasks if t.task_id==otest.id][0]
        print("test022:{} Last Done :{} Falls due:{} ({})  Expected {} Average {} Togo {}".
              format(otask.recurrence_description, lastdone,
                     otask.next_due_date, otask.next_due_message,expected_due,
                     otask.daily_use,otask.days_to_go))
        for m in otask.messages:
            print('test022:{}'.format(m))
        self.assertEqual(expected_due,otask.next_due_date,"Meter based task incorrect date")
        self.assertEqual('Estimate Based on Meter (R)', otask.next_due_message,
                         'Incorrect Message')

    def test023(self):
        '''Meter Based Task - Time Regnerate from 500 - expired'''
        oAirframe = db.session.query(Meters).filter(Meters.meter_name == 'AirFrame').first()
        oACMeter = db.session.query(ACMeters).filter(ACMeters.meter_id == oAirframe.id).first()
        thistask = Tasks(task_description = 'test023', task_basis='Meter',
                         task_meter_id=oAirframe.id, task_meter_period=50 )
        db.session.add(thistask)
        db.session.commit()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test023').first()
        #
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        lastdone=1040 * 60
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id,
                             estimate_days=365,last_done_reading=lastdone,
                             due_basis_reading=(500 * 60),
                             note="Unexpired Meter Based Task with regneration from")
        db.session.add(thisactask)
        db.session.commit()
        # Annual Airframe avg 2.166hr /day
        expected_due = datetime.date.today() + relativedelta(days=int((1050-1066.6666)/2.16666))  # 7 days
        # get the object
        try:
            omaint = ACMaint(oRDW.id)
        except Exception as e:
            self.assertFalse(str(e))

        otask = [t for t in omaint.tasks if t.task_id==otest.id][0]
        print("test023:{} Last Done :{} Falls due:{} ({})  Expected {} Average {} Togo {}".
              format(otask.recurrence_description, lastdone,
                     otask.next_due_date, otask.next_due_message,expected_due,
                     otask.daily_use,otask.days_to_go))
        for m in otask.messages:
            print('test023:{}'.format(m))
        self.assertEqual(expected_due,otask.next_due_date,"Meter based task incorrect date")
        self.assertEqual('Meter Based Task Expired (R)', otask.next_due_message,
                         'Incorrect Message')

    def test024(self):
        '''  Qty meter based task with regeneration'''
        oLandings = db.session.query(Meters).filter(Meters.meter_name == 'Landings').first()
        oACMeter = db.session.query(ACMeters).filter(ACMeters.meter_id == oLandings.id).first()
        thistask = Tasks(task_description = 'test024', task_basis='Meter',
                         task_meter_id=oLandings.id, task_meter_period=200 )
        db.session.add(thistask)
        db.session.commit()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test024').first()
        #
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        lastdone=11230  # next one is 11350
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id,
                             estimate_days=365,last_done_reading=lastdone,
                             due_basis_reading=(750),
                             note="Unexpired Meter Based Task - Qty - with regneration from")
        db.session.add(thisactask)
        db.session.commit()

        # Annual Airframe avg 1.3333hr /day  (2.333 for 12 mth)
        expected_due = datetime.date.today() + relativedelta(days=int((11350-11320)/2.3333))  #  12.8days
        # get the object
        try:
            omaint = ACMaint(oRDW.id)
        except Exception as e:
            self.assertFalse(str(e))

        otask = [t for t in omaint.tasks if t.task_id==otest.id][0]
        print("test024:{} Last Done :{} Falls due:{} ({})  Expected {} Average {} Togo {}".
              format(otask.recurrence_description, lastdone,
                     otask.next_due_date, otask.next_due_message,expected_due,
                     otask.daily_use,otask.days_to_go))
        for m in otask.messages:
            print('test024:{}'.format(m))
        self.assertEqual(expected_due,otask.next_due_date,"Meter based task incorrect date")
        self.assertEqual('Estimate Based on Meter (R)', otask.next_due_message,
                         'Incorrect Message')

    def test025(self):
        '''  Qty meter based task with regeneration - Expired'''
        oLandings = db.session.query(Meters).filter(Meters.meter_name == 'Landings').first()
        oACMeter = db.session.query(ACMeters).filter(ACMeters.meter_id == oLandings.id).first()
        thistask = Tasks(task_description='test025', task_basis='Meter',
                         task_meter_id=oLandings.id, task_meter_period=200)
        db.session.add(thistask)
        db.session.commit()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test025').first()
        #
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        lastdone = 11120  # next sb. 11150
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id,
                             estimate_days=365, last_done_reading=lastdone,
                             due_basis_reading=(750),
                             note="Unexpired Meter Based Task - Qty - with regneration from - expired")
        db.session.add(thisactask)
        db.session.commit()
        # Annual Airframe avg 1.3333hr /day  (2.333 for 12 mth)
        expected_due = datetime.date.today() + relativedelta(days=int((11150 - 11320) / 2.3333))  # -72 days
        # get the object
        try:
            omaint = ACMaint(oRDW.id)
        except Exception as e:
            self.assertFalse(str(e))

        otask = [t for t in omaint.tasks if t.task_id == otest.id][0]
        print("test025:{} Last Done :{} Falls due:{} ({})  Expected {} Average {} Togo {}".
              format(otask.recurrence_description, lastdone,
                     otask.next_due_date, otask.next_due_message, expected_due,
                     otask.daily_use, otask.days_to_go))
        for m in otask.messages:
            print('test025:{}'.format(m))
        self.assertEqual(expected_due, otask.next_due_date, "Meter based task incorrect date")
        self.assertEqual('Meter Based Task Expired (R)', otask.next_due_message,
                         'Incorrect Message')

    def test027(self):
        ''' Task with regneration on both date and meter'''
        # I have not allowed for this.  Will need to check with Peter.
        pass



    def test100(self):
        ''' Meter Based task with no readings'''
        oMGE = db.session.query(Meters).filter(Meters.meter_name == 'Motor Glider Engine Hrs').first()
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        thisrow = ACMeters(ac_id = oRDW.id, meter_id = oMGE.id, entry_uom="Decimal Hours",
                           entry_prompt="Enter the incremental hours for the event")
        db.session.add(thisrow)
        db.session.commit()
        oACMeter = db.session.query(ACMeters).filter(ACMeters.meter_id == oMGE.id).first()
        thistask = Tasks(task_description = 'test100', task_basis='Meter',
                         task_meter_id=oMGE.id, task_meter_period=50)
        db.session.add(thistask)
        db.session.commit()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test100').first()
        #
        lastdone=1040
        # Annual Airframe avg 2.166hr /day
        expected_due = datetime.date.today() # It doesn't matter - it is an error condition
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id,
                             estimate_days=365,last_done_reading=lastdone,
                             note='A task with no readings initially')
        db.session.add(thisactask)
        db.session.commit()
        # get the object
        try:
            omaint = ACMaint(oRDW.id)
        except Exception as e:
            self.assertFalse(str(e))

        otask = [t for t in omaint.tasks if t.task_id==otest.id][0]
        print("test100:{} Last Done :{} Falls due:{} ({})  Expected {} Average {} Togo {}".
              format(otask.recurrence_description, lastdone,
                     otask.next_due_date, otask.next_due_message,expected_due,
                     otask.daily_use,otask.days_to_go))
        self.assertEqual(expected_due,otask.next_due_date,"Meter based task incorrect date")
        self.assertEqual('Insufficient meter readings to determine an average', otask.next_due_message,
                         'Incorrect Message')

    def test101(self):
        ''' Meter Based task with insufficient'''
        print('Not yet written')

    def test102(self):
        ''' Omaint Class fails on load with invalid task'''
        thistask = Tasks(task_description='test102', task_basis='Calendar',
                         task_calendar_uom='Years', task_calendar_period=-2)
        db.session.add(thistask)
        db.session.commit()
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test102').first()
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id, estimate_days=365,
                             last_done=datetime.date
                             .today(),
                             note='Invalid Task Period')
        db.session.add(thisactask)
        db.session.commit()
        # get the object
        with self.assertRaises(ACMaint.ACMaintError) :
            x = ACMaint(oRDW.id)
        # now remove it otherwise it will interfere with following tests
        db.session.delete(thisactask)
        db.session.delete(otest)
        db.session.commit()

    def test103(self):
        ''' Invalid meter on standard task'''
        thistask = Tasks(task_description='test103', task_basis='Calendar',
                         task_calendar_uom='Years', task_calendar_period=2,
                         task_meter_id=345)
        db.session.add(thistask)
        db.session.commit()
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test103').first()
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id, estimate_days=365,
                             last_done=datetime.date.today(),
                             note='Invalid Task Period')
        db.session.add(thisactask)
        db.session.commit()
        # get the object
        with self.assertRaises(ACMaint.ACMaintError) :
            x = ACMaint(oRDW.id)
        db.session.delete(thisactask)
        db.session.delete(thistask)
        db.session.commit

    def test200(self):
        ''' SQL Alchemy Relationship testing'''
        oLandings = db.session.query(Meters).filter(Meters.meter_name == 'Landings').first()
        thistask = Tasks(task_description = 'test200', task_basis='Meter',
                         task_meter_id=oLandings.id, task_meter_period=100 )
        db.session.add(thistask)
        db.session.commit()
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        otest = db.session.query(Tasks).filter(Tasks.task_description == 'test200').first()
        thisactask = ACTasks(ac_id=oRDW.id, task_id=otest.id, estimate_days=365,
                             last_done=datetime.date.today(),
                             note='Chained description')
        db.session.add(thisactask)
        db.session.commit()
        # The following tests the str functions
        self.assertEqual(str(oLandings),"Landings","str function for meter failed")
        self.assertEqual(str(thistask),"test200","str function for task failed")
        # The following assert tests that the relationship works and that the __STR__ function works on the
        # relationship
        self.assertEqual(str(thisactask.std_task_rec),"test200","Failed- correct string description of task")
        # The following tests that you can chain from one relationship to another in the schema.
        self.assertEqual(thisactask.std_task_rec.std_meter_rec.uom,"Qty","Incorrect description of meter uom")

    def test201(self):
        ''' Test time meter readings'''
        oAirframe = db.session.query(Meters).filter(Meters.meter_name == 'AirFrame').first()
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        # for r in db.session.query(MeterReadings).filter(MeterReadings.meter_id==oAirframe.id):
        #     print(r, r.Hours, ":" ,r.HrsMins, ":", r.HrsMinsTD)
        lastreading = db.session.query(MeterReadings)\
            .filter(MeterReadings.meter_id==oAirframe.id)\
            .order_by(MeterReadings.reading_date.desc())\
            .first()
        correct_last_reading = datetime.date.today().strftime("%a %d %b %Y")
        correct_last_reading += " : 1066.67 (AirFrame)"
        self.assertEqual(str(lastreading),correct_last_reading
                         ,"Invalid str object of last reading")
        self.assertEqual(lastreading.HrsMins,"1066:40","Invalid HrsMins conversion")
        self.assertEqual(lastreading.Hours,
                         Decimal(1066.67).quantize(Decimal('.01')),
                         "Invalid Hours conversion")
        self.assertEqual(lastreading.HrsMinsTD,datetime.timedelta(hours=1066,minutes=40),"Invalid TimeDelta conversion")
        self.assertEqual(lastreading.meter_reading,64000,"Incorrect last reading")


    def test202(self):
        ''' Test non-time meter readings'''
        oLandings = db.session.query(Meters).filter(Meters.meter_name == 'Landings').first()
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        # for r in db.session.query(MeterReadings).filter(MeterReadings.meter_id==oLandings.id):
        # #     print(r, r.Hours, ":" ,r.HrsMins, ":", r.HrsMinsTD)
        #     print(r)
        lastreading = db.session.query(MeterReadings)\
            .filter(MeterReadings.meter_id==oLandings.id)\
            .order_by(MeterReadings.reading_date.desc())\
            .first()
        correct_last_reading = datetime.date.today().strftime("%a %d %b %Y")
        correct_last_reading += " : 11320 (Landings)"
        self.assertEqual(str(lastreading),correct_last_reading
                         ,"Invalid str object of last reading")
        self.assertIsNone(lastreading.HrsMins,"Hours Mins sb None for Qty basis")
        self.assertIsNone(lastreading.Hours,"Hours Mins sb None for Qty basis")
        self.assertIsNone(lastreading.HrsMinsTD,"Hours Mins sb None for Qty basis")
        self.assertEqual(lastreading.meter_reading,11320,"Incorrect last reading")


    def test300(self):
        ''' UI - Create a deletable task'''
        thistask = Tasks(task_description='test300 - Deletable', task_basis='Calendar',
                         task_calendar_uom='Years', task_calendar_period=-2)
        db.session.add(thistask)
        db.session.commit()

    def test301(self):
        ''' UI - Create a deletable Meter'''
        thismeter = Meters(meter_name = 'test301 - Unsed Meter - deletable', uom='Time')  #, entry_uom = 'Decimal Hours')
        db.session.add(thismeter)
        db.session.commit()

    def test302(self):
        ''' UI - Create a undeletable Meter - on task but not on ac'''
        thismeter = Meters(meter_name='test302 - Unsed Meter - undeletable', uom='Time')  # , entry_uom = 'Decimal Hours')
        db.session.add(thismeter)
        db.session.flush # to get id
        oRDW = db.session.query(Aircraft).filter(Aircraft.regn == 'RDW').first()
        thismeter = db.session.query(Meters).filter(Meters.meter_name == 'test302 - Unsed Meter - undeletable').first()
        thisrow = ACMeters(ac_id = oRDW.id, meter_id = thismeter.id,
                           entry_uom="Decimal Hours", entry_prompt="Enter the incremental hours for the event")
        db.session.add(thisrow)
        db.session.commit()

        #  todo:  need to add some tasks to another a/c so that we can differentiate between the taskid
        #       on the ac and the standard task id.

    def test900(self):
        ''' Verify some obect data by now'''
        oMaint = ACMaint('RDW')
        self.assertEqual(len(oMaint.meters),5,"There should be 5 meters at the end of the test process")
        self.assertEqual(len(oMaint.tasks),16,"There should be 16 meters at the end of the test process")
        correct_current_readings = "AirFrame:1066.67 (" + datetime.date.today().strftime("%d-%m-%y") + ")"
        correct_current_readings += ",Tachometer:616:40 (" + datetime.date.today().strftime("%d-%m-%y") + ")"
        correct_current_readings += ",Landings:11320 (" + datetime.date.today().strftime("%d-%m-%y") + ")"
        correct_current_readings += ",Motor Glider Engine Hrs:No Readings"
        correct_current_readings += ",test302 - Unsed Meter - undeletable:No Readings"
        self.assertEqual(oMaint.currentreadings,correct_current_readings,"Invalid current readings string")



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
    print('start of main')
    case1 = unittest.TestLoader().loadTestsFromTestCase(FSqlalchemyTst)
    case2 = unittest.TestLoader().loadTestsFromTestCase(CSVTst)
    case3 = unittest.TestLoader().loadTestsFromTestCase(sendgridtest)
    case4 = unittest.TestLoader().loadTestsFromTestCase(maintenance_test)
    case5 = unittest.TestLoader().loadTestsFromTestCase(maintenance_test_ac_obj)
    case6 = unittest.TestLoader().loadTestsFromTestCase(maintenance_time_values)
    case7 = unittest.TestLoader().loadTestsFromTestCase(meter_process)
    # thissuite = unittest.TestSuite([case1])
    thissuite = unittest.TestSuite([case4])

    # I don't know why but the following will work in debug mode but not if you just run it.
    # thissuite = unittest.TestLoader().loadTestsFromName('__main__.maintenance_test_ac_obj.test042')
    #

    # The next line is critical tomae the rest work.....
    with app.app_context():
        # thissuite = unittest.TestLoader().loadTestsFromName('__main__.maintenance_test_ac_obj.test042')
        print('in appcontext thing')
        unittest.TextTestRunner(verbosity=2).run(thissuite)
        # for e in thissuite.errors:
        #     print(e)
