#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
	parse_admin.py
	--------------
	commande line tool
	Parse XML file (obtain from OpenStreetMap OSM) to extract Administrative boundary and place(s)
	Try to match place(s) with INSEE city (previously extract in local SQLite database)
	
	Parse a OSM'XML local data file, extract administrative boundary and store them in separate file
	
	-h				: affiche la syntaxe (aide)
	-f(filename)	: utilise le fichier de données (filename), formatté en XML OSM
	-a				: extrait les frontières et sauvegarde sur disque (long)
	-l(level)		: extrait seulement le niveau indiqué
							0 = tous
							4 = régions
							6 = départements
							8 = communes
	
	Pierre-Alain Dorange, november 2010
"""

# standard python modules
from xml.etree import ElementTree	# fast xml parser module
import string
import time, datetime
import os.path
import sys,getopt	# handle commande-line arguments
import sqlite3

# external module
import pyOSM
import soundex

__version__="0.4"
sqlDBFileName="./data/insee.sqlite3"
default_level=4
default_file='test.xml'
default_area=False
dep_match=""
area_filename="fr_0.xml"
country_exclude=("italy","schweiz","deutschland","wales","uk","england","spain","belgium","belgique")
  
def ensure_dir(f):
	""" check and create directory if it doesn't exist on local disk """
	d=os.path.dirname(f)
	if not os.path.exists(d):
		os.makedirs(d)
		
def name_compare(x,y):
	""" sort function : by name """
	if x.name>y.name:
		return 1
	elif x.name==y.name:
		return 0
	else:
		return -1
		
def ref_compare(x,y):
	""" sort function : by reference (id) """
	if x.ref>y.ref:
		return 1
	elif x.ref==y.ref:
		return 0
	else:
		return -1
		
def population_compare(x,y):
	""" sort function : by population """
	if x.population>y.population:
		return 1
	elif x.population==y.population:
		return name_compare(x,y)
	else:
		return -1

def departement_compare(x,y):
	""" sort function : by departement """
	if x.departement>y.departement:
		return 1
	elif x.departement==y.departement:
		return name_compare(x,y)
	else:
		return -1

class OSMCity(pyOSM.Node):
	def __init__(self,id=-1,loc=(0.0,0.0)):
		pyOSM.Node.__init__(self,id,loc)
		self.country="(no-country)"
		self.county="(no-county)"
		self.region="(no-region)"
		self.population=0
		self.departement=""	# alphanuméric (corse=2B)
		self.insee=""		# alphanumeric (01110)
		self.cp=""			# alphanumeric (01110)
		self.ref=""
		self.level=8
		self.type="(no-type)"
		
	def show(self,short=True):
		if short:
			pyOSM.Node.show(self)
		else:
			print "%s (#%d) @ (%.2f,%.2f) : pop=%d, dep=%s, country=%s" % (self.name,self.osm_id,self.location[0],self.location[1],self.population,self.departement,self.country)

class OSMRegion(pyOSM.Way):
	def __init__(self,id=-1):
		pyOSM.Way.__init__(self,id)
		self.ref=0
		self.population=0
		self.node=pyOSM.Node()
		self.area=pyOSM.Area()
		self.level=4
		
	def show(self,short=True):
		if short:
			pyOSM.Way.show(self)
		else:
			print u"Région %s" % self.name
			print "(osm#%d) : ref=%d, pop=%d" % (self.osm_id,self.ref,self.population)
			if self.node:
				print "\t@ (%.3f,%.3f, id=%d, name=%s)" % (self.node.location[0],self.node.location[1],self.node.osm_id,self.node.name)
			if self.area:
				print "\tboundary has %d node(s)" % self.area.nb_nodes()

class OSMDepartement(pyOSM.Way):
	def __init__(self,id=-1):
		pyOSM.Way.__init__(self,id)
		self.ref=0
		self.population=0
		self.region=None
		self.node=pyOSM.Node()
		self.area=pyOSM.Area()
		self.level=6
		
	def show(self,short=True):
			print u"Département %s" % self.name,
			print "(osm#%d) : " % self.osm_id,
			print "ref=%d," % self.ref,
			print "pop=%d" % self.population
			if self.node:
				print "\t@ (%.3f,%.3f, id=%d, name=%s)" % (self.node.location[0],self.node.location[1],self.node.osm_id,self.node.name)
			if self.area:
				print "\tboundary has %d node(s)" % self.area.nb_nodes()

