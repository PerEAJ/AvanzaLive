import cookiehant, decimal, urllib, time, os.path, cPickle, avslut, aktie

class Depa:
    tillgangligt_for_kop = None
    tillgangligt_for_kop_valuta = None
    portfolj = {}
    handlingsbart_kap = decimal.Decimal('200000.00')
    kontotyp = None
    kontonummer = None
    totaltvarde = None
    saldo = None
    minicourtage = None
    rorligtcourtage = None
    grundvarde = decimal.Decimal('50000')
    kopsaljbalans = 0
    username = None
    password = None
    forsakrinstagare = None
    handlade_aktier = {}
    tot_kap = decimal.Decimal('200000.00')
    courtagelista = None
    blankavgift = decimal.Decimal('0.00')
    totalvinst = decimal.Decimal('0')
    totaltplatser = int(0)
    handelslogfil = "handelslog.p"
    portfoljfil = 'portfolj.p'
    handeldataplats = 'handelsdata/'
    superkanidat = None
    cookh = None

    def __init__(self, forsakringstagare, username, password, online = True):
        if online:
            self.cookh = cookiehant.Cookiehanterare()
            self.username = username.encode('base64')
            self.password  = password.encode('base64')
            self.forsakrinstagare = forsakringstagare
            self.read_from_depa(forsakringstagare, username, password)
        else:
            self.handelslogfil = 'berakningslog.p'
            self.portfoljfil  = 'berakningsportfolj.p'
            self.handeldataplats = 'beraknigshandelsdata/'

    def read_from_depa (self, forsakringstagare = None, user = None, passw = None, inloggad = False):
        """Laser in Saldo och tillgangligt for kop"""
        if not inloggad and (user == None or passw == None):
            user = self.username.decode('base64')
            passw = self.password.decode('base64')
        if forsakringstagare == None:
            forsakringstagare = self.forsakrinstagare
        time.sleep(0.1)
        if inloggad:
            theurl = 'https://www.avanza.se/aza/depa/depa.jsp'
            self.cookh.open_page(theurl = theurl)
        else:
            self.cookh.open_page(user, passw)
        time.sleep(0.1)
        hand = self.cookh.handle
        line  = 'apan'
        while line != '':
            line = hand.readline()
            if forsakringstagare in line:
                self.kontotyp = hand.readline().replace(' - ','')[:-5]
                if (self.kontotyp == "Bas Platina"):
                    self.minicourtage = decimal.Decimal('39.0')
                    self.rorligtcourtage = decimal.Decimal('0.0012')
                if (self.kontotyp == "Bas Guld"):
                    self.minicourtage = decimal.Decimal('39.0')
                    self.rorligtcourtage = decimal.Decimal('0.0013')
                if (self.kontotyp == "Bas Silver"):
                    self.minicourtage = decimal.Decimal('39.0')
                    self.rorligtcourtage = decimal.Decimal('0.0014')
                if (self.kontotyp == "Bas Brons"):
                    self.minicourtage = decimal.Decimal('39.0')
                    self.rorligtcourtage = decimal.Decimal('0.0015')
                if (self.kontotyp == "Premium Brons"):
                    self.minicourtage = decimal.Decimal('99.0')
                    self.rorligtcourtage = decimal.Decimal('0.00085')
                if (self.kontotyp == "Premium Silver"):
                    self.minicourtage = decimal.Decimal('99.0')
                    self.rorligtcourtage = decimal.Decimal('0.0008')
                if (self.kontotyp == "Premium Guld"):
                    self.minicourtage = decimal.Decimal('99.0')
                    self.rorligtcourtage = decimal.Decimal('0.00075')
                if (self.kontotyp == "Premium Platina"):
                    self.minicourtage = decimal.Decimal('99.0')
                    self.rorligtcourtage = decimal.Decimal('0.00055')
                if (self.kontotyp == "PRO 1"):
                    self.minicourtage = decimal.Decimal('49.0')
                    self.rorligtcourtage = decimal.Decimal('0.00035')
                if (self.kontotyp == "PRO 2"):
                    self.minicourtage = decimal.Decimal('39.0')
                    self.rorligtcourtage = decimal.Decimal('0.0003')
                if (self.kontotyp == "PRO 3"):
                    self.minicourtage = decimal.Decimal('29.0')
                    self.rorligtcourtage = decimal.Decimal('0.0002')
                if (self.kontotyp == "PRO 4"):
                    self.minicourtage = decimal.Decimal('29.0')
                    self.rorligtcourtage = decimal.Decimal('0.00015')
                print "kontotyp",self.kontotyp
                break
        while line != '':
            line = hand.readline()
            if "<form name='form1' action='/aza/depa/depa.jsp'>" in line:
                try:
                    int(line[68:75])
                    self.kontonummer = line[68:75]
                except:
                    line = hand.readline()
                    if "selected" in line:
                        self.kontonummer = line[15:22]
                print "Kontonummer", self.kontonummer
                break
        while line != '':
            line = hand.readline()
            if "Totalt v&auml;rde:" in line:
                hand.readline()
                self.totaltvarde = decimal.Decimal(hand.readline()[:-22].replace(',','.').replace(' ',''))
                print "Totalt varde", self.totaltvarde
