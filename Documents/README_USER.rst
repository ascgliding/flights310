.. |date| date::
.. |time| date:: %H:%M
.. header:: ASC Application: |date| |time|
.. The ### directives are processed by rst2pdf.
.. footer:: Page ###Page### of ###Total###


===========================
Flight Recording System
===========================

.. raw:: pdf

    PageBreak


.. contents:: Table of Contents

.. sectnum::

.. raw:: pdf

    PageBreak


************************
Access And Registration
************************

How to access the system
========================
The system is web based.  Goto to www.ascgliding.pythonanywhere.com.
Screen will look slightly different between phones, tablets and laptops.

User Registration
=================
As with most online systems there is a step required step to register.
When you first go to the web site you will be prompted to login or register.
Both of these options are available from the menu accessed via three horizontal lines in the top LH corner.
Note that the system will force all user names to lowercase.  This is to make it easier to login on a mobile
phone, where the operating system tends to always force the first character of to uppercase.

Once you have logged on with an approved user account you will be shown a list of days with the date underlined.

General
=======

The application is designed to work on mobile phones and tablets (in either portrait or landscape orientation).
The data that is displayed on the screen is dependant on the size of the screen available.  You will see
different things on different devices.

Adding new things is generally done by pressing the "+" symbol usually found in the top RH corner.

When a detailed screen is displayed (such as a flight) the first two buttons at the bottom of the screen
are a tick and a cross inside a blue circle.  The tick button accepts your input and updates the database.
The cross will ignore your changes and return to the previous screen.  
It is most important that you press the tick to accept your changes.  If you do not press the tick NOTHING will get upated.

The last button on the bottom line of the screen is a rubbish tin.  Use this to completely delete the record from
the database.

Try to avoid the web browser's back button.  This is often causes problems.

Caravan Hardware Setup
======================

There is a large tablet in the caravan.  There is also a mobile phone.
The tablet does not have a mobile data facility so the phone is required in order
to connect to a mobile data network (in our case "2 degrees").  The phone must have
data available.

If, for any reason, you cannot get a connection, follow these steps:

Phone - Mobile Hot Spot
-----------------------

On the phone, "mobile hotspot" must be selected.  To check this,
put your finger at the top of the screen and swipe down.  Look for icon shown in the
screen shot below, it should be white on a blue background.  If it is two shades of
grey, then it is not selected.  Tap it with your finger to get white-on-blue.

.. image:: README_USER_SCR002.jpg
   :scale: 15%

Tablet - Wifi 
-------------

On the tablet - check the wifi signal appears on the top right hand corner
The icon looks like this:


.. image:: README_USER_SCR018.jpg

It should appear here:

.. image:: README_USER_SCR011.jpg
   :scale: 15%

If this is missing follow the steps in the following section to pair the phone to the tablet


Pairing the Phone to the tablet
-------------------------------

Tap on the Apps icon on the home page:


.. image:: README_USER_SCR016.jpg
   :scale: 15%

Tap on "Settings":


.. image:: README_USER_SCR015.jpg
   :scale: 15%


Tap on Wifi and then "ASC Galaxy":


.. image:: README_USER_SCR014.jpg
   :scale: 15%

You may or may not be prompted for the password.  Once the phone has been paired once, then this should not happen again unless
the password, phone or connection name has changed.  If you are prompted for the password enter the correct password.  At time
of writing this is "udul597h9":


.. image:: README_USER_SCR013.jpg
   :scale: 15%
    
When complete it should say "Connected":

.. image:: README_USER_SCR012.jpg
   :scale: 15%

What happens when we run out of data.
-------------------------------------

Our account plan is structured so that we should have enough data for a month
in which we record 250 flights.  This is about 20 per day.  If we run out
of data then the phone will need to be topped up.

The first thing to note is that the phone must have access to the internet in some manner
in order to top it up.   THEREFORE if it runs out of data, then it cannot be topped up
using just the phone.  It must be connected to some other source that will proivide internet
access.  The easiest way is to turn on mobile hotspot on another phone and pair them.

