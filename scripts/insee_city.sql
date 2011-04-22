-- insee2sql.py (0.2) SQL dump

DROP TABLE `city` IF EXISTS;CREATE TABLE IF NOT EXISTS `city` (
					`insee` varchar(8) character set utf8 NOT NULL default '',
					`name` text character set utf8 NOT NULL,
					`county` varchar(50) character set utf8 NOT NULL default '',
					`population` int(11) NOT NULL default '0',
					`longitude` float NOT NULL default '0',
					`latitude` float NOT NULL default '0',
					`osmid` bigint(20) NOT NULL default '0',
					`osmtype` varchar(10) character set utf8 NOT NULL default '',
					PRIMARY KEY  (`insee`)
					) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_bin;


-- Contenu TABLE city

INSERT INTO `city` (`insee`, `name`, `county`, `population`, `latitude`, `longitude`, `osmid`) VALUES