
INSERT INTO "sqlite_sequence" VALUES('strategy_group',78);
INSERT INTO "sqlite_sequence" VALUES('strategy_group_yield',8);
INSERT INTO "sqlite_sequence" VALUES('strategy_group_snapshot',27);

CREATE TABLE "strategy_group" (
	"id"	INTEGER,
	"strategy_name"	TEXT,
	"bond_code"	TEXT,
	"bond_name"	INTEGER,
	"price"	REAL,
	"amount"	INTEGER,
	"premium"	REAL,
	"create_date"	DATE,
	"modify_date"	DATE,
	"before_percent"	REAL,
	"after_percent"	REAL,
	"desc"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
INSERT INTO "strategy_group" VALUES(41,'低溢价率策略','128013','洪涛转债',121.7,1640,0.0305,'2021-12-02','2021-12-08',0.0,20.55,NULL);
INSERT INTO "strategy_group" VALUES(42,'低溢价率策略','113591','胜达转债',134.6,1480,0.0329,'2021-12-02','2021-12-08',0.0,19.11,NULL);
INSERT INTO "strategy_group" VALUES(43,'低溢价率策略','128081','海亮转债',138.236,1440,0.0368,'2021-12-02','2021-12-08',0.0,20.7,NULL);
INSERT INTO "strategy_group" VALUES(44,'低溢价率策略','113570','百达转债',147.46,1350,0.0512,'2021-12-02','2021-12-08',0.0,18.99,NULL);
INSERT INTO "strategy_group" VALUES(45,'低溢价率策略','113607','伟20转债',154.54,1290,0.0036,'2021-12-02','2021-12-08',20.0,0.0,'强赎卖出');
INSERT INTO "strategy_group" VALUES(53,'低余额+双低策略','113567','君禾转债',128.47,1550,0.075,'2021-12-08','2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group" VALUES(54,'低余额+双低策略','123062','三超转债',118.699,1680,0.282,'2021-12-08','2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group" VALUES(55,'低余额+双低策略','128039','三力转债',115.0,1730,0.334,'2021-12-08','2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group" VALUES(56,'低余额+双低策略','113561','正裕转债',117.03,1700,0.342,'2021-12-08','2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group" VALUES(57,'低余额+双低策略','128091','新天转债',139.622,1430,0.118,'2021-12-08','2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group" VALUES(58,'低溢价率+双低策略','128013','洪涛转债',117.15,560,0.033,'2021-12-08','2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group" VALUES(59,'低溢价率+双低策略','113591','胜达转债',120.7,550,0.024,'2021-12-08','2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group" VALUES(60,'低溢价率+双低策略','113009','广汽转债',122.53,540,0.013,'2021-12-08','2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group" VALUES(61,'低溢价率+双低策略','127003','海印转债',122.403,540,0.067,'2021-12-08','2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group" VALUES(62,'低溢价率+双低策略','128130','景兴转债',126.665,520,0.071,'2021-12-08','2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group" VALUES(63,'低溢价率+双低策略','113567','君禾转债',128.47,510,0.075,'2021-12-08','2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group" VALUES(64,'低溢价率+双低策略','128081','海亮转债',134.4,490,0.025,'2021-12-08','2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group" VALUES(65,'低溢价率+双低策略','128121','宏川转债',138.0,480,0.069,'2021-12-08','2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group" VALUES(66,'低溢价率+双低策略','128106','华统转债',143.799,460,0.015,'2021-12-08','2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group" VALUES(67,'低溢价率+双低策略','113579','健友转债',139.08,470,0.074,'2021-12-08','2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group" VALUES(68,'低溢价率+双低策略','128145','日丰转债',145.7,450,0.075,'2021-12-08','2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group" VALUES(69,'低溢价率+双低策略','128085','鸿达转债',154.744,430,0.008,'2021-12-08','2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group" VALUES(70,'低溢价率+双低策略','123085','万顺转2',154.35,430,0.049,'2021-12-08','2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group" VALUES(71,'低溢价率+双低策略','128096','奥瑞转债',153.999,430,0.06,'2021-12-08','2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group" VALUES(72,'低溢价率+双低策略','123109','昌红转债',158.165,420,0.046,'2021-12-08','2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group" VALUES(73,'高收益率策略','128062','亚药转债',94.567,2110,2.76,'2021-12-08','2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group" VALUES(74,'高收益率策略','128127','文科转债',98.798,2020,0.351,'2021-12-08','2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group" VALUES(75,'高收益率策略','113596','城地转债',95.26,2090,1.98,'2021-12-08','2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group" VALUES(76,'高收益率策略','128138','侨银转债',110.65,1800,0.934,'2021-12-08','2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group" VALUES(77,'高收益率策略','113569','科达转债',102.55,1950,1.41,'2021-12-08','2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group" VALUES(78,'低溢价率策略','128111','中矿转债',484.0,400,-0.003,'2021-12-08','2021-12-08',0.0,20.0,'建仓');
CREATE TABLE "strategy_group_snapshot" (
	"id"	INTEGER,
	"strategy_name"	TEXT,
	"bond_code"	TEXT,
	"bond_name"	INTEGER,
	"price"	REAL,
	"amount"	INTEGER,
	"premium"	REAL,
	"date"	DATE,
	"before_percent"	REAL,
	"after_percent"	REAL,
	"desc"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
INSERT INTO "strategy_group_snapshot" VALUES(1,'低余额+双低策略','113567','君禾转债',128.47,1550,0.075,'2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(2,'低余额+双低策略','123062','三超转债',118.699,1680,0.282,'2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(3,'低余额+双低策略','128039','三力转债',115.0,1730,0.334,'2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(4,'低余额+双低策略','113561','正裕转债',117.03,1700,0.342,'2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(5,'低余额+双低策略','128091','新天转债',139.622,1430,0.118,'2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(6,'低溢价率+双低策略','128013','洪涛转债',117.15,560,0.033,'2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(7,'低溢价率+双低策略','113591','胜达转债',120.7,550,0.024,'2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(8,'低溢价率+双低策略','113009','广汽转债',122.53,540,0.013,'2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(9,'低溢价率+双低策略','127003','海印转债',122.403,540,0.067,'2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(10,'低溢价率+双低策略','128130','景兴转债',126.665,520,0.071,'2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(11,'低溢价率+双低策略','113567','君禾转债',128.47,510,0.075,'2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(12,'低溢价率+双低策略','128081','海亮转债',134.4,490,0.025,'2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(13,'低溢价率+双低策略','128121','宏川转债',138.0,480,0.069,'2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(14,'低溢价率+双低策略','128106','华统转债',143.799,460,0.015,'2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(15,'低溢价率+双低策略','113579','健友转债',139.08,470,0.074,'2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(16,'低溢价率+双低策略','128145','日丰转债',145.7,450,0.075,'2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(17,'低溢价率+双低策略','128085','鸿达转债',154.744,430,0.008,'2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(18,'低溢价率+双低策略','123085','万顺转2',154.35,430,0.049,'2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(19,'低溢价率+双低策略','128096','奥瑞转债',153.999,430,0.06,'2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(20,'低溢价率+双低策略','123109','昌红转债',158.165,420,0.046,'2021-12-08',0.0,6.67,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(21,'高收益率策略','128062','亚药转债',94.567,2110,2.76,'2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(22,'高收益率策略','128127','文科转债',98.798,2020,0.351,'2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(23,'高收益率策略','113596','城地转债',95.26,2090,1.98,'2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(24,'高收益率策略','128138','侨银转债',110.65,1800,0.934,'2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(25,'高收益率策略','113569','科达转债',102.55,1950,1.41,'2021-12-08',0.0,20.0,'建仓');
INSERT INTO "strategy_group_snapshot" VALUES(26,'低溢价率策略','113607','伟20转债',154.54,1290,0.0036,'2021-12-08',20.0,0.0,'强赎卖出');
INSERT INTO "strategy_group_snapshot" VALUES(27,'低溢价率策略','128111','中矿转债',484.0,400,-0.003,'2021-12-08',0.0,20.0,'建仓');
CREATE TABLE "strategy_group_yield" (
	"id"	INTEGER,
	"date"	DATE,
	"strategy_1"	TEXT,
	"total_money_1"	REAL,
	"remain_money_1"	REAL,
	"day_rate_1"	REAL,
	"all_rate_1"	REAL,
	"period_1"	INTEGER,
	"strategy_2"	TEXT,
	"total_money_2"	REAL,
	"remain_money_2"	REAL,
	"day_rate_2"	REAL,
	"all_rate_2"	REAL,
	"period_2"	INTEGER,
	"strategy_3"	TEXT,
	"total_money_3"	REAL,
	"remain_money_3"	REAL,
	"day_rate_3"	REAL,
	"all_rate_3"	REAL,
	"period_3"	INTEGER,
	"strategy_4"	TEXT,
	"total_money_4"	REAL,
	"remain_money_4"	REAL,
	"day_rate_4"	REAL,
	"all_rate_4"	REAL,
	"period_4"	INTEGER,
	PRIMARY KEY("id" AUTOINCREMENT)
);
INSERT INTO "strategy_group_yield" VALUES(5,'2021-12-02','低溢价率策略',1000000.0,3716.56,0.0,0.0,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "strategy_group_yield" VALUES(8,'2021-12-08','低溢价率策略',1000000.0,3152.16,-6.14,-6.14,2,'高收益率策略',1000000.0,2655.77,0.0,0.0,1,'低余额+双低策略',1000000.0,3896.72,0.0,0.0,1,'低溢价率+双低策略',1000000.0,9626.25,0.0,0.0,1);