Once you have access to the internet then you can select the 2 degrees app on the main
screen:

.. image:: README_USER_SCR003.jpg
   :scale: 15%

When the application starts you see the following screen:

.. image:: README_USER_SCR004.jpg
   :scale: 15%


This should really be checked each day.  If the available data is less than 20mb then
update the plan.  This is done as follows:

.. image:: README_USER_SCR010.jpg
   :scale: 15%


.. image:: README_USER_SCR005.jpg
   :scale: 15%


.. image:: README_USER_SCR006.jpg
   :scale: 15%


.. image:: README_USER_SCR007.jpg
   :scale: 15%


.. image:: README_USER_SCR008.jpg
   :scale: 15%


.. image:: README_USER_SCR009.jpg
   :scale: 15%





******************
Daily Transactions
******************

There are two types of entries:

* Flights : As you would expect, the details of a given flight movement.
* Notes : Any free format text.  Use this for recording things like the purchase of tow tickets, log books.  
  Any kind of text note.


The day summary screen shows all the dates on which we have had flights (in descending order).
Click on a day to see the flights on that day.

If this is the first flight of the day click on the "+" symbol to the right of the words "Day Summary".

You will be prompted for a date, the duty instructor, tow pilot and duty pilot.  The system knows the roster
so it will automatically default to the next scheduled flying day with whoever is on the roster at the time
the roster was published.  It does not know about swaps, so double check what is on the screen with who
is actually on the field.  

When this screen is accepted (by pressing the tick in the lower LHS) the system will add a note for the
nominated date containing the names of these people.

Recording flights
=================

The concept is that as soon as an a/c is gridded you can put it into the system.  It does not matter that it has not
yet left the ground.  Make a record that the flight is about to takeoff.

If you are using a phone then the date is not displayed and the system uses the greatest date in the system (of
either flights or notes).

You should enter the a/c REGN first.  You can enter anything you like in the REGN field, but if you select from one
of the predefined regns then the system will default a bunch of stuff making your life easier.
The system knows how many seats an a/c has, and it also knows how they
will be launched (i.e. SELF LAUNCH or TUG) and it also has a record of the default pilot for each a/c (for private owners).
Any time you change the regn, the pilots and launch methods are liable to change.  So put this in first.

Enter the pilots next.  As with the regn, you can enter whatever you like but the system knows about club members
and selecting from the drop down list makes data entry quicker and assists with payment options.  DO NOT type over the
name if you have selected it from the drop-down.  This is quite important.  Especially for club members.
If it is the first flight for the day change the tow pilot (and tug regn if required).  These are remembered and
default for each subsequent flight.

.. Note::

    Flight recording (as described below) has the ability to record a known pilot (usually club members)
    with a specific flight as either PIC or P2.  However the user can enter any text they like for the
    pilot names.  This is required to support visitors, cadets and the like.

    Once your userid has been approved, the sysadmin will link it to a pilot record.  This will make it easier
    to select during flight recording.  If you wish to use the Logbook feature of the application it is important
    that the PIC or P2 name is NOT changed from the system default.  The logbook feature is driven from the
    pilot **Name**

Recording times
===============

At takeoff, select the flight and press the first of the three a/c icons on the bottom.  This will record the current
time as the takeoff time.  If you want to change the time then click on the time and you can change it to anything you want.

Similarly, when the tug lands, press the yellow landing a/c icon.  This will record tug down for that flight.
Once a takeoff has occurred the main screen listing the flights for the day will show the current a/c under tow
as a button on the top RHS of the screen.  Pressing this button immediately records tug down for that glider.

When the glider lands press the blue landing a/c icon.

Enter the release height as soon as you can.  You can either ask the pilot before or after they land or ask the tow
pilot.  It doesn't matter much when you put it in, except that it must be done before recording the payment details.

Flight Notes
============

At the bottom of the flight display is note icon next to the glider landed icon.  Use this to record any useful
information pertinent to that FLIGHT.  "First Solo" or "Club paying for Flight" are examples.

