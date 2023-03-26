.open ../instance/asc.sqlite
.changes off

.print 'Altering Tables'
alter table pilots add accts_cust_code varchar;
alter table flights add accts_export_date date;
alter table flights add pic_gnz_no int;
alter table flights add p2_gnz_no int;
alter table aircraft add accts_income_acct varchar;

.print Creating Temp Table
create temporary table customers(id varchar(20),name varchar(128),addr_email varchar(128),
	firstname varchar(60),surname varchar(60));

.print Adding known customers
insert into customers (id,name,addr_email) values('000059','DAVIS Roman','');
insert into customers (id,name,addr_email) values('000039','TRIAL FLIGHT','');
insert into customers (id,name,addr_email) values('000018','PATTEN Gary','boatbldr@ihug.co.nz');
insert into customers (id,name,addr_email) values('000001','PAGE Lionel','lionelpnz@gmail.com');
insert into customers (id,name,addr_email) values('000075','WILLIAMS Andrew','');
insert into customers (id,name,addr_email) values('000072','HILLS Mark','');
insert into customers (id,name,addr_email) values('000006','BURNS Ray','ray@rayburns.nz');
insert into customers (id,name,addr_email) values('000030','GRAVES Nathan','2mj.graves@gmail.com');
insert into customers (id,name,addr_email) values('000031','GREY David','david.g.grey@gmail.com');
insert into customers (id,name,addr_email) values('000050','GOODWIN Ben','');
insert into customers (id,name,addr_email) values('000007','CARSWELL Rex','rex_carswell@hotmail.com');
insert into customers (id,name,addr_email) values('000022','STRUYCK Rudolf','rstruyck@clear.net.nz');
insert into customers (id,name,addr_email) values('000002','PILLAI Krishna','krispill@hotmail.com');
insert into customers (id,name,addr_email) values('000008','FOREMAN Steve','steve.foreman@me.com');
insert into customers (id,name,addr_email) values('000042','FOXCROFT David','');
insert into customers (id,name,addr_email) values('000025','WAGNER Jamie','jamie.wagner@outlook.co.nz');
insert into customers (id,name,addr_email) values('000026','WALLACE Steve','wallaceclan@orcon.net.nz');
insert into customers (id,name,addr_email) values('000047','ATC 3 SQN','');
insert into customers (id,name,addr_email) values('000049','GRANT Melodyanne','');
insert into customers (id,name,addr_email) values('000017','OWENS Robert','ob.owens@xtra.co.nz');
insert into customers (id,name,addr_email) values('000003','BHASHYAM Kishan','kishanbhashyam@hotmail.com');
insert into customers (id,name,addr_email) values('000058','DICKSON Clare','');
insert into customers (id,name,addr_email) values('000068','Auckland Gliding Club','');
insert into customers (id,name,addr_email) values('000028','WOODFIELD Ivor','ivor.woodfield@gmail.com');
insert into customers (id,name,addr_email) values('000037','TODD David','');
insert into customers (id,name,addr_email) values('000070','ATC 40 Sqdrn','');
insert into customers (id,name,addr_email) values('000013','MCKENZIE Fletcher','fletch@avgas.org');
insert into customers (id,name,addr_email) values('000053','DATH Joseph','');
insert into customers (id,name,addr_email) values('000057','DICKSON Joseph','');
insert into customers (id,name,addr_email) values('000012','MACKAY Andrew','andymacfly2002@yahoo.com');
insert into customers (id,name,addr_email) values('000065','Russel Raphael','');
insert into customers (id,name,addr_email) values('000052','BERNS Michael','');
insert into customers (id,name,addr_email) values('000063','ATC 5 Squadron','');
insert into customers (id,name,addr_email) values('000038','VOUCHER SALE','');
insert into customers (id,name,addr_email) values('000020','PRENTICE Tony','waterbed@ihug.co.nz');
insert into customers (id,name,addr_email) values('000041','BAGCHI Rahul','rahul_bagchi@hotmail.com');
insert into customers (id,name,addr_email) values('000054','HAY Simon','');
insert into customers (id,name,addr_email) values('000067','JASICA Kazik','');
insert into customers (id,name,addr_email) values('000032','HEALEY Genny','genny.healey@gmail.com');
insert into customers (id,name,addr_email) values('000021','ROOK Craig','craig.rook@telecom.co.nz');
insert into customers (id,name,addr_email) values('000034','MAWHINNEY Ben','');
insert into customers (id,name,addr_email) values('000069','RESTALL John','');
insert into customers (id,name,addr_email) values('000004','FOOT Jack','psfoot@xtra.co.nz');
insert into customers (id,name,addr_email) values('000071','FLETCHER Andrew','');
insert into customers (id,name,addr_email) values('000036','PEGASUS TRUST','pegasus.flying@mail.com');
insert into customers (id,name,addr_email) values('000015','OKEEFE Ian','ian.okeefe@xtra.co.nz');
insert into customers (id,name,addr_email) values('000062','ISLAND HOLIDAYS','pete@islandholidays.co.nz');
insert into customers (id,name,addr_email) values('000011','LAKE Graham','gclake@pl.net');
insert into customers (id,name,addr_email) values('000061','LEYLAND Geoff','');
insert into customers (id,name,addr_email) values('000073','BRUNTON Peter','');
insert into customers (id,name,addr_email) values('000060','ARIZA PANDIELLA Brandon','');
insert into customers (id,name,addr_email) values('000033','HODGE Graham','graham.hodge@xtra.co.nz');
insert into customers (id,name,addr_email) values('000043','BURR Isabelle','');
insert into customers (id,name,addr_email) values('000040','AIR TRAINING CORP','');
insert into customers (id,name,addr_email) values('000064','5 Squadron','');
insert into customers (id,name,addr_email) values('000045','THOMPSON Toni','');
insert into customers (id,name,addr_email) values('000035','OTHER CLUB MEMBER','');
insert into customers (id,name,addr_email) values('000009','GESTER Yves','yves.gester@bluewin.ch');
insert into customers (id,name,addr_email) values('000029','FORSTER Robert','');
insert into customers (id,name,addr_email) values('000048','MORAN Matthew','');
insert into customers (id,name,addr_email) values('000055','HAY Thomas','');
insert into customers (id,name,addr_email) values('000005','BELCHER Derry','dbelcher07@gmail.com');
insert into customers (id,name,addr_email) values('000051','Air Scouts','');
insert into customers (id,name,addr_email) values('000023','SWAN Neville','nswan@xtra.co.nz');
insert into customers (id,name,addr_email) values('000014','MOORE Brendan','bjme793@gmail.com');
insert into customers (id,name,addr_email) values('000027','WHITBY Roy','mwhitby@gmail.com');
insert into customers (id,name,addr_email) values('000019','POTE Jonathan','jonathanpote47@gmail.com');
insert into customers (id,name,addr_email) values('000046','SCARBOROUGH Phil','pscarbro@gmail.com');
insert into customers (id,name,addr_email) values('000056','BRIJACEK Vladimir','brico191441@gmail.com');
insert into customers (id,name,addr_email) values('000066','YGNZ','');
insert into customers (id,name,addr_email) values('000010','HEYNIKE Ruan','heynike@hotmail.com');
insert into customers (id,name,addr_email) values('000044','ADAMS Stephen','sladams88@gmail.com');
insert into customers (id,name,addr_email) values('000024','THORPE Peter','pbthorpe@xtra.co.nz');
insert into customers (id,name,addr_email) values('000016','OROURKE Thomas','thomas207@gmail.com');
insert into customers (id,name,addr_email) values('000074','BEST Craig','');
insert into customers (id,name,addr_email) values('000076','GONG Wenbo','');
insert into customers (id,name,addr_email) values('000077','DUNLOP Philip','');
insert into customers (id,name,addr_email) values('000078','JEFFERIES Troy','');
insert into customers (id,name,addr_email) values('000079','HAGON Daisy','');
insert into customers (id,name,addr_email) values('000080','GOW Jonathan','');
insert into customers (id,name,addr_email) values('000081','ATC','');
insert into customers (id,name,addr_email) values('000083','THOMPSON Geoff','');
insert into customers (id,name,addr_email) values('000084','GORDON Tim','');
insert into customers (id,name,addr_email) values('000085','WILTON Allely','');
insert into customers (id,name,addr_email) values('000086','CRUZ Raphael','');
insert into customers (id,name,addr_email) values('000087','FLETCHER Oliver','');
insert into customers (id,name,addr_email) values('000088','PAK Renee','');
insert into customers (id,name,addr_email) values('000089','DUSSAN Ray','');
insert into customers (id,name,addr_email) values('000090','MCMILLAN Rebekah','');
insert into customers (id,name,addr_email) values('000091','PIAKO GLIDING CLUB','');
insert into customers (id,name,addr_email) values('000092','MATAMATA SOARING CENTRE','');
insert into customers (id,name,addr_email) values('000093','READ Roger','');
insert into customers (id,name,addr_email) values('000094','MONAGHAN Connor','');
insert into customers (id,name,addr_email) values('000095','JOHNSON Marc','');
insert into customers (id,name,addr_email) values('000096','ATC 30 Sqdn','');
insert into customers (id,name,addr_email) values('000097','LEAL SCHWENKE Emilio','');
insert into customers (id,name,addr_email) values('000098','TURINSKY Mattias','');
insert into customers (id,name,addr_email) values('000099','DEWAR Bill','');
insert into customers (id,name,addr_email) values('000100','DONALDSON Jeremy','');
insert into customers (id,name,addr_email) values('000101','PEETERS Matthew','');
insert into customers (id,name,addr_email) values('000102','CABRE Gus','');
insert into customers (id,name,addr_email) values('000103','BAKER William','');
insert into customers (id,name,addr_email) values('000104','MICHAEL Alexander','');
insert into customers (id,name,addr_email) values('000105','BOOY Bronson','');
insert into customers (id,name,addr_email) values('000106','GAMMAN Caleb','');
insert into customers (id,name,addr_email) values('000107','NATARAJAN Subramanian','');
insert into customers (id,name,addr_email) values('000108','NZ Soaring Solutions 2018 Limited','modp@inspire.net.nz');
insert into customers (id,name,addr_email) values('000109','PALMA-PACK-BALDRY Brihaspati','');
insert into customers (id,name,addr_email) values('000110','DE RIDDER Immanuel','');
insert into customers (id,name,addr_email) values('000111','AH KUOI-SIMICH Kaemon','');
insert into customers (id,name,addr_email) values('000112','MARRYATT Family','');
insert into customers (id,name,addr_email) values('000113','BREEDT Debrah','');
insert into customers (id,name,addr_email) values('000114','CHURCH Jacob','');
insert into customers (id,name,addr_email) values('000115','SZCZEPANSKI Will','');
insert into customers (id,name,addr_email) values('000116','EICHLER Paul','');
insert into customers (id,name,addr_email) values('000117','BERRY Joshua','');
insert into customers (id,name,addr_email) values('000118','MOUTZOURIS Theo','');
insert into customers (id,name,addr_email) values('000119','TELFORD-SIMMS Jade','');
insert into customers (id,name,addr_email) values('000120','CHAND SHIVNEET','');
insert into customers (id,name,addr_email) values('000121','CHALMERS Logan','');
insert into customers (id,name,addr_email) values('000122','DICKSON Terry','');
insert into customers (id,name,addr_email) values('000123','ATC 6 Squadron','');
insert into customers (id,name,addr_email) values('000124','VYLE Nick','');
insert into customers (id,name,addr_email) values('000125','MILLER Xavier','');
insert into customers (id,name,addr_email) values('000126','NOONE David','');
insert into customers (id,name,addr_email) values('000127','MCGOWAN David','');
insert into customers (id,name,addr_email) values('000128','CLAPPERTON_HAYES Kyle','');
insert into customers (id,name,addr_email) values('000129','KHRIPUNOV Igor','');
insert into customers (id,name,addr_email) values('000130','RAVINA Martin','');
insert into customers (id,name,addr_email) values('000131','GAMBARO Ben','');
insert into customers (id,name,addr_email) values('000132','Hague Alistair','');
insert into customers (id,name,addr_email) values('000133','ATC 19 Squadron','matt.mills@cadetforces.org.nz');
insert into customers (id,name,addr_email) values('000134','SHETH Siddhart','');


