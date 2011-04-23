#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
	extract_osm.py
	----------------
	Based on surveillance.py
	Download man_made=surveillance from OSM data (via XAPI) for a bounding box (or not) 
	and create an SQL Export file (used the SQL data file with Import command in PhpMyAdmin)
	
	Usage :
		python surveillance.py [-download]
		- download option force downloading of OSM data (via XAPI) otherwise use (if any) existing local file
	
	OSM's XAPI specification :
		<http://wiki.openstreetmap.org/wiki/Xapi>
	The text file is formatted according to OpenLayers text layer format : 
		<http://dev.openlayers.org/docs/files/OpenLayers/Layer/Text-js.html>	
	
	Pierre-Alain Dorange, december 2010
	Code : BSD Licence
	OSM Data : CC-BY-SA 2.0
	Icons : http://wiki.openstreetmap.org/wiki/Proposed_features/Key:Surveillance
"""

# standard python modules
import os
import sys	# used to recover exception errors and messages
import urllib2	# used to download OSM data through XAPI interface
from xml.dom import minidom # used to parse XML data
import codecs # used to read/write text file with the correct encoding
import time, datetime

# specific modules
import config		# define ftp config to conenct (user, password...)
import pyOSM		# tools to handle XML/OSM data
import xlrd			# handle Microsoft Excel (tm) file (XLS), copyright 2005-2006, Stephen John Machin, Lingfo Pty Ltd
					# <http://www.lexicon.net/sjmachin/xlrd.htm>

# constants
__version__="0.2"
key="man_made"	# the OSM key to made the query
value="surveillance" # the value for the OSM key
xml_filename="./data/cctv.osm"
area_filename="./data/fr_0.xml"
sqlDBFileName="./data/insee.sqlite3"
sql_filename="./data/cctv_osm.sql"

"""
	Note about XAPI
	XAPI is not a very reliable source, default xapi servers often are offline
	beginning 2011, mapquest laucnh its own XAPI server, unfortunnally bounding box are limited to 10 degrees (not enough for France)...
