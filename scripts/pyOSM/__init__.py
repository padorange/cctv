#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
	pyosm
	
	Some class and tools to deal with OpenStreetMap
	
	Code source : licence BSD
	copyright november 2010, Pierre-Alain Dorange
"""

# Standard Python Modules
import sys				# system exeption
import os.path			# os specific file paths handler
import urllib2			# url read module
import time, datetime	# date and time handling
import zipfile			# handle zip file
import codecs			# handle string conversion (INSEE text file are iso8859-15 encoded)
import ftplib			# used to connect to ftp and push the new data file
import webbrowser
from xml.etree import ElementTree

__version__="0.2"
_debug_=True
		
def is_in(list,id):
	for w in list:
		if w.osm_id==id:
			return w
	return None

class Node():
	"""
		OSMNode : basic node handle id, location and name
	"""
	def __init__(self,id=-1,location=(0.0,0.0)):
		self.osm_id=id
		self.osm_id_type="node"
		self.location=location
		self.name="(no-name)"
		self.operator=""
		self.tags=[]
		
	def show(self):
		print "%s (#%d) @ (%.2f,%.2f)" % (self.name,self.osm_id,self.location[0],self.location[1])

	def open_in_osm(self,zoom=12,layer='0B00FTF'):
		webbrowser.open("http://www.openstreetmap.org/?lat=%f&lon=%f&zoom=%d&layers=%s" % (self.location[0],self.location[1],zoom,layer))


class Way():
	def __init__(self,id=-1):
		self.osm_id=id
		self.name="(no-name)"
		self.node_list=[]
		
	def show(self):
		print "%s, %d node(s)" % (self.name,len(self.node_list))
	
	def add_node(self,node):
		self.node_list.append(node)
		
	def get_node(self,id):
		for n in self.node_list:
			if n.osm_id==id:
				return n
		return None
	
class Area():
	"""
		Basically : a list of ways
		each way is a list of nodes forming a closed area
		+ a bounding global box to speed the "node is in" test
	"""
	def __init__(self,id=-1):
		self.nodes=[]
		self.ways=[]
		self.osm_id=id
		self.name=""
		self.box=None
		
	def nb_nodes(self):
		return len(self.nodes)
							
	def add_node(self,node,way=None):
		self.nodes.append(node)
		if way:
			way.add_node(node)
		x,y=node.location
		if self.box==None:
			self.box=[x,y,x,y]
		else:
			if x<self.box[0]:
				self.box[0]=x
			if y<self.box[1]:
				self.box[1]=y
			if x>self.box[2]:
				self.box[2]=x
			if y>self.box[3]:
				self.box[3]=y
				
	def add_way(self,way):
		self.ways.append(way)
		
	def add_sorted_ways(self,waylist):
		"""
			waylist if a list of OSMWay, came from OSM data file
			each way if composed of sorted node, but the different ways are not in the correct order
			ordered them.
			Then concatene node lists into a single one and remove dupplicates
		"""
		nb=len(waylist)
		if nb>0:
			index=0
		else:	
			index=-1
		reverse=False
		sorted=[]
		if _debug_:
			log=codecs.open("log_sort.txt","w",encoding="utf-8")
		else:
			log=None
		added=[]
		newArea=None
		while index>=0:	# continue until we reach the end of waylist
			if log:
				log.write("+ index %d : way %d has %d node(s)\n" % (index,waylist[index].osm_id,len(waylist[index].node_list)))
			w=waylist[index]
			if reverse:	# reverse list order if necessary
				if log:
					log.write("\treverse\n")
				w.node_list.reverse()
			if newArea==None:
				if log:
					log.write("\tnew area\n")
				newArea=w
				self.add_way(w)
			if log:
				log.write("\tadd %d node(s)\n" % len(waylist[index].node_list))
			for n in w.node_list:	# append all nodes of the current way
				if not n.osm_id in added:
					self.add_node(n,newArea)
					added.append(n.osm_id)
			if len(w.node_list)>0:
				prev_last=w.node_list[-1]
			else:
				if log:
					log.write("break, current",index,"way has no node\n")
				index=-1
			sorted.append(w)
			
			if len(sorted)<len(waylist):	# find the new way to add
				w=waylist[index]
				if len(w.node_list)>0:
					first0=w.node_list[0]
					last0=w.node_list[-1]
					if log:
						log.write("\tfirst : %d - last : %d\n" % (first0.osm_id,last0.osm_id))
					find=False
					loop=True
					j=0
					while loop and not find:
						if waylist[j] not in sorted and j!=index:
							if len(waylist[j].node_list)>0:
								first=waylist[j].node_list[0]
								last=waylist[j].node_list[-1]
								if log:
									log.write("\tcheck against index %d, way %d (has %d node(s))\n" % (j,waylist[j].osm_id,len(waylist[j].node_list)))
									log.write("\t\tfirst : %d - last : %d\n" % (first.osm_id,last.osm_id))
								if first.osm_id==last0.osm_id:
									find=True
									reverse=False
								if last.osm_id==last0.osm_id:
									find=True
									reverse=True
						if loop and not find:
							j=j+1
							if j>=nb:
								loop=False
								j=-1
					if find:
						index=j
					else:
						if log:
							log.write("break, no matching found\n")
						index=index+1
						if index==len(waylist):
							index=-1
						newArea=None
			else:
				if log:
					log.write("break, all sorted : STOP\n")
				index=-1
		if log:
			log.close()
	
	def save(self,filename="area.xml"):
		if _debug_:
			print "Saving to",filename
		root=ElementTree.Element("osm")
		root.set('version','0.6')
		root.set('generator','pyosm %s' % __version__)
		bounds=ElementTree.SubElement(root,"bounds")
		if self.box:
			bounds.set('minlat','%.5f' % self.box[0])
			bounds.set('maxlat','%.5f' % self.box[2])
			bounds.set('minlon','%.5f' % self.box[1])
			bounds.set('maxlon','%.5f' % self.box[3])
		for n in self.nodes:
			node=ElementTree.SubElement(root,"node")
			node.set('id','%d' % n.osm_id)
			node.set('lat','%.5f' % n.location[0])
			node.set('lon','%.5f' % n.location[1])
			node.set('version','1')
		for w in self.ways:
			way=ElementTree.SubElement(root,"way")
			way.set('id','%d' % w.osm_id)
			way.set('name',w.name)
			way.set('version','1')
			for n in w.node_list:
				node=ElementTree.SubElement(way,"nd")
				node.set('ref','%d' % n.osm_id)
		tree=ElementTree.ElementTree(root)
		tree.write(filename,encoding='utf-8')
	
	def read(self,filename="area.xml"):
		print "read",filename
		self.osm_id=-1
		self.name=""
		self.nodes=[]
		self.ways=[]
		self.box=None
		tree=ElementTree.parse(filename)
		root=tree.getroot()
		g=root.get('generator')
		self.name=root.get('name')
		nodes=root.getiterator('node')
		ways=root.getiterator('way')
		for w in ways:
			way=Way(long(w.get('id')))
			self.add_way(way)
			wn=w.getiterator('nd')
			for n in wn:
				ref=long(n.get('ref'))
				for i in nodes:
					id=long(i.get('id'))
					if ref==id:
						x=float(i.get('lat'))
						y=float(i.get('lon'))
						node=Node(id,(x,y))
						self.add_node(node,way)
						break
		
	def node_in(self,node):
		"""
			Ray Casting Algorythm to check if a point is inside a polygon
			http://en.wikipedia.org/wiki/Point_in_polygon
			
			node must be OSMNode and way OSMWay
		"""
		x,y=node.location	
		inside=False	
		if x>=self.box[0] and y>=self.box[1] and x<=self.box[2] and y<=self.box[3]:
			for w in self.ways:
				inside=False
				n=len(w.node_list)
				if n>1:
					p1x,p1y=w.node_list[0].location
					for i in range(n+1):
						p2x,p2y=w.node_list[i % n].location
						if y>min(p1y,p2y):
							if y<=max(p1y,p2y):
								if x<=max(p1x,p2x):
									if p1y!=p2y:
										xinters=(y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
									if p1x==p2x or x<=xinters:
										inside=not inside
						p1x,p1y=p2x,p2y
				if inside:
					break
					
		return inside
	
def FtpUpload(host,user,password,directory,filename):
	print "Uploading to FTP",filename
	try:
		file=open(filename,"r")
		try:	
			ftp=ftplib.FTP(host)
			ftp.login(user,password)
			ftp.set_pasv(True)
			ftp.storlines("STOR %s/%s" % (directory,filename),file)
			file.close()
			ftp.quit()
		except ftplib.all_errors:
			print "FTP errorcmd :"
			print "\thost:",host
			print "\tuser:",user,password
			print "\tdirectory:",directory
			print "\tfilename:",filename
			print sys.exc_info()
		except:
			print "error during ftp :",sys.exc_info()
	except:
		print "error reading local file %s :" % filename,sys.exc_info()

if __name__ == '__main__' :
    print "pyOSM module",__version__
