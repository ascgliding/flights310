.. |date| date::
.. |time| date:: %H:%M
.. header:: Expenses Application: |date| |time|
.. The ### directives are processed by rst2pdf.
.. footer:: Page ###Page### of ###Total###

***************************
Misc SQL that may be useful
***************************

Pilots with more than 10 flights ::

    SELECT pilot, count(*)
    FROM
    (
    SELECT p2 pilot FROM flights
    WHERE p2 NOT NULL AND p2 <> ''
    UNION all
    SELECT pic FROM flights
    )
    GROUP BY pilot
    HAVING count(*) > 5
