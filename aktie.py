# -*- coding: utf-8 -*-
import avslut, time, os, decimal,cPickle, urllib2, cookiehant, sys
import matplotlib.pyplot as plt
from httplib import IncompleteRead
from random import uniform, random #, randrange, choice

class Aktie:
    sucessfull_download = None
    lista = None
    orderbookId = None
    omxid = 'apan' # Andras manuellt i .p filen
    market = None  # Tas annu inte in
    countryCode = None
    searchString = None
    currency = None
    borspost = None
    pE = None
    volatilitet = None
    direktavkastning = None
    kurs_egetkap = None
    oms_aktie = None
    intro_datum = None
    handlas_exkl_utd = None
    utdelning_aktie = None
    borslista = None
    borsvarde = None
    pS = None
    vinst_aktie = None
    egetkap_aktie = None
    forsaljning_aktie = None
    effektivavkastn = None
    utdelningsdag = None
    extra_utdelning_aktie = None
    historia = []
    senast_sparade_avslut = None
    sakerhetskrav = None
    eval_perMA = None
    fastfakt = None
    eval_perCaplvl = None
    caplvlfaktor = None
    stoptid = None
    mA_opt = None
    nivaer_opt = None
    plothi = None
    mAplothi = None
    kalibreringsresultat = None
    kalibreringshistoria = None
    mAfil = None
    handelsfil = None
    stopniva = None
    stoptidpunkt = None
    berakningsinfo = None
    handelsdata = None
    kursfix = None
    kursfixfil = None
    oldhandelskurs = None
    frambak = None
    
    def __init__(self, orderbook_Id, cookiehanterare, lista):
        self.lista = lista
        self.orderbookId = orderbook_Id
        self.sucessfull_download = self.download_data(cookiehanterare)
        self.historia = [avslut.Avslut("00:00:00", -1, 0)]  # lagger in objekt i botten for att python inte ska aliasa ihop dem
        self.eval_perMA = 172800
        self.eval_perCaplvl = 8000
        self.kursfixfil = lista + '/' + orderbook_Id + '/kursfix.p'

    def tidssokning(self, tid, efter = True, historia = None):
        """Efter anger huruvida den returnnerade positionen ar efter eller fore tiden"""
        if historia == None:
            historia = self.historia
        langd = len(historia)
        forstatid = historia[0].tid
        if tid <= forstatid:
            return 0
        sistatid = historia[-1].tid
        if tid >= sistatid:
            return langd-1
        pos = int(((tid - forstatid) / (sistatid-forstatid))*langd)        
        ovre = langd -1
        undre = 0
        if pos > ovre:
            pos = ovre - 3
        p = 0
        if efter:
            extra = 1
        else:
            extra = 0
#        print "borjar tidssokning med", str(tid), "sista i historien ar", str(historia[-1].tid)
        while not (historia[pos + extra -1].tid <= tid and historia[pos+extra].tid > tid):
            p += 1
            postid = historia[pos].tid
            if undre >= ovre:
                return pos
            if postid > tid:
                ovre = pos
            else:
                undre = pos
            
            pos = int((ovre+undre) /2)
            if p > 20:
                if ovre - 1 == undre:
                    if efter:
                        return ovre
                    else:
                        return undre
                print "fel i tidssokning"
                break
#        print "antal steg", str(p),"historie langd", str(len(historia))
        return pos

    def createCapLevels(self, forstatid=None, sistatid=None):
#        print "create cap"
        if sistatid == None:
            sistatid = time.time()
        if forstatid == None:
            if self.eval_perCaplvl == None or self.eval_perCaplvl < 7400:
                self.eval_perCaplvl = 8000
            forstatid = sistatid - self.eval_perCaplvl
        caplevels = {}
        startvard = self.tidssokning(forstatid, efter = False)
        slutvard = self.tidssokning(sistatid, efter = True)
        for avslu in self.historia[startvard:slutvard]:
            if cmp(avslu.tid, forstatid) < 0:
                continue
            if cmp(avslu.tid, sistatid) > 0:
                return caplevels
            if self.possible_kurs(avslu.kurs) in caplevels:
                caplevels[self.possible_kurs(avslu.kurs)] += avslu.volym
            else:
                caplevels[self.possible_kurs(avslu.kurs)] = avslu.volym
        return caplevels
    
    def updateCapLevels(self, oldcaplevels, oldforst, oldsist, forstatid, sistatid):
        caplevels = oldcaplevels
        startvard = self.tidssokning(forstatid, efter = False)
        slutvard = self.tidssokning(sistatid, efter = True)
        oldstart = self.tidssokning(oldforst, efter = False)
        oldslut = self.tidssokning(oldsist, efter = True)
        for avslu in self.historia[oldstart:startvard]:
            if avslu.kurs in caplevels:
                caplevels[avslu.kurs] -= avslu.volym
        for avslu in self.historia[oldslut:slutvard]:
            if cmp(avslu.tid, sistatid) > 0:
                return caplevels
            if avslu.kurs in caplevels:
                caplevels[self.possible_kurs(avslu.kurs)] += avslu.volym
            else:
                caplevels[self.possible_kurs(avslu.kurs)] = avslu.volym
        return caplevels
    
    def rensa_historia(self):
        if self.historia != None and len(self.historia) > 1:
            oldtid = 0
            place = 0
            for av in self.historia:
                if av.tid < oldtid:
                    del self.historia[place]
                place += 1

    def download_senaste_avslut(self, cookiehanterare):
        senast_nedladdade_avslut = []
        urladress = 'https://www.avanza.se/aza/aktieroptioner/kurslistor/avslut.jsp?orderbookId=' + self.orderbookId
        hand = None
        try:
            time.sleep(0.1)
            hand = cookiehanterare.urlopen(urladress)
            time.sleep(0.05)
        except urllib2.URLError:
            print "URLError -> Kunde inte ladda ner avslut for ", self.searchString, ", kl ", time.strftime("%H:%M:%S") 
            return
        except:
            print "Okant error -> Kunde inte ladda ner avslut for ", self.searchString, ", kl ", time.strftime("%H:%M:%S"), sys.exc_info()[0]
            return
        line = 'apa'
        sista_avslut = None
        while line != '':
            try:
                line = hand.readline()
            except IncompleteRead:
                print "Incomplete Read: ", self.orderbookId, ", kl ", time.strftime("%H%M%S") 
                break
            pos = line.find(".jsp?broker_id=")
            if pos > 10 and line[pos + 15:pos + 18].isalpha():
                pos2 = line[pos + 18:].find(".jsp=broker_id=") + pos + 18
                sista_avslut = line[pos + 15:pos + 18] + line[pos2 + 15:pos2 + 18] + line[-90:-10]
                break
        pos = line.find("</TD><TD class='neutral'>")
        tmpavslut = sista_avslut
        oldtid = None
        oldkurs = None
        while tmpavslut != self.senast_sparade_avslut and pos > 10:
            pos2 = line[pos + 25:].find("</TD><TD class='neutral'>") + pos + 25
            pos3 = line[pos2 + 25:].find("</TD><TD class='neutral'>") + pos2 + 25
            tid = line[pos + 25 : pos2]
            kurs = decimal.Decimal(line[pos2 +25:pos3].replace(',', '.'))
            volym = int(line[pos3 + 25:-11])
            if tid == oldtid and kurs == oldkurs:
                senast_nedladdade_avslut[0].volym += volym
            else:
                if (len(senast_nedladdade_avslut) > 0 and tid < senast_nedladdade_avslut[-1].tid) or (len(self.historia) > 1 and tid < self.historia[-1]):
                    print "download_senaste_avslut - senare avslut holl pa att laggas till i", self.searchString
                    continue
                senast_nedladdade_avslut.insert(0, avslut.Avslut(tid, kurs, volym))
                oldtid = tid
                oldkurs = kurs
            line = hand.readline()
            pos = line.find(".jsp?broker_id=")
            pos2 = line[pos + 18:].find(".jsp=broker_id=") + pos + 18
