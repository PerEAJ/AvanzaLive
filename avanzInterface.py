# -*- coding: utf-8 -*-
import time, os, aktie, cPickle, cookiehant, multiprocessing, depa, getpass, urllib2, decimal, math, sys
from random import randrange, uniform, random, choice
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

def spara_aktielista(aktielista, turn_off = False):
	orderbookId_lista = []
	for aktie in aktielista:
		place = aktie.lista + '/'
		if not os.path.exists(place):
			os.makedirs(place)
		aktie.spara_historik(turn_off)
		if turn_off:
#			spara_objekt(aktie, place + aktie.orderbookId + '.p')
			orderbookId_lista.append(aktie.orderbookId)
	if turn_off:
		spara_objekt(orderbookId_lista, "orderlista.p")
		
def uppdatera_avslut(internlista ,cookiehanterare, lista, contryCode = 'SE', dep = None):
	depafil = "depa.p"
	urlgrund = 'http://www.avanza.se/aza/aktieroptioner/kurslistor/kurslistor.jsp?cc='
	try:
		if contryCode == 'CA' or contryCode == 'US':
			hand = cookiehanterare.urlopen(urlgrund + contryCode + '&lkey=' + lista)
		else:
			hand = cookiehanterare.urlopen(urlgrund + contryCode + '&lkey=' + lista + '.' + contryCode)
	except urllib2.URLError:
		print "URLError i uppdatera_avslut"
		return False, dep
	except:
		print "Okant error:", sys.exc_info()[0]
		return False, dep
	line = 'apa'
	succ = 0
#	while line != '':
#		print line
#		time.sleep(1)
#		line = hand.readline()
#	return False, dep
	while (not ( line.find('Logga ut') > 1 or line.find('signdin') > 1)) and dep != None and succ < 3:
		line = hand.readline()
		if line == '':
			succ += 1
			username = dep.username.decode('base64')
			password = dep.password.decode('base64')
			print "Har blivit utloggad fran avslutsuppdateringen, loggar in igen"
			cookieh = cookiehant.Cookiehanterare()
			time.sleep(1)
			cookieh.open_page(username, password)
			cookiehanterare = cookieh
			try:
				if contryCode == 'CA' or contryCode == 'US':
					time.sleep(0.01)
					hand = cookiehanterare.urlopen(urlgrund + contryCode + '&lkey=' + lista)
				else:
					time.sleep(0.01)
					hand = cookiehanterare.urlopen(urlgrund + contryCode + '&lkey=' + lista + '.' + contryCode)
			except urllib2.URLError:
				print "URLError i uppdatera_avslut"
				return False, dep
			except:
				print "Okant error:", sys.exc_info()[0]
				return False, dep
	feworders = []
	for a in internlista:
		pos = line.find(a.orderbookId)
		succ = 0
		while pos < 10 and line != '':
			try:
				line = hand.readline()
			except urllib2.URLError:
				print "URLError i uppdatera_avslut"
				if succ > 3:
					return False, dep
				else:
					succ += 1
			except:
				print "okanterror i uppdatera_avslut", sys.exc_info()[0]
				if succ > 3:
					return False, dep
				else:
					succ += 1
			pos = line.find(a.orderbookId)
		if pos > 9:
			if len(a.historia) > 1:
				try:
					hour = int(line[-101:-99])
				except:
					if line.find('Du kan inte handla i detta v&auml;rdepapper') > 2:
						pass
					else:
#						print "Kunde inte lasa timmen"
						a.download_senaste_avslut(cookiehanterare)
#						print "sista avslut", time.strftime("%H:%M:%S",time.localtime(a.historia[-1].tid))
#						print "kursnu",str(a.historia[-1].kurs)
						if dep != None:
							handel = dep.bevaka(a)
							if handel:
								dep.uppdatera_handlade_aktier()
								save = dep.cookh
								dep.cookh = None
								spara_objekt(dep, depafil)
								dep.cookh = save
					continue
				if line[-101:-93] != time.strftime("%H:%M:%S",time.localtime(a.historia[-1].tid)) and not (hour > 17):
					a.download_senaste_avslut(cookiehanterare)
					if dep != None:
						handel = dep.bevaka(a)
						if handel:
							dep.uppdatera_handlade_aktier()
							save = dep.cookh
							dep.cookh = None
							spara_objekt(dep, depafil)
							dep.cookh = save
			else:
				a.download_senaste_avslut(cookiehanterare)
				feworders.append(a.searchString)
#				print "	",a.searchString, "kursnu", str(a.historia[-1].kurs)
	if len(feworders) == 1:
		print feworders[0], "saknar laddad historia"
	elif len(feworders) > 1:
		print "Foljade aktier saknar laddad historia: ",
		for searchStr in feworders[0:-2]:
			print searchStr + ',',
		print feworders[-2] + " och",
		print feworders[-1] + "."
	return True, dep
				
def handelstid(tid):
	tid_struct = time.localtime(tid)
	if tid_struct.tm_wday == 5 or tid_struct.tm_wday == 6:
		return False
	if tid_struct.tm_hour < 9:
		return False
	if tid_struct.tm_hour > 17 or (tid_struct.tm_hour == 17 and tid_struct.tm_min >25):
		return False
	if tid_struct.tm_mon == 12:
		if 23 < tid_struct.tm_mday < 27 or tid_struct.tm_mday == 31:
			return False
	if tid_struct.tm_mon == 6 and tid_struct.tm_mday == 6:
		return False
	if tid_struct.tm_year == 2012:
		if tid_struct.tm_mon == 1:
			if tid_struct.tm_mday == 6:
				return False
			if tid_struct.tm_mday == 5 and tid_struct.tm_hour > 12:
				return False
		if tid_struct.tm_mon == 4:
			if tid_struct.tm_mday == 6 or tid_struct.tm_mday == 9:
				return False
			if tid_struct.tm_mday == 21 and tid_struct.tm_hour > 12:
				return False
		if tid_struct.tm_mon == 5 and (tid_struct.tm_mday == 1 or tid_struct.tm_mday == 17):
			return False
		if tid_struct.tm_mon == 6:
			if tid_struct.tm_mday == 22:
				return False
			if tid_struct.tm_mday == 1 and tid_struct.tm_hour > 12:
				return False
		if tid_struct.tm_mon == 11 and tid_struct.tm_mday == 4 and tid_struct.tm_hour > 12:
			return False
		if tid_struct.tm_mon == 12 and tid_struct.tm_mday == 31:
			return False
	return True
				
def kontinuerlig_nedladdning(username, password, uppdat_mellanrum = 180, sparmellanrum = 900, aktielista = None, c_child = None):
	fortsatt = True
	cookieh = cookiehant.Cookiehanterare()
	cookieh.open_page(username, password)
	depafil = "depa.p"
	dep = ladda_objekt(depafil)
	if dep!=None:
		dep.cookh = cookiehant.Cookiehanterare()
		dep.ladda_portfolj()
		dep.read_from_depa()
		dep.uppdatera_handlade_aktier()
		dep.kopsaljbalansuppdat()
		dep.superkanidat = ladda_objekt('SUPERresultat.p')
#		dep.superkanidat = None
	place = "depakopior/"
	print "uppdaterat"
	if aktielista == None:
		print "laddar aktielista"
		aktielista = ladda_aktielista(cookieh,'LargeCap' , 'SE', dep, dagar = 3)
		print "aktielista laddad"
	kal = None
	if dep.superkanidat == None or dep.superkanidat['kalibtid'] + 12*24*3600 < time.time():
		print "\nStartar snart ny kalibrering\n"
