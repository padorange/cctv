#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
	extract_insee.py
	----------------
	Récupère des données depuis le site de l'INSEE (Institut National de la Statistique et des études économiques)
	Pour permettre une vérification d'intégrité des données OpenStreetMap (OSM) pour la France,
	au niveau des communes, départements et régions.
	Les données INSEE sont stockés dans une base de données locale (SQLite3) pour pouvoir être utilisé par d'autres scripts.
	
	INSEE fournit des données COG (Code Officiel Géographique) à télécharger, ainsi que les résultats du recensement
	Adresse de téléchargement COG :
		<http://www.insee.fr/fr/methodes/nomenclatures/cog/telechargement.asp>
	Adresse de téléchargement recencement 2008 (en vigueur au 1er janvier 2011)
		<http://www.insee.fr/fr/ppp/bases-de-donnees/recensement/populations-legales/france-departements.asp?annee=2008>
	Documentation COG
		<http://www.insee.fr/fr/methodes/nomenclatures/cog/documentation.asp>
	Licence des données INSEE (équivalent CC-BY-SA)
		<http://www.insee.fr/fr/publications-et-services/default.asp?page=copyright.htm>
	
	Usage : python extract_insee.py [-download]
		-download : force download data from insee web site, otherwise use local copy (if present)
	
	Code source : licence BSD
	copyright april 2011, Pierre-Alain Dorange
