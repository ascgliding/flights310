.open ../instance/asc.sqlite
.changes off

.print 'Altering Tables'
alter table pilots add accts_cust_code varchar;
alter table flights add accts_export_date date;
--alter table flights add pic_gnz_no int;
--alter table flights add p2_gnz_no int;
alter table flights add payer varchar;
alter table aircraft add accts_income_acct varchar;
alter table aircraft add accts_income_tow varchar;


.print Adding known customers
.print ----------------------
.changes off
update pilots set accts_cust_code = '000015' where gnz_no = 2399; -- ian
update pilots set accts_cust_code = '000102' where gnz_no = 6018; -- gus
update pilots set accts_cust_code = '000097' where gnz_no = 5955; -- emelio
update pilots set accts_cust_code = '000013' where gnz_no = 5381; -- fletc
update pilots set accts_cust_code = '000110' where gnz_no = 6040; -- de ridder
update pilots set accts_cust_code = '000111' where gnz_no = 6037; -- kaemon
update pilots set accts_cust_code = '000114' where gnz_no = 6061; -- jacob
update pilots set accts_cust_code = '000090' where gnz_no = 5906; -- Rebekah
update pilots set accts_cust_code = '000118' where gnz_no = 6076; -- Theo
update pilots set accts_cust_code = '000016' where gnz_no = 4183; -- Thomas
update pilots set accts_cust_code = '000128' where gnz_no = 6148; -- kyle
update pilots set accts_cust_code = '000131' where gnz_no = 6175; -- Ben
update pilots set accts_cust_code = '000134' where gnz_no = 6205; -- Sidd
update pilots set accts_cust_code = '000127' where gnz_no = 6147; -- David McGowan
update pilots set accts_cust_code = '000104' where gnz_no = 6001;
update pilots set accts_cust_code = '000071' where gnz_no = 4188;
update pilots set accts_cust_code = '000099' where gnz_no = 10;
update pilots set accts_cust_code = '000109' where gnz_no = 6021;
update pilots set accts_cust_code = '000105' where gnz_no = 6000;
update pilots set accts_cust_code = '000058' where gnz_no = 5639;
update pilots set accts_cust_code = '000094' where gnz_no = 5919;
update pilots set accts_cust_code = '000074' where gnz_no = 5806;
update pilots set accts_cust_code = '000007' where gnz_no = 969;
update pilots set accts_cust_code = '000037' where gnz_no = 3672;
update pilots set accts_cust_code = '000113' where gnz_no = 6056;
update pilots set accts_cust_code = '000005' where gnz_no = 1088;
update pilots set accts_cust_code = '000097' where gnz_no = 5955;
update pilots set accts_cust_code = '000013' where gnz_no = 5381;
update pilots set accts_cust_code = '000061' where gnz_no = 5633;
update pilots set accts_cust_code = '000011' where gnz_no = 3901;
update pilots set accts_cust_code = '000102' where gnz_no = 6018;
update pilots set accts_cust_code = '000015' where gnz_no = 2399;
update pilots set accts_cust_code = '000110' where gnz_no = 6040;
update pilots set accts_cust_code = '000043' where gnz_no = 5466;
update pilots set accts_cust_code = '000028' where gnz_no = 3948;
update pilots set accts_cust_code = '000114' where gnz_no = 6061;
update pilots set accts_cust_code = '000100' where gnz_no = 6005;
update pilots set accts_cust_code = '000019' where gnz_no = 4821;
update pilots set accts_cust_code = '000057' where gnz_no = 5641;
update pilots set accts_cust_code = '000117' where gnz_no = 6070;
update pilots set accts_cust_code = '000111' where gnz_no = 6037;
update pilots set accts_cust_code = '000067' where gnz_no = 5708;
update pilots set accts_cust_code = '000003' where gnz_no = 5077;
update pilots set accts_cust_code = '000002' where gnz_no = 4574;
update pilots set accts_cust_code = '000001' where gnz_no = 3610;
update pilots set accts_cust_code = '000048' where gnz_no = 5506;
update pilots set accts_cust_code = '000101' where gnz_no = 6004;
update pilots set accts_cust_code = '000023' where gnz_no = 998;
update pilots set accts_cust_code = '000087' where gnz_no = 5867;
update pilots set accts_cust_code = '000116' where gnz_no = 6071;
update pilots set accts_cust_code = '000024' where gnz_no = 1174;
update pilots set accts_cust_code = '000041' where gnz_no = 5477;
update pilots set accts_cust_code = '000006' where gnz_no = 1940;
update pilots set accts_cust_code = '000090' where gnz_no = 5906;
update pilots set accts_cust_code = '000027' where gnz_no = 4413;
update pilots set accts_cust_code = '000010' where gnz_no = 5440;
update pilots set accts_cust_code = '000054' where gnz_no = 5541;
update pilots set accts_cust_code = '000008' where gnz_no = 4669;
update pilots set accts_cust_code = '000026' where gnz_no = 1655;
update pilots set accts_cust_code = '000107' where gnz_no = 6002;
update pilots set accts_cust_code = '000118' where gnz_no = 6076;
update pilots set accts_cust_code = '000016' where gnz_no = 4183;
update pilots set accts_cust_code = '000045' where gnz_no = 5017;
update pilots set accts_cust_code = '000020' where gnz_no = 5101;
update pilots set accts_cust_code = '000119' where gnz_no = 4972;
update pilots set accts_cust_code = '000052' where gnz_no = 5509;
update pilots set accts_cust_code = '000086' where gnz_no = 5840;
update pilots set accts_cust_code = '000004' where gnz_no = 5214;
update pilots set accts_cust_code = '000106' where gnz_no = 5901;
update pilots set accts_cust_code = '000049' where gnz_no = 5520;
update pilots set accts_cust_code = '000032' where gnz_no = 4931;
update pilots set accts_cust_code = '000127' where gnz_no = 6147;
update pilots set accts_cust_code = '000014' where gnz_no = 5393;
update pilots set accts_cust_code = '000126' where gnz_no = 6149;
update pilots set accts_cust_code = '000018' where gnz_no = 4775;
update pilots set accts_cust_code = '000093' where gnz_no = 122;
update pilots set accts_cust_code = '000021' where gnz_no = 3903;
update pilots set accts_cust_code = '000046' where gnz_no = 165;
update pilots set accts_cust_code = '000115' where gnz_no = 6078;
update pilots set accts_cust_code = '000098' where gnz_no = 5962;
update pilots set accts_cust_code = '000075' where gnz_no = 5805;
update pilots set accts_cust_code = '000085' where gnz_no = 5866;
update pilots set accts_cust_code = '000056' where gnz_no = 5618;
update pilots set accts_cust_code = '000121' where gnz_no = 6099;
update pilots set accts_cust_code = '000120' where gnz_no = 6086;
update pilots set accts_cust_code = '000128' where gnz_no = 6148;
update pilots set accts_cust_code = '000042' where gnz_no = 3599;
update pilots set accts_cust_code = '000131' where gnz_no = 6175;
update pilots set accts_cust_code = '000076' where gnz_no = 5814;
update pilots set accts_cust_code = '000084' where gnz_no = 5113;
update pilots set accts_cust_code = '000080' where gnz_no = 5504;
update pilots set accts_cust_code = '000030' where gnz_no = 5044;
update pilots set accts_cust_code = '000031' where gnz_no = 4805;
update pilots set accts_cust_code = '000079' where gnz_no = 5828;
update pilots set accts_cust_code = '000055' where gnz_no = 5581;
update pilots set accts_cust_code = '000095' where gnz_no = 5922;
update pilots set accts_cust_code = '000129' where gnz_no = 6178;
update pilots set accts_cust_code = '000012' where gnz_no = 2730;
update pilots set accts_cust_code = '000022' where gnz_no = 5039;
update pilots set accts_cust_code = '000124' where gnz_no = 6139;
update pilots set accts_cust_code = '000134' where gnz_no = 6205;