"""
xapi_url="http://www.informationfreeway.org/api/0.6/"
#xapi_url="http://open.mapquestapi.com/xapi/api/0.6/" #openmapquest do not handle large bounding box at the moment
world=False
if world:
	xapi="%s*[%s=%s]"	# url for the XAPI query
	url=xapi % (key,value)
else:
	bbox=(-5.5,42.31,8.3,51.28)	# the bounding box coordinates to get OSM data (France)
	xapi="%s*[%s=%s][bbox=%.2f,%.2f,%.2f,%.2f]"	# url for the XAPI query
	url=xapi % (xapi_url,key,value,bbox[0],bbox[1],bbox[2],bbox[3])

# objects
class OSMSurveillance(pyOSM.Node):
	"""
		OSMSurveillance : node dedicated to surveillance cctv (man_made=surveillance in OSM)
	"""
	def __init__(self,id=-1,location=(0.0,0.0)):
		pyOSM.Node.__init__(self,id,location)
		self.type=type
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
		
	def scan_tags(self,xml,element,area=None):
		tagList=element.getElementsByTagName("tag")
		query=False
		name=""
		operator=""
		type=""
		description=""
		note=""
		web=""
		amenity=""
		for tag in tagList:	# for one node, scan each tags and recover informations
			if tag.hasAttribute("k"):
				k=tag.getAttribute("k")
				if k==key:
					if tag.hasAttribute("v"):
						v=tag.getAttribute("v")
						if v==value:
							query=True
				elif k=="name":
					if tag.hasAttribute("v"):
						name=tag.getAttribute("v")
				elif k=="surveillance":
					if tag.hasAttribute("v"):
						type=tag.getAttribute("v")
						query=True
				elif k=="operator":
					if tag.hasAttribute("v"):
						operator=tag.getAttribute("v")
				elif k=="description":
					if tag.hasAttribute("v"):
						description=tag.getAttribute("v")
				elif k=="note":
					if tag.hasAttribute("v"):
						note=note+tag.getAttribute("v")
				elif k=="note:en":
					if tag.hasAttribute("v"):
						note=note+tag.getAttribute("v")
				elif k=="website" or k=="url":
					if tag.hasAttribute("v"):
						web=tag.getAttribute("v")
				elif k=="amenity":
					if tag.hasAttribute("v"):
						amenity=tag.getAttribute("v")
		if query:	# if it match the query create a surveillance node
			tagName=""
			(lat,lon)=(0.0,0.0)
								
			if element.hasAttribute("id"):
				try:
					id=long(element.getAttribute("id"))
				except:
					id=-1
					print "* error retrieving attribute 'id'"
			if element.tagName=="node":	# if it's a node, easy
				tagName="node"
				if element.hasAttribute("lat"):
					try:
						lat=float(element.getAttribute("lat"))
					except:
						print "* error node #%d : retrieving attribute 'lat'" %id
				if element.hasAttribute("lon"):
					try:
						lon=float(element.getAttribute("lon"))
					except:
						print "* error node #%d : retrieving attribute 'lon'" %id
			if element.tagName=="way":	# for a way : build the node list and compute the center (build there a single node)
				tagName="way"
				nodeList=element.getElementsByTagName("nd")
				nodeWay=[]
				for nd in nodeList:
					if nd.hasAttribute("ref"):
						ref=long(nd.getAttribute("ref"))
						nodeWay.append(ref)
				if len(nodeWay)>0:
					nb=0
					nodes=xml.getElementsByTagName("node")
					for node in nodes:
						if node.hasAttribute("id"):
							ref=long(node.getAttribute("id"))
							if ref in nodeWay:		
								if node.hasAttribute("lat"):
									ll=float(node.getAttribute("lat"))
									if node.hasAttribute("lon"):
										lo=float(node.getAttribute("lon"))
										nb=nb+1
										lat=lat+ll
										lon=lon+lo
					if nb>0:
						lat=lat/nb
						lon=lon/nb
					
			if element.tagName=="relation":	# for a relation scan members, add nodes and scan way to add nodes
				tagName="relation"
				memberList=element.getElementsByTagName("member")
				nodeWay=[]
				wayWay=[]
				for m in memberList:
					if m.hasAttribute("node"):
						ref=long(m.getAttribute("ref"))
						nodeWay.append(ref)
					if m.hasAttribute("way"):
						ref=long(m.getAttribute("ref"))
						wayWay.append(ref)
				if len(wayWay)>0:
					ways=xml.getElementsByTagName("way")
					for way in ways:
						if way.hasAttribute("id"):
							ref=long(node.getAttribute("id"))
							if ref in wayWay:
								nodeList=way.getElementsByTagName("nd")
								for nd in nodeList:
									if nd.hasAttribute("ref"):
										ref=long(nd.getAttribute("ref"))
										nodeWay.append(ref)
				if len(nodeWay)>0:
					nb=0
					nodes=xml.getElementsByTagName("node")
					for node in nodes:
						if node.hasAttribute("id"):
							ref=long(node.getAttribute("id"))
							if ref in nodeWay:		
								if node.hasAttribute("lat"):
									ll=float(node.getAttribute("lat"))
									if node.hasAttribute("lon"):
										lo=float(node.getAttribute("lon"))
										nb=nb+1
										lat=lat+ll
										lon=lon+lo
					if nb>0:
						lat=lat/nb
						lon=lon/nb
			
			# build the surveillance node and store information taken from tags
			surveillance=OSMSurveillance(id,(lat,lon))
			if area:
				is_in=area.node_in(surveillance)
			else:
				is_in=True
			if is_in:
				if len(name)==0:
					name="CCTV"
				if len(description)==0:
					prefix=""
				else:
					prefix="</br>"
				if len(operator)>0:
					description=description+"%soperator: %s" % (prefix,operator)
					prefix="</br>"
				if len(note)>0:
					description=description+"%snote: %s" % (prefix,note)
					prefix="</br>"
				if len(amenity)>0:
					description=description+"%samenity: %s" % (prefix,amenity)
					prefix="</br>"
				if len(web)>0:
					description=description+"%s<a href='%s'>website</a>" % (prefix,web)
					prefix="</br>"
				if len(description)==0:
					description="video surveillance"
				if len(type)>0:
					description=description+"%stype: %s" % (prefix,type)
				
				surveillance.tagName=tagName
				surveillance.name=name
				surveillance.type=type
				surveillance.description=description
				
				self.list.append(surveillance)
				return 1
	
		return 0

	def parse_osm(self,fname,key,value,area=None):
		xmldoc=minidom.parse(fname)
		nb=0

		# parse the node list
		nodes=xmldoc.getElementsByTagName("node")
		print "Scanning",len(nodes),"node(s) for %s=%s" % (key,value)
		for node in nodes:	# scan each node
			nb=nb+self.scan_tags(xmldoc,node,area)
		
		# parse the way list
		ways=xmldoc.getElementsByTagName("way")
		print "Scanning",len(ways),"way(s) for %s=%s" % (key,value)
		for way in ways:	# scan each way
			tags=way.getElementsByTagName("tag")
			nb=nb+self.scan_tags(xmldoc,way,area)
		
		# parse the relation list
		relations=xmldoc.getElementsByTagName("relation")
		print "Scanning",len(relations),"relation(s) for %s=%s" % (key,value)
		for relation in relations:	# scan each way
			tags=relation.getElementsByTagName("tag")
			nb=nb+self.scan_tags(xmldoc,relation,area)
				
		return nb

# functions

def GetData(url,fname):
	print "-------------------------------------------------"
	print "Download to %s from OSM (via xapi)..." % fname
	try:
		stream=urllib2.urlopen(url, None)
		if stream:
			size=stream.info().getheader("Content-Length")
			file=open(fname,"wb")
			data=stream.read()
			bytes=0
			for line in data:
				bytes=bytes+len(line)
				file.write(line)
			stream.close()
			file.close()
	except:
		print "error can't load over internet : ",sys.exc_info()
		
def Convert2SQL(in_fname,out_fname,area=None):
	print "Parsing the XML file for %s=%s" % (key,value)
	nodes=OSMNodeList()
	nbTot=nodes.parse_osm(in_fname,key,value,area)
	print "%d %s(s) founded" % (nbTot,value)
	print "Generate SQL Export file: %s" % out_fname

	file=codecs.open(out_fname,"w",encoding="utf-8")
	file.write("-- extract_osm.py (%s) SQL dump\n\n"% __version__)
	file.write(""""DROP TABLE `osmcctv` IF EXISTS;\n\n""")
	file.write("""CREATE TABLE IF NOT EXISTS `osmcctv` (
					`osmid` bigint(20) NOT NULL default '0',
					`id` varchar(8) collate utf8_bin NOT NULL default '',
					`insee` varchar(8) collate utf8_bin NOT NULL default '',
					`longitude` float NOT NULL default '0',
					`latitude` float NOT NULL default '0',
					`osmtype` varchar(10) collate utf8_bin NOT NULL default '',
					`cctvtype` int(11) NOT NULL default '0',
					`name` varchar(80) collate utf8_bin NOT NULL default '',
					`source` text collate utf8_bin NOT NULL,
					`date` date NOT NULL default '0000-00-00',
					PRIMARY KEY  (`osmid`)
					) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_bin;""")
	file.write("\n\n")
	file.write("\n-- Contenu TABLE city\n\n")

	nbOut=0
	nbIn=0
	nbPub=0
	nbOther=0
	nbNode=0
	nbWay=0
	nbRel=0
	file.write("INSERT INTO `osmcctv` (`osmid`, `longitude`, `latitude`, `name`, `source`) VALUES")
	prefix="\n"
	for s in nodes.list:
		if s.type=="outdoor":
			nbOut=nbOut+1
		elif s.type=="indoor":
			nbIn=nbIn+1
		elif s.type=="public":
			nbPub=nbPub+1
		else:
			nbOther=nbOther+1
		if s.tagName=="node":
			nbNode=nbNode+1
		elif s.tagName=="way":
			nbWay=nbWay+1
		elif s.tagName=="relation":
			nbRel=nbRel+1
		file.write('%s(%d,%.6f,%.6f,"%s","%s")' % (prefix,s.osm_id,s.location[1],s.location[0],s.name,s.description))
		prefix=",\n"
	file.write(";\n")
	file.close()
	print "  Type Statistics (%s) :" % value
	print "  \tOutdoor  : %d" % nbOut
	print "  \tIndoor   : %d" % nbIn
	print "  \tPublic   : %d" % nbPub
	print "  \t(unknow) : %d" % nbOther
	print "  Topologic Statistics (%s) :" % value
	print "  \tNode     : %d" % nbNode
	print "  \tWay      : %d" % nbWay
	print "  \tRelation : %d" % nbRel
			
def main(args):
	download=False
	for arg in args:
		if arg=="-download" : 
			download=True
	if not download:
		if not os.path.exists(xml_filename):
			download=True
	if download:
		GetData(url,xml_filename)

	# get french area to filter nodes in this area
	area=pyOSM.Area()
	area.read(area_filename)		

	Convert2SQL(xml_filename,sql_filename,area)
	
	print "-------------------------------------------------"
		
if __name__ == '__main__' :
    main(sys.argv[1:])