#		kal = multiprocessing.Process(target=superprocess, args=(aktielista,dep))
#		kal.start()
	else:
		print "Senaste kalibrering:", time.strftime("%y-%m-%d %H:%M:%S", time.localtime(dep.superkanidat['kalibtid'])), "\nNästa kalibrering:", time.strftime("%y-%m-%d %H:%M:%S", time.localtime(dep.superkanidat['kalibtid'] + 12*24*3600))
		print 
	tid_senast = time.time() - uppdat_mellanrum - 900
	senast_sparad = time.time() -900
	senast_handuppdat = time.time() -900
	while fortsatt:
		tid_nu = time.time() # - 900 för 15 min forskjutning vid ej realtid
		if handelstid(tid_nu) and tid_nu > tid_senast + uppdat_mellanrum:
			print "				laddar ner avslut", time.strftime("%H:%M:%S %y-%m-%d", time.localtime()), "nästa uppdatering:", time.strftime("%H:%M:%S", time.localtime(senast_handuppdat + sparmellanrum * 2))
			print "    " + "Namn".ljust(35) + "ordId".ljust(9) + "kurs".rjust(10) + "stopnivå".rjust(11) + "XXXXXX > XXXXXX > XXXXXX".rjust(27) + "köpt för".rjust(12) + "Vol.".rjust(10)
			try:
				lyckas, dep = uppdatera_avslut(aktielista, cookieh, 'LargeCap' , 'SE', dep = dep)
			except ValueError:
				print " i kontinuerlig_nerladdning error 1", sys.exc_info()
			if tid_nu > senast_sparad + sparmellanrum:
				if tid_nu > senast_handuppdat + sparmellanrum * 1.5:
					gamlhandlade = dep.handlade_aktier
					dep.uppdatera_handlade_aktier()
					try:
						if not kal.is_alive():
							print "\nStart ny kalibrering\n"
							kal = multiprocessing.Process(target=superprocess, args=(aktielista,dep))
							kal.start()
						else:
							pass
					except:
						print "\nStart ny kalibrering\n"
						kal = multiprocessing.Process(target=superprocess, args=(aktielista,dep))
						kal.start()
					aktny = None
					byt = 0
#					for aktId in dep.handlade_aktier:
#						if not (aktId in gamlhandlade or aktId in dep.portfolj):
#							byt = 0
#							try:
#								for i in xrange(len(aktielista)):
#									akt = aktielista[i]
#									if akt.orderbookId == aktId:
#										vp = cPickle.load( open(akt.lista + '/' + akt.orderbookId + '.p' ,'rb') )
##										ladddagar = (vp.eval_perMA / 86400) + 2
#										ladddagar = 3
#										vp.ladda_historik(ladddagar)
#										aktielista[i] = vp
#										break
#							except:
#								print "Error i kontinuerlig nerladdning 1", sys.exc_info()[0]
#								continue
#					for aktId in gamlhandlade:
#						if not aktId in dep.handlade_aktier and not not aktId in dep.portfolj:
#							try:
#								for akt in aktielista:
#									if akt.orderbookId == aktId:
#										ladddagar = 3
#										akt.ladda_historik(ladddagar)
#										break
#							except:
#								print "Error i kontinuerlig nerladdning 2" , sys.exc_info()[0]
#								continue
					aktievarde = decimal.Decimal('0')
					for ordiD in dep.portfolj:
						for vp in aktielista:
							if vp.orderbookId == ordiD:
								aktievarde += vp.historia[-1].kurs * dep.portfolj[ordiD]
								break
					dep.totaltvarde = dep.tot_kap + aktievarde
					print "totalvärde för depå", str(dep.totaltvarde), "SEK,", "minicourtage", str(dep.minicourtage), "SEK," ,"likvida medel", str(dep.tot_kap), "SEK"
					depspar = dep.portfolj
					dep.portfolj = None
					save = dep.cookh
					dep.cookh = None
					spara_objekt(dep, depafil)
					dep.cookh = save
					dep.portfolj = depspar
					senast_handuppdat = tid_nu
					print "Har nu uppdatterat handlingsbara aktier"
#				print "ska nu spara aktielistan"
				spara_aktielista(aktielista, turn_off = False)
				print "historian sparad"
				dep.superkanidat = ladda_objekt('SUPERresultat.p')
				senast_sparad = tid_nu
			if lyckas:
				tid_senast = tid_nu
			else:
				print "Kunde inte uppdatera avslut nu men provar strax igen"
		if not handelstid(tid_nu) and c_child == None:
			tid_struct = time.localtime(tid_nu)
			if tid_struct.tm_hour >= 17 and tid_struct.tm_min >=30:
				spara_aktielista(aktielista, turn_off = True)
				break
		if c_child != None and c_child.poll():
			mottaget = c_child.recv()
			if isinstance(mottaget, aktie.Aktie):
				b = 0
				print "tog emot aktie"
				for akt in aktielista:
					if akt.orderbookId == mottaget.orderbookId:
						tmp = akt.historia
						akt = mottaget
						akt.historia = tmp
						c_child.send("Succesfully updated")
						b = 1
						break
				if b == 0:
					c_child.send("Kunde inte lägga till aktien")
			elif isinstance(mottaget, str):
				if mottaget == "Turn off":
					if dep != None:
						dep.spara_portfolj()
						if not os.path.exists(place):
							os.makedirs(place)
						datumkopia = place + time.strftime("%y%m%d", time.localtime()) + depafil
						aktievarde = decimal.Decimal('0')
						for ordiD in dep.portfolj:
							for vp in aktielista:
								if vp.orderbookId == ordiD:
									aktievarde += vp.historia[-1].kurs * dep.portfolj[ordiD]
									break
						dep.totaltvarde = dep.tot_kap + aktievarde
						print "totalvärde för depå", str(dep.totaltvarde), "SEK,", "minicourtage", str(dep.minicourtage), "SEK," ,"likvida medel", str(dep.tot_kap), "SEK"
						dep.portfolj = None
						save = dep.cookh
						dep.cookh = None
						spara_objekt(dep, depafil)
						spara_objekt(dep, depafil)
						dep.cookh = save
					try:
						if kal.is_alive():
							kal.terminate()
					except:
						pass
					spara_aktielista(aktielista, turn_off = True)
					fortsatt = False
				else:
					b = 0
					for akt in aktielista:
						if akt.searchString.find(mottaget) != -1:
							c_child.send(akt)
							b = 1
							break
					if b == 0:
						c_child.send("Hittade inte aktien")
			else:
				c_child.send("Felaktigt objekt, tog emot: ", str(type(mottaget)))
		else:
			if handelstid(tid_nu):