#            temptemp = tmpavslut
            tmpavslut = line[pos + 15:pos + 18] + line[pos2 + 15:pos2 + 18] + line[-90:-10]
            pos = line.find("</TD><TD class='neutral'>")
#        if len(senast_nedladdade_avslut) > 0:
#            print "lagger till", len(senast_nedladdade_avslut), "Avslut fran", time.strftime("%H:%M:%S", time.localtime(senast_nedladdade_avslut[0].tid)),"till", time.strftime("%H:%M:%S", time.localtime(senast_nedladdade_avslut[-1].tid)), "i",self.searchString
#            print "senaste tmp:       ", temptemp
#            print "senast sparade:    ", self.senast_sparade_avslut
#        else:
#            print "Inga nya avslut i", self.searchString
        self.senast_sparade_avslut = sista_avslut
#        if len(senast_nedladdade_avslut) > 0:
#            print "sist", str(senast_nedladdade_avslut[-1].kurs), self.searchString
        if self.historia[-1].kurs == -1 and len(senast_nedladdade_avslut) > 0:
            self.historia = senast_nedladdade_avslut
        else:
            self.historia.extend(senast_nedladdade_avslut)
#        print self.searchString, "kursnu", str(self.historia[-1].kurs)
#        print "hist",str(self.historia),"senast",str(senast_nedladdade_avslut)
        return

    def download_data (self, cookiehanterare = None):
        urladress = 'https://www.avanza.se/aza/aktieroptioner/kurslistor/aktie.jsp?orderbookId=' + self.orderbookId
        # req = Request(urladress)
        # create a request object
        if cookiehanterare == None:
            cookiehanterare = cookiehant.Cookiehanterare()
        sucess = 0
        while sucess < 3:
            try:
                time.sleep(0.01)
                hand = cookiehanterare.urlopen(urladress)
                time.sleep(0.01)
                sucess = 10
            except urllib2.HTTPError:
                sucess += 1
                print "HTTPerror i download_data"
            except urllib2.URLError:
                sucess += 1
                print "URLerror i download_data"
            except:
                sucess += 1
                print "Okant error i download_data"
        if sucess != 10:
            return False
        line = 'apa'
        try:
            while line != '':
                line = hand.readline()
                pos = line.find('greydark11')
                if  pos != -1:
                    self.searchString = line[pos+12:-7]
                    break
            while line != '':
                line = hand.readline()
                if line.find('Handlas i') != -1:
                    self.currency = line[71:-6]
                    if self.currency == 'SEK':
                        self.countryCode = 'SE'
                    elif self.currency == 'EUR':
                        self.countryCode = 'FI'
                    elif self.currency == 'DKK':
                        self.countryCode = 'DK'
                    elif self.currency == 'USD':
                        self.countryCode = 'US'
                    elif self.currency == 'CAD':
                        self.countryCode = 'CA'
                    break
            while line != '':
                line = hand.readline()
                pos = line.find('B&ouml;rsv&auml;rde MSEK')
                if pos != -1:
                    tmp = decimal.Decimal(line[pos + 30:-11].replace(',', '.'))
                    break
            while line != '':
                line = hand.readline()
                if line.find('B&ouml;rspost:') != -1:
                    self.borspost = int(line[93:-6])
                    break
            while line != '':
                line = hand.readline()
                if line.find('P/S-tal') != -1:
                    val = line[83:-11].replace(',', '.')
                    if val != '-' and val != '':
                        self.pS = decimal.Decimal(val)
                    break
            while line != '':
                line = hand.readline()
                if line.find('P/E-tal') != -1:
                    self.pE = line[69:-6].replace(',', '.')
                    if val != '-' and val != '':
                        self.pE = decimal.Decimal(val)
                    break
            while line != '':
                line = hand.readline()
                if line.find('Vinst/aktie SEK') != -1:
                    val = line[73:-11].replace(',', '.')
                    if val != '-' and val != '':
                        self.vinst_aktie = decimal.Decimal(val)
                    break
            while line != '':
                line = hand.readline()
                pos = line.find('Volatilitet')
                if pos != -1:
                    tmp = line[1:-len(line) + 4].replace(',', '.')
                    if tmp.isdigit():
                        self.sakerhetskrav = decimal.Decimal(tmp)
                    else:
                        self.sakerhetskrav = None
                    tmp = line[pos + 19:-6].replace(',', '.')
                    if tmp != '-' and val != '':
                        self.volatilitet = decimal.Decimal(tmp)
                    break
            while line != '':
                line = hand.readline()
                if line.find('Eget kapital/aktie') != -1:
                    val = line[80:-11].replace(',', '.').replace(' -' , '')
                    if val != '-' and val != '':
                        self.egetkap_aktie = decimal.Decimal(val)
                    break
            while line != '':
                line = hand.readline()
                pos = line.find('Direktavkastning')
                if pos != -1:
                    val = line[pos + 24:-6].replace(',', '.').replace(' -' , '')
                    if val != '-' and val != '':
                        self.direktavkastning = decimal.Decimal(val)
                    break
            while line != '':
                line = hand.readline()
                if line.find('F&ouml;rs&auml;ljning/aktie') != -1:
                    val = line[107:-11].replace(',', '.').replace(' -' , '')
                    if val != '-' and val != '':
                        self.forsaljning_aktie = decimal.Decimal(val)
                    break
            while line != '':
                line = hand.readline()
                if line.find('Kurs/Eget kap') != -1:
                    val = line[76:-6].replace(',', '.').replace(' -' , '')
                    if val != '-' and val != '':
                        self.kurs_egetkap = decimal.Decimal(val)
                    break
            while line != '':
                line = hand.readline()
                if line.find('Effektivavkastn.') != -1:
                    val = line[76:-11].replace(',', '.').replace(' -' , '')
                    if val != '-' and val != '':
                        self.effektivavkastn = decimal.Decimal(val)
                    break
            while line != '':
                line = hand.readline()
                if line.find('Oms./aktie') != -1:
                    val = line[94:-39].replace(',', '.').replace(' -' , '')
                    if val != '-' and val != '':
                        self.oms_aktie = decimal.Decimal(val)
                    break
            while line != '':
                line = hand.readline()
                if line.find('Intro.datum') != -1:
                    intro_datum = line[73:-6]
                    self.intro_datum = datumstrangtilltid(intro_datum)
                    break
            while line != '':
                line = hand.readline()
                if line.find('Handlas exkl. utd.') != -1:
                    handlas_exkl_utd = line[98:-6]
                    self.handlas_exkl_utd = datumstrangtilltid(handlas_exkl_utd)
                    break
            while line != '':
                line = hand.readline()
                if line.find('Utdelningsdag') != -1:
                    utdelningsdag = line[89:-11]
                    self.utdelningsdag = datumstrangtilltid(utdelningsdag)
                    break
            while line != '':
                line = hand.readline()
                if line.find('Utdelning/aktie') != -1:
                    val = line[81:-6].replace(',', '.')
                    if val != '-' and val != '':
                        self.utdelning_aktie = decimal.Decimal(val)
                    break
            while line != '':
                line = hand.readline()
                if line.find('Extra utdelning/aktie') != -1:
                    val = line[83:-11].replace(',', '.')
                    if val != '-' and val != '':
                        self.extra_utdelning_aktie = decimal.Decimal(val)
                    break
            return True
        except ValueError:
            return False

    def handelstid(self, tid):
        if self.countryCode == None:
            self.countryCode = 'SE'
        tid_struct = time.localtime(tid)
        if tid_struct.tm_wday == 5 or tid_struct.tm_wday == 6:
            return False
        elif self.countryCode == 'SE' or self.countryCode == 'FI' or self.countryCode == 'NO':
            if tid_struct.tm_hour < 9:
                return False
            if (tid_struct.tm_hour == 17 and tid_struct.tm_min > 25) or tid_struct.tm_hour > 17:
                return False
            if self.countryCode == 'SE' and tid_struct.tm_year == 2012:
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
        elif self.countryCode == 'US' or self.countryCode == 'CA':
            if tid_struct.tm_hour < 15 or (tid_struct.tm_hour == 15 and tid_struct.tm_min < 30):
                return False
            if tid_struct.tm_hour > 21:
                return False
            return True
        elif self.countryCode == 'DK':
            if tid_struct.tm_hour < 9:
                return False
            if tid_struct.tm_hour > 16:
                return False
            return True
        return False

    def build_plot_history(self, starttid, sluttid, mellanrum=360):
        plot_history = []
        pos = 0
        last = None
        oldvalue = self.historia[1].kurs
