-- CONNECTION: url=jdbc:sqlite:c:\users\rayb\pythonvenv\flask31\instance\asc.sqlite



SELECT
t0.id,
t0.flt_date,
t0.pic,
t0.p2,
COALESCE(t1.TYPE,"Unknown") actype,
CASE WHEN ac_regn = 'TUG ONLY'
    THEN tug_regn
    ELSE ac_regn
END regn,
time(takeoff) takoff,
time(landed) landed,
coalesce(round((julianday(t0.landed) - julianday(t0.takeoff)) * 1440,0),0) totalmins,
coalesce(t1.seat_count,0) seat_count,
CASE WHEN t0.p2 = t2.fullname THEN 'P2'
    WHEN t1.seat_count = 1 THEN 'P1'
    WHEN t1.seat_count = 2 AND t0.p2 = '' THEN 'P1'
    WHEN t1.seat_count = 2 AND t2.instructor = 1 THEN 'DI' 
    ELSE 'P1'
END crew_capacity
FROM flights t0
LEFT OUTER JOIN aircraft t1 ON t0.ac_regn = t1.regn
LEFT OUTER JOIN pilots t2 ON t2.userid = 3
WHERE t2.fullname = t0.pic OR t2.fullname = t0.p2


SELECT * FROM aircraft

UPDATE pilots SET userid = NULL where id = 40