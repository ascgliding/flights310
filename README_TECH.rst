.. |date| date::
.. |time| date:: %H:%M
.. header:: ASC Application: |date| |time|
.. The ### directives are processed by rst2pdf.
.. footer:: Page ###Page### of ###Total###

.. sectnum ::

.. contents:: Table of Contents

.. raw:: pdf

    PageBreak

===========================
User Documentation
===========================

*****
Setup
*****

Aircraft
=========

Note that there is a special aircraft called 'WINCH'.  All aircraft with registrations that DO NOT start with "G" are
considered tow aircraft.

Pilots
======

There is not much to pilot maintenance.  However, it is important to understand the relevance of the Full Name field.
The main flights table contains PIC and P2.  These are the names of the individuals.  We have people cominging
and going all the time that are not members of the club (trial flights, ATC, paxes etc) so it is important that
users have the flexibility to enter whatever they like in these fields.  HOWEVER:  if the person is a club member
they MUST appear in the pilots list and their name must be the same in the pilots list as it is on the flights
table.  This is important.  Charges, integration with the accounting system and personal logbooks revolve around this concept.
The tow pilot option is used to populate the list of tow pilots.

All members except honorary life members and "blue-suiters" must be "B Scheme Participants".

Users
======

Users can register themselves by selecting the "Register" button from the drop down menu when there is
no one logged in.

Alternatively, the system administrator can create new users.  Note however, whilst the sysadmin can set a
password when the new user is created, they cannot alter the password once setup.  If a user forgets
their password then the only option is to delete the user and re-add them.

.. raw:: pdf

    PageBreak

==================
Purpose and Design
==================

The idea behind this project is to have a single web-based application into which flight
data can be entered either on field or after flying.  The data is then immediately available
to engineers, treasurers, instructors and CFI's.

******
Design
******
Key features in the design are:

*   Must be able to record ANY aircraft and ANY pilot in order to handle visitors or away trips such as Piako.
    This results in free text in PIC, P2 and Regn so any data validation in these fields must include values
    that are not currently in the lookup tables for pilots and aircraft.  The Pilots and aircraft tables should
    be considered defaults for ASC members and aircraft only.
*   Must support mobile phones in landscape and portrait.  The CSS includes mobile_port_suppress and mobile_land_suppress
    for suppression of fields in either landscape or portrait mode.
*   Data recording on the airfield should be as simple as possible.
*   Multi user using flask-login
*   Ability to export and import data
*   Phone use on the field via responsive design.

Flights
=======

Note the prompt for pilots includes those in the pilots file plus
all those who have flown in the last 180 days.

Slots
=====

Slot types

+--------------+----------------------------------------------------+
| RANK         |Air force ranks and "CIV" and "JUNIOR"              |
+--------------+----------------------------------------------------+
| MEMBERTYPE   |Member types such as FLYING, JUNIOR, SOCIAL         |
+--------------+----------------------------------------------------+
| TRANSTYPE    |Member transactions such as BFR, ICR.               |
+--------------+----------------------------------------------------+
| RATING       |BCAT, FRTO etc                                      |
+--------------+----------------------------------------------------+


==============================
Technical Application Notes
==============================

*********
TODO List
*********

*   Create single click buttons on PC version for glider down
*   Delete User
*   Change the way the takeoff and landing buttons work.  There is no need to use
    javascript.
*   Add a note add button to daysummary.
*   New Flight - Regn 'Tug only' appears twice.

********
Database
********

The application uses sqlite to store data.
The database is in asc.sqlite.
Maintenance is done via

sqlite3 /home/rayb/PycharmProjects/flask31/instance/asc.sqlite

or, (in the development environment):

Windows Shell::

    cd C:\Users\rayb\pythonvenv\flask31\instance>
    "C:\Program Files (x86)\sqlite3\sqlite3.exe" asc.sqlite


CLI (SQLITE3)
=============

