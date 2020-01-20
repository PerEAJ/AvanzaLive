# -*- coding: utf-8 -*-
import urllib, urllib2, os.path, time

class Cookiehanterare:


    COOKIEFILE='cookies.lwp'
    # the path and filename to save your cookies in
    login_data = None
    cj = None
    ClientCookie = None
    cookielib = None
    urlopen = None
    Request = None
    opener = None
    handle = None
    txheaders = None

    def __init__(self):
        self.declare()


    # Let's see if cookielib is available
    def declare (self):
        """Declares urlopen, Request and opener"""

        try:
            import cookielib
        except ImportError:
            # If importing cookielib fails
            # let's try ClientCookie
            try:
                import ClientCookie
            except ImportError:
                # ClientCookie isn't available either
                self.urlopen = urllib2.urlopen
                self.Request = urllib2.Request
            else:
                # imported ClientCookie
                self.urlopen = ClientCookie.urlopen
                self.Request = ClientCookie.Request
                self.cj = ClientCookie.LWPCookieJar()
        
        else:
            # importing cookielib worked
            self.urlopen = urllib2.urlopen
            self.Request = urllib2.Request
            self.cj = cookielib.LWPCookieJar()
            # This is a subclass of FileCookieJar
            # that has useful load and save methods
    
        if self.cj is not None:
        # we successfully imported
        # one of the two cookie handling modules
        
            if os.path.isfile(self.COOKIEFILE):
                # if we have a cookie file already saved
                # then load the cookies into the Cookie Jar
                self.cj.load(self.COOKIEFILE)
        
            # Now we need to get our Cookie Jar
            # installed in the opener;
            # for fetching URLs
            if cookielib is not None:
                # if we use cookielib
                # then we get the HTTPCookieProcessor
                # and install the opener in urllib2
                self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
                urllib2.install_opener(self.opener)
        
            else:
                # if we use ClientCookie
                # then we get the HTTPCookieProcessor
                # and install the opener in ClientCookie
                self.opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(self.cj))
                ClientCookie.install_opener(self.opener)
    

    def open_page(self, username = None, password = None, theurl = 'https://www.avanza.se/aza/login/login.jsp?from=7&msgId=16', inloggad = False):
    
        if not inloggad and (username != None and password != None) and theurl[:21] == 'https://www.avanza.se':
            self.login_data = urllib.urlencode({'redirect' :'' ,'username' : username, 'password' : password, 'from' : '7'})
#            self.login_data = urllib.urlencode({'username' : 'kusin', 'password' : 'apan'})
        elif theurl == 'http://www.nasdaqomxnordic.com/nordic/Nordic.aspx/SignIn':
            "Du måste först lägga in användarnamn och lösenord till http://www.nasdaqomxnordic.com/ för att den ska kunna hämta orderdjupet"
            omxAnvandarnamn = 
            omxLosenord = 
            self.login_data = 'EmailUsername=' + omxAnvandarnamn + '&Password=' + omxLosenord + '&Remember=true&FromURL=http%3A%2F%2Fwww.nasdaqomxnordic.com%2Fnordic%2FNordic.aspx'
        # if we were making a POST type request,
        # we could encode a dictionary of values here,
        # using urllib.urlencode(somedict)
        
        self.txheaders =  {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
        # fake a user agent, some websites (like google) don't like automated exploration
        succes = False
        oldtime = None
        oldreson = None
        while(succes == False):
            try:
                if not inloggad:
                    req = self.Request(theurl, self.login_data, self.txheaders)
                else:
                    req = self.Request(theurl, self.txheaders)
                # create a request object
            
                self.handle = self.urlopen(req)
                succes = True
                # and open it to return a handle on the url
            
            except IOError, e:
                if oldtime == None or (hasattr(e,'code') and oldreson != e.code) or (not hasattr(e,'code') and (hasattr(e,'reason') and oldreson != e.reason)):
                    print 'We failed to open "%s".' % theurl
                    if hasattr(e, 'code'):
                        print 'We failed with error code - %s.' % e.code
                        oldreson = e.code
                    elif hasattr(e, 'reason'):
                        print "The error object has the following 'reason' attribute :"
                        print e.reason
                        print "This usually means the server doesn't exist,"
                        print "is down, or we don't have an internet connection."
                        oldreson = e.reason
                    oldtime = time.time()
                    print "Sleeps 15 min before trying again"
                else:
                    print "Sleeps 15 min before trying again, sleep began",time.strftime("%H%M%S",time.localtime(oldtime))
                time.sleep(900)
                
        self.cj.save(self.COOKIEFILE) 
        #else:
            # print 'Here are the headers of the page :'
            # print handle.info()
            # print handle.geturl()
            # read_from_depa(handle)
            # handle.read() returns the page
            # handle.geturl() returns the true url of the page fetched
            # (in case urlopen has followed any redirects, which it sometimes does)
    
    def printandsavecookies (self):    
        print
        if self.cj is None:
            print "We don't have a cookie library available - sorry."
            print "I can't show you any cookies."
        else:
            print 'These are the cookies we have received so far :'
            for index, cookie in enumerate(self.cj):
                print index, '  :  ', cookie
            self.cj.save(self.COOKIEFILE)      
    
