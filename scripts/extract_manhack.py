#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
	extract-manhack.py
	----------------
	Extrait les données du tableur ManHack remanié des caméras et produit un fichier SQL à importer.
	Utilise XLRD pour lire le tableur excel.
	
	Pierre-Alain Dorange, november 2010
	Code : BSD Licence
	OSM Data : CC-BY-SA 2.0
"""

# standard python modules
import os
import sys	# used to recover exception errors and messages
import urllib2	# used to download OSM data through XAPI interface
from xml.dom import minidom # used to parse XML data
import webbrowser # used to open the user browser
import codecs # used to read/write text file with the correct encoding
import time, datetime
import math
import sqlite3			# sqlite database (simple local sql database, one user at a time)
import re

# specific modules
import pyOSM

# External Python Modules (require installation)
import xlrd				# handle Microsoft Excel (tm) file (XLS), copyright 2005-2006, Stephen John Machin, Lingfo Pty Ltd
						# <http://www.lexicon.net/sjmachin/xlrd.htm>

# constants
__version__="0.4"
xls_filename="./data/manhack.xls"	# remise en forme
text_filename="./data/cctv_manhack.sql"
sqlDBFileName="./data/insee2007.sqlite3"

# objects
class OSMNode():
	"""
		OSMNode : basic node handle id, location and name
			location is (latitude,longitude)
	"""
	def __init__(self,id=-1,location=(0.0,0.0)):
		self.osm_id=id
		self.location=location
		self.name="(no-name)"
		
	def show(self):
		print "%s @ (%.2f,%.2f)" % (self.name,self.location[0],self.location[1])

	def open_in_osm(self,zoom=12,layer='0B00FTF'):
		webbrowser.open("http://www.openstreetmap.org/?lat=%f&lon=%f&zoom=%d&layers=%s" % (self.location[0],self.location[1],zoom,layer))

class OSMSurveillance(OSMNode):
	"""
		OSMSurveillance : node dedicated to surveillance cctv (man_made=surveillance in OSM)
	"""
	def __init__(self,id=-1,location=(0.0,0.0)):
		OSMNode.__init__(self,id,location)
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
		c.execute("""SELECT communes.name,communes.population,communes.departement,departements.name,regions.name,communes.id,communes.latitude,communes.longitude FROM communes,departements,regions WHERE communes.name LIKE "%s" AND communes.departement=departements.id AND communes.region=regions.id;""" % name)
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
			print "no database, run parse_insee.py before"
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
								src_name1=values[7]
								src_link1=values[8]
								src_name2=values[9]
								src_link2=values[10]
								#print "\tsource:",src_name,src_link
								if data:
									#print "\tlocation:",lat,lon
									node=OSMSurveillance()	# create the node object with data
									node.insee=data.insee
									node.name=data.name
									node.county="%s (%s)" % (data.dep_name,data.dep_id)
									node.location=(lat,lon)
									d=calculate_distance(node.location[0],node.location[1],data.location[0],data.location[1])
									#print "> distance : %.3f" % d
									node.nbcam=nb_cam
									node.description=cam_comment
									if len(cam_comment)==0:
										prefix=""
									else:
										prefix="</br>"							
									if len(price)>0:
										node.description=node.description+prefix+u"Coût : "+price
										prefix="</br>"
									node.src1=src_link1
									node.src2=src_link2
									node.title1=src_name1
									node.title2=src_name2
																				
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
	print "Parsing the XLS file",in_fname
	nodes=OSMNodeList()
	nbTot=nodes.parse_xls(in_fname)
	print "%d founded" % (nbTot)
	print "Generate SQL export file %s" % out_fname
	
	# create the SQL formatted file
	file=codecs.open(out_fname,"w",encoding="utf-8")
	file.write("-- extract_manhack.py (%s) SQL dump \n\n"% __version__)
	file.write("""DROP TABLE `cctv` IF EXISTS;\n\n""")
	file.write("""CREATE TABLE IF NOT EXISTS `cctv` (
					`insee` varchar(8) NOT NULL default '',
					`nb_actual` int(11) NOT NULL default '0',
					`cam_comm` text NOT NULL,
					`source1` text NOT NULL,
					`source2` text NOT NULL,
					`source_title1` text NOT NULL,
					`source_title2` text NOT NULL,
					PRIMARY KEY  (`insee`)
				);\n\n""")
	file.write("\n-- Contenu TABLE city\n\n")
	min=9999
	max=0
	nbcam=0
	for s in nodes.list:	# compute min/max camera per city to handle icon size
		nbcam=nbcam+s.nbcam
		if s.nbcam<min:
			min=s.nbcam
		if s.nbcam>max:
			max=s.nbcam
	print u"\tnombre total de caméras:",nbcam
	
	file.write("INSERT INTO `cctv` (`insee`, `nb_actual`, `cam_comm`, `source_title1`, `source1`, `source_title2`, `source2`) VALUES")
	prefix="\n"
	for s in nodes.list:	# generate the SQL export for city
		county=""
		population=0
		type=""
		file.write('%s("%s","%s","%s","%s","%s","%s","%s")' % (prefix,s.insee,s.nbcam,s.description,s.title1,s.src1,s.title2,s.src2))
		prefix=",\n"
	file.write(";\n")
	
	file.close()
			
def main(args):
	print "-------------------------------------------------"
	print "extract surveillance data from",xls_filename
	Convert2SQL(xls_filename,text_filename)
	print "-------------------------------------------------"
		
if __name__ == '__main__' :
    main(sys.argv[1:])