#        print "starttid: ", str(starttid), " sluttid: ", str(sluttid)
        for avslu in self.historia:
#            print "Avslut, tid: ", str(avslu.tid), " kurs: ", str(avslu.kurs), "volym: ", str(avslu.volym), "langd av historik: ", str(len(plot_history))
            if avslu.kurs <= 1 or (abs(avslu.kurs - oldvalue) / oldvalue) > 0.2 or not self.handelstid(avslu.tid): # 0 ska tas bort men finns pga gamal historik
                continue
            if (avslu.tid < starttid or last is None):
                last = avslu
                continue
            x_tid = starttid + pos * mellanrum
            if (avslu.tid > sluttid):
                while x_tid < sluttid:
                    if self.handelstid(x_tid):
                        plot_history.append(last.kurs)
                    pos += 1
                    x_tid = starttid + pos * mellanrum
                return plot_history
            while x_tid < avslu.tid:
                if self.handelstid(x_tid):
                    plot_history.append(last.kurs) 
                pos += 1
                x_tid = starttid + pos * mellanrum
            last = avslu
            oldvalue = avslu.kurs
#        pylab.plot(plot_history, 'k')
#        pylab.show()
        return plot_history

    def uppdatera_kalres(self, dep):
        cani = {}
        cani['caplevper'] = self.eval_perCaplvl
        cani['faktorandring'] = self.caplvlfaktor
        cani['mAeval'] = self.eval_perMA
        cani['nivaer'] = self.nivaer_opt
        cani['stoptid'] = self.stoptid
        cani['frambak'] = self.frambak
        if self.fastfakt == None:
            cani['fastfakt'] = 0.05
        else:
            cani['fastfakt'] = self.fastfakt
        tid = time.time()
        while not self.handelstid(tid):
            tid -= 5
        if not isinstance(self.kalibreringsresultat, list):
            self.kalibreringsresultat = []
            gamres = 0.1
        else:
            gamres = self.kalibreringsresultat[-1]['res']
        kurshist = self.build_plot_history(starttid = self.historia[0].tid, sluttid = time.time(), mellanrum = 360)
        resultat = self.vektorEMA_eval(dep, canidate = cani, kurshistoria = kurshist, mellanrum = 360)
        tid = time.time()
        if resultat > 1.0 or gamres > 1.0 or len(self.kalibreringsresultat) < 1:
            uppdat = {'tid':tid,'res':resultat}
            self.kalibreringsresultat.append(uppdat)
        return resultat

    def mAnow(self, superkanidat, tid = None):
        """anpassad for 0 min fordrojning"""
        self.spara_historik(turn_off=False)
        senastkurs = self.historia[-1].kurs
        ladddagar = 3
        if len(self.historia) < 50:
            ladddagar = 3
            self.ladda_historik(ladddagar)
            if len(self.historia) < 50:
                if tid == None:
                    print "Historia langd", len(self.historia), self.searchString, self.orderbookId
                self.ladda_historik(dagar=3)
                return None, None
        if senastkurs != self.historia[-1].kurs:
            print "1mAnow - Senast registrearde kuren andrades nar kurshistoria laddades, nogot ar fel for", self.searchString,"historiklangd",str(len(self.historia))
        if tid == None:
            tid_nu = time.time()
            self.mAfil = self.lista + '/' + self.orderbookId + '/' + 'berakningsinfo.p'
            slutplats = -1
        else:
            tid_nu = tid
            self.mAfil = 'provberakning' + '/' + self.orderbookId + 'provberakningsinfo.p'
            slutplats = self.tidssokning(tid, efter=False)
        decimal.getcontext().prec = 30
        if self.berakningsinfo == None:
            if os.path.exists(self.mAfil):
                self.berakningsinfo = cPickle.load(open(self.mAfil, 'rb'))
        if not 'slowmA' in self.berakningsinfo:
            self.berakningsinfo = {}
            oldtid = tid_nu - superkanidat['mAeval']
            if oldtid < self.historia[0].tid:
                ladddagar = superkanidat['mAeval'] / (8 * 3600)
                self.ladda_historik(dagar = ladddagar)
            kurshist = self.build_plot_history(oldtid, tid_nu, mellanrum = 360)
            if len(kurshist) < 100:
                print self.orderbookId,"    ", self.searchString, "len(kurshist):",len(kurshist)
                if ladddagar != 3 or self.historia[0].tid < tid_nu - 48 * 3600:
                    self.ladda_historik(dagar = 3)
                return None,None
            slowmA = sum(kurshist)/len(kurshist)
            fastmA = sum(kurshist[int(-len(kurshist)*superkanidat['fastfakt']):]) / int(len(kurshist)*superkanidat['fastfakt'])
            self.berakningsinfo['slowmA'] = slowmA
            self.berakningsinfo['fastmA'] = fastmA
            self.berakningsinfo['mAtid'] = tid_nu
            cPickle.dump(self.berakningsinfo, open(self.mAfil, 'wb'))
            if ladddagar != 3:
                self.ladda_historik(dagar =3)
            return slowmA, fastmA
        start = self.tidssokning(self.berakningsinfo['mAtid'], efter = False)
        oldtid = self.berakningsinfo['mAtid']
        slowmA = self.berakningsinfo['slowmA']
        fastmA = self.berakningsinfo['fastmA']
        slowtime = superkanidat['mAeval']
        fasttime = superkanidat['mAeval'] * superkanidat['fastfakt']
        if oldtid < self.historia[0].tid:
            ladddagar = superkanidat['mAeval'] / (8 * 3600)
            self.ladda_historik(dagar = ladddagar)
        for avslu in self.historia[start:slutplats]:
            if avslu.tid < self.berakningsinfo['mAtid']:
                continue
            else:
                avstand = avslu.tid - oldtid
                if avstand > 28800 and time.localtime(oldtid).tm_mday != time.localtime(avslu.tid).tm_mday:
                    oldtid = avslu.tid
                    continue
                if avstand > slowtime:
                    slowmA = fastmA = avslu.kurs
                else:
                    if avstand > fasttime:
                        fastmA = avslu.kurs
                        slowmA += decimal.Decimal(avslu.kurs - slowmA) * decimal.Decimal(avstand/float(slowtime))
                    else:
                        fastmA += decimal.Decimal(avslu.kurs - fastmA) * decimal.Decimal(avstand/float(fasttime))
                        slowmA += decimal.Decimal(avslu.kurs - slowmA) * decimal.Decimal(avstand/float(slowtime)) 
                oldtid = avslu.tid
        if time.localtime(oldtid).tm_mday != time.localtime(tid_nu).tm_mday:
            self.berakningsinfo['slowmA'] = slowmA
            self.berakningsinfo['fastmA'] = fastmA
            self.berakningsinfo['mAtid'] = tid_nu
            cPickle.dump(self.berakningsinfo, open(self.mAfil, 'wb'))
            if ladddagar != 2 or self.historia[0].tid < tid_nu - 48 * 3600:
                self.ladda_historik(dagar =2)
            return slowmA, fastmA
        avstand = tid_nu - oldtid
        if avstand > slowtime:
            slowmA = fastmA = self.historia[slutplats].kurs
        else:
            if avstand > fasttime:
                fastmA = self.historia[slutplats].kurs
                slowmA += decimal.Decimal(self.historia[slutplats].kurs - slowmA) * decimal.Decimal(avstand/float(slowtime))
            else:
                slowmA += decimal.Decimal(self.historia[slutplats].kurs - slowmA) * decimal.Decimal(avstand/float(slowtime))
                fastmA += decimal.Decimal(self.historia[slutplats].kurs - fastmA) * decimal.Decimal(avstand/float(fasttime))
        self.berakningsinfo['fastmA'] = fastmA
        self.berakningsinfo['slowmA'] = slowmA
        self.berakningsinfo['mAtid'] = tid_nu
        cPickle.dump(self.berakningsinfo, open(self.mAfil, 'wb'))
        if senastkurs != self.historia[-1].kurs:
            print "2mAnow - Senast registrearde kuren andrades nar kurshistoria laddades, nogot ar fel for", self.searchString,"historiklangd",str(len(self.historia))
        if ladddagar != 3 or self.historia[0].tid < tid_nu - 3* 24 * 3600:
            self.ladda_historik(dagar =3)
        return slowmA, fastmA

    def hitta_stoppniva(self, kurs, caplevles=None, under=True, n_nivaer = None, tid = None, faktorandring = None):
        if faktorandring == None:
            if self.caplvlfaktor != None:
                faktorandring = self.caplvlfaktor
            else:
                faktorandring = 0.98
        faktorandring = decimal.Decimal(faktorandring)
        if caplevles == None:
            if tid == None:
                tid = time.time()
            caplevles = self.createCapLevels(sistatid=tid)
        if n_nivaer == None:
            if self.nivaer_opt != None:
                n_nivaer = self.nivaer_opt
            else:
                n_nivaer = 10
        if n_nivaer > 40:
            nivaer = range(40)
        else:
            nivaer = range(int(n_nivaer))
        flest = 0
        flestniva = 0
        if under:
            niva = self.possible_kurs(kurs - decimal.Decimal('0.0001'), over = False)
            for x in nivaer:
                if x > 1 and niva in caplevles:
                    antal = caplevles[niva] * (faktorandring**x)
                    if antal > flest:
                        flest = antal
                        flestniva = niva
                niva = self.possible_kurs(niva - decimal.Decimal('0.0001'), over = False)
            stoppniva = self.possible_kurs(flestniva - decimal.Decimal('0.0001'), over = False)
        else: 
            niva = self.possible_kurs(kurs + decimal.Decimal('0.0001'), over=True)
            for x in nivaer:
                if niva in caplevles:
                    antal = caplevles[niva] * (faktorandring**x)
                    if antal > flest:
                        flest = antal
                        flestniva = niva
                niva = self.possible_kurs(niva + decimal.Decimal('0.0001'), over=True)
            stoppniva = self.possible_kurs(flestniva + decimal.Decimal('0.0001'), over=True)
        if flest == 0:
            stoppniva = niva
        return stoppniva
    
    def mA_vid(self,tid, mAlangd):
        if not self.handelstid(tid):
            tid_st = time.localtime(tid)
            if tid_st.tm_hour < 9:
                tid -= ((tid_st.tm_hour + 7) * 3600) + ((tid_st.tm_min - 30) * 60) + (tid_st.tm_sec)
            else:
                tid -= ((tid_st.tm_hour - 17) * 3600) + ((tid_st.tm_min - 30) * 60) + (tid_st.tm_sec)
        startplats = self.tidssokning(tid = tid - mAlangd, efter = False)
        slutplats = self.tidssokning(tid = tid, efter = True)
        mAtid = tid - mAlangd
        mA = float(self.historia[startplats].kurs)
        oldkurs = self.historia[startplats].kurs
        komp = False
        for avslu in self.historia[startplats -1:slutplats]:
            if avslu.tid < tid - mAlangd:
                oldkurs = avslu.kurs
                continue
            if avslu.tid > tid:
                mA += (float(oldkurs) / mAlangd - (mA /mAlangd))*(tid-mAtid)
                komp = True
                break
            avstand = avslu.tid - mAtid
            if avstand > 28800:
                if time.localtime(mAtid).tm_mday != time.localtime(avslu.tid).tm_mday:
                    mAtid = avslu.tid
                    continue
            if avstand > mAlangd:
                mA = avslu.kurs
            else:
                mA += (float(oldkurs) / mAlangd -(mA /mAlangd)) * avstand
            mAtid = avslu.tid
            oldkurs = avslu.kurs
        if komp == False:
            mA += (float(oldkurs) / mAlangd - (mA /mAlangd)) * (tid-mAtid)
        return decimal.Decimal(mA)
              
    def vektorEMA_eval(self, depa , canidate, kurshistoria, mellanrum = 360, plot = False):
        """Köper när fastEMA är högre än slowEMA och säljer vid tvärt om då frambak == 0, om frambak == 1
        gäller istället det omvända"""
        plot = False
        if plot:
            slowEMAvektor = []
            fastEMAvektor = []
            fig = plt.figure()
        starttid = self.historia[0].tid
        oldcapstart = starttid-canidate['caplevper']
        oldcapslut = starttid
        caplevels = self.createCapLevels(oldcapstart, oldcapslut)
        hist = range(1,len(kurshistoria))
        likvid = likvid2 = depa.grundvarde
        slowalpha = mellanrum / float(canidate['mAeval'])
        fastalpha = mellanrum / (canidate['mAeval'] * canidate['fastfakt'])
        startpos = canidate['mAeval'] / mellanrum
        faktorandring = canidate['faktorandring']
        handelskurs = stopniva = None
        vol = 0
        if len(kurshistoria) < 300:
            return decimal.Decimal('0.1')
        slowEMA = fastEMA = float(kurshistoria[0])
        k = 0
        for pos in hist:
            if (abs(kurshistoria[pos] - kurshistoria[pos-1]) / kurshistoria[pos]) > 0.2:
                continue 
            postid = starttid + (pos + k) * mellanrum
            if not self.handelstid(postid):
                tid_st = time.localtime(postid)
                if tid_st.tm_hour < 9:
                    k += (9 - tid_st.tm_hour) * 10 - int(tid_st.tm_min / 6)
                else:
                    k += 100 - ((tid_st.tm_hour - 9) * 10) - int(tid_st.tm_min / 6)
                postid = starttid + (pos + k) * mellanrum
            slowEMA = slowalpha * float(kurshistoria[pos]) + (1.0 - slowalpha) * slowEMA
            fastEMA = fastalpha * float(kurshistoria[pos]) + (1.0 - fastalpha) * fastEMA
            if plot:
                slowEMAvektor.append(slowEMA)
                fastEMAvektor.append(fastEMA)
            try:
                if pos > startpos and ((canidate['frambak'] == 0 and fastEMA > kurshistoria[pos] > slowEMA) or (canidate['frambak'] == 1 and fastEMA < kurshistoria[pos] < slowEMA)) and not vol > 0 and not (stopniva != None and stopniva >= kurshistoria[pos] > (0.995 * float(handelskurs))):
                    """koper garanterat"""
                    handelskurs = self.possible_kurs(kurshistoria[pos], over=True)
                    if vol != 0:
                        affarsvarde = vol * handelskurs
                        if postid - capslut > 9 * 3600:
                            likvid = likvid - depa.courtage(affarsvarde) - 200 + affarsvarde
                        else:
                            likvid = likvid - depa.courtage(affarsvarde) + affarsvarde
                        likvid2 = likvid2 + affarsvarde
                    vol = int(((likvid - depa.courtage(likvid)) - (likvid - depa.courtage(likvid)) % handelskurs) / handelskurs)
                    affarsvarde = vol * handelskurs
                    likvid = likvid- depa.courtage(affarsvarde) - affarsvarde
                    likvid2 = likvid2 - affarsvarde
                    capslut = postid
                    capstart = capslut - canidate['caplevper']
                    caplevels = self.updateCapLevels(caplevels, oldcapstart, oldcapslut, capstart, capslut)
                    oldcapstart = capstart
                    oldcapslut = capslut
                    stopniva = self.hitta_stoppniva(handelskurs, under=True, n_nivaer=canidate['nivaer'], caplevles=caplevels, faktorandring = faktorandring)
                    if plot:
                        plt.plot([pos], [handelskurs], 'g+')
                        plt.plot([pos, pos], [stopniva,handelskurs], 'g')
                        plt.plot([pos, pos + 200], [stopniva, stopniva], 'g')