About Views
===========
At the top of the day screen there is a button marked "View".  This will allow you to select from a set of pre-defined
views.  The current view name is shown on the LHS of the screen.  The intention of the views is to allow you to find
a particular flight a little quicker.

There are five defined views:

=============     ===========================================================================================
Name              Description
-------------     -------------------------------------------------------------------------------------------
All Flights       All flights recorded for the day.
Airborne          Flights that have a takeoff time but no landed time.
Gridded           Flights that have no takeoff time
Landed            Flights that have a landed time
Unpaid            Flights for which no amount or payment record has been made
=============     ===========================================================================================

***********
Other Items
***********

Recording payment
=================
Select a flight.  Press the blue dollar icon at the bottom.

The payment screen will be displayed.  Press the CALC button to automatically calculate the amount and payer.
Note again that these items are suggestions. Not all rules are built into the calculation so do not accept
the values as gospel.

Select the payment method from the down list.

Changing the Tow Pilot and Tow Aircraft
=======================================

This is a simple case of changing the values on the first flight (or any flight) of
the day.  Subsequent new
records will default from the previous flight.

Recording Trial Flights
=======================

Set the P2 to "Trial Flight".
Add a note to the flight that includes the name of the person.

In the payments section use the calc tab.  The payer should be set to "Trial Flight".
Put ALL of the amount in the aerotow.  Normally this will be $150.  Service people pay the normal
tow rate plus $1/min for the glider hire.  Override the amounts as required.

Set the payment type as appropriate.  This will be voucher (add the voucher number after selecting
'voucher' from the drop down list).  Note, that if the person paid for the trial flight via Internet
Banking and did not have a physical voucher, the payment type should still be recorded as Voucher.
'Internet' is only for payments received AFTER the flight.

Recording flights in a motor glider
===================================

A self launching glider should be recorded as normal except that the Tug regn must be set to 'SELF LAUNCH'.
This can be found in the drop down list.  A takeoff time and a landed time is required but no tug down
time is required.
Motor gliders that are in the master aircraft table should have their default launch method set to 'SELF LAUNCH'
and this will cause the tow details to be set automatically.

Recording non-towing flights in RDW
===================================

If a pilot flies the tow plane without towing a glider, the glider regn should be set to "TUG ONLY".
This is a valid value in the drop down list.  A takeoff and tug down time needs to be recorded but
release height and landed times are left blank.

Recording ATC Flying in an ASC Aircraft
=======================================

Each sqn is setup ass a customer in the pilots table.  Select the appropriate sqn from the drop down.
Usually the amount is $65.  Put this in the aerotow field on the payments screen.

.. raw:: pdf

    PageBreak

***************************
Aircraft Maintenance System
***************************

Introduction
============

The aircraft maintenance system is designed to alert users to upcoming aircraft maintenance.

Each maintenance item is defined as a "task".
Lifed items are simply a task to replace the lifed item.

Both meter based tasks (e.g. every 50 hours) and calendar based tasks are supported.  

The system has a security function that provides control over who can do what by
aircraft registration.

There is a concept of "standard" tasks and meters where all available tasks and
meters are defined, and a set of "aircraft" tasks and meters where specific
tasks and meters are attached to specific aircraft.

A general note about id numbers
-------------------------------

Throughout the application rows on screens often have an ID number on the left
hand side.  Often this is underlined.  Clicking on the ID number will provide
access to the item.

Note that ID numbers are not necessarily consecutive on ANY screen.  They are
just a number.  There is very likely to be gaps in the sequence.  This is
normal.

Standard Items
==============

Standard Meters
---------------

A standard meter contains only two data items:

    *   The name of the meter
    *   The unit of measure.  

        This is what the meter is measuring.  It can only be a counter of some
        kind, such as the number of landings, the number of takeoffs or a time
        unit such as tach meter, engine hours meter, airswitch meter, hobbs
        meter.

Standard Tasks
--------------

