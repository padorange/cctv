#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
	insee.py
	clasess for dealing with INSEE data
	
	INSEE fournit des données COG (Code Officiel Géographique) à télécharger, ainsi que les résultats du recensement
	Adresse de téléchargement COG :
		<http://www.insee.fr/fr/methodes/nomenclatures/cog/telechargement.asp>
	Documentation COG
		<http://www.insee.fr/fr/methodes/nomenclatures/cog/documentation.asp>
	Licence des données INSEE (équivalent CC-BY-SA)
		<http://www.insee.fr/fr/publications-et-services/default.asp?page=copyright.htm>
	
	Code source : licence BSD
	copyright novembre 2010, Pierre-Alain Dorange
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
__version__="0.3"
botName="InseeOsmBot"
botVersion=__version__
temp_folder="./temp/"

"""
	Codage Insee (COG)
	TNCC	: Type d'article à ajouter au nom (ou charnière)
				0 = pas d'article et le nom commence par une consonne (De)
				1 = pas d'article et le nom commence par une voyelle (D')
				2 = article Le (Du)
				3 = article La (De la"
				4 = article Les (Des)
				5 = article L' (de l')
				6 = article Aux (Des)
				7 = article Las (De las)
				8 = article Los (De los)
				Pour les noms de communes l'article est obligatoire, pour les départements/région il ne l'est pas (uniquement charnière)
	NCCENR  : Nom enrichi (minuscules+accents)
	REGION  : code région
	DEP		: code département
	COM		: code commune (ajouter le code département avant)
"""

# articles
insee_article=("","","Le ","La ","Les ","L'","Aux ","Las ","Los ")
	
class Insee_COG():
	""" 
		type de base pour les objets régions, départements et communes
		intègre le type d'article (TNCC), le nom enrichi (NCCENR), le nom complet (reconstruit) et la population
	"""
	def __init__(self):
		self.tncc=0
		self.nccenr=""
		self.name="(not build)"
		self.population=0
	
	def build_name(self):
		self.name=self.nccenr
		
	def get_name(self):
		return self.name
		
class Region(Insee_COG):
	""" 
	Doc INSEE du fichier Régions : 
	<http://www.insee.fr/fr/methodes/default.asp?page=nomenclatures/cog/doc_flregions.htm>
	Champs :	REGION		Code Région
				CHEFLIEU	Code de la commune chef-lieu de région (alphanumérique Corse=2A)
				TNCC		Type de nom en clair (indique l'article a ajouter devant)
				NCC			Libellé (en majuscule)
				NCCENR		Libellé enrichi (accents)
	"""
	def __init__(self):
		Insee_COG.__init__(self)
		self.cheflieu=""
	
	def set(self,list):
		self.region=int(list[0])
		self.cheflieu=list[1]
		self.tncc=int(list[2])
		self.nccenr=list[4].strip('\n').strip('\r')
		self.build_name()
		
	def get_index(self):
		return self.region
		
	def __repr__(self):
		print "Région",self.name,"(%d)" % self.region,"/ chef lieu : %d" % self.cheflieu
	
class Departement(Insee_COG):
	""" 
	Doc INSEE du fichier Département : 
	<http://www.insee.fr/fr/methodes/default.asp?page=nomenclatures/cog/doc_fldepart.htm>
	Champs :	REGION		Code Région
				DEP			Code Département (alphanumérique Corse=2A)
				CHEFLIEU	Code de la commune chef-lieu de région (alphanumérique Corse=2A)
				TNCC		Type de nom en clair (indique l'article a ajouter devant)
				NCC			Libellé (en majuscule)
				NCCENR		Libellé enrichi (accents)
	"""
	def __init__(self):
		Insee_COG.__init__(self)
		self.dep=""
		self.region=0
		self.cheflieu=""
	
	def set(self,list):
		self.region=int(list[0])
		self.dep=list[1]
		self.cheflieu=list[2]
		self.tncc=int(list[3])
		self.nccenr=list[5].strip('\n').strip('\r')
		self.build_name()
		
	def get_index(self):
		return self.dep
		
	def __repr__(self):
		print "Département",self.name,"(%d)" % self.dep,"/ Région",self.region,"/ chef lieu : %d" % self.cheflieu
	
