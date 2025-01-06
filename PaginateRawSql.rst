======================================
Raw SQL Pagination.
======================================

***********
General Use
***********

Sqlalchemy has a very good class called paginate which is great for displaying html pages of data.
It does not handle raw sql.

To solve this there is a lass called PaginateRawSql in oPaginateRawSql.py.  This class emulates
the paginate class in sqlalchemy and exposes the same methods and properties so that the same
code can be used for pagination whether raw sql or ORM pagination is used on pages.

The purpose of this class is to create a class that mirrors the sqlalchemy "paginate" class.
this class implements the same properties and methods used in sqlAlchemy paginate so that the
pagination function can be used on pages that do not lend themselves to the sqlalchemy approach.
An example is a query such as ::

    select
        starttime::date -  date_part('dow', starttime::date - 1)::integer startwk,
        min(starttime) earliest, max(endtime) latest, sum(elapsedtime) hours
        from timesheet
        group by startwk
        order by startwk desc

is difficult to code in sqlalchemy but easy in plain sql, but we still want it paginated.
To paginate the results use code such as::

    from apps.oPaginateRawSql import PaginateRawSql
    ...
    @bp.route('/timesheet_weeks_paged', methods=['GET', 'POST'])
    @bp.route('/timesheet_weeks_paged/<int:page>', methods=['GET', 'POST'])
    def timesheet_weeks_paged(page=1):
        thisqry = '''\
                    select
                        starttime::date -  date_part('dow', starttime::date - 1)::integer startwk,
                        min(starttime) earliest, max(endtime) latest, sum(elapsedtime) hours
                        from timesheet
                        group by startwk
                        order by startwk desc
                        '''
        paginatedlist = PaginateRawSql(db.session.connection(),thisqry,page=page,per_page=26)
        return render_template('timesheet_weeks_paged.html', entries=paginatedlist)

The object is primarily a iterable over the result set but also contains some key properties that
support the pagination.  In particular, the current page, the total number of pages, and a method
called "iter_pages()" which returns a list of pages to be displayed at the bottom of a page.

Note that the query can either be a string containing the sql (as shown in the above example) or
it can also be a sqlalchemy.sql.text object or sqlalchemy.sql.selectable.TextualSelect (see the section below).

The easies way to display the navigable pages is to create a macro which should be included in base.html::

    {% macro render_pagination(pagination, endpoint) %}
      <hr/>
      <div class="page-items">
        Rows {{ pagination.first }} - {{ pagination.last }} of {{ pagination.total }}
      </div>
      <div class=pagination>
        Pages:
        {% for page in pagination.iter_pages() %}
          {% if page %}
            {% if page != pagination.page %}
              <a class=onepage href="{{ url_for(endpoint, page=page) }}">{{ page }}</a>
            {% else %}
              <span class=selectedpage>{{ page }}</span>
            {% endif %}
          {% else %}
            <span class=ellipsis> … </span>
          {% endif %}
        {% endfor %}
      </div>
    {% endmacro %}

The template then merely needs to include something like the following.  Note that
the rows returned from the select are still iterable just as if you were displaying
the rows returned from the select statement.  But, most imprtantly, note the render_pagintation
macro as the last item on the page::

    <table class=entries>
        <tr>
            <th width="200px">Week Ending</th>
            <th width="90px">Start Date</th>
            <th width="90px" style="text-align:center;">End Date</th>
            <th width="60px" style="text-align:right;">Hours</th>
        </tr>
        {% for entry in entries %}
            <tr>
                <td>{{ entry['startwk']|stddate }}</td>
                <td class="text">{{ entry['earliest']|stddate or ''}}</td>
                <td style="text-align:center;">{{ entry['latest']|stddate or '' }}</td>
                <td class="numeric">{{ entry['hours'] or '' }}</td>
            </tr>
        {% else %}
            <div class="flash">Unbelievable. No entries here so far</div>
        {% endfor %}
    </table>
    </hr>
    {{ render_pagination(entries,'timesheet.timesheet_weeks_paged') }}

Finally, the css should include support for the classes defined in the macro above::

    /* pagination */
    .page-items {   align-items:center;
                    display:flex;
                    justify-content:center;
                    color:var(--main-fg-colour);
    }
    .ellipsis   {   display:flex;
    }
    .pagination {   display:flex;
                    align-items:center;
                    justify-content:center;
                    padding:20px;
    }
    .onepage    {   border: 2px solid rgb(95 97 110);
                    border-radius: 0.5em;
                    padding: 2px;
                    width: 2em;
                    margin:0 5px;
                    text-align:center;}

    .selectedpage { border: 2px solid rgb(95 97 110);
                    border-radius: 0.5em;
                    padding: 2px;
                    width: 2em;
                    margin:0 5px;
                    text-align:center;
                    background:var(--main-fg-colour);
                    color:var(--main-bg-colour);
                    }

****************
Query Definition
****************

Parameter two to the class instantiation can either be a valid a Sql statement or a
sqlalchemy.sql.text object.

Parameters
----------

Where the sql statement contains parameters such as ::

        SELECT
        flt_date, sum(case when linetype='FL' then 1 else 0 end) movements,
        max(id) last_id
        FROM flights
        WHERE regn = :acregn
        AND pic = :pilot_in_command
        GROUP BY flt_date
        ORDER BY flt_date desc