#				print '..'
				time.sleep(1)
			else:
				if handelstid(tid_nu - 120) and dep != None:
					print "Dagen ar nu slut och kopior pa depa ska goras"
					dep.spara_portfolj()
					if not os.path.exists(place):
						os.makedirs(place)
					datumkopia = place + time.strftime("%y%m%d", time.localtime()) + depafil
					aktievarde = decimal.Decimal('0')
					for ordiD in dep.portfolj:
						for vp in aktielista:
							if vp.orderbookId == ordiD:
								aktievarde += vp.historia[-1].kurs * dep.portfolj[ordiD]
								break
					dep.totaltvarde = dep.tot_kap + aktievarde
					dep.portfolj = None
					save = dep.cookh
					dep.cookh = None
					spara_objekt(dep, depafil)
					spara_objekt(dep, datumkopia)			
					dep.cookh = save
					dep.ladda_portfolj()
					passtime = 0
					while handelstid(tid_nu - 120 + passtime):
						passtime += 10
					time.sleep(passtime)
				elif handelstid(tid_nu + 120) and dep != None:
					print "Snart borjar dagen och depan uppdateras"
					dep.read_from_depa()
					aktielista = ladda_aktielista(cookieh,'LargeCap' , 'SE', dep)
					dep.superkanidat = ladda_objekt('SUPERresultat.p')
					dep.uppdatera_handlade_aktier()
					dep.ladda_portfolj()
					passtime = 0
					while not handelstid(tid_nu + passtime):
						passtime += 5
					time.sleep(passtime)
				else:
					time.sleep(3)
					try:
						if not kal.is_alive():
							print "\nStart ny kalibrering\n"
							kal = multiprocessing.Process(target=superprocess, args=(aktielista,dep))
							kal.start()
						else:
							pass
					except:
						print "\nStart ny kalibrering\n"
						kal = multiprocessing.Process(target=superprocess, args=(aktielista,dep))
						kal.start()
	return aktielista
			
def print_meny():
	print """	
	1.	Logga in och börja ladda ner data
	2.	Stäng av och spara
	3.	Skriv ut menyn
	4.	Hämta ut aktie från register att jobba med, avslutsuppdateringar
		som sker under markeringen skrivs över om den markerade aktien
		skriv tillbaka till registret
	5.	Markera aktie från filsystemet
	6.	Avmarkera och uppdattera aktie i register
	7.	Testa optimeringsfunktion på aktie
	8.	Ladda depåinformtion
	9.	Kalibrera variabler för markerad aktie
	10.	Kalibrera som egen process
	11.	Skriv ut vilka som kalibreras
	12.	Handla markerad aktie
	13.	Skriv ut aktier i depån
	14.	Rensa markerad akties historik från felordnad historik
	"""
		
def huvud():
	p = None
	k = None
	orderbookId_listfil = "orderlista.p"
	depafil = "depa.p"
	dep = ladda_objekt(depafil)
	if dep != None:
		dep.cookh = cookiehant.Cookiehanterare()
		dep.ladda_portfolj()
	forsakringstagare = None
	aktielista = None
	lock = multiprocessing.Lock()
	conn_parrent, conn_child = multiprocessing.Pipe()
	markerad_aktie = None
	orderbookId_lista = ladda_objekt(orderbookId_listfil)
	akt_som_kalibreras = {}
	fortsatt = True
	if dep != None and dep.username != None and dep.password != None:
		username = dep.username.decode('base64')
		password = dep.password.decode('base64')
	else:
		username = None
		password = None
	if fortsatt:
		print "orderbookid_lista length: ", len(orderbookId_lista)
		print_meny()
	while fortsatt:
		if conn_parrent.poll():
			mottaget = conn_parrent.recv()
			if isinstance(mottaget, str):
				print mottaget
			else:
				print "Tog emot felaktigt objekt"
		command = raw_input("Vad vill du göra? ")
		if command == '1':
			if username == None or password == None:
				username = raw_input('Användarnamn: ')
				password = getpass.getpass('Lösenord: ')
			if p == None or not p.is_alive():
				p = multiprocessing.Process(target=Loggain_borjaladdaner, args=(username, password, conn_child))
				p.start()
				print "Process startad"
			else:
				print "Redan igång"
		elif command == '2':
			if p != None:
				if p.is_alive():
					conn_parrent.send("Turn off")
				if aktielista != None:
					spara_aktielista(aktielista, turn_off = True)
			else:
				save = dep.cookh
				dep.cookh = None
				spara_objekt(dep, depafil)
				dep.cookh = save
			for key in akt_som_kalibreras:
				akt_som_kalibreras[key].terminate()
			print "Sparar "
			if p != None:
				while p.is_alive():
					print '.'
					time.sleep(1)
			fortsatt = False
		elif command == '3':
			print_meny()
		elif command == '4':
			if not handelstid(time.time()):
				print "5:an är bättre när det inte är handelstid"
				continue
			sok_ord = raw_input('Sökord: ')
			conn_parrent.send(sok_ord)
			if p != None and p.is_alive() and handelstid(time.time()):
				print "Letar efter aktie"
				mottaget = conn_parrent.recv()
				b = 0
				if isinstance(mottaget, aktie.Aktie):
					b = 1
					markerad_aktie = mottaget
				elif isinstance(mottaget, str):
					print mottaget
				if b == 0:
					print "Kunde inte markera den eftersökta aktien tidigare markeringar gäller fortfarande\n"
			elif p == None:
				print "Du måste börja nerladdning (alternativ 1) innan du kan hämta en aktie från den kontinuerliga nerladdningen"
			if markerad_aktie != None:
				print "Markerad aktie: " + markerad_aktie.searchString
				l = str(len(markerad_aktie.historia))
				print "Antal registrerade avslut: ", l
				if l < 2:
					print "Första registrerade avslut: ", time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(markerad_aktie.historia[1].tid))
		elif command == '5':
			sok_ord = raw_input('Sökord: ')
			if aktielista == None:
				aktielista = []
				for ordid in orderbookId_lista:
					if os.path.isfile('LargeCap/' + ordid + '.p'):
						vp = cPickle.load( open('LargeCap/' + ordid + '.p' ,'rb') )
						aktielista.append(vp)
			b = 0
			for akt in aktielista:
				if akt.searchString.find(sok_ord) != -1:
					if akt_som_kalibreras.has_key(akt.searchString) and akt_som_kalibreras[akt.searchString].is_alive():
						print """
Den aktuella aktien håller på att kalibreas,
och markering kommer gälla den förra kalibreringen"""
					if akt_som_kalibreras.has_key(akt.searchString) and not akt_som_kalibreras[akt.searchString].is_alive():
						print "Den aktuella aktien har kalibrarats färdigt och laddas från fil"
						vp = cPickle.load(open(akt.lista + '/' + akt.orderbookId + '.p' ,'rb'))
						akt = vp
					markerad_aktie = akt
					print "Säkerhestkrav: ", str(markerad_aktie.sakerhetskrav)
					b = 1
					break
			if b == 0:
				print """
Kunde inte markera den eftersökta aktien
tidigare markeringar gäller fortfarande"""
			if markerad_aktie != None:
				print "Markerad aktie: " + markerad_aktie.searchString
				markerad_aktie.ladda_historik(dagar = 100)
				print "Antal registrerade avslut: ", str(len(markerad_aktie.historia)), "\nFörsta registrerade avslut: ", time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(markerad_aktie.historia[1].tid))
		elif command == '6':
			if isinstance(markerad_aktie, aktie.Aktie) and akt_som_kalibreras.has_key(markerad_aktie.searchString) and akt_som_kalibreras[markerad_aktie.searchString].is_alive():
				print """
Den aktuella aktien håller på att kalibreas,
och den förra kalibreringen kommer istället användas"""
			if handelstid(time.time()) and isinstance(markerad_aktie, aktie.Aktie):
				print "Skickar uppdaterad aktie, kan ta en stund"
				conn_parrent.send(markerad_aktie)
				if conn_parrent.poll():
					mottaget = conn_parrent.recv()
					if isinstance(mottaget, str):
						print mottaget
					else:
						print "Tog emot felaktigt objekt"
			elif (not handelstid(time.time())) and isinstance(markerad_aktie, aktie.Aktie):
				tmp = markerad_aktie.historia
				markerad_aktie.historia = []
				cPickle.dump(markerad_aktie, open(markerad_aktie.lista + '/' + markerad_aktie.orderbookId + '.p' , 'wb'))
				markerad_aktie.historia = tmp
				print "Uppdaterat registret"
			else:
				print "Ingen aktie markerad"
		elif command == '7':
			if markerad_aktie == None:
				print "Ingen aktie markerad \n"
			else:
				if akt_som_kalibreras.has_key(markerad_aktie.searchString) and akt_som_kalibreras[markerad_aktie.searchString].is_alive():
					print """Den aktuella aktien håller på att kalibreas,
					och testet kommer köras på den förra kalibreringen"""
				if dep == None:
					if username == None or password == None:
						username = raw_input('Användarnamn: ')
						password = getpass.getpass('Lösenord: ')
					if forsakringstagare == None:
						forsakringstagare = raw_input('Försäkringstagare: ')
					dep = uppdattera_depa(forsakringstagare, username, password)