class Commune(Insee_COG):
	""" 
	Doc INSEE du fichier Communes existantes au 1er janvier : 
	<http://www.insee.fr/fr/methodes/default.asp?page=nomenclatures/cog/doc_fcomsimp.htm>
	Champs :	CDC			Découpage de la commune en cantons
				CHEFLIEU	Code de la commune chef-lieu (alphanumérique Corse=2A)
				REG			Code Région
				DEP			Code Département (alphanumérique Corse=2A)
				COM			Code Commune
				AR			Code Arrondissement
				CT			Code Canton
				TNCC		Type de nom en clair (indique l'article a ajouter devant)
				ARTMAJ		Article (en majuscule)
				NCC			Libellé (en majuscule)
				ARTMIN		Article enrichi (accents)
				NCCENR		Libellé enrichi (accents)
	"""
	def __init__(self):
		Insee_COG.__init__(self)
		self.cdc=0
		self.cheflieu=""
		self.reg=0
		self.dep=""
		self.com=0
		self.ar=0
		self.ct=0
		self.insee=""
	
	def set(self,list):
		self.cdc=int(list[0])
		self.cheflieu=list[1]
		self.reg=int(list[2])
		self.dep=list[3]
		self.com=int(list[4])
		self.ar=int(list[5])
		self.ct=int(list[6])
		self.tncc=int(list[7])
		self.nccenr=list[11].strip('\n').strip('\r')
		self.build_name()
		try:
			if int(self.dep)>100:
				self.insee="%s%02d" % (self.dep,self.com)
			else:
				self.insee="%s%03d" % (self.dep,self.com)
		except:
			self.insee="%s%03d" % (self.dep,self.com)

	def get_index(self):
		return self.insee
		
	def __repr__(self):
		print "Commune",self.name,"(%d)" % self.insee,"/ Département",self.dep,"/ Région",self.reg,"/ chef lieu : %d" % self.cheflieu
		
	def show(self,regions,departements):
		print "Code INSEE :",self.get_index()
		print "Commune :",self.get_name()
		print "Population :",self.population
		d=departements.find_by_index(self.dep)
		if d!=None:
			print "\tDépartement :",d.get_name(),d.get_index(),
			if d.cheflieu==self.insee:
				print "Chef-Lieu"
			else:
				print
			print "\tPopulation :",d.population
		else:
			print "pas de département",self.dep
		r=regions.find_by_index(self.reg)
		if r!=None:
			print "\tRégion :",r.get_name(),r.get_index(),
			if r.cheflieu==self.insee:
				print "Chef-Lieu"
			else:
				print
			print "\tPopulation :",r.population
		else:
			print "pas de région",self.reg
	
	def build_name(self):
		try:
			self.name=insee_article[self.tncc]+self.nccenr
		except:
			print "error build_name\n",sys.exc_info()

class Population():
	"""
		Extraction des données population depuis le tableau XLS fournit par l'INSEE.
		<http://www.insee.fr/fr/ppp/bases-de-donnees/recensement/populations-legales/france-departements.asp?annee=2008>
		Données 2008, valable à partir du 1er janvier 2011.
		Le tableau XLS est décomposé en feuilles : Région, Département, Arrondissement, Canton et Communes.
		Chacun comportant les références en codifucation COG et les données (population)
		Les données population sont ainsi extraites et reliés au données COG précédement extraite.
	"""
	def __init__(self):
		self.id=0
		self.name=""
		self.data_class=None
		self.population=0
		
class insee():
	"""
		Structure de base pour traiter les données de l'INSEE
	"""
	def __init__(self,url,folder):
		self.url=url
		self.directory=folder
		self.data_list=[]
		self.data_class=None
		l=self.url.split('/')
		if len(l)>0:
			self.filename=l[-1]
		else:
			self.filename="insee_file"
			
	def find_by_index(self,search):
		"""
			Binary search (sorted list)
		"""
		left=0
		right=len(self.data_list)
		previous_center=-1
		if search<self.data_list[0].get_index():
			return None
		while 1:
			center=(left+right)/2
			candidate=self.data_list[center]
			c_index=candidate.get_index()
			if search==c_index:
				return candidate
			if center==previous_center:
				return None
			if search<c_index:
				right=center
			else:
				left=center
			previous_center=center
		return None
			
	def find_by_name(self,name):
		for item in self.data_list:
			if item.get_name()==name:
				return item
				break
		return None
		
	def download(self,override=False):
		try:
			if len(self.url)==0:
				raise
			fname="%s%s" % (self.directory,self.filename)
			if not(override) and os.path.isfile(fname):
				return
			opener=urllib2.build_opener()	# declare the user-agent
			opener.addheaders = [('User-agent', "%s/%s" % (botName,botVersion))]
			stream=opener.open(self.url)
			if stream:
				print fname
				file=open(fname,"wb")
				for line in stream:
					file.write(line)
				file.close()
				stream.close()
				
		except urllib2.HTTPError, e:
			print "*",self.url
			print "* HTTPError", e.code
		except urllib2.URLError, e:
			print "*",self.url
			print "* URLError", e.reason
		except:
			print "*",self.url
			print "error can't load over internet : ",sys.exc_info()
	