#                        print "koper for:", str(handelskurs), "har nu", str(vol),"st", "likvid", str(likvid)
                elif pos > startpos and ((canidate['frambak'] == 0 and fastEMA < kurshistoria[pos] < slowEMA) or (canidate['frambak'] == 1 and fastEMA > kurshistoria[pos] > slowEMA)) and not vol < 0 and not (stopniva != None and  stopniva <= kurshistoria[pos] < 1.005*float(handelskurs)):
                    """saljer garanterat"""
                    handelskurs = self.possible_kurs(kurshistoria[pos], over=False)
                    if vol != 0:
                        affarsvarde = vol * handelskurs
                        likvid = likvid - depa.courtage(affarsvarde) + affarsvarde
                        likvid2 = likvid2 + affarsvarde
                    vol = - int(((likvid-depa.courtage(likvid)) - (likvid - depa.courtage(likvid)) % handelskurs) / handelskurs)
                    affarsvarde = vol * handelskurs
                    likvid = likvid - depa.courtage(affarsvarde) - affarsvarde
                    likvid2 = likvid2 - affarsvarde
                    capslut = postid
                    capstart = capslut - canidate['caplevper']
                    caplevels = self.updateCapLevels(caplevels, oldcapstart, oldcapslut, capstart, capslut)
                    oldcapstart = capstart
                    oldcapslut = capslut
                    stopniva = self.hitta_stoppniva(handelskurs, under=False, n_nivaer=canidate['nivaer'], caplevles=caplevels, faktorandring = faktorandring)
                    if plot:
                        plt.plot([pos], [handelskurs], 'r+')
                        plt.plot([pos, pos], [stopniva,handelskurs], 'r')
                        plt.plot([pos, pos + 200], [stopniva, stopniva], 'r')