class OSMCommune(pyOSM.Way):
	def __init__(self,id=-1):
		pyOSM.Way.__init__(self,id)
		self.ref=0
		self.population=0
		self.region=None
		self.departement=None
		self.node=pyOSM.Node()
		self.area=pyOSM.Area()
		self.level=8
		
	def show(self,short=True):
			print "Commune %s (osm#%d) : ref=%d, pop=%d" % (self.name,self.osm_id,self.ref,self.population)
			if self.node:
				print "\t@ (%.3f,%.3f, id=%d, name=%s)" % (self.node.location[0],self.node.location[1],self.node.osm_id,self.node.name)
			if self.area:
				print "\tboundary has %d node(s)" % self.area.nb_nodes()

class OSMCityList():
	""" list of OSMCity """
	def __init__(self):
		self.list=[]
		
	def sort(self,cmp=ref_compare,r=False):
		self.list.sort(cmp,reverse=r)
		
	def parse_osm(self,fname,area=None):
		""" parse place in OSM data and extract related tag
			tag scheme for place=city|town|village : http://wiki.openstreetmap.org/wiki/Place """
		tree=ElementTree.parse(fname)
		root=tree.getroot()
		nodes=root.getiterator("node")
		print "scanning",len(nodes),"nodes"
		nbCity=0
		nbPlace=0
		for node in nodes:	# scan each nodes
			tags=node.getiterator("tag")
			isCity=False
			inCountry=True
			name=""
			pop=0
			dep=""
			country=""
			type=""
			ref=""
			insee=""
			cp=""
				
			trace=False
			#trace=(id==26691495)
			
			for tag in tags:	# for one node, scan each tags
				k=tag.get("k")
				if k=='place':
					nbPlace=nbPlace+1
					try:
						v=string.lower(tag.get("v"))
						isCity=(v=='city') or (v=='town') or (v=='village')
						type=v
					except:
						print "* error node #%d : retrieving 'place'" % id
				elif (k=='is_in:country') or (k=='is_in'):
					try:
						country=string.lower(tag.get("v"))
						for c in country_exclude:
							if country.find(c)>=0:
								inCountry=False
								break
					except:
						print "* error node #%d : retrieving 'is_in:country'" %id
				elif k=='name':
					name=tag.get("v")
				elif k=='population':
					try:
						pop=int(tag.get("v"))
					except:
						pop=-1
				elif k=='code_departement':
					try:
						dep=tag.get("v")
						inCountry=True
					except:
						dep=""
				elif k=='ref':
					try:
						ref=tag.get("v")
					except:
						ref=""
				elif k=='ref:INSEE':
					try:
						insee=tag.get("v")
						inCountry=True
					except:
						insee=""
				elif k=='postal_code':
					try:
						cp=tag.get("v")
					except:
						cp=""
			if isCity:
				if inCountry:
					if dep_match=="" or (dep_match!="" and (dep==dep_match or insee[0:2]==dep_match)):
						nbCity=nbCity+1
						try:
							id=long(node.get("id"))
						except:
							id=-1
						try:
							lat=float(node.get("lat"))
							lon=float(node.get("lon"))
						except:
							lat=0.0
							lon=0.0
							
						city=OSMCity(id,(lat,lon))
						if area.node_in(city):
							city.name=name
							city.location=(lat,lon)
							city.country=country
							city.population=pop
							city.departement=dep
							city.ref=ref
							city.insee=insee
							city.cp=cp
							city.type=type
							#city.show(False)
							self.list.append(city)
						#else:
							#print "> %s out of area" % name
					#else:
						#print "> %s (%s,%s) don't match %s" % (name,insee,dep,dep_match)
				#else:
					#print "> %s (%s,%s) out of country" % (name,insee,dep)
		return nbPlace