class insee_txt(insee):
	"""
		accesse TEXT formatted INSEE data (iso8859-15)
	"""
	def __init__(self,url,folder):
		insee.__init__(self,url,folder)
		self.data_separator='\t'
			
	def scan(self):
		try:
			# traiter le fichier texte, ligne par ligne
			fname="%s%s" % (self.directory,self.filename)
			file=codecs.open(fname,"r","iso8859-15")
			for line in file :
				data=self.process(line)
				if data!=None:
					self.data_list.append(data)
			# trier par index
			self.data_list.sort(key=lambda item:item.get_index())
		except:
			print "error can't scan txt file",fname,":",sys.exc_info()
	
	def process(self,line):
		try:
			data=self.data_class()
			list=line.split(self.data_separator)
			data.set(list)
			return data
		except:
			return None
	
class insee_zip(insee_txt):
	"""
		access ZIP/TEXT formatted INSEE data (iso8859-15)
	"""
	def __init__(self,url,folder):
		insee_txt.__init__(self,url,folder)
		
	def scan(self):
		try:
			# traiter le fichier zip ligne par ligne (dézipper el premier fichier de l'archive)
			fname="%s%s" % (self.directory,self.filename)
			zfile=zipfile.ZipFile(fname,"r")
			list=zfile.namelist()
			raw_data=zfile.read(list[0])
			raw_list=raw_data.split('\n')
			for line in raw_list :
				data=self.process(line.decode("iso8859-15"))
				if data!=None:
					self.data_list.append(data)
			zfile.close()
			# trier par index
			self.data_list.sort(key=lambda item:item.get_index())
		except:
			print "error can't scan zip file",fname,":",sys.exc_info()
	
class insee_xls(insee):
	"""
		accesse XLS formatted INSEE data
		retrieve population data and store into according list
	"""
	def __init__(self,url,folder):
		insee.__init__(self,url,folder)
		
	def scan(self,regions,departements,communes):
		try:
			fname="%s%s" % (self.directory,self.filename)
			book=xlrd.open_workbook(fname)
			try:
				# traiter le feuillet 0 (régions)
				sheet=book.sheet_by_index(0)
				rowx=8
				while 1:
					values=sheet.row_values(rowx,0,7)
					reg=int(values[0])
					r=regions.find_by_index(reg)
					if r!=None:
						r.population=int(values[6])
					else:
						print "Région",reg,"not found"
					rowx=rowx+1
			except IndexError:
				pass
			try:
				# traiter le feuillet 1 (départements)
				sheet=book.sheet_by_index(1)
				rowx=8
				while 1:
					values=sheet.row_values(rowx,0,9)
					dep=str(values[2])
					d=departements.find_by_index(dep)
					if d!=None:
						d.population=int(values[8])
					else:
						print "Departement",dep,"not found"
					rowx=rowx+1
			except IndexError:
				pass
			try:
				# traiter le feuillet 4 (communes)
				sheet=book.sheet_by_index(4)
				rowx=8
				while 1:
					values=sheet.row_values(rowx,0,10)
					dep=str(values[2])
					if len(dep)>2:
						dep=dep[:2]
					code="%s%03d" % (dep,int(values[5]))

					c=communes.find_by_index(code)
					if c!=None:	# store population according to insee code
						c.population=int(values[9])
					else:	# no insee code found, merge according to name
						names=values[6].split()
						if len(names)>0:
							c=communes.find_by_name(names[0])
						else:
							c=None
						if c!=None:
							c.population=c.population+int(values[9])
						else:
							print "Commune",code,"not found"
					rowx=rowx+1
			except IndexError:
				pass
		except:
			print "error can't scan xls file",fname,":",sys.exc_info()

class insee_region(insee_txt):
	def __init__(self,url,folder):
		insee_txt.__init__(self,url,folder)
		self.data_class=Region

class insee_departement(insee_txt):
	def __init__(self,url,folder):
		insee_txt.__init__(self,url,folder)
		self.data_class=Departement

class insee_commune(insee_zip):
	def __init__(self,url,folder):
		insee_zip.__init__(self,url,folder)
		self.data_class=Commune

class insee_population(insee_xls):
	def __init__(self,url,folder):
		insee_xls.__init__(self,url,folder)
		self.data_class=Population

if __name__ == '__main__' :
    print "insee",__version__,"module"