#                        print "saljer for:", str(handelskurs), "har nu", str(vol),"st", "likvid", str(likvid)
            except IndexError:
                print "plot hisoriklangd: " + str(len(self.historia))
                print "forsoker lasa index: " + str(pos)
        forandring = (likvid + vol * kurshistoria[-1]) / depa.grundvarde
        forandring2 = (likvid2 + vol * kurshistoria[-1]) / depa.grundvarde
        if plot:
            plt.plot(kurshistoria, 'k')
            plt.plot(slowEMAvektor, 'b')
            plt.plot(fastEMAvektor, 'm')
            plt.title(self.searchString + " res: " + str(round(forandring,4)) + " res2: " + str(round(forandring2,4)))
            try:
                fig.savefig("kalibres/" + self.orderbookId + '.png', dpi = 200)
            except:
                plt.title(self.orderbookId + " res: " + str(round(forandring,4)) + " res2: " + str(round(forandring2,4)))
                try:
                    fig.savefig("kalibres/" + self.orderbookId + '.png',dpi = 200)
                except:
                    print "\n\n\n        searchstring "+ self.searchString + " ordid " + self.orderbookId + "\n\n\n"
            plt.close()
        return forandring
    
    def possible_kurs (self, kurs, over=False):
        if self.lista == 'LargeCap':
            if kurs < decimal.Decimal('0.5') and kurs > 0:
                if over: return (kurs - kurs % decimal.Decimal('0.0001') + decimal.Decimal('0.0001')).quantize(decimal.Decimal("0.0001"), decimal.ROUND_HALF_UP)
                return (kurs - kurs % decimal.Decimal('0.0001')).quantize(decimal.Decimal("0.0001"), decimal.ROUND_HALF_UP)
            if kurs < 1:	
                if over: return (kurs - kurs % decimal.Decimal('0.0005') + decimal.Decimal('0.0005')).quantize(decimal.Decimal("0.0001"), decimal.ROUND_HALF_UP)
                return (kurs - kurs % decimal.Decimal('0.0005')).quantize(decimal.Decimal("0.001"), decimal.ROUND_HALF_UP)
            if kurs < 5:	
                if over: return (kurs - kurs % decimal.Decimal('0.001') + decimal.Decimal('0.001')).quantize(decimal.Decimal("0.001"), decimal.ROUND_HALF_UP)
                return (kurs - kurs % decimal.Decimal('0.001')).quantize(decimal.Decimal("0.001"), decimal.ROUND_HALF_UP)
            if kurs < 10:	
                if over: return (kurs - kurs % decimal.Decimal('0.005') + decimal.Decimal('0.005')).quantize(decimal.Decimal("0.001"), decimal.ROUND_HALF_UP)
                return (kurs - kurs % decimal.Decimal('0.005')).quantize(decimal.Decimal("0.001"), decimal.ROUND_HALF_UP)
            if kurs < 50:	
                if over: return (kurs - kurs % decimal.Decimal('0.01') + decimal.Decimal('0.01')).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)
                return (kurs - kurs % decimal.Decimal('0.01')).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)
            if kurs < 100:	
                if over: return (kurs - kurs % decimal.Decimal('0.05') + decimal.Decimal('0.05')).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)
                return (kurs - kurs % decimal.Decimal('0.05')).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)
            if kurs < 500:	
                if over: return (kurs - kurs % decimal.Decimal('0.1') + decimal.Decimal('0.1')).quantize(decimal.Decimal("0.10"), decimal.ROUND_HALF_UP)
                return (kurs - kurs % decimal.Decimal('0.1')).quantize(decimal.Decimal("0.10"), decimal.ROUND_HALF_UP)
            if kurs < 1000:	
                if over: return (kurs - kurs % decimal.Decimal('0.5') + decimal.Decimal('0.5')).quantize(decimal.Decimal("0.10"), decimal.ROUND_HALF_UP)
                return (kurs - kurs % decimal.Decimal('0.5')).quantize(decimal.Decimal("0.10"), decimal.ROUND_HALF_UP)
            if kurs < 5000:	
                if over: return (kurs - kurs % 1 + 1).quantize(decimal.Decimal("1.00"), decimal.ROUND_HALF_UP)
                return (kurs - kurs % 1).quantize(decimal.Decimal("1.00"), decimal.ROUND_HALF_UP)
            if kurs < 10000:
                if over: return (kurs - kurs % 5 + 5).quantize(decimal.Decimal("1.00"), decimal.ROUND_HALF_UP)
                return (kurs - kurs % 5).quantize(decimal.Decimal("1.00"), decimal.ROUND_HALF_UP)
            if over: return (kurs - kurs % 10 + 10).quantize(decimal.Decimal("1.00"), decimal.ROUND_HALF_UP)
            return (kurs - kurs % 10).quantize(decimal.Decimal("1.00"), decimal.ROUND_HALF_UP)
        if kurs < 5:	
            if over: return (kurs - kurs % decimal.Decimal('0.01') + decimal.Decimal('0.01')).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)
            return (kurs - kurs % decimal.Decimal('0.01')).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)
        if kurs < 15:	
            if over: return (kurs - kurs % decimal.Decimal('0.05') + decimal.Decimal('0.05')).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)
            return (kurs - kurs % decimal.Decimal('0.05')).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)
        if kurs < 50:	
            if over: return (kurs - kurs % decimal.Decimal('0.1') + decimal.Decimal('0.1')).quantize(decimal.Decimal("0.10"), decimal.ROUND_HALF_UP)
            return (kurs - kurs % decimal.Decimal('0.1')).quantize(decimal.Decimal("0.10"), decimal.ROUND_HALF_UP)
        if kurs < 150:	
            if over: return (kurs - kurs % decimal.Decimal('0.25') + decimal.Decimal('0.25')).quantize(decimal.Decimal("0.10"), decimal.ROUND_HALF_UP)
            return (kurs - kurs % decimal.Decimal('0.25')).quantize(decimal.Decimal("0.10"), decimal.ROUND_HALF_UP)
        if kurs < 500:	
            if over: return (kurs - kurs % decimal.Decimal('0.50') + decimal.Decimal('0.50')).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)
            return (kurs - kurs % decimal.Decimal('0.50')).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)
        if kurs < 5000:	
            if over: return (kurs - kurs % 1 + 1).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)
            return (kurs - kurs % 1).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)
        if over: return (kurs - kurs % 5 + 5).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)
        return (kurs - kurs % 5).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)

    def spara_historik(self, turn_off=False):
        dagsavslut = None
        place = self.lista + '/' + self.orderbookId + '/'
        olddate = "start.p"
        if not os.path.exists(place):
            os.makedirs(place)
        if self.historia != None:
            for avslut in self.historia:
                date = time.strftime("%y%m%d.p", time.localtime(avslut.tid))
                if dagsavslut == None: 
                    dagsavslut = [avslut]
                    olddate = date
                    continue
                if date != olddate:
                    cPickle.dump(dagsavslut, open(place + olddate, 'wb'))
                    dagsavslut = [avslut]
                    olddate = date
                else:
                    dagsavslut.append(avslut)
        if dagsavslut != None and len(dagsavslut) > 1:
            cPickle.dump(dagsavslut, open(place + date, 'wb'))
        if turn_off:
            self.historia = None

    def ladda_historik(self, dagar=1, tid = time.time()):
        if dagar > 200:
            dagar = 200
        self.historia = [avslut.Avslut("00:00:00", -1, 0)]
        place = self.lista + '/' + self.orderbookId + '/'
        dagsavslut = []
        if not os.path.exists(place):
            return 0
        k = 0
        l = 0
        laddadedagar = 0
        que = []
        while l < dagar:
            wday = time.strftime("%w", time.localtime(tid - k))
            if wday == '6':
                k += 172800
            elif wday == '5':
                k += 86400
            else:
                l += 1
                date = time.strftime("%y%m%d.p", time.localtime(tid - k))
                if os.path.isfile(place + date):
                    try:
                        time.sleep(0.01)
                        dagsavslut = cPickle.load(open(place + date, 'rb'))
                        laddadedagar += 1
                        que.insert(0, dagsavslut)
                    except AttributeError:
                        print "AttributeError: ", self.orderbookId
                        print "Problem i ", place + date
                    except cPickle.BadPickleGet:
                        print "BadPickleGet: ", self.orderbookId
                        print "Problem i ", place + date
                    except EOFError:
                        print "EOFError: ", self.orderbookId
                        print "Problem i ", place + date
                    except cPickle.UnpickleableError:
                        print "UnpickleableError: ", self.orderbookId
                        print "Problem i ", place + date
                    except cPickle.UnpicklingError:
                        print "UnpicklingError: ", self.orderbookId
                        print "Problem i ", place + date
                    except ValueError:
                        print "ValueError: ", self.orderbookId
                        print "Problem i ", place + date
                k += 86400
        for dav in que:
            if len(self.historia) < 2:
                self.historia = dav
            else:
                self.historia.extend(dav)
        return laddadedagar                        

    def EA_Calibration (self, dep):