DESCRIPTION
       To  start a sqlite3 interactive session, invoke the sqlite3 command and optionally provide the name of a database file.
       If the database file does not exist, it will be created.  If the database file does exist, it will be opened.

       For example, to create a new database file named "mydata.db", create a table named  "memos"  and  insert  a  couple  of
       records into that table:

       $ sqlite3 mydata.db
       SQLite version 3.8.8
       Enter ".help" for instructions
       sqlite> create table memos(text, priority INTEGER);
       sqlite> insert into memos values('deliver project description', 10);
       sqlite> insert into memos values('lunch with Christine', 100);
       sqlite> select * from memos;
       deliver project description|10
       lunch with Christine|100
       sqlite>

	   You can create a file of commands (which may include the .open meta command and redirect it as input

	   sqlite3 < myfile.sql

       If no database name is supplied, the ATTACH sql command can be used to attach to existing or create new database files.
       ATTACH can also be used to attach to multiple databases within the same interactive session.  This is  useful  for  
       mmigrating data between databases, possibly changing the schema along the way.

       Optionally,  a SQL statement or set of SQL statements can be supplied as a single argument.  Multiple statements should
       be separated by semi-colons.

       For example:

       $ sqlite3 -line mydata.db 'select * from memos where priority > 20;'
       text = lunch with Christine
       priority = 100

OPTIONS
       sqlite3 has the following options:

========================== =================================================================================
-bail                      Stop after hitting an error.
-------------------------- ---------------------------------------------------------------------------------
-batch                     Force batch I/O.
-------------------------- ---------------------------------------------------------------------------------
-column                    Query results will be displayed in a table like form, using whitespace characters 
                           to separate  the  columns  and align the output.
-------------------------- ---------------------------------------------------------------------------------
-cmd command               run command before reading stdin
-------------------------- ---------------------------------------------------------------------------------
-csv                       Set output mode to CSV (comma separated values).
-------------------------- ---------------------------------------------------------------------------------
-echo                      Print commands before execution.
-------------------------- ---------------------------------------------------------------------------------
-init file                 Read and execute commands from file , which can contain a mix of SQL statements i
                           and meta-commands.
-------------------------- ---------------------------------------------------------------------------------
-[no]header                Turn headers on or off.
-------------------------- ---------------------------------------------------------------------------------
-help                      Show help on options and exit.
-------------------------- ---------------------------------------------------------------------------------
-html                      Query results will be output as simple HTML tables.
-------------------------- ---------------------------------------------------------------------------------
-interactive               Force interactive I/O.
-------------------------- ---------------------------------------------------------------------------------
-line                      Query  results will be displayed with one value per line, rows separated by a 
                           blank line.  Designed to be easily parsed by scripts or other programs
-------------------------- ---------------------------------------------------------------------------------
-list                      Query results will be displayed with the separator character 
                           between each field value.  The default is the pipe symbol.
-------------------------- ---------------------------------------------------------------------------------
-mmap N                    Set default mmap size to N
-------------------------- ---------------------------------------------------------------------------------
-nullvalue string          Set string used to represent NULL values.  Default is '' (empty string).
-------------------------- ---------------------------------------------------------------------------------
-separator separator       Set output field separator.  Default is the pipe symbol.
-------------------------- ---------------------------------------------------------------------------------
-stats                     Print memory stats before each finalize.
-------------------------- ---------------------------------------------------------------------------------
-version                   Show SQLite version.
-------------------------- ---------------------------------------------------------------------------------
-vfs name                  Use name as the default VFS.
========================== =================================================================================

INIT FILE
       sqlite3  reads  an initialization file to set the configuration of the interactive environment.  Throughout 
       initialization, any previously specified setting can be overridden.  The sequence of initialization is as follows:

       o The default configuration is established as follows:

       mode            = LIST
       separator       = "|"
       main prompt     = "sqlite> "
       continue prompt = "   ...> "

       o If the file ~/.sqliterc exists, it is processed first.  can be found in the user's home directory,  it  is  read  and
       processed.  It should generally only contain meta-commands.

       o If the -init option is present, the specified file is processed.

       o All other command line options are processed.


META COMMANDS

======================== ==========================================================
.archive ...             Manage SQL archives
------------------------ ----------------------------------------------------------
.auth ON|OFF             Show authorizer callbacks
------------------------ ----------------------------------------------------------
.backup ?DB? FILE        Backup DB (default "main") to FILE
------------------------ ----------------------------------------------------------
.bail on|off             Stop after hitting an error.  Default OFF
------------------------ ----------------------------------------------------------
.binary on|off           Turn binary output on or off.  Default OFF
------------------------ ----------------------------------------------------------
.cd DIRECTORY            Change the working directory to DIRECTORY
------------------------ ----------------------------------------------------------
.changes on|off          Show number of rows changed by SQL
------------------------ ----------------------------------------------------------
.check GLOB              Fail if output since .testcase does not match
------------------------ ----------------------------------------------------------
.clone NEWDB             Clone data into NEWDB from the existing database
------------------------ ----------------------------------------------------------
.connection [close] [#]  Open or close an auxiliary database connection
------------------------ ----------------------------------------------------------
.databases               List names and files of attached databases
------------------------ ----------------------------------------------------------
.dbconfig ?op? ?val?     List or change sqlite3_db_config() options
------------------------ ----------------------------------------------------------
.dbinfo ?DB?             Show status information about the database
------------------------ ----------------------------------------------------------
.dump ?OBJECTS?          Render database content as SQL
 
                         Use this with .output

                         .output flights.sql

                         .dump flights

                         drop table flights;

                         < now edit flights.sql with vi and change the schema >

                         .read flights.sql
------------------------ ----------------------------------------------------------
.echo on|off             Turn command echo on or off
------------------------ ----------------------------------------------------------
.eqp on|off|full|...     Enable or disable automatic EXPLAIN QUERY PLAN
------------------------ ----------------------------------------------------------
.excel                   Display the output of next command in spreadsheet
------------------------ ----------------------------------------------------------
.exit ?CODE?             Exit this program with return-code CODE
------------------------ ----------------------------------------------------------
.expert                  EXPERIMENTAL. Suggest indexes for queries
------------------------ ----------------------------------------------------------
.explain ?on|off|auto?   Change the EXPLAIN formatting mode.  Default: auto
------------------------ ----------------------------------------------------------
.filectrl CMD ...        Run various sqlite3_file_control() operations
------------------------ ----------------------------------------------------------
.fullschema ?--indent?   Show schema and the content of sqlite_stat tables
------------------------ ----------------------------------------------------------
.headers on|off          Turn display of headers on or off
------------------------ ----------------------------------------------------------
.help ?-all? ?PATTERN?   Show help text for PATTERN
------------------------ ----------------------------------------------------------
.import FILE TABLE       Import data from FILE into TABLE
------------------------ ----------------------------------------------------------
.imposter INDEX TABLE    Create imposter table TABLE on index INDEX
------------------------ ----------------------------------------------------------
.indexes ?TABLE?         Show names of indexes
------------------------ ----------------------------------------------------------
.limit ?LIMIT? ?VAL?     Display or change the value of an SQLITE_LIMIT
------------------------ ----------------------------------------------------------
.lint OPTIONS            Report potential schema issues.
------------------------ ----------------------------------------------------------
.load FILE ?ENTRY?       Load an extension library
------------------------ ----------------------------------------------------------
.log FILE|off            Turn logging on or off.  FILE can be stderr/stdout
------------------------ ----------------------------------------------------------
.mode MODE ?TABLE?       Set output mode
------------------------ ----------------------------------------------------------
.nonce STRING            Disable safe mode for one command if the nonce matches
------------------------ ----------------------------------------------------------
.nullvalue STRING        Use STRING in place of NULL values
------------------------ ----------------------------------------------------------
.once ?OPTIONS? ?FILE?   Output for the next SQL command only to FILE
------------------------ ----------------------------------------------------------
.open ?OPTIONS? ?FILE?   Close existing database and reopen FILE
------------------------ ----------------------------------------------------------
.output ?FILE?           Send output to FILE or stdout if FILE is omitted
                         
                         .output /tmp/asc.sql

                         .schema

                         Creates a file called asc.sql with the database
                         schema in it.
------------------------ ----------------------------------------------------------
.parameter CMD ...       Manage SQL parameter bindings
------------------------ ----------------------------------------------------------
.print STRING...         Print literal STRING
------------------------ ----------------------------------------------------------
.progress N              Invoke progress handler after every N opcodes
------------------------ ----------------------------------------------------------
.prompt MAIN CONTINUE    Replace the standard prompts
------------------------ ----------------------------------------------------------
.quit                    Exit this program
------------------------ ----------------------------------------------------------
.read FILE               Read input from FILE
------------------------ ----------------------------------------------------------
.recover                 Recover as much data as possible from corrupt db.
------------------------ ----------------------------------------------------------
.restore ?DB? FILE       Restore content of DB (default "main") from FILE
------------------------ ----------------------------------------------------------
.save FILE               Write in-memory database into FILE
------------------------ ----------------------------------------------------------
.scanstats on|off        Turn sqlite3_stmt_scanstatus() metrics on or off
------------------------ ----------------------------------------------------------
.schema ?PATTERN?        Show the CREATE statements matching PATTERN
------------------------ ----------------------------------------------------------
.selftest ?OPTIONS?      Run tests defined in the SELFTEST table
------------------------ ----------------------------------------------------------
.separator COL ?ROW?     Change the column and row separators
------------------------ ----------------------------------------------------------
.session ?NAME? CMD ...  Create or control sessions
------------------------ ----------------------------------------------------------
.sha3sum ...             Compute a SHA3 hash of database content
------------------------ ----------------------------------------------------------
.shell CMD ARGS...       Run CMD ARGS... in a system shell
------------------------ ----------------------------------------------------------
.show                    Show the current values for various settings
------------------------ ----------------------------------------------------------
.stats ?ARG?             Show stats or turn stats on or off
------------------------ ----------------------------------------------------------
.system CMD ARGS...      Run CMD ARGS... in a system shell
------------------------ ----------------------------------------------------------
.tables ?TABLE?          List names of tables matching LIKE pattern TABLE
------------------------ ----------------------------------------------------------
.testcase NAME           Begin redirecting output to 'testcase-out.txt'
------------------------ ----------------------------------------------------------
.testctrl CMD ...        Run various sqlite3_test_control() operations
------------------------ ----------------------------------------------------------
.timeout MS              Try opening locked tables for MS milliseconds
------------------------ ----------------------------------------------------------
.timer on|off            Turn SQL timer on or off
------------------------ ----------------------------------------------------------
.trace ?OPTIONS?         Output each SQL statement as it is run
------------------------ ----------------------------------------------------------
.vfsinfo ?AUX?           Information about the top-level VFS
------------------------ ----------------------------------------------------------
.vfslist                 List all available VFSes
------------------------ ----------------------------------------------------------
.vfsname ?AUX?           Print the name of the VFS stack
------------------------ ----------------------------------------------------------
.width NUM1 NUM2 ...     Set minimum column widths for columnar output
======================== ==========================================================



***********************
All changes to consider
***********************

Security
========

The application is designed to be multi user.  There is a user maintenance function.
Once users register, there is an approval process which must be done by a system
administrator.

The Flask-Login module is used to support security.
auth.py controls both the login function, password change and user authorisation

The login_user functions logs the user in and it has a "remember" parameter with a duration set to 5 days.
So users will stay logged in for 5 days before being asked again.
Some functions use the @login_required decorator which ensures that a user has logged in
during THIS session.  This is particularly true of the user administration functions.


Mobility
========

The application must support Mobile devices.
This is done largely in the css.

Two important styles are mobile_port_suppress and mobile_land_supress.
As the name implies, when a page is shown on a mobile device in PORTrait or LANDscape rotation
the content will be suppressed.

For example:: html

      <div class="cell mobile_port_supress mobile_land_supress " align="left">{{ f.tow_pilot }}</div>
	  
What constitutes "Mobile"?
	This is done in the CSS by specifying the max-width attribute.
	Currently this is set at 30em for portrait and 60em for landscape.



Sql Alchemy
===========

I started using sqlalchemy and the methods for accessing the database in sqlalchemy
are shown in testcases.py and cli.py and schema.py

I then changed to flask-sqlalchemy and the methods for use with this are in
fschema, ftestcases and fcli.

***************************
Particular functional notes
***************************

Capturing forms data changes
============================

On certain forms there may be buttons that can only be selected if the data on the form has been saved.
An example of this is the main flight maintenance form (changeflight.html).  It contains a button to
all the user to jump to recording payment details.  But what if the user pressed "flight down" immediately
prior to pressing the payment button?  We want to ensure that the payment button cannot be selected unless
the user pressed the save (or possibly cancel) button first.

To achieve this we load a little bit of javascript in the html that contains the form and the button.

Below is the java script required to caputre that::

    {% block header %}
    <script>
      $(document).ready(function(){
        // At form load caputure the contents of the form to a variable via the serialize function
        // Note that the form must have the id=trapchange
        var trapchange_data = $("#trapchange").serialize();

        // when the button with id "matpaymentbtn" is pressed, check to see if the current form
        // content matches the content when the form was loaded.  If not prevent the button action
        // by returning false.
        $("#matpaymentbtn").on("click", function() {
              if ($("#trapchange").serialize() != trapchange_data) {
                alert('Data on the form Changed.  You need to accept or cancel the changes first')
                return false;
              }
          });
        });
    </script>
    {% endblock %}

***************
Running the CLI
***************

Inside pycharm
==============
create a config.  Note that "Add content roots to PYTHONPATH" must be selected.

=================   ====================================================
Item                Value
=================   ====================================================
Script Path         /home/rayb/PycharmProjects/flask31/asc/cli.py
Parameter           --test (or whatever)
Working Directory   /home/rayb/PycharmProjects/flask31
=================   ====================================================

At pythonanywhere
=================

*   Start a Bash Console.
*   workon flask31.  You will get an error about no module named site.  You can ignore this.
*   Ensure the current folder is the parent of the instance folder
    and that should also be the parent of the asc folder.  (i.e. PWD
    should be /home/ascgliding.
*   export PYTHONPATH=$PWD
*   export FLASK_ENV=development
*   python asc/cli.py --test
*   or to blow away the data and restart: python asc/cli.py --demodata

CLI Functions
=============

============     ===================== ==========================================================
Parameter        Function              Notes
============     ===================== ==========================================================
--init           init_db()             Drops all the tables and recreates them.
                                       Required for database changes
------------     --------------------- ----------------------------------------------------------
--test           test001()             Simple test that the CLI is working.  lists first 10
                                       flights from the database.
------------     --------------------- ----------------------------------------------------------
--loadcsv        csvload()             Imports flights from a flatfile from utilitisation
                                       spreadsheet
------------     --------------------- ----------------------------------------------------------
--demodata       add_demo_data()       note that this calls init_db()

                                       - Adds rayb user
                                       - Adds RDW
                                       - Imports aircraft
                                       - Imports aircraft from aircraft.csv
                                       - Imports Pilots from pilots.csv
                                       - Imports flights from flights.csv
------------     --------------------- ----------------------------------------------------------
--loadmbr        add_mbr_data          Deletes the membership table and trans tables
                                       Reloads from flask31/membershipdb_members.csv
------------     --------------------- ----------------------------------------------------------
--updmbr         periodic_mbr_update() Use this function to periodically update the list of
                                       Members and pilots from the membership database.

                                       - Open the membership database.
                                       - Use the export function to export all the records from
                                         columns B to AD.
                                       - Make sure dates are in y-m-dddd format (most important)
                                       - Copy this file to the PARENT of the instance folder.
                                       - Run this function.

============     ===================== ==========================================================



===========
Environment
===========

******************
Package Versioning
******************

I cannot begin to tell you how important it is that the platform that you are developing on
has EXACTLY the same versions of all the packages as the one in which the application is running.

I spent two days trying to get it to run on windows.  Finally I removed all the packages and
then added them back one by one specifying the versions.  Worked.

Create the requirements file with::

    pip freeze > REQUIREMENTS.txt

Upgrading to Python 3.10
========================


The following things need doing:

    *   Upgrade all packes to their latest versions
    *   Change all references from wtforms.fields.html5 to simply wtforms.fields.
    *   Change wtforms_ext.py remove HTMLString
    *   Change wtforms_ext.py add from markupsafe import Markup
    *   Change wtforms_ext.py change return HTMLString to return Markup (2 places)
    *   PIP install email_validator
    *   pip install WTForms-Ext
    *   pip install MarkupSafe
    *   change membership.py add import email_validator

**************
Platforms
**************

This project is deployed with PythonAnywhere (a unix based platform).

This project uses a unix based module to get the current user (for logging purposes).
However this is not actually used in the python log anywhere so it is a bit academic.
It does use sqlite and there is a subtle difference opening the database in windows
platforms compared with unix platforms.

To allow development on pycharm on a windows environment but deployment on a unix environment
the config.py contains a DEVELOPMENT config and a PRODUCTION CONFIG.
The development config ASSUMES windows and the production config assumes UNIX.

All pycharm configs must have FLASK_ENV set to "Development" and the WSGI file in Unix must be set to
'Production'

Note the difference in the code above is the number of "/" characters in the DATABASE_URI config.


As at 30 May 2021 the maintenance of this code is done
on my windows machine.

Start the project - "RUN ASC" config.  goto \\\\mydemo\:5000

****************************
Moving the Code
****************************

The parent folder of the .py files and the templates foolder  must be named asc.

***************
Windows Pycharm
***************

Note that the working directory for all configurations should be set to
blahblahblah/flask31/asc.  i.e. always the asc folder.

This is because this is what it is set to on pythonanywhere and paths to
CSV files must be relative to this folder.


*********************
PythonAnywhere Config
*********************

WSGI Configuration File
=======================
This is a critical file.  It is not stored as part of the project folder so it is not
overwritten when code is uploaded to pythonanywhere.  It is stored here:

/var/www/ascgliding_pythonanywhere_com_wsgi.py

And it looks like this ::

    # +++++++++++ FLASK +++++++++++
    # Flask works like any other WSGI-compatible framework, we just need
    # to import the application.  Often Flask apps are called "app" so we
    # may need to rename it during the import:
    #
    #
    import sys
    import os
    import time

    os.environ["TZ"] = "Pacific/Auckland"
    time.tzset()

    #
    ## The "/home/ascgliding" below specifies your home
    ## directory -- the rest should be the directory you uploaded your Flask
    ## code to underneath the home directory.  So if you just ran
    ## "git clone git@github.com/myusername/myproject.git"
    ## ...or uploaded files to the directory "myproject", then you should
    ## specify "/home/ascgliding/myproject"
    os.environ['FLASK_APP'] = 'asc'
    os.environ['FLASK_ENV'] = 'production'
    #path = '/home/ascgliding'
    #if path not in sys.path:
    #    sys.path.append(path)

    project_home = u'/home/ascgliding'

    if project_home not in sys.path:
        sys.path = [project_home] + sys.path

    #
    #from main_flask_app_file import app as application  # noqa
    #from asc import asc as application
    from asc.runit import app as application
    # NB -- many Flask guides suggest you use a file called run.py; that's
    # not necessary on PythonAnywhere.  And you should make sure your code
    # does *not* invoke the flask development server with app.run(), as it
    # will prevent your wsgi file from working.

Uploading Code
==============

To upload a new version of the system:

*   On PythonAnywhere: Create a backup of asc using tar and copy to local machine
*   Zip the contents of the asc folder on windows.
*   copy to /home/ascgliding on pythonanywhere
*   Start a bash console
*   Type 'unzip asc.zip'.  You will be asked to replace the first file.  Answer 'A' to replace all.
*   Close the console.
*   From the Web function reload the app
*   Run any upgrade code via the cli







Python Anywhere
===============

To use Sqlite3:

*   Start a bash console
*   cd ~/instance
*   sqlite3 asc.sqlite


=================================
Schema as at 2 Jan 23
=================================

Schema::


    CREATE TABLE users (
        id INTEGER NOT NULL,
        name VARCHAR NOT NULL,
        fullname VARCHAR,
        email VARCHAR,
        administrator BOOLEAN,
        authenticated BOOLEAN,
        password_hash VARCHAR,
        approved BOOLEAN,
        inserted DATETIME,
        updated DATETIME, gnz_no integer,
        PRIMARY KEY (id),
        UNIQUE (name),
        CHECK (administrator IN (0, 1)),
        CHECK (authenticated IN (0, 1)),
        CHECK (approved IN (0, 1))
    );
    CREATE TABLE flights (
        id INTEGER NOT NULL,
        flt_date DATE,
        linetype VARCHAR(2),
        pic VARCHAR,
        p2 VARCHAR,
        ac_regn VARCHAR,
        tow_pilot VARCHAR,
        tug_regn VARCHAR,
        takeoff TIME,
        tug_down TIME,
        landed TIME,
        release_height INTEGER,
        tow_charge INTEGER NOT NULL,
        glider_charge INTEGER NOT NULL,
        other_charge INTEGER NOT NULL,
        payment_note VARCHAR,
        general_note VARCHAR,
        inserted DATETIME,
        updated DATETIME,
        PRIMARY KEY (id)
    );
    CREATE TABLE pilots (
        id INTEGER NOT NULL,
        code VARCHAR NOT NULL,
        fullname VARCHAR NOT NULL,
        email VARCHAR,
        userid INTEGER,
        towpilot BOOLEAN,
        instructor BOOLEAN,
        bscheme BOOLEAN,
        inserted DATETIME,
        updated DATETIME, gnz_no integer,
        PRIMARY KEY (id),
        UNIQUE (code),
        CHECK (towpilot IN (0, 1)),
        CHECK (instructor IN (0, 1)),
        CHECK (bscheme IN (0, 1))
    );
    CREATE TABLE slots (
        id INTEGER NOT NULL,
        userid INTEGER,
        slot_type VARCHAR NOT NULL,
        slot_key VARCHAR NOT NULL,
        slot_desc VARCHAR,
        slot_data VARCHAR,
        inserted DATETIME,
        updated DATETIME,
        PRIMARY KEY (id)
    );
    CREATE TABLE aircraft (
        id INTEGER NOT NULL,
        regn VARCHAR,
        type VARCHAR,
        launch BOOLEAN,
        rate_per_hour INTEGER NOT NULL,
        flat_charge_per_launch INTEGER NOT NULL,
        rate_per_height INTEGER NOT NULL,
        per_height_basis INTEGER NOT NULL,
        rate_per_hour_tug_only INTEGER NOT NULL,
        bscheme BOOLEAN,
        default_launch VARCHAR,
        default_pilot VARCHAR,
        seat_count INTEGER,
        inserted DATETIME,
        updated DATETIME,
        PRIMARY KEY (id),
        CHECK (launch IN (0, 1)),
        CHECK (bscheme IN (0, 1))
    );
    CREATE TABLE members (
        id INTEGER NOT NULL,
        active BOOLEAN,
        gnz_no INTEGER,
        type VARCHAR(8),
        surname VARCHAR,
        firstname VARCHAR,
        rank VARCHAR,
        note TEXT,
        email_address VARCHAR,
        dob DATE,
        phone VARCHAR,
        mobile VARCHAR,
        address_1 VARCHAR,
        address_2 VARCHAR,
        address_3 VARCHAR,
        service BOOLEAN,
        roster VARCHAR(2),
        email_2 VARCHAR,
        phone2 VARCHAR,
        mobile2 VARCHAR,
        committee BOOLEAN,
        instructor BOOLEAN,
        tow_pilot BOOLEAN,
        oo BOOLEAN,
        duty_pilot BOOLEAN,
        nok_name VARCHAR,
        nok_rship VARCHAR,
        nok_phone VARCHAR,
        nok_mobile VARCHAR,
        glider VARCHAR,
        inserted DATETIME,
        updated DATETIME,
        PRIMARY KEY (id),
        CHECK (active IN (0, 1)),
        CHECK (type IN ('FLYING', 'JUNIOR', 'VFP BULK', 'SOCIAL')),
        CHECK (service IN (0, 1)),
        CHECK (roster IN ('D', 'T', 'I', 'IT', 'D', 'N')),
        CHECK (committee IN (0, 1)),
        CHECK (instructor IN (0, 1)),
        CHECK (tow_pilot IN (0, 1)),
        CHECK (oo IN (0, 1)),
        CHECK (duty_pilot IN (0, 1))
    );
    CREATE TABLE membertrans (
        id INTEGER NOT NULL,
        memberid INTEGER,
        transdate DATE,
        transtype VARCHAR(3),
        transsubtype VARCHAR,
        transnotes TEXT,
        inserted DATETIME,
        updated DATETIME,
        PRIMARY KEY (id),
        FOREIGN KEY(memberid) REFERENCES members (id),
        CHECK (transtype IN ('IR', 'MF', 'DCG', 'MD', 'ICR', 'RTG', 'BFR', 'NOT'))
    );
