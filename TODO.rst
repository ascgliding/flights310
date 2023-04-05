===========
TODO
===========

Time Buttons
------------

History
~~~~~~~

Originally, the concept was that whole page would be submitted with the submit button and the time
buttons were simply to set the fields on the screen via Javascript.

Later on we decided that the buttons should do a submit.

Stupidly, I decided to implement the submit via Java, rather than just capturing the button in python,
setting the time and updating the database.  This involved changing every reference to any
submit button because you cannot call it "submit" if you are going to do it via Java.

What needs doing now is reversing the java.

changeflight.html::

    <div style="display:table-cell; text-align: right;">
        {{ form.btnsubmit() }}
        {{ form.cancel(onclick="goBack()") }}
        <!-- add this button -->
        {{ form.btntakeoff() }}
        <!-- remove these buttons -->
    <!--    <button class="materialbtn" type="button", id="takeoffbtn" name="takeoffbtn" title="Set takeoff time to now" value="takeoffbtn" onclick="resettime('takeoff');">flight_takeoff</button>-->
        <button class="materialbtn" style="color:yellow;background-color: var(--main-fg-colour);", type="button", id="tug_downbtn" name="tug_downbtn" title="Set Tug Down time to now" value="tug_downbtn" onclick="resettime('tug_down');">flight_land</button>
        <button class="materialbtn" type="button", id="landingbtn" name="landingbtn" title="Set Landing time to now" value="landingbtn" onclick="resettime('landed');">flight_land</button>
        {{ form.note() }}
        {{ form.payment() }}
        {{ form.delete() }}
      </div>

flights.py::

    delete = MatButtonField('delete', id='matdeletebtn',
                            icon='delete',
                            help='Press to delete this record',
                            render_kw={'onclick': 'return ConfirmDelete()'})
    # add buttons like this to the form definition
    btntakeoff = MatButtonField('takeoff',
                                id='mattakeoffbtn',
                                icon='flight_takeoff',
                                help="Record Takeoff Time")


changeflight function::

           elif thisform.delete.data:
                db.session.delete(thisrec)
                applog.info('Flight {} deleted'.format(id))
        # change the function to capture the button and set the time.
            elif thisform.btntakeoff.data:
                # to nearest minute
                thisrec.takeoff = datetime.time(datetime.datetime.now().hour, datetime.datetime.now().minute)
            else:
                # if this a tug only flight make sure that tug down and landed are the same
                # thisrec.pic_gnz_no = thisrec.get_pic_gnz_no()


GitHub
------

What do we want :

*   Only one person working on a bit of code at a time
*   Ray to approve commits
*   Pycharm integration
*   Ability to see changes (both)
*   Ability to see uncommitted changes on local version.
*   Ability to see who is working on what files (server).

Problems

*   In pycharm I can only pull the entire branch - is it not possible to pull a single file

Structure

*   Two versions - python 3.10 and python 3.6

Questions

*   What is the difference between push/merge and rebase

Add New Note button to daysummary
---------------------------------

When adding the note for the instructor and so on to the day, and there is nothing for the day
You have to select the PREVIOUS day, insert a note and override the date.  Butt ugly.

I have created the roster table and verified that it will be created when the application starts.
Need to create a datagrid with an import button

Tug Only appears twice in Regn drop down
----------------------------------------

Caused in flights/changeflight.  The problem is that it is explicitly added and also that it appears
in the sql once one tug only flight has been added

Flights.py::

   # A/C List
    sql = sqltext("""
        select distinct ac_regn
        from flights
        where flt_date > :date
        and linetype = 'FL'
       union
        select regn
        from aircraft
        order by ac_regn
        """)
    if thisrec.flt_date is not None:
        activeacdate = thisrec.flt_date - datetime.timedelta(days=90)
    else:
        activeacdate = datetime.date.today()
    acregnlist = [r[0] for r in db.engine.execute(sql, date=activeacdate).fetchall()]
    acregnlist.append(constREGN_FOR_TUG_ONLY)

Payments
--------

This is a pain in the phone platform.

1.  Trial Flights need to have the money split between the tug and the glider.
2.  We need a landscape screen that lists the payments detail so the user can
    see a summary of which ones we need release heights, notes, and payment details
    so the user can see at a glance which is still to be done.
3.  Need some clear policies about recording payment types for differnt transactions
    Trial Flights with / Without vouchers, returning trials

Movements Counter
-----------------

The movements counter on the day summary sheet is out by one.