#                print "vardeforandring", float(self.totaltvarde) / #Hårdkodat startvärde kan läggas in här
                break
        while line != '':
            line = hand.readline()
            if "Saldo" in line:
                hand.readline()
                self.tot_kap = self.saldo = decimal.Decimal(hand.readline().replace(',','.').replace(' ',''))
                print "Saldo", self.tot_kap
                break
        while line != '':
            line = hand.readline()
            if "Tillg&auml;ngligt f&ouml;r k&ouml;p:" in line:
                hand.readline()
                tillgangligt_for_kop_str = hand.readline().replace(',','.').replace(' ','')
                self.tillgangligt_for_kop = decimal.Decimal(tillgangligt_for_kop_str[:-9])
                self.tillgangligt_for_kop_valuta = tillgangligt_for_kop_str[-9:-6]
                print "Tillgangligt for kop", self.tillgangligt_for_kop, self.tillgangligt_for_kop_valuta
                break
        self.read_aktier(hand)

    def read_aktier (self, hand = None):
        if hand == None:
            user = self.username.decode('base64')
            passw = self.password.decode('base64')
            self.cookh.open_page(user, passw)
            hand = self.cookh.handle
        line = hand.readline()
        portfolj = {}
        while line != '':
            line = hand.readline()
            pos1 = line.find("aktie.jsp?orderbookId=")
            if  pos1 != -1:
                idslut = line.find('\"',pos1)
                orderId = line[pos1+22:idslut]
                pos2 = line.find("<nobr>")
                pos3 = line.find("</nobr>",pos2 + 6)
                volstring = line[pos2+6:pos3]
                delchar = volstring.strip('1234567890')
                vol = int(volstring.translate(None,delchar))
                portfolj[orderId] = vol
        print "Ska nu skriva ut aktier i portfolj"
        if len(portfolj) > 0:
            self.portfolj = portfolj
        else:
            print """\nKunde inte lasa in aktier i portfolj\n"""
        for ordId in portfolj:
            print "orderID",ordId,"Antal",str(portfolj[ordId])
        
    def kopsaljbalansuppdat(self):
        balans = 0
        for aktId in self.portfolj:
            volym = self.portfolj[aktId]
            if volym > 0:
                balans += 1
            elif volym < 0:
                balans -= 1
            else:
                del self.portfolj[aktId]
        self.kopsaljbalans = balans
#        print "kopsaljbalans:", balans
        return balans
        
    def handla_aktie_riktigt(self, vp, volym, kurs, user = None, passw = None):
        if volym > 0:
            buyorsell = 'buy'
        else:
            buyorsell = 'sell'
            volym = - volym
        if user == None or passw == None:
            user = self.username.decode('base64')
            passw = self.password.decode('base64')
        theurl = "https://www.avanza.se/aza/login/login.jsp"
        self.cookh.open_page(user, passw, theurl)
        """Tar forst bort gamla ordrar"""
        order = 'account=' + self.kontonummer + '&transitionId=81&toggleClosings=false&toggleOrderDepth=false&toggleAdvanced=false&commit=true&currencyRate=&popped=false'
        theurl = "https://www.avanza.se/aza/order/aktie/kopsalj.jsp"
        req = self.cookh.Request(theurl, order, self.cookh.txheaders)
        handle = self.cookh.urlopen(req)
        if vp.market == None:
            market = 'AZAM'
        else:
            market = vp.market
        condition = ''
        priceMultiplier = '1.0'
        contractSize = '1.0'
        preFill = 'false'
        popped = 'false'
        if vp.currency == 'SEK':
            currencyRate = '1.0'
        if vp.countryCode == None:
            vp.countryCode = "SE"
        datum = time.strftime("%Y-%m-%d", time.localtime())
        order = urllib.urlencode({'advanced':'true'})+ '&' + urllib.urlencode({'account': self.kontonummer})+ '&' + urllib.urlencode({'countryCode':vp.countryCode})+ '&' + urllib.urlencode({'searchString':vp.searchString})+ '&' + urllib.urlencode({'orderbookId':vp.orderbookId})+ '&' + urllib.urlencode({'market':market})+ '&' +urllib.urlencode({'volume':str(int(volym))})+ '&' + urllib.urlencode({'price':str(kurs)})+ '&' +urllib.urlencode({'validDate':datum})+ '&' + urllib.urlencode({'condition':condition})+ '&' +urllib.urlencode({'intendenOrderType':buyorsell})+ '&' +urllib.urlencode({'toggleClosings':'false'})+ '&' + urllib.urlencode({'toggleOrderDepth':'false'})+ '&' +urllib.urlencode({'toggleAdvanced':'false'})+ '&' + urllib.urlencode({'transitionId':'12'})+ '&' +urllib.urlencode({'jspTemplate':'states/s.jsp'})+ '&' + urllib.urlencode({'priceMultiplier':priceMultiplier})+ '&' +urllib.urlencode({'marketCode':market})+ '&' + urllib.urlencode({'currency':vp.currency})+ '&' +urllib.urlencode({'currencyRate':currencyRate})+ '&' + urllib.urlencode({'contractSize':contractSize})+ '&' +urllib.urlencode({'preFill':preFill})+ '&' + urllib.urlencode({'popped':popped})
        """Forsta utsandningen"""