#        print "Ska göra en population"
        start = time.time()
        kalibreringsslut = start - 1209600
        pop = self.createPop(dep, popsize = 1, kalibslut = kalibreringsslut)
        kurshist = self.build_plot_history(self.historia[0].tid, sluttid = time.time(), mellanrum = 360)
#        self.vektorEMA_eval(dep, canidate = pop[0], kurshistoria = kurshist, mellanrum = 360, plot = True)
#        print self.searchString, "Ny population bäst",str(round(pop[0]['result'],4)),"tionde",str(round(pop[9]['result'],4)),"tretionde",str(round(pop[29]['result'],4))
#        print "bestmAeval",str(pop[0]['mAeval']),"fastfakt",str(pop[0]['fastfakt']), "bestniv", str(pop[0]['nivaer']),"caplev",str(pop[0]['caplevper']),"fak",pop[0]['faktorandring'] # ,"stoptid",str(pop[0]['stoptid'])
#        print self.searchString, "tidsuppskattning 1 kalibrationen är färdig ca", time.strftime("%H:%M, %d %b",time.localtime(start + (time.time()-start)*(float(114)/40))), "för",self.searchString
#        pop = self.evolve(pop, dep, popsize = 40, kalibslut = kalibreringsslut)
#        print self.searchString, "andra generationen bäst",str(round(pop[0]['result'],4)),"tionde",str(round(pop[9]['result'],4)),"tretionde",str(round(pop[29]['result'],4))
#        print "bestmAeval",str(pop[0]['mAeval']),"fastfakt",str(pop[0]['fastfakt']), "bestniv", str(pop[0]['nivaer']),"caplev",str(pop[0]['caplevper']),"fak",pop[0]['faktorandring'] # ,"stoptid",str(pop[0]['stoptid'])          
#        print self.searchString, "tidsuppskattning 2 kalibrationen är färdig ca", time.strftime("%H:%M, %d %b",time.localtime(start + (time.time()-start)*(float(114)/76))), "för",self.searchString
#        pop = self.evolve(pop, dep, popsize = 40, kalibslut = kalibreringsslut)
#        print self.searchString, "tredje generationen bäst",str(round(pop[0]['result'],4)),"tionde",str(round(pop[9]['result'],4)),"tretionde",str(round(pop[29]['result'],4))
#        print "bestmAeval",str(pop[0]['mAeval']),"fastfakt",str(pop[0]['fastfakt']), "bestniv", str(pop[0]['nivaer']),"caplev",str(pop[0]['caplevper']),"fak",pop[0]['faktorandring'] # ,"stoptid",str(pop[0]['stoptid'])
        self.vektorEMA_eval(dep, canidate = pop[0], kurshistoria = kurshist, mellanrum = 360, plot = True)
        self.eval_perCaplvl = pop[0]['caplevper']
        self.caplvlfaktor = pop[0]['faktorandring']
        self.eval_perMA = pop[0]['mAeval']
        self.nivaer_opt = pop[0]['nivaer']