#				resultat = markerad_aktie.compl_eval(dep.minicourtage,dep.rorligtcourtage , plot = True)
				resultat = markerad_aktie.complete_eval_MA(dep.minicourtage, dep.rorligtcourtage, plot = True)
				print "Resultat: ", str(resultat)
		elif command == '8':
			if username == None or password == None:
				username = raw_input('Användarnamn: ')
				password = getpass.getpass('Lösenord: ')
			if forsakringstagare == None:
				forsakringstagare = raw_input('Försäkringstagare: ')
			dep = uppdattera_depa(forsakringstagare, username, password)
			print "Tillgängligt för köp: " + str(dep.tillgangligt_for_kop)
		elif command == '9':
			if markerad_aktie == None:
				print "Ingen aktie markerad \n"
			else:
				if dep == None:
					if username == None or password == None:
						username = raw_input('Användarnamn: ')
						password = getpass.getpass('Lösenord: ')
					if forsakringstagare == None:
						forsakringstagare = raw_input('Försäkringstagare: ')
					dep = uppdattera_depa(forsakringstagare, username, password)
				res = markerad_aktie.Calibration(dep.minicourtage,dep.rorligtcourtage)
				print "Resultat från optimeringstestet (hela historieperioden): ", str(round(res,5))
		elif command == '10':
			if markerad_aktie == None:
				print "Ingen aktie markerad \n"
			else:
				if akt_som_kalibreras.has_key(markerad_aktie.searchString):
					if akt_som_kalibreras[markerad_aktie.searchString].is_alive():
						print "Aktien kalibreras redan"
						continue
				if dep == None:
					if username == None or password == None:
						username = raw_input('Användarnamn: ')
						password = getpass.getpass('Lösenord: ')
					if forsakringstagare == None:
						forsakringstagare = raw_input('Försäkringstagare: ')
					dep = uppdattera_depa(forsakringstagare, username, password)
				k = multiprocessing.Process(target=calibrationprocess, args=(markerad_aktie, dep.minicourtage, dep.rorligtcourtage))
				k.start()
				akt_som_kalibreras[markerad_aktie.searchString] = k
		elif command == '11':
			print "Aktiva kalibreringar:"
			for key in akt_som_kalibreras:
				if akt_som_kalibreras[key].is_alive():
					print key
			print "Färdiga kalibreringar:"
			for key in akt_som_kalibreras:
				if not akt_som_kalibreras[key].is_alive():
					print key
		elif command == '12':
			if dep == None:
				print "Ingen depå laddad"
				continue
			if markerad_aktie == None:
				print "Ingen aktie markerad"
				continue
			print "Aktie markerad", markerad_aktie.searchString, "orderid",markerad_aktie.orderbookId
			print "Senast registrade kursen", str(markerad_aktie.historia[-1].kurs)
			if markerad_aktie.orderbookId in dep.portfolj:
				print "Nuvarde ägd volym:", dep.portfolj[markerad_aktie.orderbookId]
			volym = raw_input('Antal aktier som ska handlas (postivt om köp ska genomföras och negativt om försäljning ska ske): ')
			pris = decimal.Decimal(raw_input('Pris som handeln ska ske vid: '))
			dep.handla_aktie_riktigt(markerad_aktie, volym, pris)
		elif command == '13':
			if dep == None or dep.portfolj == None:
				if dep != None:
					dep.ladda_portfolj()
					print str(dep.portfolj)
			else:
				print "I portföljen"
				for ordId in dep.portfolj:
					print "	ID:",ordId,"	volym:",dep.portfolj[ordId]
		elif command == '14':
			if markerad_aktie == None:
				print "Ingen aktie markerad \n"
			else:
				markerad_aktie.rensa_historia()
		else:
			print_meny()
			
def autostart(turnoff = True):
	depafil = "depa.p"
	orderbookId_listfil = "orderlista.p"
	dep = ladda_objekt(depafil)
	if dep!=None:
		dep.cookh = cookiehant.Cookiehanterare()
	lock = multiprocessing.Lock()
	conn_parrent1, conn_child1 = multiprocessing.Pipe()
	conn_parrent2, conn_child2 = multiprocessing.Pipe()
	orderbookId_lista = ladda_objekt(orderbookId_listfil)
	if dep.username != None and dep.password != None:
		username = dep.username.decode('base64')
		password = dep.password.decode('base64')
	else:
		exit()
	p = multiprocessing.Process(target=Loggain_borjaladdaner, args=(username, password, conn_child1))
	p.start()
#	k = multiprocessing.Process(target=kontinuerlig_kalibrering, args = (orderbookId_lista, 'LargeCap', dep, conn_child2))
#	k.start()
	if turnoff:
		if not handelstid(time.time()):
			time.sleep(900)
		while handelstid(time.time()):
			time.sleep(600)
		conn_parrent1.send("Turn off")
		conn_parrent2.send("Trun off")
		p.join(540)
		k.join(60)
	else:
		return p, conn_parrent1#, k, conn_parrent2

def calibrationprocess(aktie, dep):
	resultat = aktie.EA_Calibration(dep)
	aktie.historia = None
	cPickle.dump(aktie, open(aktie.lista + '/' + aktie.orderbookId + '.p' , 'wb'))
	return resultat

def uppdat_kalres(aktie, dep):
	if not (hasattr(aktie, 'frambak') and (aktie.frambak == 0 or aktie.frambak == 1)):
		return decimal.Decimal('0.4')
	resultat = aktie.uppdatera_kalres(dep)
#	print "Uppdaterat resultat för", aktie.searchString.ljust(30), aktie.orderbookId.ljust(8), ":",str(round(resultat,4))
	aktie.historia = None
	aktie.plothi = None
	aktie.mAplothi = None
	if aktie.omxid == 'apan' or aktie.omxid == None:
		aktie.omxid = 'katten'
	if hasattr(aktie, 'MAplothi'):
		del aktie.MAplothi
	cPickle.dump(aktie, open(aktie.lista + '/' + aktie.orderbookId + '.p' , 'wb'))
	return resultat

def uppdattera_depa(forsakringstagare, username, password):
	dep = depa.Depa(forsakringstagare, username, password)
	return dep

def ladda_objekt(filename):
	if os.path.exists(filename):
		return cPickle.load(open(filename, 'rb'))
	else:
		return None
	
def spara_objekt(objekt, filename):
	cPickle.dump(objekt ,open( filename , 'wb'))
		