#        theurl = "https://www.avanza.se/aza/order/aktie/kopsalj.jsp"
        req = self.cookh.Request(theurl, order, self.cookh.txheaders)
        handle = self.cookh.urlopen(req)
        theurl = handle.geturl()
        order = urllib.urlencode({'advanced':'true'})+ '&' + urllib.urlencode({'account': self.kontonummer})+ '&' + urllib.urlencode({'orderbookId':vp.orderbookId})+ '&' + urllib.urlencode({'market':market})+ '&' + urllib.urlencode({'volume':str(int(volym))+'.0'})+ '&' + urllib.urlencode({'price':str(round(kurs,50))})+ '&' + urllib.urlencode({ 'openVolume':'0.0'})+ '&' + urllib.urlencode({'validDate':datum})+ '&' + urllib.urlencode({'condition':condition})+ '&' + urllib.urlencode({'orderType':buyorsell})+ '&' + urllib.urlencode({'intendenOrderType':buyorsell})+ '&' + urllib.urlencode({'toggleClosings':'false'})+ '&' + urllib.urlencode({'toggleOrderDepth':'false'})+ '&' + urllib.urlencode({'toggleAdvanced':'false'})+ '&' + urllib.urlencode({'searchString':vp.searchString})+ '&' + urllib.urlencode({'transitionId':'21'})+ '&' + urllib.urlencode({'commit':'true'})+ '&' + urllib.urlencode({'contractSize':contractSize})+ '&' + urllib.urlencode({'market':market})+ '&' + urllib.urlencode({'currency':vp.currency})+ '&' + urllib.urlencode({'currencyRate':currencyRate})+ '&' + urllib.urlencode({'countryCode':vp.countryCode})+ '&' + urllib.urlencode({'orderType':buyorsell})+ '&' + urllib.urlencode({'priceMultiplier':priceMultiplier})+ '&' + urllib.urlencode({'popped':popped})
        """Bekraftelsen"""
        req = self.cookh.Request(theurl, order, self.cookh.txheaders)
        handle = self.cookh.urlopen(req)
        time.sleep(2)
        self.read_from_depa(inloggad = True)
                     
    def handla_aktie_log(self, vp, volym, samstkurs, user = None, passw = None):
        if volym > 0:
            buyorsell = 'buy'
        else:
            buyorsell = 'sell'
        tid_nu = time.time()
        if hasattr(vp, 'omxid') and vp.omxid != 'apan' and vp.omxid != 'katten':
            cookh2 = cookiehant.Cookiehanterare()
            cookh2.open_page(theurl = 'http://www.nasdaqomxnordic.com/nordic/Nordic.aspx/SignIn')
            url = 'http://www.nasdaqomxnordic.com/omxlinkproxy/omxlinkproxy.asmx?proxyTarget=prod&SubSystem=Prices&Action=GetInstrument&Exception=false&cache=skip&json=2&callback=jQuery17108075247211721699_1331151327759&Instrument=' + vp.omxid +'&inst.e=1&inst.an=t,fnm&pd.a=3&ts=0&_=1331151333160%20HTTP/1.1'
            hand = cookh2.urlopen(url)
            line = hand.readline()
#            print line
            succ = 0
            pos = 0
            pos3 = 0
            delvol = 0
            kurs = samstkurs