.echo off
.print Missed pilots
.print --------------

select fullname,gnz_no,accts_cust_code from pilots where accts_cust_code is null;

.print Setting other customer in slots
.print -------------------------------

insert into slots(slot_type,slot_key,slot_data) values ('DEFAULT','OTHERCUSTOMER','000035');

.print Updating Aircraft with income acct
.print ----------------------------------

update aircraft set accts_income_acct = 'Income:Flying Income:RDW Income:RDW Private Hire' where regn = 'RDW';
update aircraft set accts_income_tow = 'Income:Flying Income:RDW Income:RDW Aerotows' where regn = 'RDW';
update aircraft set accts_income_acct = 'Income:Flying Income:GMP Hire' where regn = 'GMP';
update aircraft set accts_income_acct = 'Income:Flying Income:GVF Hire' where regn = 'GVF';
update aircraft set accts_income_acct = 'Income:Flying Income:GNF Hire' where regn = 'GNF';
--UPDATE flights SET tow_charge = 0 WHERE p2 LIKE 'Trial Fl%'

.print Update Payers
.print -------------

-- tug only
update flights set payer = pic
    where payer is null and flights.ac_regn = 'TUG ONLY';
-- single seater
update flights set payer = pic
    where payer is null and (p2 is null or p2 = '');
-- p2 is on flight but not a pilot (pax) pic pays
update flights set payer = pic
    where payer is null and not exists(select * from pilots where pilots.fullname = flights.p2);
--  # p2 exists but pic is not an instructor - pic pays
update flights set payer = pic
    where payer is null and (select instructor from pilots where pilots.fullname = flights.p2) = 0;
-- remaingin must be instuctional
update flights set payer = p2
    where payer is null;




--.print Update gnz nos in flights table
--.print -------------------------------
--
--UPDATE flights
--    SET pic_gnz_no = (SELECT gnz_no FROM pilots WHERE pilots.fullname = flights.pic)
--    WHERE exists(SELECT gnz_no FROM pilots WHERE pilots.fullname = flights.pic AND pilots.gnz_no IS NOT null);
--
--UPDATE flights
--    SET p2_gnz_no = (SELECT gnz_no FROM pilots WHERE pilots.fullname = flights.p2)
--    WHERE exists(SELECT gnz_no FROM pilots WHERE pilots.fullname = flights.p2 AND pilots.gnz_no IS NOT null);