The standard task is a bit more complex.  The standard task contains:

    *   A description of the task.
    *   Whether the task is calendar based or meter based.

        Where a task is required at the earlier of some time period or some
        meter reading, then the task basis MUST be set to CALENDAR, and meter
        id specified as well as the calendar  details.

    *   For calendar based tasks then a calendar unit of measure (years, months
        or days) is required and the number of years, months or days.
    *   Similarly, where a task is meter based, then the meter name and the reading
        is required.

Aircraft Items
==============

The system keeps track of which aircraft you are currently working on in each
session.  The first time in each session it will prompt you for the
registration.  After you select the aircraft it will remember that registration
until you change it.

For each aircraft you need to define which meters are installed and which tasks
are required.

Meters
------

Add a new meter by pressing the "+" icon in the top RH corner.  A drop down list
of available meters that are *NOT YET INSTALLED* on the aircraft is displayed.  Press enter
to select the appropriate one.

Once selected, the meter is added to the airraft and appears in the list.  
You should **Immediately** click on the underscored id on the LHS to then set
the following attributes for the meter:

    *   Meter Prompt

        This is the label text that will appear on the screen when prompting the
        user to enter a meter reading.  It is very important that you include in
        the text something that clearly identifies to anyone adding a meter
        reading that the value that should be entered is incremental (such as
        the nunber of landings) as opposed to the a finishing total value (such
        as a hobbs meter reading from the aircraft).  It is also a good idea
        to include some reference to the unit of measure.

        Do not assume that qty based readings will be incremental and meter
        time based meters will be closing values.  The tow plane has all
        maintenance performed on airframe hours (wheels up to wheels down) and
        the readings are recorded as the total time in the air in each flying
        day.  However, it also has a tachometer and the CLOSING meter reading is
        recorded each day.

    *   Display Unit

        There are three entry / display units.  They are :

        *   Qty.  Use this for number of things such landings count.

        *   Decimal Hours.  Use this for recording time in decimal hours. A
            decimal point will spearate the hours from the decimal component.
            When entering values, users will be required to enter the decimal
            point.  This is useful when the meter being recorded is in decimal
            hours.

        *   Hours:Minutes.  Use this for recording time in hours and minutes.  A
            colon will separate the hours from the minutes and user will be
            required to enter the colon to separate the hours from the minutes.
            Useful when the meter being recorded displays hours and minutes.

    *   Entry Method.

        This is what we are expecting the user to enter.  There are two options.

        *   Final meter reading.  This is the TOTAL of what we are measuring and
            used when we are recording something from a displayed meter.

        *   Incremental change.  This is the change in the reading.  For example
            if you are recording a number of landings, then this is the the
            number of landings for a given day. 

    *   Auto Update.

        Select this box to have the dayend process automatically add meter
        readings.  For qty based meter a count of the number of movements will
        be added.  For Time based meters the time from the flight system (either
        tow or glider as appropriate) will be added.

        When users are prompted to enter a reading, they are still prompted for
        these readings but they can be left empty.

Viewing readings
~~~~~~~~~~~~~~~~

Meter readings can be viewed by clicking on the underlined "readings" word on
the RHS of each meter in the list.

The readings are listed.  If a mistake is made entering a reading then the last
meter reading (only) can be removed.  You cannot change readings other than the
last one because each reading contains both the CLOSING value and the difference
between this reading and the previous reading.  Removing anything other than the
last one will cause these two numbers to get out of sync.

Tasks
-----

After selecting the tasks option from the menu a list of defined tasks for the
aircraft is displayed.  For each task, the name of the task and when it is next
due is displayed.  Next to the date is a note describing how the due date was
derived.  It may be a simple calendar basis or meter basis or the earlier of the
two (or a few others such as the date having already expired).

Below each task line is a line that describes the task frequency and the daily
average.  For time based tasks this is a *daily* average in **MINUTES**.

Note that daily averages are based on elapsed days not flying days.  i.e. it
does not matter whether the a/c has flown or not, the average is still
calculated over the elapsed days.  This because we are trying to determine when
the task is due and that is completely independant of actual flying.