#            print "senast registreade avsultet", time.strftime("%H:%M:%S", time.localtime(vp.historia[-1].tid))
            while succ < 7 and vp.historia[-1].tid > tid_nu - 1800:
                succ += 1
                if volym < 0:
                    pos = pos3 + line[pos3:].find('b=')
                    pos2 = pos + line[pos:].find('bv=')
                    pos3 = pos2 + line[pos2:].find('am=')
                    bidvol = line[pos2 + 4:pos3 - 2]
                    try:
                        bidvol = int(bidvol)
                    except:
                        print "kunde inte omvandla",bidvol,"till int1"
                        return decimal.Decimal('-1')
                    if bidvol + delvol > -volym:
                        handelskurs = line[pos +3:pos2 -2]
                        try:
                            kurs = decimal.Decimal(handelskurs)
                        except:
                            print "kunde inte omvandla",handelskurs,"till decimal.Decimal"
                        if kurs < samstkurs:
                            print "for doliga bud for att salja, bidprice", kurs, "samst", samstkurs
                            return decimal.Decimal('-1')
                        break
                    else:
                        delvol += bidvol
                else:
                    pos = pos3 + line[pos3:].find('a=')
                    pos2 = pos + line[pos:].find('av=')
                    pos3 = pos2 + line[pos2:].find('l=')
                    askvol = line[pos2 + 4:pos3 - 2]
                    try:
                        askvol = int(askvol)
                    except:
                        print "kunde inte omvandla",askvol,"till int2"
                        return decimal.Decimal('-1')
                    if askvol + delvol > volym:
                        handelskurs = line[pos +3:pos2 -2]
                        try:
                            kurs = decimal.Decimal(handelskurs)
                        except:
                            print "kunde inte omvandla",handelskurs,"till decimal.Decimal"
                        if kurs > samstkurs:
                            print "for dyrt att kopa, askprice", kurs, "samst", samstkurs
                            return decimal.Decimal('-1')
                        break
                    else:
                        delvol += askvol
            if succ > 6:
                print "finns inte tillrakligt med aktier i orderdjupet"
                return decimal.Decimal('-2')
        varde = kurs*volym
        court = self.courtage(varde)
        self.tot_kap -= (varde + court)
        self.tot_kap = self.tot_kap.quantize(decimal.Decimal('.01'))
        handelskostnad = court
        
        place = self.handeldataplats
        if not os.path.exists(place):
            os.makedirs(place)
        if vp.handelsfil == None:
            vp.handelsfil = place + vp.orderbookId + '.p'
        tid = time.strftime("%H:%M:%S", time.localtime())
        avslu = avslut.Avslut(tid, kurs, volym)
        if vp.orderbookId in self.portfolj:
            nyvol = self.portfolj[vp.orderbookId] + volym
        else:
            nyvol = volym
        if vp.handelsdata == None and not os.path.exists(vp.handelsfil):
            vp.handelsdata = {}
            vp.handelsdata['handelshistoria'] = [avslu]
            vp.handelsdata['resultat'] = decimal.Decimal('0') - handelskostnad
        else:
            if vp.handelsdata == None and os.path.exists(vp.handelsfil):
                vp.handelsdata = cPickle.load(open(vp.handelsfil, 'rb'))
            vp.handelsdata['handelshistoria'].append(avslu)
            if vp.handelsdata['nuvol'] < 0 and volym >= -vp.handelsdata['nuvol']:
                if vp.handelsdata['handelshistoria'][-2].tid < time.time() - 36000:
                    """Har haft aktier blankade over natt, 199 SEK i administrationsavgift"""
                    self.tot_kap -= decimal.Decimal('199')
                    handelskostnad += decimal.Decimal('199')
            if abs(vp.handelsdata['nuvol'] + volym) < abs(vp.handelsdata['nuvol']) + abs(volym):
                vardeforandring = kurs - vp.handelsdata['oldhandelskurs']
                if (vp.handelsdata['nuvol'] < 0 and nyvol >= 0) or (vp.handelsdata['nuvol'] > 0 and nyvol <= 0):
                    vp.handelsdata['resultat'] += vardeforandring * vp.handelsdata['nuvol'] - handelskostnad
                else:
                    vp.handelsdata['resultat'] += vardeforandring * - volym - handelskostnad
                vp.handelsdata['resultat'] = decimal.Decimal(vp.handelsdata['resultat']).quantize(decimal.Decimal('.01'))
            else:
                vp.handelsdata['resultat'] -= handelskostnad
        vp.handelsdata['nuvol'] = nyvol
        vp.handelsdata['oldhandelskurs'] = kurs
        vp.oldhandelskurs = kurs
        datumstrang = aktie.tidtilldatumstrang(tid_nu)
        if self.courtagelista == None:
            self.courtagelista = [{'datum':datumstrang, 'courtage': court, 'antal':1}]
        elif datumstrang == self.courtagelista[-1]['datum']:
            self.courtagelista[-1]['courtage'] += court
            self.courtagelista[-1]['antal'] += 1
        else:
            self.courtagelista.append({'datum':datumstrang,'courtage':court, 'antal':1})
        self.blankavgift += handelskostnad - court
        cPickle.dump(vp.handelsdata, open(vp.handelsfil, 'wb'))
        if not vp.orderbookId in self.portfolj:
            self.portfolj[vp.orderbookId] = volym
        else:
            self.portfolj[vp.orderbookId] += volym
            if self.portfolj[vp.orderbookId] == 0:
                del self.portfolj[vp.orderbookId]
        self.kopsaljbalansuppdat()
        self.handla_aktie_riktigt(vp, volym, kurs, user, passw)
        if volym < 0:
            volym = - volym
        logstrang = ladda_objekt(self.handelslogfil)
        if logstrang == None:
            logstrang = ""
        handelse = "handel " + time.strftime("%H:%M:%S %y, %m, %d ", time.localtime())+ "id " + vp.orderbookId +' '+ vp.searchString.ljust(24) + ' ' + buyorsell.ljust(5) + str(volym).ljust(6) + "for " + str(kurs).ljust(7) + "samstk. " + str(round(samstkurs,2)).ljust(7) + "nyvol " + str(nyvol).ljust(6)+ "i kassan " + str(self.tot_kap).ljust(11) + "tot res. f. vp. " + str(vp.handelsdata['resultat'])
        vp.handelsdata = None
        logstrang = logstrang, handelse
        print handelse
        spara_objekt(logstrang, self.handelslogfil)
        self.spara_portfolj()
        return kurs
    
    def courtage(self, totalkostnad):
        rorligt = decimal.Decimal(abs(totalkostnad) * self.rorligtcourtage)
        if rorligt > self.minicourtage:
            return rorligt.quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_UP)
        else:
            return self.minicourtage
    
    def bevaka(self, vp):
        """Framvand koper vid fastEMA hogre an slowEMA och tvart om"""
        if self.handlade_aktier == None:
            self.uppdatera_handlade_aktier()
        if not (vp.orderbookId in self.handlade_aktier or vp.orderbookId in self.portfolj):
            return False
        tid_nu = time.time()
        if self.superkanidat == None or self.superkanidat['kalibtid'] < tid_nu - 777600:
            superfil = 'SUPERresultat.p'
            if os.path.isfile(superfil):
                self.superkanidat = ladda_objekt(superfil)
                if not hasattr(self.superkanidat, 'kalibtid'):
                    self.superkanidat['kalibtid'] = 1344888903.038604
            else:
                self.superkanidat = {}
                self.superkanidat['fastfakt'] = 0.02144
                self.superkanidat['mAeval'] = 82911
                self.superkanidat['frambak'] = 1
                self.superkanidat['kalibtid'] = 1344888903.038604
        slowmA, fastmA = vp.mAnow(superkanidat = self.superkanidat)
        if slowmA == None or fastmA == None:
#            print "mA kunde inte beraknas for", vp.searchString, vp.orderbookId
            return False
        kursnu = vp.historia[-1].kurs
        if vp.orderbookId in self.portfolj:
            nuvol = self.portfolj[vp.orderbookId]
        else:
            nuvol = 0
        handelsvolym = 0
        if vp.mAfil == None:
            vp.mAfil = vp.lista + '/' + vp.orderbookId + '/' + 'berakningsinfo.p'
        if vp.berakningsinfo == None:
            if os.path.exists(vp.mAfil):
                vp.berakningsinfo = cPickle.load(open(vp.mAfil, 'rb'))
            else:
                vp.berakningsinfo = {}
        if not 'stopniva' in vp.berakningsinfo:
            if vp.orderbookId in self.portfolj:
                if self.portfolj[vp.orderbookId] > 0:
                    vp.berakningsinfo['stopniva'] = vp.hitta_stoppniva(kurs=kursnu,under = True)
                else:
                    vp.berakningsinfo['stopniva'] = vp.hitta_stoppniva(kurs=kursnu,under = False)
                cPickle.dump(vp.berakningsinfo, open(vp.mAfil, 'wb'))
        elif not vp.orderbookId in self.portfolj:
            del vp.berakningsinfo['stopniva']
        oldhandelskurs = float(kursnu)*0.98
        if 'stopniva' in vp.berakningsinfo and (not hasattr(vp, 'oldhandelskurs') or ( vp.oldhandelskurs == None)):
            vp.handelsfil = self.handeldataplats + vp.orderbookId + '.p'
            if os.path.exists(vp.handelsfil):
                vp.handelsdata = cPickle.load(open(vp.handelsfil, 'rb'))
                oldhandelskurs = vp.oldhandelskurs = vp.handelsdata['oldhandelskurs']
        elif 'stopniva' in vp.berakningsinfo:
            oldhandelskurs = float(vp.oldhandelskurs)
        storst_strang = ''
        if kursnu > slowmA > fastmA:
            storst_strang =  "KURSNU > slowmA > fastmA"
        elif slowmA > kursnu > fastmA:
            storst_strang =  "slowmA > KURSNU > fastmA"
        elif slowmA > fastmA > kursnu:
            storst_strang = "slowmA > fastmA > KURSNU"
        elif kursnu < slowmA < fastmA:
            storst_strang =  "fastmA > slowmA > KURSNU"
        elif slowmA < kursnu < fastmA:
            storst_strang =  "fastmA > KURSNU > slowmA"
        elif slowmA < fastmA < kursnu:
            storst_strang =  "KURSNU > fastmA > slowmA"
        if vp.orderbookId in self.portfolj:
            print "    "+ vp.searchString.ljust(35) + vp.orderbookId.ljust(9) + str(kursnu).rjust(10) + str(vp.berakningsinfo['stopniva']).rjust(10) + storst_strang.rjust(27) +str(oldhandelskurs).rjust(12) + str(self.portfolj[vp.orderbookId]).rjust(10)
        else:
            print "    "+ vp.searchString.ljust(35) + vp.orderbookId.ljust(9) + str(kursnu).rjust(10) + "saknas".rjust(10) + storst_strang.rjust(27)

        insats = self.grundvarde
        oldstopniv = None
        if ((vp.frambak == 0 and fastmA > kursnu > slowmA) or (vp.frambak == 1 and fastmA < kursnu < slowmA) or (vp.frambak==2 and kursnu > fastmA > slowmA)) and not nuvol > 0 and not ('stopniva' in vp.berakningsinfo and vp.berakningsinfo['stopniva'] >= kursnu > 0.995*float(oldhandelskurs)):
            """Ska kopa"""
            if vp.orderbookId in self.portfolj:
                stopniv = vp.hitta_stoppniva(vp.possible_kurs(kursnu, over = True), under = True)
                if vp.orderbookId in self.handlade_aktier and vp.sakerhetskrav != None and self.kopsaljbalans < 2:
                    nyvol = int((insats - insats % kursnu)/kursnu)
                    handelsvolym =  nyvol - nuvol
                else:
                    handelsvolym = - nuvol
            elif vp.orderbookId in self.handlade_aktier and len(self.portfolj) < self.totaltplatser:# and not self.kopsaljbalans > 4:
                stopniv = vp.hitta_stoppniva(vp.possible_kurs(kursnu, over = True), under = True)
                handelsvolym = int((insats - insats % kursnu)/kursnu)
            if handelsvolym != 0:
                if self.tot_kap < handelsvolym*kursnu:
                    handelsvolym = -nuvol
                    if self.tot_kap < handelsvolym*kursnu:
                        print "Kapitalbrist kan ej kopa tillbaka blankade aktier, nagot allvarligt ar fel1"
                        return False
                if 'stopniva' in vp.berakningsinfo:
                    oldstopniv = vp.berakningsinfo['stopniva']
                vp.berakningsinfo['stopniva'] = stopniv
                if vp.frambak == 1:
                    handelskurs = self.handla_aktie_log(vp, volym = handelsvolym, samstkurs = slowmA)
                else:
                    handelskurs = self.handla_aktie_log(vp, volym = handelsvolym, samstkurs = fastmA)
                if handelskurs == decimal.Decimal('-1') and oldstopniv != None:
                    vp.berakningsinfo['stopniva'] = oldstopniv