def Loggain_borjaladdaner(username, password, con_chi):
	passtime = 0
	while(not handelstid(time.time() + passtime)):
		passtime += 120
#	print "\n" + str(passtime) + " sekunder tills data börjar laddas ner\n"
#	time.sleep(passtime)
	kontinuerlig_nedladdning(username, password, 120, 600, c_child = con_chi)
	print 'slut för idag\n'
	
def kontinuerlig_kalibrering(Id_lista, lista, dep, c_child = None):
	kalhistfil = 'kalibreringshistorik.p'
	kalreshistfil = 'kalresuppdathistorik.p'
	kaliprocesser = {}
	resuppdatprocesser = {}
	if os.path.isfile(kalhistfil):
		kalibreringshistoria = ladda_objekt(kalhistfil)
	else:
		kalibreringshistoria = {}
	if os.path.isfile(kalreshistfil):
		kalreshistoria = ladda_objekt(kalreshistfil)
	else:
		kalreshistoria = {}
	""" kalibrerar inte for tillfallet"""
	fortsatt = False
	antalsomresuppdaterar = 0
	antalsomkalibreras = 0
	while fortsatt:
		tid_nu = time.time() -900
		if handelstid(tid_nu) or handelstid(tid_nu+10800):
			kalibmax = 0
			resmax = 0
		elif handelstid(tid_nu + 25200): #Pluss sju timmar
 			kalibmax = 0
			resmax = 0
		elif antalsomresuppdaterar > 0:
			kalibmax = 0
			resmax= 1
		else:
			kalibmax = 0
			resmax = 2
		if c_child != None and c_child.poll():
			mottaget = c_child.recv()
			if isinstance(mottaget, str):
				if mottaget == "Turn off":
					for iD in kaliprocesser:
						kaliprocesser[iD].terminate()
					for iD in resuppdatprocesser:
						resuppdatprocesser[iD].terminate()
					fortsatt = False
		kalto_del = []
		for iD in kaliprocesser:
			if not kaliprocesser[iD].is_alive():
#				print iD, "Har kalibrerats fardigt"
				kalibreringshistoria[iD] = time.time()
				antalsomkalibreras -= 1
				spara_objekt(kalibreringshistoria, kalhistfil)
				kalto_del.append(iD)
		for d in kalto_del:
			del kaliprocesser[d]
		resuppto_del = []
		for iD in resuppdatprocesser:
			if not resuppdatprocesser[iD].is_alive():
				kalreshistoria[iD] = time.time()
				antalsomresuppdaterar -= 1
				spara_objekt(kalreshistoria, kalreshistfil)
				resuppto_del.append(iD)
		for d in resuppto_del:
			del resuppdatprocesser[d]
		if fortsatt and antalsomkalibreras < kalibmax:
			tidigasttid = None
			tidigastiD  = None
#			print "len Id_lista",len(Id_lista)
			for iD in Id_lista:
				if iD in kaliprocesser:
					continue
				if not iD in kalibreringshistoria:
					tidigastiD = iD
					break
				elif tidigasttid == None or kalibreringshistoria[iD] < tidigasttid:
					tidigastiD = iD
					tidigasttid = kalibreringshistoria[iD]
			if os.path.isfile(lista + '/' + tidigastiD + '.p'):
				vpfil = lista + '/' + tidigastiD + '.p'
				vp = ladda_objekt(vpfil)
				dagar = vp.ladda_historik(dagar = 100)
				if dagar > 3:
					try:
						vp.download_data()
					except urllib2.URLError:
						"kunde inte uppdatera data för",vp.searchString
					print "Startar kalibrering", vp.searchString, vp.orderbookId, ", antal dagars historik:", dagar
					k = multiprocessing.Process(target=calibrationprocess, args=(vp, dep))
					k.start()
					antalsomkalibreras += 1
					kaliprocesser[tidigastiD] = k
				else:
					print vp.searchString, "har inte tillräckligt lång historia, kunde ladda:", dagar, "dagar"
					vp.kalibreringsresultat = decimal.Decimal('1.0')
					kalibreringshistoria[tidigastiD] = time.time()
					spara_objekt(kalibreringshistoria, kalhistfil)
			else:
				Id_lista.remove(tidigastiD)
		if fortsatt and antalsomresuppdaterar < resmax:
			tidigasttid = None
			tidigastiD  = None
			for iD in Id_lista:
				if iD in resuppdatprocesser:
					continue
				if not iD in kalreshistoria:
					tidigastiD = iD
					break
				elif tidigasttid == None or kalreshistoria[iD] < tidigasttid:
					tidigastiD = iD
					tidigasttid = kalreshistoria[iD]
			if os.path.isfile(lista + '/' + tidigastiD + '.p'):
				vpfil = lista + '/' + tidigastiD + '.p'
				vp = ladda_objekt(vpfil)
				if isinstance(vp.eval_perMA, tuple):
					vp.eval_perMA = vp.eval_perMA[0]
				laddagar = int(14 + math.ceil(vp.eval_perMA / 30600))
				dagar = vp.ladda_historik(dagar = laddagar)
				if dagar > 2 and vp.stoptid != None:
					try:
						vp.download_data()
					except urllib2.URLError:
						"kunde inte uppdatera data för",vp.searchString
					k = multiprocessing.Process(target=uppdat_kalres, args=(vp, dep))
					k.start()
					antalsomresuppdaterar += 1
					resuppdatprocesser[tidigastiD] = k
				elif vp.stoptid == None:
					print vp.searchString, 'har inte kalibrerats'
					vp.kalibreringsresultat = decimal.Decimal('0.9')
					kalreshistoria[tidigastiD] = time.time()
					vp.historia = None
					spara_objekt(vp, vpfil)
					spara_objekt(kalreshistoria, kalreshistfil)
				else:
					print vp.searchString, "har inte tillräckligt lång historia"
					vp.kalibreringsresultat = decimal.Decimal('0.9')
					kalreshistoria[tidigastiD] = time.time()
					vp.historia = None
					spara_objekt(vp, vpfil)
					spara_objekt(kalreshistoria, kalreshistfil)
			else:
				Id_lista.remove(tidigastiD)
		if fortsatt:
			time.sleep(1)

def totalresultat():
	pass

def ladda_aktielista(cookiehanterare, lista, contryCode = 'SE',dep = None, dagar = None):
	aktielista = []
	urlgrund = 'http://www.avanza.se/aza/aktieroptioner/kurslistor/kurslistor.jsp?cc='
	print "ska ladda aktielista"
	if contryCode == 'CA' or contryCode == 'US':
		hand = cookiehanterare.urlopen(urlgrund + contryCode + '&lkey=' + lista)
	else:
		hand = cookiehanterare.urlopen(urlgrund + contryCode + '&lkey=' + lista + '.' + contryCode)
	print "sidan nerladdad"
	line = 'apa'
	ladddagar = 1
	while line != '':
		line = hand.readline()
		pos = line.find('.jsp?orderbookId=')
		if pos > 300:
			orderbookId = line[pos + 17:pos + 23]
			if os.path.isfile(lista + '/' + orderbookId + '.p'):
#				print "laddar", orderbookId
				vp = cPickle.load( open(lista + '/' + orderbookId + '.p' ,'rb') )
				if dagar == None:
					if vp.eval_perMA != None and dep != None and (vp.orderbookId in dep.portfolj or vp.orderbookId in dep.handlade_aktier):
						ladddagar = (vp.eval_perMA / 86400) + 2
					else:
						ladddagar = 1
				else:
					ladddagar = dagar