"""

# Standard Python Modules
import sys				# system exeption
import os.path			# os specific file paths handler
import urllib2			# url read module
import time, datetime	# date and time handling
import zipfile			# handle zip file
import codecs			# handle string conversion (INSEE text file are iso8859-15 encoded)
import sqlite3			# sqlite database (simple local sql database, one user at a time)
import time

# External Python Modules (require installation)
import xlrd				# handle Microsoft Excel (tm) file (XLS), copyright 2005-2006, Stephen John Machin, Lingfo Pty Ltd
						# <http://www.lexicon.net/sjmachin/xlrd.htm>
						
# Local module
import insee
import soundex

__version__="0.4"	# updated for 2011 insee data
botName="InseeOsmBot"
botVersion=__version__
baseUrl="http://www.insee.fr"
insee_year=2008
regionUrl="http://www.insee.fr/fr/methodes/nomenclatures/cog/telechargement/2011/txt/reg2011.txt"
deptUrl="http://www.insee.fr/fr/methodes/nomenclatures/cog/telechargement/2011/txt/depts2011.txt"
commUrl="http://www.insee.fr/fr/methodes/nomenclatures/cog/telechargement/2011/txt/comsimp2011.zip"
popUrl="http://www.insee.fr/fr/ppp/bases-de-donnees/recensement/populations-legales/pages2010/xls/ensemble.xls"
sqlDBFileName="./data/insee.sqlite3"

def main(args):
	override=False	# par défaut, ne pas recharger les fichiers locaux (si ils existent)
	for arg in args:
		if arg=="-download" : 
			override=True
			
	print "--------------------------------------------------------------"
	print botName,botVersion
	
	print "Analyse Régions"
	clk=time.time()
	regions=insee.insee_region(regionUrl)
	regions.download(override)
	regions.scan()
	print "> %d region(s), t=%.2f" % (len(regions.data_list),time.time()-clk)
		
	print "Analyse Départements"
	clk=time.time()
	departements=insee.insee_departement(deptUrl)
	departements.download(override)
	departements.scan()
	print "> %d département(s), t=%.2f" % (len(departements.data_list),time.time()-clk)
	
	print "Analyse Communes"
	clk=time.time()
	communes=insee.insee_commune(commUrl)
	communes.download(override)
	communes.scan()
	print "> %d communes, t=%.2f" % (len(communes.data_list),time.time()-clk)
		
	print "Analyse Populations %d" % insee_year
	clk=time.time()
	populations=insee.insee_population(popUrl)
	populations.download(override)
	if override:
		print "> Download %.2f" % (time.time()-clk)
	clk=time.time()
	populations.scan(regions,departements,communes)
	print "> Scan %.2f" % (time.time()-clk)
	
	clk=time.time()
	dbName=sqlDBFileName
	if not os.path.isfile(dbName):
		sql=sqlite3.connect(dbName)
		sql.execute('''CREATE TABLE regions (id INTEGER PRIMARY KEY NOT NULL,name TEXT,sname TEXT,center TEXT,population INTEGER,year INTEGER,osm_node_id INTEGER,latitude REAL,longitude REAL);''')
		sql.execute('''CREATE TABLE departements (id VARCHAR(5) PRIMARY KEY NOT NULL,region INTEGER,name TEXT,sname TEXT,center TEXT,population INTEGER,year INTEGER,osm_node_id INTEGER,latitude REAL,longitude REAL);''')
		sql.execute('''CREATE TABLE communes (id VARCHAR(10) PRIMARY KEY NOT NULL,name TEXT,sname TEXT,departement VARCHAR(5),region INTEGER,population INTEGER,year INTEGER,osm_node_id INTEGER,latitude REAL,longitude REAL);''')
		sql.commit()
		print "create new database"
	else:
		sql=sqlite3.connect(dbName)
		print "open existing database"
	c=sql.cursor()
	nc=0
	nu=0
	
	print "update regions data (%d)" % len(regions.data_list)
	for r in regions.data_list:
		sname=soundex.soundex(r.name)
		c.execute('''SELECT * FROM regions WHERE id=%d;''' % r.region)
		answer=c.fetchone()
		if answer==None:
			t=(r.region,r.name,sname,r.cheflieu,r.population,insee_year)
			c.execute('''INSERT INTO regions (id,name,sname,center,population,year) VALUES (?,?,?,?,?,?);''',t)
			nc=nc+1
		else:
			t=(r.name,sname,r.cheflieu,r.population,insee_year,r.region)
			c.execute('''UPDATE regions SET name=?,sname=?,center=?,population=?,year=? WHERE id=?;''',t)
			nu=nu+1
	sql.commit()

	print "update departements data (%d)" % len(departements.data_list)
	for d in departements.data_list:
		sname=soundex.soundex(d.name)
		c.execute('''SELECT * FROM departements WHERE id="%s";''' % d.dep)
		answer=c.fetchone()
		if answer==None:
			t=(d.dep,d.region,d.name,sname,d.cheflieu,d.population,insee_year)
			c.execute('''INSERT INTO departements (id,region,name,sname,center,population,year) VALUES (?,?,?,?,?,?,?);''',t)
			nc=nc+1
		else:
			t=(d.region,d.name,sname,d.cheflieu,d.population,insee_year,d.dep)
			c.execute('''UPDATE departements SET region=?,name=?,sname=?,center=?,population=?,year=? WHERE id=?;''',t)
			nu=nu+1
	sql.commit()
	
	print "update communes data (%d)" % len(communes.data_list)
	for cc in communes.data_list:
		sname=soundex.soundex(cc.name)
		c.execute('''SELECT * FROM communes WHERE id="%s";''' % cc.insee)
		answer=c.fetchone()
		if answer==None:
			t=(cc.insee,cc.name,sname,cc.dep,cc.reg,cc.population,insee_year)
			try:
				c.execute('''INSERT INTO communes (id,name,sname,departement,region,population,year) VALUES ("%s","%s","%s","%s",%d,%d,%d);''' % t)
			except:
				print "\terror with",cc.insee,cc.nccenr
				print sys.exc_info()
			nc=nc+1
		else:
			t=(cc.name,sname,cc.dep,cc.reg,cc.population,insee_year,cc.insee)
			c.execute('''UPDATE communes SET name="%s",sname="%s",departement="%s",region=%d,population=%d,year=%d WHERE id="%s";''' % t)
			nu=nu+1
	sql.commit()
	
	print "> Database update %.2f" % (time.time()-clk)
	print "database, %d ajout(s) et %d mise à jour" % (nc,nu)
	print
	
	c.close()
	sql.close()
		
	print "--------------------------------------------------------------"

if __name__ == '__main__' :
    main(sys.argv[1:])
