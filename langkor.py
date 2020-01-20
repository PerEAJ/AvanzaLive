# -*- coding: utf-8 -*-
from avanzInterface import autostart
from time import sleep
import multiprocessing
    
def langkor(string, turnoffchild):
    laddaner, laddanerpipe = autostart(turnoff = False)
    sleep(10)
    while True:
        if turnoffchild.poll() and turnoffchild.recv() == 'off':
            laddanerpipe.send("Turn off")
#            kalibrerapipe.send("Turn off")
            print "Väntar i trettio sekunder på att den ska stänga av"
            laddaner.join(30)
            if laddaner.is_alive():
                laddaner.terminate()
#            kalibrera.join(120)
#            if kalibrera.is_alive():
#                kalibrera.terminate()
            print "Avstängda"
            break
        if not laddaner.is_alive():
            laddaner, laddanerpipe = autostart(turnoff = False)
        sleep(5)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    turnoffparrent, turnoff_c = multiprocessing.Pipe()
    p = multiprocessing.Process(target=langkor, args=('apa',turnoff_c))
    p.start()
    while True:
        print """
            Skriv "off" och tryck Enter för att stänga av programmet.
            """
        command = raw_input("Vad vill du göra? ")
        if command == 'off':
            print "Ska nu stänga av"
            turnoffparrent.send('off')
            p.join(240)
            if p.is_alive():
                p.terminate()
            break
    exit()