#				print "laddar historia dagar",ladddagar
				try:
					vp.ladda_historik(ladddagar)
				except:
					print "kunde inte ladda historik for",vp.searchString, vp.orderbookId , sys.exc_info()[0]
					continue
#				print "laddar data"
				try:
					vp.download_data(cookiehanterare)
				except:
					print "Kunde inte ladda ner data for",vp.searchString, vp.orderbookId, sys.exc_info()[0]
					continue
			else:
				print "nylagger in", orderbookId
				vp = aktie.Aktie(orderbookId, cookiehanterare, lista)
				if dagar != None:
					ladddagar = dagar
				else:
					laddagar = 1
				vp.ladda_historik(ladddagar)
				time.sleep(0.1)
			if vp.kursfixfil == None:
				vp.kursfixfil = lista + '/' + orderbookId + 'kursfix.p'
			vp.kursfix = ladda_objekt(vp.kursfixfil)
			tid_nu = time.time()
			if isinstance(vp.handlas_exkl_utd, float) and vp.handlas_exkl_utd < tid_nu:
				ratt = False
				if vp.kursfix == None:
					vp.kursfix = []
				else:
					dat = aktie.tidtilldatumstrang(vp.handlas_exkl_utd)
					for just in vp.kursfix:
						if dat == just['tid']:
							ratt = True
				if not ratt:
					utdelningsjustering = vp.utdelning_aktie
					try:
						utdelningsjustering += vp.extra_utdelning_aktie
					except:
						pass
					vp.ladda_historik(dagar=1000)
					utpos = vp.tidssokning(vp.handlas_exkl_utd, efter=False)
					utdelningsjustering = (vp.historia[utpos].kurs - utdelningsjustering) / vp.historia[utpos].kurs
					for avslu in vp.historia[:utpos + 1]:
						avslu.kurs *= utdelningsjustering
					justering = {'tid':aktie.tidtilldatumstrang(vp.handlas_exkl_utd), 'just':utdelningsjustering}
					vp.mAfil = vp.lista + '/' + vp.orderbookId + "/berakningsinfo.p"
					if os.path.exists(vp.mAfil):
						vp.berakningsinfo = cPickle.load(open(vp.mAfil, 'rb'))
						if 'ma_opt' in vp.berakningsinfo and ((vp.handlas_exkl_utd > tid_nu - vp.berakningsinfo['mA_opt']) or (time.localtime(vp.handlas_exkl_utd).tm_mday == time.localtime().tm_mday)):	
							vp.berakningsinfo['mA'] *= utdelningsjustering
							cPickle.dump(vp.berakningsinfo, open(vp.mAfil, 'wb'))
					vp.spara_historik(turn_off=True)
					vp.ladda_historik(dagar=ladddagar)
					vp.kursfix.append(justering)
					spara_objekt(vp.kursfix, vp.kursfixfil)
			if vp.sucessfull_download == True:
				aktielista.append(vp)
	return aktielista

def superkurshistoria(aktielista):
	print 'ST',
	oldsist = None
	superhistoria = []
	for idx, akt in enumerate(aktielista):
		laddadedagar = akt.ladda_historik(dagar=randrange(20,100,1))
		if laddadedagar < 15:
			continue
		kurshist = akt.build_plot_history(starttid = akt.historia[0].tid, sluttid = time.time(), mellanrum=360)
		akt.ladda_historik(dagar= 1)
		if oldsist != None:
			skalning = oldsist / kurshist[0]
			kurshist = map(lambda x: x * skalning, kurshist)
		oldsist = kurshist[-1]
		superhistoria.extend(kurshist)
		print '.',
		if idx % 10 == 0:
			print 'x'
			print "SUPER Har lagt ihop historien för " + str(idx) + " aktier av " + str(len(aktielista)),
	print 'SL',
	return superhistoria

def eval_EMA(minicourt, rorligtcourt, eMAcanidate, plot_hist = None, show=False):
	if show:
		slowEMAvek = []
		fastEMAvek = []
		fig = plt.figure()
	grundcap = testcap = minicourt / rorligtcourt
	minicourt += decimal.Decimal('50')
	mellanrum = 360.0
	slowEMA = fastEMA = float(plot_hist[0])
	volym = 0
	slowalpha = mellanrum/ float(eMAcanidate['mAeval'])
	fastalpha = mellanrum/ (float(eMAcanidate['mAeval']) * eMAcanidate['fastfakt'])
	for idx, kurs in enumerate(plot_hist):
		slowEMA = slowalpha * float(kurs) + (1.0 - slowalpha) * slowEMA
		fastEMA = fastalpha * float(kurs) + (1.0 - fastalpha) * fastEMA
		if show:
			slowEMAvek.append(slowEMA)
			fastEMAvek.append(fastEMA)
		if not idx > 1000:
			continue
		if minicourt > (testcap + kurs * volym):
			return -0.1
		if not volym > 0 and ((fastEMA > kurs > slowEMA and eMAcanidate['frambak'] == 0) or (slowEMA > kurs > fastEMA and eMAcanidate['frambak'] == 1) or (kurs > fastEMA > slowEMA and eMAcanidate['frambak'] == 2)):
			kopvolym = int((testcap - testcap % kurs)/kurs)
			volym += kopvolym
			testcap -= kopvolym * kurs + minicourt * 2
		elif not volym < 0 and ((slowEMA > kurs > fastEMA and eMAcanidate['frambak'] == 0) or (fastEMA > kurs > slowEMA and eMAcanidate['frambak'] == 1) or (kurs < fastEMA < slowEMA and eMAcanidate['frambak'] == 2)):
			if volym > 0:
				testcap += kurs * volym - minicourt
				volym = 0
			saljvolym = - int((testcap - testcap% kurs)/kurs)
			volym += saljvolym
			testcap -= saljvolym * kurs + minicourt
	forandring = (testcap + kurs * volym) / grundcap
	if show:
		plt.plot(plot_hist, 'k')
		plt.plot(slowEMAvek, 'b')
		plt.plot(fastEMAvek, 'm')
		plt.title('fb'+str(eMAcanidate['frambak']) + ' ' +str(eMAcanidate['mAeval'])+' '+str(round(eMAcanidate['fastfakt'],2)) + " res: " + str(round(forandring,4)))
		try:
			fig.savefig("kalibres/"+'f'+str(eMAcanidate['frambak'])+'b' + str(round(forandring,2))+'m'+ str(eMAcanidate['mAeval']) +'f'+ str(round(eMAcanidate['fastfakt'],2)) + '.png', dpi = 100)
			time.sleep(2)
		except:
			pass
		plt.close()
	return forandring

def superprocess(aktielista,dep):
	if not isinstance(aktielista[0], aktie.Aktie):
		print "\nFel i argumenten till funktionen\n"
	superkan = superkalibrering([p for p in aktielista if p.orderbookId in dep.handlade_aktier], show=False)
	if superkan == None:
		return
	totres = 1
	for akt in aktielista:
		totres *= akt.superuppdat(dep,superkan)
	superkan['totres'] = float(totres) ** (1.0/float(len(aktielista)))
	old = None
	try:
		oldkan = ladda_objekt('SUPERresultat.p')
		if superkan['totres'] > (oldkan['totres'] ** (12.0 / (12.0 + (superkan['kalibtid']-oldkan['kalibtid'])/86400))):
			print "Sparar resultatet i SUPERresultat.p"
			spara_objekt(superkan, "SUPERresultat.p")
			spara_objekt(superkan, "SUPERres/" + time.strftime("%y%m%d",time.localtime()) + ".p")
	except:
		if superkan['totres'] > 1.00:
			print "Sparar resultatet i SUPERresultat.p"
			spara_objekt(superkan, "SUPERresultat.p")
			spara_objekt(superkan, "SUPERres/" + time.strftime("%y%m%d",time.localtime()) + ".p")
	print "\nTotalt resultat for alla aktier:",superkan['totres'],"\n"
	
