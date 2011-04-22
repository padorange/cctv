#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
	soundex.py
	----------
	Convert string into a soundex/phonex value corresponding to french prononciation
	strings can then be easily compared
	
	phonex algo from Frédéric Brouard (31/03/1999)
	http://www-lium.univ-lemans.fr/~carlier/recherche/soundex.html
	Adapted to unicode
	
	usage :
		python soundex.py [string]
		return soundex or phonex string corresponding to the source string
	
	Pierre-Alain Dorange, november 2010, BSD Licence
"""

import sys, string, re

allChar = (string.uppercase + string.lowercase).decode(sys.getfilesystemencoding())
soundExChar=	(u"91239129922455912623919292" * 2)
accent=			u"'-éèêëàùçôöîïâñÉÈÊËÀÚÇÔÖÎÏÂÑ"
sans_accent=	u"  eeeeaucooiianEEEEAUCOOIIAN"
soundEx=		u"  eeeeausooiianEEEEAUSOOIIAN"
		
def clean_str(str,intab,outtab):
	""" remove accent from a string, to made comparaison easier """
	try:
		i=0
		while i<len(intab):
			str=str.replace(intab[i],outtab[i])
			i=i+1
		str=str.replace(' ','')
	except:
		print "error clean_str : ",str,"\n",sys.exc_info()
	return str

def soundex(source,trace=False):
	"convert string to Soundex equivalent"

	# Soundex requirements:
	# source string must be at least 1 character
	if (not source):
		if trace:
			print "no string"
		return "0000"

	# 0. Replace clean string and remove spaces
	source = clean_str(source,accent,soundEx)
	if trace:
		print "cleaned",source

    # and must consist entirely of letters
	if (not source.isalpha()):
		if trace:
			print "no all alpha",source
		return "0000"

	# Soundex algorithm:
	# 1. make first character uppercase
	# 2. translate all other characters to Soundex digits
	digits = source[0].upper() + clean_str(source[1:],allChar,soundExChar)

	# 3. remove consecutive duplicates
	digits2 = digits[0]
	for d in digits[1:]:
		if digits2[-1] != d:
			digits2 += d
        
	# 4. remove all "9"s
	# 5. pad end with "0"s to 4 characters
	str=(digits2.replace('9', '') + '000')[:4]
	if trace:
		print "Soundex:",str
	return str
	
def phonex(chaine,trace=False): 
	chaine = chaine.upper() 
	chaine = chaine.replace("-","")
	chaine = chaine.replace(" ","")
	if trace: print '0:'+chaine,len(chaine)
   
	#1 remplacer les y par des i 
	r = chaine.replace('Y','I') 
	if trace: print '1:'+r ,len(r)
   
	#2 supprimer les h qui ne sont pas précédés de c ou de s ou de p 
	r = re.sub(r'([^P|C|S])H', r'\1', r) 
	if trace: print '2:'+r,len(r)

	#3 remplacement du ph par f 
	r = r.replace(r'PH', r'F') 
	if trace: print '3:'+r ,len(r)
   
	#4 remplacer les groupes de lettres suivantes : 
	r = re.sub(r'G(AI?)','K\1',r) 
	if trace: print '4:'+r ,len(r)
   
	#5 remplacer les occurrences suivantes, si elles sont suivies par une lettre a, e, i, o, ou u : 
	r = re.sub(r'I(AEIOU)','YN\1',r) 
	if trace: print '5:'+r ,len(r)
     
	#6 remplacement de groupes de 3 lettres (sons 'o', 'oua', 'ein') : 
	r = r.replace('EAU','O') 
	r = r.replace('OUA','2') 
	r = r.replace('EIN','4') 
	r = r.replace('AIN','4') 
	r = r.replace('EIM','4') 
	r = r.replace('AIM','4') 
	if trace: print '6:'+r ,len(r)
   
	#7 remplacement du son ‘é’ : 
	print type(r)
	r = r.replace(u'É','Y') 
	r = r.replace(u'È','Y') 
	r = r.replace(u'Ê','Y') 
	r = r.replace(u'é','Y') 
	r = r.replace(u'è','Y') 
	r = r.replace(u'ê','Y') 
	r = r.replace('AI','Y') 
	r = r.replace('EI','Y') 
	r = r.replace('ER','YR') 
	r = r.replace('ESS','YS') 
	r = r.replace('ET','YT') #CP : différence entre la version Delphi et l'algo 
	r = r.replace('EZ','YZ') 
	if trace: print '7:'+r ,len(r)

	#8 remplacer les groupes de 2 lettres suivantes (son ‘an’ et ‘in’), sauf s’il sont suivi par une lettre a, e, i o, u ou un son 1 à 4 :
	r = re.sub(r'AN([^A|E|I|O|U|1|2|3|4])',r'1\1',r) 
	r = re.sub(r'AM([^A|E|I|O|U|1|2|3|4])',r'1\1',r) 
	r = re.sub(r'EN([^A|E|I|O|U|1|2|3|4])',r'1\1',r) 
	r = re.sub(r'EM([^A|E|I|O|U|1|2|3|4])',r'1\1',r) 
	r = re.sub(r'IN([^A|E|I|O|U|1|2|3|4])',r'4\1',r) 
	if trace: print '8:'+r ,len(r)

	#9 remplacer les s par des z s’ils sont suivi et précédés des lettres a, e, i, o,u ou d’un son 1 à 4 
	r = re.sub(r'()S()',r'\1Z\2',r) 
	#CP : ajout du Y à la liste 
	if trace: print '9:'+r ,len(r)
   
	#10 remplacer les groupes de 2 lettres suivants : 
	r = r.replace('OE','E') 
	r = r.replace('EU','E') 
	r = r.replace('AU','O') 
	r = r.replace('OI','2') 
	r = r.replace('OY','2') 
	r = r.replace('OU','3')   
	if trace: print '10:'+r ,len(r)

	#11 remplacer les groupes de lettres suivants 
	r = r.replace('CH','5') 
	r = r.replace('SCH','5') 
	r = r.replace('SH','5') 
	r = r.replace('SS','S') 
	r = r.replace('SC','S') #CP : problème pour PASCAL, mais pas pour PISCINE ? 
	if trace: print '11:'+r ,len(r)

	#12 remplacer le c par un s s’il est suivi d’un e ou d’un i 
	#CP : à mon avis, il faut inverser 11 et 12 et ne pas faire la dernière ligne du 11 
	r = re.sub(r'C()',r'S\1',r) 
	if trace: print '12:'+r ,len(r)
   
	#13 remplacer les lettres ou groupe de lettres suivants : 
	r = r.replace('C','K') 
	r = r.replace('Q','K') 
	r = r.replace('QU','K') 
	r = r.replace('GU','K') 
	r = r.replace('GA','KA') 
	r = r.replace('GO','KO') 
	r = r.replace('GY','KY') 
	if trace: print '13:'+r ,len(r)

	#14 remplacer les lettres suivante : 
	r = r.replace('A','O') 
	r = r.replace('D','T') 
	r = r.replace('P','T') 
	r = r.replace('J','G') 
	r = r.replace('B','F') 
	r = r.replace('V','F') 
	r = r.replace('M','N') 
	if trace: print '14:'+r ,len(r)
  
	#15 Supprimer les lettres dupliquées 
	oldc='#' 
	newr='' 
	for c in r: 
		if oldc != c: 
			newr=newr+c 
		oldc=c 
	r = newr 
	if trace: print '15:'+r ,len(r)

	#16 Supprimer les terminaisons suivantes : t, x 
	r = re.sub(r'(.*)$',r'\1',r) 
	if trace: print '16:'+r ,len(r)

	#17 Affecter à chaque lettres le code numérique correspondant en partant de la dernière lettre 
	num =['1','2','3','4','5','E','F','G','H','I','K','L','N','O','R','S','T','U','W','X','Y','Z'] 
	l = []
	for c in r: 
		try:
			v=num.index(c)
			l.append(v) 
		except:
			print "error '%s' (%d) not in list\n\t%s (%d)" % (c,ord(c),r,len(r))
	if trace: print '17:',l 
   
	#18 Convertissez les codes numériques ainsi obtenu en un nombre de base 22 exprimé en virgule flottante. 
	res=0.0
	i=1 
	for n in l: 
		res = n*22**-i+res 
		i=i+1 
	if trace: print '18:',res 
	
	return res
	
def main(argv):
	if len(argv)>0:
		str=argv[0].decode(sys.getfilesystemencoding())
		#str=argv[0]
	else:
		str=u"Test"
		
	print str,type(str)
	print "-- soundex --"
	s=soundex(str)
	print str,">",s
	print "-- phonex --"
	v=phonex(str)
	print str,">",v

if __name__ == '__main__' :
    main(sys.argv[1:])