#                    """andring for ej blankning, nu endast med 9493781"""
        elif ((vp.frambak == 0 and fastmA < kursnu < slowmA) or (vp.frambak == 1 and fastmA > kursnu > slowmA) or (vp.frambak==2 and kursnu < fastmA < slowmA)) and nuvol > 0 and not ('stopniva' in vp.berakningsinfo and vp.berakningsinfo['stopniva'] <= kursnu < 1.005*float(oldhandelskurs)):
            if self.kontonummer == '9493781':
                if vp.orderbookId in self.handlade_aktier and self.kopsaljbalans > -2 and len(self.portfolj) < self.totaltplatser:
                    nyvol = -int((insats - insats % kursnu)/kursnu)
                else:
                    nyvol = 0
            else:
                nyvol = 0
            handelsvolym = nyvol - nuvol
            if handelsvolym != 0:
                if 'stopniva' in vp.berakningsinfo:
                    oldstopniv = vp.berakningsinfo['stopniva']
                vp.berakningsinfo['stopniva'] = vp.hitta_stoppniva(vp.possible_kurs(kursnu, over = False), under = False)
                if vp.frambak == 1:
                    handelskurs = self.handla_aktie_log(vp, volym = handelsvolym, samstkurs = slowmA)
                else:
                    handelskurs = self.handla_aktie_log(vp, volym = handelsvolym, samstkurs = fastmA)
                if handelskurs == decimal.Decimal('-1') and oldstopniv != None:
                    vp.berakningsinfo['stopniva'] = oldstopniv
        if handelsvolym != 0:
            cPickle.dump(vp.berakningsinfo, open(vp.mAfil, 'wb'))
            return True
        else:
            return False
    
    def uppdatera_handlade_aktier(self):
        orderbookId_listfil = "orderlista.p"
        orderbookId_lista = ladda_objekt(orderbookId_listfil)
        if orderbookId_lista == None:
            return
        if self.totaltvarde != None:
            antal = int(self.totaltvarde / (decimal.Decimal('1.01')*self.grundvarde))
        else:
            antal = int(self.handlingsbart_kap / (decimal.Decimal('1.01')*self.grundvarde))
        self.totaltplatser = antal - antal % 2
        antal *= 2
        handlade_aktier = {}
        samst = 10e10
        samstId = None
        tid_nu = time.time()
        stopmarginal = 7 * 24 * 3600
#        print "Uppdaterar handlade aktier, antal platser:",antal
        for ordid in orderbookId_lista:
            if os.path.isfile('LargeCap/' + ordid + '.p'):
                VP = cPickle.load( open('LargeCap/' + ordid + '.p' ,'rb') )
                if isinstance(VP.kalibreringsresultat,list):
                    kalres = VP.kalibreringsresultat[-1]['res']
                else:
                    continue
                VP.ladda_historik(dagar = 7)
                dagsomsatt = len(VP.historia)
#                print VP.searchString, "kalres", kalres, "ordid", VP.orderbookId
                if kalres == None or kalres < 0.8 or VP.sakerhetskrav == None:
                    continue
                if VP.handlas_exkl_utd != None and isinstance(VP.handlas_exkl_utd, float) and ((VP.handlas_exkl_utd - stopmarginal < tid_nu and VP.handlas_exkl_utd > tid_nu) or (VP.handlas_exkl_utd + stopmarginal > tid_nu and VP.handlas_exkl_utd < tid_nu)):
                    continue
                if VP.intro_datum != None and isinstance(VP.intro_datum, float) and VP.intro_datum > tid_nu - 80 * 24 * 3600:
                    continue
                if dagsomsatt < 1000:
                    continue
                if VP.handelsfil == None:
                    handelsfil = self.handeldataplats + VP.orderbookId + '.p'
                if os.path.exists(handelsfil):
                    handelsdata = cPickle.load(open(handelsfil, 'rb'))
                    if 'handelshistoria' in handelsdata and len(handelsdata['handelshistoria']) > 0 and handelsdata['handelshistoria'][-1].tid > tid_nu - 86400:
                        continue
                if len(handlade_aktier) < antal:
#                    print "lade till",VP.orderbookId.ljust(8), VP.searchString.ljust(23), "kalibreringsresultat", str(round(kalres,4))
                    handlade_aktier[ordid] = dagsomsatt
                    if dagsomsatt < samst:
                        samst = dagsomsatt
                        samstId = ordid
                elif dagsomsatt > samst:
#                    print "Tar bort", samstId
                    del handlade_aktier[samstId]