#        self.stoptid = pop[0]['stoptid']
        self.fastfakt = pop[0]['fastfakt']
        self.frambak = pop[0]['frambak']
        if self.kalibreringshistoria == None:
            self.kalibreringshistoria = []
        tid_nu = time.time()
        kalibrering = {'tid':tid_nu,'cani':pop[0]}
        self.kalibreringshistoria.append(kalibrering)
        return pop[0]['result']
    
    def superuppdat(self,dep,superkanidat):
        self.ladda_historik(dagar = 30)
        if len(self.historia)< 2000:
            return 1
        maxi = int(self.historia[-1].tid - self.historia[10].tid)
        kurshist = self.build_plot_history(self.historia[0].tid, sluttid=time.time(), mellanrum=360)
        can = superkanidat
        can['nivaer'] = 5
        can['faktorandring'] = 0.94
        can['caplevper'] = int(maxi / 10)
        self.eval_perCaplvl = can['caplevper']
        self.caplvlfaktor = can['faktorandring']
        self.eval_perMA = can['mAeval']
        self.nivaer_opt = can['nivaer']
        self.fastfakt = can['fastfakt']
        self.frambak = can['frambak']
        res = self.vektorEMA_eval(dep, canidate = can, kurshistoria = kurshist, mellanrum = 360, plot = True)
        return res
  
    def evolve(self,pop, dep, popsize = 60, kalibslut = time.time()):
        matepop = pop[:int(popsize * 0.45)]
        nypop = pop
        kurshist = self.build_plot_history(self.historia[0].tid, sluttid = kalibslut, mellanrum = 360)
        for canidate in matepop:
            narmaste = []
            langst = 0
            for cani in pop:
                dist = self.canidateDist(canidate, cani)
                if len(narmaste) < 4:
                    if dist > langst:
                        langst = dist
                    succ = 0
                    for n in xrange(0,len(narmaste)):
                        if dist < narmaste[n]['d']:
                            succ = 1
                            narmaste.insert(n,{'d': dist, 'c':cani})
                            break
                    if succ == 0:
                        narmaste.append({'d': dist, 'c':cani})
                else:
                    if dist > langst:
                        continue
                    else:
                        for n in xrange(0,len(narmaste)):
                            if dist < narmaste[n]['d']:
                                narmaste.insert(n,{'d': dist, 'c':cani})
                                break
                        narmaste = narmaste[:5]
                        langst = narmaste[4]['d']
            best = None
            bestres = 0
            nast = None
            nastres = 0
            for distandcani in narmaste:
                vagtresultat = float(distandcani['c']['result']) * (1.0 + 1.0/ float(distandcani['c']['caplevper']))
                """vid lika resultat sorteras det forst pa lagst caplevper 
                sedan pa lagst antal nivaer"""
                if distandcani['c']['result'] > nastres or (distandcani['c']['result'] == nastres and distandcani['c']['nivaer'] < nast['nivaer']):
                    if distandcani['c']['result'] > bestres or (distandcani['c']['result'] == bestres and distandcani['c']['nivaer'] < best['nivaer']):
                        nast = best
                        nastres = bestres
                        bestres = vagtresultat
                        best = distandcani['c']
                    else:
                        nastres = vagtresultat
                        nast = distandcani['c']
            mates = [best, nast]
            for mate in mates:
                child = self.mateCanidate(canidate, mate)
                child['result'] = self.vektorEMA_eval(dep, child, kurshistoria = kurshist)
                nypop = self.popInsert(child, nypop)