class OSMAdminList():
	"""	Handle administrative areas """
	def __init__(self):
		self.departements=[]
		self.regions=[]
		self.communes=[]
		self.pays=[]
		
	def sort(self,cmp=ref_compare,r=False):
		self.communes.sort(cmp,reverse=r)
		self.departements.sort(cmp,reverse=r)
		self.regions.sort(cmp,reverse=r)
		self.pays.sort(cmp,reverse=r)
		
	def parse_osm(self,fname,target,dname="area",get_area=False,override_area=False):
		tree=ElementTree.parse(fname)
		root=tree.getroot()
		relations=root.getiterator("relation")
		ways=root.getiterator("way")
		nodes=root.getiterator("node")
		print "scanning",len(relations),"relations"
		nbAdmin=0
		for r in relations:	# scan each relation
			isAdmin=False
			inCountry=False
			name=""
			pop=0
			ref=0
			admin_level=0
			country=""
			try:
				id=long(r.get("id"))
			except:
				id=-1
				print "* error retrieving attribute 'id' for admin relation"
			
			for tag in r.getiterator("tag"):	# for one relation, scan each tags
				k=tag.get("k")
						
				if k=='admin_level':
					nbAdmin=nbAdmin+1
					try:
						v=int(tag.get("v"))
						isAdmin=((target<>0) and (v==target)) or ((target==0)and(v==4 or v==6 or v==8))
						admin_level=v
					except:
						print "* error relation #%d : retrieving 'place'" %id
				if k=='name':
					name=tag.get("v")
				if k=='population':
					try:
						pop=int(tag.get("v"))
					except:
						pop=-1
				if k=='ref' or k=='ref:INSEE':
					try:
						ref=int(tag.get("v"))
						inCountry=True
					except:
						ref=-1
			if isAdmin and inCountry:
				t0=time.time()
				print "> %s (%d), admin=%d" % (name,ref,v)
				# create the object to store data
				if admin_level==4:	# region
					o=OSMRegion(id)
					self.regions.append(o)
				if admin_level==6:	# departement
					o=OSMDepartement(id)
					self.departements.append(o)
				if admin_level==8:	# communes
					o=OSMCommune(id)
					self.communes.append(o)
				o.name=name
				o.population=pop
				o.ref=ref
				o.level=admin_level

				# get the admin_centre node or compute the barycentre + store nodes (if get_area==True)
				waysID=[]
				nodesID=[]
				if get_area:
					nodearea=[]
					wayarea=[]
				is_node=-1
				for m in r.getiterator("member"):
					ref=long(m.get("ref"))
					type=m.get("type")
					role=m.get("role")
					if type=="node" and (role=="admin_centre" or role=="admin_center"):	# has an admin_centre
						is_node=ref
					if type=="way":
						waysID.append(ref)
						if get_area:
							wayarea.append(pyOSM.Way(ref))
				if is_node>0:	# store the admin_centre
					o.node.osm_id=is_node
					try:
						o.node.name="not found"
						for n in nodes:
							ref=long(n.get("id"))
							if ref==is_node:
								ll=float(n.get("lat"))
								lo=float(n.get("lon"))
								o.node.location=(ll,lo)
								try:
									for tag in n.getiterator("tag"):
										k=tag.get("k")
										if k=="name":
											o.node.name=tag.get("v")
								except:
									o.node.name="admin_centre has no name"
								break
					except:
						o.node.location=(0.0,0.0)
						print "admin_centre %d for %s has no location" % (is_node,o.name)
				if is_node<0 or get_area: # compute a barycentre and store nodes
					if len(waysID)>0:
						for w in ways:
							wr=long(w.get("id"))
							if get_area:
								wo=pyOSM.is_in(wayarea,wr)
							else:
								wo=None
							if wr in waysID:
								for n in w.getiterator("nd"):
									nr=long(n.get("ref"))
									nodesID.append(nr)
									if wo:
										nodearea.append((wr,nr))
										wo.add_node(pyOSM.Node(nr))
					if len(nodesID):
						nb_nodes=0
						lat,lon=(0.0,0.0)
						for n in nodes:
							ref=long(n.get("id"))
							if ref in nodesID:
								nb_nodes=nb_nodes+1
								ll=float(n.get("lat"))
								lo=float(n.get("lon"))
								if ll and lo:
									lat=lat+ll
									lon=lon+lo
								if get_area:
									for wr,nr in nodearea:
										if nr==ref:
											wo=pyOSM.is_in(wayarea,wr)
											if wo:
												no=wo.get_node(ref)
												if ll==0.0 or lo==0.0:
													print "bad location for node %d in way %d" % (wr,nr)
												no.location=(ll,lo)
											else:
												print "wo %d not found for node %d" % (wr,nr)
						if nb_nodes>0:
							lat=lat/nb_nodes
							lon=lon/nb_nodes
						if get_area:
							o.area.add_sorted_ways(wayarea)
							noloc=[]
							for n in o.area.nodes:
								ll,lo=n.location
								if ll==0.0 or lo==0.0:
									noloc.append(n.osm_id)
							print "\t%d node missing" % len(noloc)
							if len(noloc)>0:
								print "\t",noloc
							o.area.osm_id=o.osm_id
							o.area.name=o.name
							filename=os.path.join(dname,"fr%d_%d_%s.xml" % (o.level,o.ref,o.name))
							ensure_dir(filename)
							if not os.path.exists(filename) or override_area:
								o.area.save(filename)
						o.node.osm_id=is_node
						if is_node<0:
							o.node.name="barycenter"
							o.node.location=(lat,lon)
				t0=time.time()-t0
				o.show(False)
				print "\t>%.1f seconds" % t0
					
		return nbAdmin
	