THEN, the class must also include the para_dict parameter::

        paginatedlist = PaginateRawSql(db.session.connection(),thisqry,
                        page=page,per_page=26,
                        paradict={'acregn':'GBU','pilot_in_command':'Biggles')

sqlalchemy.sql.text
-------------------

Parameter two can either be a string OR an sqlalchemy.sql.text object

The sqlalchemy text class is the usual way of executing plain text sql (and is what this class uses)
The use of this object provides support for defining the datatype for each field.
This is extremely important in databases such as sqlite which have no inherent column typing.
So it is possible to call the PaginateRawSql class passing a text object::

    from sqlalchemy.sql import text
    ...
    sql = text("""
    SELECT
        flt_date,
        sum(case when linetype='FL' then 1 else 0 end) movements,
        max(id) last_id
        FROM flights
        GROUP BY flt_date
        ORDER BY flt_date desc
        """)
    sql = sql.columns(flt_date=db.Date, movements=db.Integer)
    paginatedlist = PaginateRawSql(db.session.connection(), sql, page=page, per_page=20)

*********
Mobility
*********

When displaying on a mobile device, especially in portrait mode, it may be preferable not to
display the same number of pages (as it will take up quite a bit of screen width).

The iter_pages method has four parameters that control the number of pages displayed.
See the reference section below for more detail on these parameters.

Assuming that the CSS has some classes for controlling what is displayed for mobile, portrait
and non-mobile, then altering the number of pages can be altered in the pagination macro
similar to the following  (note the parameters passed to iter_pages for portrait mode)::

    {% macro render_pagination(pagination, endpoint) %}
        <hr/>
        <div class="mobile_port_suppress mobile_land_suppress">
            <div class="page-items">
                Rows {{ pagination.first }} - {{ pagination.last }} of {{ pagination.total }}
            </div>
        </div>
        <div class="mobile_port_suppress">
            <div class=pagination>
                <span>Pages:</span>
                {% for page in pagination.iter_pages() %}
                    {% if page %}
                        {% if page != pagination.page %}
                            <a class=onepage href="{{ url_for(endpoint, page=page) }}">{{ page }}</a>
                        {% else %}
                            <span class=selectedpage>{{ page }}</span>
                        {% endif %}
                    {% else %}
                            <span class=ellipsis> … </span>
                    {% endif %}
                {% endfor %}
            </div>
        </div>
        <div class="full_screen_suppress mobile_land_suppress">
            <div class="pagination">
                {% for page in pagination.iter_pages(1,2,2,1) %}
                    {% if page %}
                        {% if page != pagination.page %}
                            <a class=onepage href="{{ url_for(endpoint, page=page) }}">{{ page }}</a>
                        {% else %}
                            <span class=selectedpage>{{ page }}</span>
                        {% endif %}
                    {% else %}
                        <span class=ellipsis> … </span>
                    {% endif %}
                {% endfor %}
            </div>
        </div>
    {% endmacro %}

*********
Reference
*********

Object instantiation
--------------------

    ============== =====================================================
    Parameter      Description
    ============== =====================================================
    Connection     This should be the session connection object.
                   typically db.session.connection()
    -------------- -----------------------------------------------------
    SQL            Either a string containing a valid sql statement
                   or an sqlalchemy.sql.text object or an
                   sqlalchemy.sql.selectable.TextualSelect object
    -------------- -----------------------------------------------------
    Page           The page number to display
    -------------- -----------------------------------------------------
    Per Page       The number of entries to display on each page
    -------------- -----------------------------------------------------
    paras_dict     A dictionary of parameters.
    ============== =====================================================

Public Properties
-----------------

========= ============== ========================================================
Name      Data Type      Description
========= ============== ========================================================
page      int            The current page number
--------- -------------- --------------------------------------------------------
per_page  int            The number of rows on each apge
--------- -------------- --------------------------------------------------------
pages     int            The total number of pages
--------- -------------- --------------------------------------------------------
total     int            The total number of rows
--------- -------------- --------------------------------------------------------
has_next  boolean        True if there is another page
--------- -------------- --------------------------------------------------------
has_prev  boolean        True if there is a previous page
--------- -------------- --------------------------------------------------------
next      PaginateRawSql A paginate raw sql object for the next page
--------- -------------- --------------------------------------------------------
prev      PaginateRawSql A paginate raw sql object for the previous page
--------- -------------- --------------------------------------------------------
first     int            The row number of the first row on the current page
--------- -------------- --------------------------------------------------------
last      int            The row number of the last row on the curent page
--------- -------------- --------------------------------------------------------
next_num  int            The next page number
--------- -------------- --------------------------------------------------------
prev_num  int            The previous page number
--------- -------------- --------------------------------------------------------
rows      list           The list of rows
========= ============== ========================================================

Public Methods
--------------

============ ==== ====================================================================
Name         Type Description
============ ==== ====================================================================
iter_pages() List A list of integers containing the page numbers to display at the
                  bottom of a page.

                  The first two items in the list are the first two pages

                  The last two items are the last two pages

                  Inbetween these are pages, two before the current page, the
                  current page and four after the current page.

                  Potentially a None is inserted between the first two, the middle
                  section and the last two if there is a gap in the sequence of numbers.
                  The None is rendered as an ellipisis on the render_pagination macro
                  to indicate missing pages in the list.

                  This function can be passed 4 parameters which are all intgers:

                    * The number of pages from the start to the frist ellipsis
                    * The number of pages after the first ellipsis before the
                      current page
                    * The numbere of pages after the current page but before the
                      last pages
                    * the number of pages to show after the last ellipsis

                  The default values are 2,2,5,2


============ ==== ====================================================================
