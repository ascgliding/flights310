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

Table - Wifi 
------------

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