def usage():
	print
	print "pase_admin.py usage"
	print "\t-h (--help) : aide (syntaxe)"
	print "\t-f (--file) : fichier à analyser (osm standard format)"
	print "\t-l (--level) : admin level a traiter"
	print "\t\t0 = tous"
	print "\t\t4 = régions (region)"
	print "\t\t6 = départements (county)"
	print "\t\t8 = communes (city)"
	print "\t-a (--area) : extrait et sauvegarde les frontières des éléments administratifs"
		
def noaccent_str(str):
	""" remove accent from a string, to made comparaison easier """
	try:
		accent=			u"'-éèêëàùçôöîïâñÉÈÊËÀÚÇÔÖÎÏÂÑ"
		sans_accent=	u"  eeeeaucooiianEEEEAUCOOIIAN"
		i=0
		while i<len(accent):
			str=str.replace(accent[i],sans_accent[i])
			i=i+1
		str=str.replace(' ','')
	except:
		print "error noaccent : ",str,"\n",sys.exc_info()
	return str

def main(argv):
	try:
		opts,args=getopt.getopt(argv,"hf:l:",["help","file=","level="])
	except:
		print "syntaxe incorrecte",sys.exc_info()
		usage()
		sys.exit(2)
	
	file=default_file
	level=default_level
	do_area=default_area
	for opt,arg in opts:
		if opt in ("-h","--help"):
			usage()
			sys.exit()
		elif opt in ("-f","--file"):
			file=arg
		elif opt in ("-a","--area"):
			do_area=True
		elif opt in ("-l","--level"):
			try:
				level=int(arg)
			except:
				print "level doit être un entier"

	print "-------------------------------------------------"
	print "Recherche des villes françaises et frontières dans un fichier OSM/XML..."

	cities=OSMCityList()
	admin=OSMAdminList()

	print "Fichier:",file,"admin_level:",level
	if level==0 or level==8:	# 8 = city
		print "Analyse des villes pour place=city/town/village"
		t0=time.time()
		area=pyOSM.Area()
		area.read(area_filename)		
		nbPlace=cities.parse_osm(file,area)
		t0=time.time()-t0
		print "> parsing cities : %.1f seconds" % t0
		nbCity=len(cities.list)
		cities.sort(ref_compare)
		
		print "comparaison des données OSM de %d ville(s) avec les données INSEE" % nbCity
		t0=time.time()
		dbName=sqlDBFileName
		if not os.path.isfile(dbName):
			print "pas de base de données locale, exécuter parse_insee.py avant"
		else:
			sql=sqlite3.connect(dbName)
		
			errNo=0
			errName=0
			errRef=0
			errDep=0
			errPop=0
			errMany=0
			
			c=sql.cursor()
			for city in cities.list:
				print "--"
				
				# 1/ recherche par code INSEE
				search_by_name=False
				c.execute("SELECT communes.name,communes.population,communes.year,communes.departement,departements.name,regions.name,communes.id,communes.sname FROM communes,departements,regions WHERE communes.id='%s' AND communes.departement=departements.id and communes.region=regions.id;" % city.insee)
				datas=c.fetchall()
				if len(datas)==0:
					print "aucune référence INSEE correspondante",city.insee,city.name,city.ref
					data=None
					search_by_name=True
				elif len(datas)==1:
					# contrôler le nom en enlevant les "-" et en coupant mot par mot
					data=datas[0]
					istr=data[0]
					istr.replace("-"," ")
					iws=istr.split(" ")
					ostr=city.name
					ostr.replace("-"," ")
					ows=ostr.split(" ")
					match=0
					for w in iws:
						if w in ows:
							match=match+1
					if match==0:	# aucun mot en commune, en fait une recherche par nom
						search_by_name=True
						print "le couple ref/nom ne correspond pas (%s,%s) (%s,%s)" % (city.insee,city.name,data[6],data[0])
					elif match<len(iws):
						print u"le nom correspond à %.0f for (%s,%s)" % (100*match/len(iws),city.name,data[0])
				else:
					print len(datas)," référence(s) INSEE pour",city.insee
					errMany=errMany+1
					data=None
				if data==None and search_by_name:
					# 2/ Recherche par nom nécessaire (code erroné ou nom erronné)
					print "\trecherche par nom"
					n=city.name.replace("'","''")
					c.execute("SELECT communes.name,communes.population,communes.year,communes.departement,departements.name,regions.name,communes.id,communes.sname FROM communes,departements,regions WHERE communes.name='%s' AND communes.departement=departements.id AND communes.region=regions.id;" % n)
					datas=c.fetchall()
					if len(datas)==1:
						data=datas[0]
					if data==None:
						# 3/ Recherche par soundex sur le nom
						print "\trecherche par LIKE"
						c.execute("SELECT communes.name,communes.population,communes.year,communes.departement,departements.name,regions.name,communes.id,communes.sname FROM communes,departements,regions WHERE communes.name LIKE '%s' AND communes.departement=departements.id AND communes.region=regions.id;" % n)
						datas=c.fetchall()
						if len(datas)==1:
							data=datas[0]
						elif len(datas)==0:
							data=None
						else:
							errMany=errMany+1
							print len(datas),"résultat(s) pour",city.name
							data=None
				
				if data==None:
					errNo=errNo+1
					print "\taucun (ou trop) résultat dans la base INSEE"
				else:
					if city.name!=data[0]:
						errName=errName+1
						displayName=True
					else:
						displayName=False
					if city.insee!=data[6]:
						errRef=errRef+1
						displayRef=True
					else:
						displayRef=False
					if city.population!=int(data[1]):
						errPop=errPop+1
					if city.departement!=data[3]:
						errDep=errDep+1
						displayDep=True
					else:
						displayDep=False
					if displayName or displayRef or displayDep:
						if displayName:
							print "nom\t%s (%s)\t%s" % (city.name,data[6],data[0])
						else:
							print "nom\t%s (%s)" % (city.name,data[6])
					if displayRef:	
						print "insee\t'%s'\t'%s'" % (city.insee,data[6])
					if displayDep:
						print "dep\t%s (%s)\t%s (%s)" % (city.county,city.departement,data[4],data[3])
					c.execute('''UPDATE communes SET longitude=%.8f, latitude=%.8f, osm_id=%d, osm_type="%s" WHERE id="%s";''' % (city.location[0],city.location[1],city.osm_id,city.osm_id_type,data[6]))
			sql.commit()
			c.close()
			sql.close()

			print "-- erreur(s) --"
			print "Total : %d ville(s) traitée(s)" % len(cities.list)
			print "%d\taucun résultat" % errNo
			print "%d\tnom différent" % errName
			print "%d\tcode INSEE différent" % errRef
			print "%d\tdépartement différent" % errDep
			print "%d\tpopulation différente" % errPop
			print "%d\ttrop de résultats" % errMany

		t0=time.time()-t0
		print "> comparing INSEE : %.1f seconds" % t0

	if do_area:
		print "Parsing for admin_level"
		t0=time.time()
		nbAdmin=admin.parse_osm(file,level,get_area=do_area)
		t0=time.time()-t0
		print "> parsing admin : %.1f seconds" % t0
		admin.sort(ref_compare)
	
		print "-------------------------------------------------"
		print "%d cities" % len(cities.list)
		print "%d city boundaryies (admin_level=8)" % len(admin.communes)
		print "%d county (admin_level=6)" % len(admin.departements)
		print "%d region (admin_level=4)" % len(admin.regions)
		print "%d country (admin_level=2)" % len(admin.pays)
		print "-------------------------------------------------"

if __name__ == '__main__' :
    main(sys.argv[1:])
	
"""
	match dep=16
		16348,16199,16146,16271...
	sql data miss
		16166 L'Isle d'Espagnac
	


	place correction
	according to place sheme : http://wiki.openstreetmap.org/wiki/Place
	
	place=city|town]village (according to population size)
		city (more than 100000)
		town (from 10000 to 100000)
		village (less than 10000)00000000
	name=xxxx
	is_in:country= (pays)
	is_in:county= (département)
	is_in:region= (région)
	population= (population légale)
	ref:INSEE= (code INSEE)
	postal_code= (code postal)
	census:population= (année pour la population)
	source:population= (source pour la population)
	code_departement= (code département)
	wikipedia=
	website=
"""
