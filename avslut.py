import time

class Avslut:
    volym = None
    kurs = None
    tid = None

    def __init__(self, tid, kurs, volym):
        wday = time.strftime("%w", time.localtime())
        if wday == '0':
            datestring = time.strftime("%y, %m, %d ", time.localtime(time.time() - 172800))
        elif wday == '6':
            datestring = time.strftime("%y, %m, %d ", time.localtime(time.time()-86400))
        else:
            datestring = time.strftime("%y, %m, %d ", time.localtime())
        dateandtime = datestring + str(tid)
        self.tid = time.mktime(time.strptime(dateandtime, "%y, %m, %d %H:%M:%S"))
        self.kurs = kurs
        self.volym = volym