#                    print "lagger till", VP.orderbookId.ljust(8), VP.searchString.ljust(23), "kalibreringsres.", str(round(kalres,4))
                    handlade_aktier[ordid] = dagsomsatt
                    samst = 10e10
                    for Id in handlade_aktier:
                        if handlade_aktier[Id] < samst:
                            samst = handlade_aktier[Id]
                            samstId = Id
        self.handlade_aktier = handlade_aktier
    
    def uppdatera_handlade_aktier_historikt(self, tid = time.time()):
        orderbookId_listfil = "orderlista.p"
        orderbookId_lista = ladda_objekt(orderbookId_listfil)
        if orderbookId_lista == None:
            return
        if self.totaltvarde != None:
            antal = int(self.totaltvarde / (decimal.Decimal('1.01')*self.grundvarde))
        else:
            antal = int(self.handlingsbart_kap / (decimal.Decimal('1.01')*self.grundvarde))
        self.totaltplatser = antal
        handlade_aktier = {}
        samst = 10e10
        samstId = None
        tid_nu = time.time()
        stopmarginal = 7 * 24 * 3600
        print "Uppdaterar handlade aktier, antal platser:",antal
        for ordid in orderbookId_lista:
            if os.path.isfile('LargeCap/' + ordid + '.p'):
                VP = cPickle.load( open('LargeCap/' + ordid + '.p' ,'rb') )
                if isinstance(VP.kalibreringsresultat,list) and VP.kalibreringsresultat[1]['tid'] < tid:
                    for i in xrange(len(VP.kalibreringsresultat)):
                        kalres = VP.kalibreringsresultat[-i]['res']
                        if VP.kalibreringsresultat[-i]['tid'] < tid:
                            break
                else:
                    continue
                if isinstance(VP.kalibreringshistoria,list) and VP.kalibreringshistoria[1]['tid'] < tid:
                    for i in xrange(len(VP.kalibreringshistoria)):
                        stoptid = VP.kalibreringshistoria[-i]['cani']['stoptid']
                        nivaer_opt = VP.kalibreringshistoria[-i]['cani']['nivaer']
                        if VP.kalibreringshistoria[-i]['tid'] < tid:
                            break
                else:
                    continue
                VP.ladda_historik(dagar = 2, tid = tid)
                dagsomsatt = len(VP.historia)
#                print VP.searchString, "kalres", kalres, "ordid", VP.orderbookId
                if kalres == None or kalres < 1.01 or VP.stoptid == None or stoptid < 1800 or nivaer_opt < 5:
                    continue
                if VP.handlas_exkl_utd != None and isinstance(VP.handlas_exkl_utd, float) and ((VP.handlas_exkl_utd - stopmarginal < tid and VP.handlas_exkl_utd > tid) or (VP.handlas_exkl_utd + stopmarginal > tid and VP.handlas_exkl_utd < tid)):
                    continue
                if VP.intro_datum != None and isinstance(VP.intro_datum, float) and VP.intro_datum > tid - 80 * 24 * 3600:
                    continue
                if len(VP.historia) < 200:
                    continue
                if VP.handelsfil == None:
                    handelsfil = self.handeldataplats + VP.orderbookId + '.p'
                if os.path.exists(handelsfil):
                    handelsdata = cPickle.load(open(handelsfil, 'rb'))
                    kill = False
                    if 'handelshistoria' in handelsdata:
                        for i in xrange(len(handelsdata['handelshistoria'])):
                            if handelsdata['handelshistoria'][-i].tid > tid:
                                continue
                            else:
                                if handelsdata['handelshistoria'][-i].tid > tid - 86400:
                                    kill = True
                                    break
                        if kill:
                            continue
                if len(handlade_aktier) < antal:
                    print "lade till",VP.orderbookId, VP.searchString
                    handlade_aktier[ordid] = dagsomsatt
                    if dagsomsatt < samst:
                        samst = dagsomsatt
                        samstId = ordid
                elif dagsomsatt > samst:
                    print "Tar bort", samstId
                    del handlade_aktier[samstId]
                    print "lagger till", VP.orderbookId, VP.searchString
                    handlade_aktier[ordid] = dagsomsatt
                    samst = 10e10
                    for Id in handlade_aktier:
                        if handlade_aktier[Id] < samst:
                            samst = handlade_aktier[Id]
                            samstId = Id
        self.handlade_aktier = handlade_aktier

    def uppdatera_handlade_aktierreserv(self):
        orderbookId_listfil = "orderlista.p"
        orderbookId_lista = ladda_objekt(orderbookId_listfil)
        if orderbookId_lista == None:
            return
        if self.totaltvarde != None:
            antal = int(self.totaltvarde / (decimal.Decimal('1.01')*self.grundvarde))
        else:
            antal = int(self.handlingsbart_kap / (decimal.Decimal('1.01')*self.grundvarde))
        self.totaltplatser = antal
        handlade_aktier = {}
        samst = 10
        samstId = None
        tid_nu = time.time()
        stopmarginal = 7 * 24 * 3600
        print "Uppdaterar handlade aktier, antal platser:",antal
        for ordid in orderbookId_lista:
            if os.path.isfile('LargeCap/' + ordid + '.p'):
                VP = cPickle.load( open('LargeCap/' + ordid + '.p' ,'rb') )
                if isinstance(VP.kalibreringsresultat,list):
                    kalres = VP.kalibreringsresultat[-1]['res']
                else:
                    continue