.print Fix some of the names
.print ---------------------

update pilots set fullname = 'Steve Wallace'
	where gnz_no = 1655;


-- select * from customers;
.print Changing Name structure

WITH RECURSIVE pcase(id, rest, result) AS (
  SELECT ID,
         Name,
         ''
  FROM customers

  UNION ALL

  SELECT id,
         substr(rest, 2),
         result || CASE WHEN substr(result, -1) GLOB '[A-Za-z]'
                        THEN lower(substr(rest, 1, 1))
                        ELSE upper(substr(rest, 1, 1))
                   END
  FROM pcase
  WHERE rest <> ''
)
--.print updating customers with first and last name
update customers set surname = substr(pcase.result,1,instr(pcase.result,' ') - 1) ,
	firstname = substr(pcase.result,instr(pcase.result,' ') + 1) 
	   from pcase where pcase.id = customers.id;


--SELECT id,
 --      substr(result,1,instr(result,' ') - 1) as first_name,
  --     substr(result,instr(result,' ') + 1) as last_name
--FROM pcase
--WHERE rest = '';

.print Names in customers table
.print ------------------------
select id, firstname || ' ' || surname from customers;
.print Matched pilot records
.print ----------------------------------
select name, firstname,surname, fullname, gnz_no
	from customers t0
	left outer join pilots t1 on t1.fullname = t0.firstname || ' ' || t0.surname
	where fullname is not null;

.print GNU customers with no pilot record
.print ----------------------------------
select name, firstname,surname, fullname, gnz_no
	from customers t0
	left outer join pilots t1 on t1.fullname = t0.firstname || ' ' || t0.surname
	where fullname is null;

.print updating pilots
.echo on
.changes on
update pilots 
	set accts_cust_code = customers.id
	from customers 
		where customers.firstname || ' ' || customers.surname = pilots.fullname;

.echo off
.print updating pilots that are not automatic
.print --------------------------------------
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

.echo off
.print Missed pilots
.print --------------

select fullname,gnz_no,accts_cust_code from pilots where accts_cust_code is null;