Select the "+" in the top LH side to add a new new task.  When this is selected
a screen with dropdown list is displayed.  Only tasks that are not already on
this aircraft are displayed.  After selecting a new task the task list is
re-displayed.  Select the underlined id number on the left hand side to define
the following attributes: 

    *   Last Done & Last Done Meter Reading

        Probably the two most important fields.  The system cannot predict when
        a task is due if it does not know when it was last done.  Add an
        appropriate date and the meter reading (if applicable) when it was last
        done.

    *   Regeneration Basis.

        In general, the determination of the next due date for a given task is based
        on when the task was LAST done.  It is possible that a task may need to
        be next performed on when it was last DUE rather than when it was last
        DONE.  For example, a 50 hour check on the two plane is repeated when
        it was due.  To effect this, enter a value in the regeneration basis
        field.  This value should be less than the next due and is likely to
        be some time in the distant past.  For example if you enter "1200"
        in the field, then the task will fall due at meter readings of 1250,
        1300, 1350, 1400, 1450 and so on.  The system will select the next
        value greater than when it was last done.  Using the above example, if
        the task was last done at 1455 hours, then it will be next due at 1500
        hours.

    *   Average over days.

        This is only related to tasks which are triggered by a meter reading.
        The Average over days field will have no impact on calendar based tasks.

        The is the number of days in the past the system will look to determine
        an average.  Gliding typically occurs more in the summer than the winter
        and therefore tasks that are based on a meter reading of some sort will
        be affected if an average is taken at the beginning of a season (where
        it will be more impacted by winter readings) than at the end of a season
        (where it will be more impacted by summer readings).

        Entering a small number of days in this field will make the prediction
        more responsive to changes in the pattern than a large number.  Where a
        task typically takes more than a year to occur (e.g. 3000 hour check)
        then the average days should be set to 365. Where the task comes around
        quickly (e.g. 50 hour inspection) then the average should be set shorter
        (30 days).

        The system will use a maximum of 365 days and a minimum of 30 days.
        Values less than 30 will be set to 30 for calculation purposes and
        values greater than 365 will be set to 365.

    *   Warning Days and Warning Email.  

        The number of days before a task is predicted to be required before an
        email is sent.  The Warning EMail is self-evident.

    *   Completion.

        The completion button at the bottom of the screen is used to reccord the
        completion of a task.  Completing a task will prompt for a completion
        date, some text and a meter reading (if the task has a linked meter).
        Where a meter reading is recorded for task, the system will create a
        record in the readings table if possible.  It is possible to record
        completion of a task some time later than it was actually performed.  If
        subsequent meter readings have been recorded then the completion
        function will keep a record of the meter reading on the history table
        but it will NOT be able to record the reading on the readings table.

    *   History

        The history button at the bottom of the screen will display the
        maintenance history for this task.  The history function on the main
        screen will display the history for all tasks.



Adding new readings
-------------------

Users can enter meter readings at any time.  When the option is selected the
user is prompted with a data and a note field and then a prompt for each meter
recorded against the aircraft.

The last reading is shown on the screen in red.

Meter readings can only go upwards.  Days in the past or meter readings less
than the previous are not allowed.

Security
========

Only system administrators are able to change the standard tasks or standard
meters or the aircraft security.

For a user to be able to access anything to do with an aircraft they must be
recorded in the aircraft security table.  Each user must be assigned to the
aircraft and the given access to either *All* the maintenance functions for an
aeroplane or just the ability to enter meter readings.

Starting with a New Aircraft
============================

To establish a new aircraft follow these steps:

    #.  Select the Aircraft
    #.  Add the Meters
    #.  Review each meter and check the prompts and units
    #.  Add Meter readings.  The last 3 months is a good starting point
    #.  Add the tasks

Phase 2
=======

At time of this documentation the following items are planned but not yet delivered:

    *   Auto update - not yet written
    *   Auto emails - not yet written
    *   Log book Spreadsheet

        The intention is that a spreadsheet will be able to be produced that
        will be akin to the aircraft logbook.  There will be one sheet listing
        all meter readings by date.  A second sheet will list the maintenance
        history (also by date).
