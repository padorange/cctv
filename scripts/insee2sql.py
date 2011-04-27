#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
	insee2sql.py
	----------------
	Extrait les données du SQLite local et crée un fichier MYSQL Export.
	
	Pierre-Alain Dorange, november 2010
	Code : BSD Licence
	OSM Data : CC-BY-SA 2.0
"""

# standard python modules
import os
import sys	# used to recover exception errors and messages
import codecs # used to read/write text file with the correct encoding
import time, datetime
import math
import sqlite3			# sqlite database (simple local sql database, one user at a time)
import re

# specific modules
import config
import pyOSM
import xlrd			# handle Microsoft Excel (tm) file (XLS), copyright 2005-2006, Stephen John Machin, Lingfo Pty Ltd
					# <http://www.lexicon.net/sjmachin/xlrd.htm>

# constants
__version__="0.2"
text_filename="%sinsee_city.sql" % config.osm_data_folder
sqlDBFileName="%sinsee.sqlite3" % config.osm_data_folder

# objects

class OSMTown(pyOSM.Node):
	"""
		OSMSurveillance : node dedicated to surveillance cctv (man_made=surveillance in OSM)
	"""
	def __init__(self,id=-1,location=(0.0,0.0)):
		pyOSM.Node.__init__(self,id,location)
		self.insee=""
		self.county=""
		self.population=0
		self.nbcam=0
		self.date=""
		self.operator=""
		self.description=""
		
	def show(self):
		print "%s @ (%.2f,%.2f)" % (self.name,self.location[0],self.location[1])
		
	def show(self,short=True):
		if short:
			OSMNode.show(self)
		else:
			print "%s (%d) @ (%.2f,%.2f) : type=%s, operator=%s" % (self.name,self.osm_id,self.location[0],self.location[1],self.type,self.operator)

class OSMNodeList():
	"""
		Handle a Surveillance node list (build)
	"""
	def __init__(self):
		self.list=[]
		
	def getinsee(self,sql,name,departement):
		c=sql.cursor()
		c.execute("""SELECT communes.id,communes.name,departements.name,communes.departement,communes.population,communes.latitude,communes.longitude,communes.osm_id FROM communes,departements,regions WHERE communes.name LIKE "%s" AND communes.departement=departements.id AND communes.region=regions.id;""" % name)
		datas=c.fetchall()
		data=None
		if len(datas)>0:
			if len(datas)==1:
				data=datas[0]
			else:
				for d in datas:
					if departement==d[3]:
						data=d
						break
				if data==None:
					print "> more than one results",len(datas)
		if data:
			node=OSMNode()
			node.name=data[0]
			node.population=data[1]
			node.dep_id=data[2]
			node.dep_name=data[3]
			node.reg_name=data[4]
			node.insee=data[5]
			node.location=(data[6],data[7])
		else:
			node=None
			
		c.close()
		
		return node
		
	def parse_xls(self,fname):
		"""
			analyse du fichier "manhack.xls"
		"""
		if not os.path.isfile(sqlDBFileName):
			print "no database [%s], run extract_insee.py before" % sqlDBFileName
		else:
			sql=sqlite3.connect(sqlDBFileName)
			try:
				err=0
				book=xlrd.open_workbook(fname)
				try:
					sheet=book.sheet_by_index(0)
					rowx=1
					while 1:
						try:
							# extract raw data from XLS cells and format them
							values=sheet.row_values(rowx,0,11)
							city=values[0].strip(" ")
							if len(city)>0:
								departement=values[1].strip(" ")
								data=self.getinsee(sql,city,departement)
								if data==None:
									print rowx,city
									print "\tNo Match for INSEE '%s' (%s)" % (city,departement)
								if type(values[2])==float:	# nb camera can be float, int or string
									nb_cam=int(values[2])
								elif type(values[2])==int:
									nb_cam=values[2]
								else:
									nb_cam=0
								if type(values[3])==int:
									cam_comment="%d" % values[3]
								elif type(values[3])==float:
									cam_comment="%.0f" % values[3]
								else:
									cam_comment=values[3]
								#print "\tnbcam: %d" % nb_cam
								if type(values[4])==float:	# latitude can be float or string (using . instead of ,)
									price=u"%.0f €" % values[4]
								else:
									price=values[4]
								#print "\tprice:",price
								if type(values[5])==float:	# latitude can be float or string (using . instead of ,)
									lat=values[5]
								else:
									try:
										lat=float(values[5].replace(",","."))
									except:
										lat=0.0
								if type(values[6])==float:	# longitude can be float or string (using . instead of ,)
									lon=values[6]
								else:
									try:
										lon=float(values[6].replace(",","."))
									except:
										lon=0.0
								src_name=values[7]
								src_link=values[8]
								#print "\tsource:",src_name,src_link
								if data:
									#print "\tlocation:",lat,lon
									node=OSMTown()	# create the node object with data
									node.insee=data.insee
									node.name=data.name
									node.county="%s (%s)" % (data.dep_name,data.dep_id)
									node.location=(lat,lon)
									d=calculate_distance(node.location[0],node.location[1],data.location[0],data.location[1])
									#print "> distance : %.3f" % d
									node.nbcam=nb_cam
									node.description=""
									prefix=""
									if len(cam_comment)>0:
										if nb_cam==0:
											node.description=node.description+prefix+u"Caméra(s) : %s" % cam_comment
										else:
											node.description=node.description+prefix+u"Caméra(s) : %d (%s)" % (nb_cam,cam_comment)
									else:
										if nb_cam==0:
											node.description=node.description+prefix+u"Caméra(s) : nombre inconnu"
										else:
											node.description=node.description+prefix+u"Caméra(s) : %d" % nb_cam
									prefix="</br>"							
									if len(price)>0:
										node.description=node.description+prefix+u"Coût : "+price
										prefix="</br>"
									if len(src_name)>0:
										if len(src_link)>0:
											source="<a href='%s'>%s</>" % (src_name,src_link)
										else:
											source=src_name
										node.description=node.description+prefix+"Source : "+source
										prefix="</br>"
																				
									self.list.append(node)	# add object to the list
								else:
									err=err+1
							else:
								break
						except IndexError:
							print "IndexError",rowx
							pass
						except:
							print "error parsing XLS line",rowx,sys.exc_info()
							err=err+1
						rowx=rowx+1
				except IndexError:
					pass
			except:
				print "error parsing XLS",sys.exc_info()
			
			print "Match INSEE error :",err
			sql.close()
			
		return len(self.list)
			
# functions

def calculate_distance(lat1, lon1, lat2, lon2):
	'''
	* Calculates the distance between two points given their (lat, lon) co-ordinates.
	* It uses the Spherical Law Of Cosines (http://en.wikipedia.org/wiki/Spherical_law_of_cosines):
	*
	* cos(c) = cos(a) * cos(b) + sin(a) * sin(b) * cos(C)                        (1)
	*
	* In this case:
	* a = lat1 in radians, b = lat2 in radians, C = (lon2 - lon1) in radians
	* and because the latitude range is  [-π/2, π/2] instead of [0, π]
	* and the longitude range is [-π, π] instead of [0, 2π]
	* (1) transforms into:
	*
	* x = cos(c) = sin(a) * sin(b) + cos(a) * cos(b) * cos(C)
	*
	* Finally the distance is arccos(x)
	'''

	if ((lat1 == lat2) and (lon1 == lon2)):
		return 0

	try:
		delta = lon2 - lon1
		a = math.radians(lat1)
		b = math.radians(lat2)
		c = math.radians(delta)
		x = math.sin(a) * math.sin(b) + math.cos(a) * math.cos(b) * math.cos(c)
		distance = math.acos(x) # in radians
		distance = distance * 6530 # km
		return distance
	except:
		return 0
			
def Convert2SQL(in_fname,out_fname):
	"""
		Create a list from the XLS file and create a SQL formatted text file
	"""
	# extract data from XLS file
	print "Parsing the SQLite file",in_fname

	print "Generate SQL export file %s" % out_fname
	
	# create the text layers formatted file
	file=codecs.open(out_fname,"w",encoding="utf-8")
	file.write("-- insee2sql.py (%s) SQL dump\n\n"% __version__)
	file.write("""DROP TABLE IF EXISTS `city`;
				  CREATE TABLE IF NOT EXISTS `city` (
					`insee` varchar(8) collate utf8_bin NOT NULL default '',
					`name` text collate utf8_bin NOT NULL,
					`county` varchar(50) collate utf8_bin NOT NULL default '',
					`population` int(11) NOT NULL default '0',
					`longitude` float NOT NULL default '0',
					`latitude` float NOT NULL default '0',
					`osmid` bigint(20) NOT NULL default '0',
					`osmtype` varchar(10) collate utf8_bin NOT NULL default '',
					PRIMARY KEY  (`insee`)
					) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_bin;""")
	file.write("\n\n")
	file.write("\n-- Contenu TABLE city\n\n")

	file.write("INSERT INTO `city` (`insee`, `name`, `county`, `population`, `latitude`, `longitude`, `osmid`, `osmtype`) VALUES")
	prefix="\n"

	sql=sqlite3.connect(sqlDBFileName)
	c=sql.cursor()
	c.execute("""SELECT communes.id,communes.name,departements.name,communes.departement,communes.population,communes.latitude,communes.longitude,communes.osm_id,communes.osm_type FROM communes,departements,regions WHERE communes.departement=departements.id AND communes.region=regions.id AND communes.osm_id IS NOT NULL;""")

	for data in c.fetchall():	# generate the SQL export for city
		county=""
		population=0
		type=""
		file.write('%s("%s","%s","%s (%s)",%s,%s,%s,%s)' % (prefix,data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7]))
		prefix=",\n"
	file.write(";\n")
	
	file.close()
	c.close()
	sql.close()
			
def main(args):
	print "-------------------------------------------------"
	print "extract surveillance data from",sqlDBFileName
	Convert2SQL(sqlDBFileName,text_filename)
	print "-------------------------------------------------"
		
if __name__ == '__main__' :
    main(sys.argv[1:])