#                print VP.searchString, "kalres", kalres, "ordid", VP.orderbookId
                if kalres == None or kalres < 0.92 or kalres > 1.02 or VP.stoptid == None or VP.stoptid < 1800 or VP.nivaer_opt < 5:
                    continue
                if VP.handlas_exkl_utd != None and isinstance(VP.handlas_exkl_utd, float) and ((VP.handlas_exkl_utd - stopmarginal < tid_nu and VP.handlas_exkl_utd > tid_nu) or (VP.handlas_exkl_utd + stopmarginal > tid_nu and VP.handlas_exkl_utd < tid_nu)):
                    continue
                if VP.intro_datum != None and isinstance(VP.intro_datum, float) and VP.intro_datum > tid_nu - 80 * 24 * 3600:
                    continue
                VP.ladda_historik(2)
                if len(VP.historia) < 200:
                    continue
#                if VP.handelsfil == None:
#                    handelsfil = 'handelsdata/' + VP.orderbookId + '.p'
#                if os.path.exists(handelsfil):
#                    handelsdata = cPickle.load(open(handelsfil, 'rb'))
#                    if 'handelshistoria' in handelsdata and len(handelsdata['handelshistoria']) > 0 and handelsdata['handelshistoria'][-1].tid > tid_nu - 86400:
#                        continue
                if len(handlade_aktier) < antal:
                    print "lade till",VP.orderbookId, VP.searchString
                    handlade_aktier[ordid] = kalres
                    if kalres < samst:
                        samst = kalres
                        samstId = ordid
                elif kalres > samst:
                    print "Tar bort", samstId
                    del handlade_aktier[samstId]
                    print "lagger till", VP.orderbookId, VP.searchString
                    handlade_aktier[ordid] = kalres
                    samst = 10
                    for Id in handlade_aktier:
                        if handlade_aktier[Id] < samst:
                            samst = handlade_aktier[Id]
                            samstId = Id
        self.handlade_aktier = handlade_aktier
                                 
    def ledigt_kap(self):
        return self.tot_kap
    
    def spara_portfolj(self):
        spara_objekt(self.portfolj, self.portfoljfil)
        place = "depakopior/portfoljkopior/"
        if not os.path.exists(place):
            os.makedirs(place)
        datumkopia = place + time.strftime("%y%m%d", time.localtime()) + self.portfoljfil
        spara_objekt(self.portfolj, datumkopia)

    def ladda_portfolj(self):   
        self.portfolj = ladda_objekt(self.portfoljfil)
        if self.portfolj == None:
            self.portfolj = {}
        
    def uppdatera_courtage(self):
        antal = 0
        totcourtage = decimal.Decimal('0')
        tidsgrans = time.time() - 2592000
        while aktie.datumstrangtilltid( self.courtagelista[0]['datum']) < tidsgrans:
            del self.courtagelista[0]
        for courtagedag in self.courtagelista:
            antal += courtagedag['antal']
            totcourtage += courtagedag['courtage']
        if antal > 517:
            self.minicourtage = decimal.Decimal('29')
            self.rorligtcourtage = decimal.Decimal('0.00015')
        elif antal > 344:
            self.minicourtage = decimal.Decimal('29')
            self.rorligtcourtage = decimal.Decimal('0.0002')
        elif antal > 192:
            self.minicourtage = decimal.Decimal('39')
            self.rorligtcourtage = decimal.Decimal('0.0003')
        elif antal > 81:
            self.minicourtage = decimal.Decimal('49')
            self.rorligtcourtage = decimal.Decimal('0.00034')
        elif self.totaltvarde > 1000000 or totcourtage > 1000:
            if self.grundvarde > 82500:
                self.minicourtage = decimal.Decimal('99')
                self.rorligtcourtage = decimal.Decimal('0.00055')
            else:
                self.minicourtage = decimal.Decimal('39')
                self.rorligtcourtage = decimal.Decimal('0.0012')
        elif self.totaltvarde > 250000 or totcourtage > 250:
            if self.grundvarde > 82500:
                self.minicourtage = decimal.Decimal('99')
                self.rorligtcourtage = decimal.Decimal('0.00075')
            else:
                self.minicourtage = decimal.Decimal('39')
                self.rorligtcourtage = decimal.Decimal('0.0013')
        elif self.totaltvarde > 100000 or totcourt > 100:
            if self.grundvarde > 82500:
                self.minicourtage = decimal.Decimal('99')
                self.rorligtcourtage = decimal.Decimal('0.0008')
            else:
                self.minicourtage = decimal.Decimal('39')
                self.rorligtcourtage = decimal.Decimal('0.0014')
        else:
            if self.grundvarde > 82500:
                self.minicourtage = decimal.Decimal('99')
                self.rorligtcourtage = decimal.Decimal('0.00085')
            else:
                self.minicourtage = decimal.Decimal('39')
                self.rorligtcourtage = decimal.Decimal('0.0015')
            
def ladda_objekt(filename):
    if os.path.exists(filename):
        return cPickle.load(open(filename, 'rb'))
    else:
        return None

def spara_objekt(objekt, filename):
    cPickle.dump(objekt ,open( filename , 'wb'))
    