#                if len(nypop) % 50 == 0:
#                    print "evolve nypop",len(nypop),"kanidater för", self.searchString
        return nypop
                 
    def mateCanidate(self, can1, can2):
        child = {}
        child['caplevper'] = int((can1['caplevper'] - float(can1['caplevper'] - can2['caplevper']) * random()) * uniform(0.95,1.05))
#        dniv = float(can1['nivaer'] - can2['nivaer']) * random()
#        nyniv = (can1['nivaer'] - dniv) * uniform(0.95,1.05)
        nyniv = 30
        child['nivaer'] = int(nyniv)
#        child['stoptid'] = int((can1['stoptid'] - (can1['stoptid'] - can2['stoptid'])* random()) * uniform(0.95,1.05))
        child['faktorandring'] = (can1['faktorandring'] - (can1['faktorandring'] - can2['faktorandring']) * random()) * uniform(0.99,1.01)
        child['mAeval']  = can1['mAeval']
        child['fastfakt'] = can1['fastfakt']
        child['frambak'] = can1['frambak']
#        child['mAeval']  = (can1['mAeval'] - (can1['mAeval'] - can2['mAeval'])*random())*uniform(0.95,1.05)
#        child['fastfakt'] = (can1['fastfakt'] - (can1['fastfakt'] - can2['fastfakt'])*random())*uniform(0.95,1.05) 
        return child
        
    def canidateDist(self, can1, can2):
        maxi = int(self.historia[-1].tid - self.historia[10].tid)
        dcap = (can1['caplevper'] - can2['caplevper'])/float(maxi / 10 -900)
        dniv = float(can1['nivaer'] - can2['nivaer'])/47
#        dsto = (can1['stoptid'] - can2['stoptid'])/float(maxi/10 - 900)
        dfak = (can1['faktorandring'] - can2['faktorandring'])/float(0.06)
#        dmAe = (can1['mAeval'] - can2['mAeval'])/float(maxi/10 - 14400)
#        dfmA = can1['fastfakt'] - can2['fastfakt']
#        return (dcap**2 + dniv**2 + dsto**2 + dfak**2 + dmAe**2 + dfmA**2)**(1/float(2))
        if can1['frambak'] == can2['frambak']:
            return (dcap**2 + dniv**2+dfak**2)**(1.0/2.0)
        else:
            return 5 + (dcap**2 + dniv**2+dfak**2)**(1.0/2.0)
    
    def createPop(self, dep, popsize = 60, kalibslut = time.time()):
        pop = None
        savecaplev = self.eval_perCaplvl
        savefaktor = self.caplvlfaktor
        start = time.time()
        kurshist = self.build_plot_history(self.historia[0].tid, sluttid = kalibslut, mellanrum = 360)
        for i in xrange(popsize):
#            if i % 10 == 0:
#                print "har gjort",i,"kanidater"
            canidate = self.randomCanidate()
            canidate['result'] = self.vektorEMA_eval(dep, canidate, kurshistoria = kurshist)
            if i % 20 == 0 and i > 19:
                print "tidsuppskattning populationen är färdig", time.strftime("%H:%M, %d %b",time.localtime(start + (time.time()-start)*(float(popsize)/(i+1)))), "för",self.searchString, "har gjort", i, "kanidater"
            pop = self.popInsert(canidate, pop)
        self.eval_perCaplvl = savecaplev
        self.caplvlfaktor = savefaktor
        return pop
                        
    def randomCanidate(self):
        maxi = int(self.historia[-1].tid - self.historia[10].tid)
        canidate = {}
        canidate['caplevper'] = int(maxi / 10)
        canidate['nivaer'] = 5
#        canidate['nivaer'] = randrange(3,50,1)
#        canidate['stoptid'] = randrange(900, int(maxi / 10),10)
        canidate['faktorandring'] = 0.94
#        canidate['mAeval'] = randrange(14400,int(maxi / 10),600)
#        canidate['fastfakt'] = random()
        canidate['mAeval'] = 82911
        canidate['fastfakt'] = 0.02144
        canidate['frambak'] = 1
        return canidate
    
    def popInsert(self, canidate, pop):
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
#                    print "hi",higher,"low",lower,"pos",pos,"hivalue",pop[pos]['result'], "innanvalue", pop[pos-1]['result'],"res",res
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
    
    def timeaddition(self,time1, time2):
        timesum = time1 + time2
        if time.localtime(timesum).tm_mday == time.localtime(time1).tm_mday:
            if self.handelstid(timesum):
                return timesum
            if self.handelstid(timesum + 55800):
                return timesum + 55800
            return timesum + 228600
        
        
        
def datumstrangtilltid(strang):
    if isinstance(strang, str) and len(strang) == 6:
        tid_str = time.strptime(strang, "%y%m%d")
        tid = time.mktime(tid_str)
        return tid
    else:
        return None
        
def tidtilldatumstrang(tid):
    return time.strftime("%y%m%d" , time.localtime(tid))
    