def superkalibrering(aktielista, show = False):
	if show:
		plt.close('all')
		fig = plt.figure()
		ax = fig.add_subplot(111, projection='3d')
		ax.set_xlabel('mAeval')
		ax.set_ylabel('fastfakt')
		ax.set_zlabel('Resultat')
		x1 = y1 = z1 = x2 = y2 = z2 = []
	start = time.time()
	kalibreringsslut = start - 1209600
	minicourt = decimal.Decimal('39')
	rorligtcourt = decimal.Decimal('0.0013')
	superhistoria = superkurshistoria(aktielista)
	if len(superhistoria) < 4000:
		return None
	pop = createPop(minicourt, rorligtcourt,superhistoria, popsize = 300, kalibslut = kalibreringsslut)
	if show:
		x0 = map(lambda x: x['mAeval'],filter(lambda y: y['frambak']==0,pop))
		y0 = map(lambda x: x['fastfakt'],filter(lambda y: y['frambak']==0,pop))
		z0 = map(lambda x: float(x['result']),filter(lambda y: y['frambak']==0,pop))

		x1 = map(lambda x: x['mAeval'],filter(lambda y: y['frambak']==1,pop))
		y1 = map(lambda x: x['fastfakt'],filter(lambda y: y['frambak']==1,pop))
		z1 = map(lambda x: float(x['result']),filter(lambda y: y['frambak']==1,pop))

		x2 = map(lambda x: x['mAeval'],filter(lambda y: y['frambak']==2,pop))
		y2 = map(lambda x: x['fastfakt'],filter(lambda y: y['frambak']==2,pop))
		z2 = map(lambda x: float(x['result']),filter(lambda y: y['frambak']==2,pop))
		if len(x0) != 0:
			ax.scatter(x0, y0, z0, c='g', marker='o')
		if len(x1) != 0:
			ax.scatter(x1, y1, z1, c='g', marker='^')
		if len(x2) != 0:
			ax.scatter(x2, y2, z2, c='g', marker='8')
		
	print "SUPER Ny population bäst",str(round(pop[0]['result'],4)),"tjugonde",str(round(pop[19]['result'],4)),"tretionde",str(round(pop[49]['result'],4))
	print "SUPER bestmAeval",str(pop[0]['mAeval']),"fastfakt",str(pop[0]['fastfakt']), "frambak" , str(pop[0]['frambak'])
	print "SUPER tidsuppskattning 1 kalibrationen är färdig ca", time.strftime("%H:%M, %d %b",time.localtime(start + (time.time()-start)*(float(114)/40))),
	pop = evolve(pop, minicourt, rorligtcourt, superhistoria, popsize = 300, kalibslut = kalibreringsslut)
	if show:
		x0 = map(lambda x: x['mAeval'],filter(lambda y: y['frambak']==0,pop))
		y0 = map(lambda x: x['fastfakt'],filter(lambda y: y['frambak']==0,pop))
		z0 = map(lambda x: float(x['result']),filter(lambda y: y['frambak']==0,pop))

		x1 = map(lambda x: x['mAeval'],filter(lambda y: y['frambak']==1,pop))
		y1 = map(lambda x: x['fastfakt'],filter(lambda y: y['frambak']==1,pop))
		z1 = map(lambda x: float(x['result']),filter(lambda y: y['frambak']==1,pop))

		x2 = map(lambda x: x['mAeval'],filter(lambda y: y['frambak']==2,pop))
		y2 = map(lambda x: x['fastfakt'],filter(lambda y: y['frambak']==2,pop))
		z2 = map(lambda x: float(x['result']),filter(lambda y: y['frambak']==2,pop))
		
		if len(x0) != 0:
			ax.scatter(x0, y0, z0, c='y', marker='o')
		if len(x1) != 0:
			ax.scatter(x1, y1, z1, c='y', marker='^')
		if len(x2) != 0:
			ax.scatter(x2, y2, z2, c='y', marker='8')
	print "SUPER andra generationen bäst",str(round(pop[0]['result'],4)),"tjugonde",str(round(pop[19]['result'],4)),"tretionde",str(round(pop[29]['result'],4))
	print "SUPER bestmAeval",str(pop[0]['mAeval']),"fastfakt",str(pop[0]['fastfakt']), "frambak" , str(pop[0]['frambak'])
	print "SUPER tidsuppskattning 2 kalibrationen är färdig ca", time.strftime("%H:%M, %d %b",time.localtime(start + (time.time()-start)*(float(114)/76))),
	pop = evolve(pop, minicourt, rorligtcourt, superhistoria, popsize = 300, kalibslut = kalibreringsslut)
	if show:
		x0 = map(lambda x: x['mAeval'],filter(lambda y: y['frambak']==0,pop))
		y0 = map(lambda x: x['fastfakt'],filter(lambda y: y['frambak']==0,pop))
		z0 = map(lambda x: float(x['result']),filter(lambda y: y['frambak']==0,pop))

		x1 = map(lambda x: x['mAeval'],filter(lambda y: y['frambak']==1,pop))
		y1 = map(lambda x: x['fastfakt'],filter(lambda y: y['frambak']==1,pop))
		z1 = map(lambda x: float(x['result']),filter(lambda y: y['frambak']==1,pop))

		x2 = map(lambda x: x['mAeval'],filter(lambda y: y['frambak']==2,pop))
		y2 = map(lambda x: x['fastfakt'],filter(lambda y: y['frambak']==2,pop))
		z2 = map(lambda x: float(x['result']),filter(lambda y: y['frambak']==2,pop))
		
		if len(x0) != 0:
			ax.scatter(x0, y0, z0, c='r', marker='o')
		if len(x1) != 0:
			ax.scatter(x1, y1, z1, c='r', marker='^')
		if len(x2) != 0:
			ax.scatter(x2, y2, z2, c='r', marker='8')
		
	print "SUPER tredje generationen bäst",str(round(pop[0]['result'],4)),"tjugonde",str(round(pop[19]['result'],4)),"tretionde",str(round(pop[29]['result'],4))
	print "SUPER bestmAeval",str(pop[0]['mAeval']),"fastfakt",str(pop[0]['fastfakt']), "frambak" , str(pop[0]['frambak'])
	pop[0]['kalibtid'] = time.time()
	print "\n 		Super kalibrering resultat:\n frambak:", str(pop[0]['frambak']),"\n mAeval:" + str(pop[0]['mAeval']) + "\n fastfakt: " + str(pop[0]['fastfakt']),
	if show:
		plt.show()
	return pop[0]
	
def createPop(minicourt, rorligtcourt,superhistoria, popsize = 60, kalibslut = time.time()):
	pop = None
	start = time.time()
	for i in xrange(popsize):
		if i  % 10 == 1:
			print ".",
#			print "SUPER har gjort",i,"kanidater bäst: " + str(round(pop[0]['result'],4))
		canidate = randomCanidate()
		canidate['result'] = eval_EMA(minicourt, rorligtcourt, eMAcanidate = canidate, plot_hist = superhistoria)
		if i % 100 == 99 or i == 9:
			print "x"
			print "SUPER tidsuppskattning populationen är färdig", time.strftime("%H:%M, %d %b",time.localtime(start + (time.time()-start)*(float(popsize)/(i+1)))), "har gjort", str(i+1), "kanidater",
		pop = popInsert(canidate, pop)
	print '.'
	return pop

def createPopPool(minicourt, rorligtcourt,superhistoria, popsize = 60, kalibslut = time.time()):
	arbetare = multiprocessing.Pool()
	pop = arbetare.map(randomPoolCanidate(minicourt,rorligtcourt,plot_hist = superhistoria),range(popsize))
	sorteradpop = None
	for can in pop:
		sorteradpop = popInsert(canidate, sorteradpop)
	return sorteradpop

def randomPoolCanidate(minicourt, rorligtcourt, plot_hist, maxi = 70 * 24 * 3600):
	canidate = {}
	canidate['mAeval'] = randrange(1080,600000,360)
	fasfakt = 2
	while not 0.05 < fasfakt < 0.9:
		fasfakt = random()
	canidate['fastfakt'] = fasfakt
#	canidate['frambak'] = 1
	canidate['frambak'] = choice([0, 1, 2])
	canidate['result'] = eval_EMA(minicourt, rorligtcourt, eMAcanidate = canidate, plot_hist=plot_hist)
	return canidate

def randomCanidate(maxi = 70 * 24 * 3600):
	canidate = {}
	canidate['mAeval'] = randrange(1080,1200000,360)
	fasfakt = 2
	while not 0.03 < fasfakt < 0.9:
		fasfakt = random()
	canidate['fastfakt'] = fasfakt
	canidate['frambak'] = 1
#	canidate['frambak'] = choice([0, 1, 2])
	return canidate

def evolve(pop, minicourt, rorligtcourt,superhistoria, popsize=60, kalibslut=time.time()):
	print 'ST',
	matepop = pop[:int(popsize * 0.45)]
	nypop = pop[:int(popsize*0.1)]
	for canidate in matepop:
		narmaste = []
		langst = 0
		for cani in pop:
			dist = canidateDist(canidate, cani)
			if len(narmaste) < 4:
				if dist > langst:
					langst = dist
				succ = 0
				for n in xrange(0, len(narmaste)):
					if dist < narmaste[n]['d']:
						succ = 1
						narmaste.insert(n, {'d': dist, 'c':cani})
						break
				if succ == 0:
					narmaste.append({'d': dist, 'c':cani})
			else:
				if dist > langst:
					continue
				else:
					for n in xrange(0, len(narmaste)):
						if dist < narmaste[n]['d']:
							narmaste.insert(n, {'d': dist, 'c':cani})
							break
					narmaste = narmaste[:5]
					langst = narmaste[4]['d']
		best = None
		bestres = 0
		nast = None
		nastres = 0
		for distandcani in narmaste:
			if distandcani['c']['result'] > nastres:
				if distandcani['c']['result'] > bestres:
					nast = best
					nastres = bestres
					bestres = distandcani['c']['result']
					best = distandcani['c']
				else:
					nastres = distandcani['c']['result']
					nast = distandcani['c']
		mates = [best, nast]
		for mate in mates:
			child = mateCanidate(canidate, mate)
			child['result'] = eval_EMA(minicourt, rorligtcourt, eMAcanidate = child, plot_hist = superhistoria)
			nypop = popInsert(child, nypop)
			if len(nypop) % 20 == 0:
				print '.',
#				print "SUPER evolve nypop",len(nypop)
	print 'SL'
	return nypop

def evolvePool(pop, minicourt, rorligtcourt,superhistoria, popsize=60, kalibslut=time.time()):
	arbetare = multiprocessing.Pool()
	matepop = pop[:int(popsize * 0.45)]
	nypop = pop[:int(popsize*0.1)]
	for canidate in matepop:
		narmaste = []
		langst = 0
		for cani in pop:
			dist = canidateDist(canidate, cani)
			if len(narmaste) < 4:
				if dist > langst:
					langst = dist
				succ = 0
				for n in xrange(0, len(narmaste)):
					if dist < narmaste[n]['d']:
						succ = 1
						narmaste.insert(n, {'d': dist, 'c':cani})
						break
				if succ == 0:
					narmaste.append({'d': dist, 'c':cani})
			else:
				if dist > langst:
					continue
				else:
					for n in xrange(0, len(narmaste)):
						if dist < narmaste[n]['d']:
							narmaste.insert(n, {'d': dist, 'c':cani})
							break
					narmaste = narmaste[:5]
					langst = narmaste[4]['d']
		best = None
		bestres = 0
		nast = None
		nastres = 0
		for distandcani in narmaste:
			if distandcani['c']['result'] > nastres:
				if distandcani['c']['result'] > bestres:
					nast = best
					nastres = bestres
					bestres = distandcani['c']['result']
					best = distandcani['c']
				else:
					nastres = distandcani['c']['result']
					nast = distandcani['c']
		mates = [best, nast]
		mates = map(lambda mate: mateCanidate(canidate, mate),mates)
		result = arbetare.map(lambda child: eval_EMA(minicourt, rorligtcourt, eMAcanidate = child, plot_hist = superhistoria), mates)
		for k in xrange(len(mates)):
			mates[k]['result'] = result[k]
			nypop = popInsert(mates[k], nypop)
#			if len(nypop) % 50 == 0:
#				print "SUPER evolve nypop",len(nypop)
	return nypop
				 
def mateCanidate(can1, can2):
	child = {}
	child['mAeval']  = (can1['mAeval'] - (can1['mAeval'] - can2['mAeval'])*random())*uniform(0.95,1.05)
	child['fastfakt'] = (can1['fastfakt'] - (can1['fastfakt'] - can2['fastfakt'])*random())*uniform(0.95,1.05) 
	child['frambak'] = can1['frambak']
	return child
		
def canidateDist(can1, can2, maxi = 70 * 24 * 3600):
	dmAe = (can1['mAeval'] - can2['mAeval'])/float(maxi/10 - 14400)
	dfmA = can1['fastfakt'] - can2['fastfakt']
	if can1['frambak'] == can2['frambak']:
		return (dmAe**2 + dfmA**2)**(1/float(2))
	else:
		return 5 + (dmAe**2 + dfmA**2)**(1/float(2))
	
def popInsert(canidate, pop):
	res = canidate['result']
	if pop == None:
		pop = [canidate]
		return pop
	length = len(pop)
	if length == 1:
		if pop[0]['result'] > canidate['result']:
			pop.append(canidate)
		else:
			pop.insert(0,canidate)
	elif length < 30:
		for i in xrange(length):
			if pop[i]['result'] < res:
				pop.insert(i,canidate)
				return pop
		pop.append(canidate)
	else:
		higher = length -1
		if res < pop[higher]['result']:
			pop.append(canidate)
		elif res > pop[0]['result']:
			pop.insert(0,canidate)
		else:
			lower = 0
			pos = (higher + lower)/2
			p = 0
			while higher > lower and not (pop[pos-1]['result'] >= res and pop[pos]['result'] <= res):
				p += 1
#				print "hi",higher,"low",lower,"pos",pos,"hivalue",pop[pos]['result'], "innanvalue", pop[pos-1]['result'],"res",res
				if pop[pos]['result'] > res:
					lower = pos
				elif pop[pos]['result'] < res:
					higher = pos
				else:
					break
				pos = int((higher + lower)/2)
				if p > 10:
					break
			pop.insert(pos,canidate)
	return pop
	
