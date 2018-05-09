from PyQt5 import QtCore, QtGui
import time
import numpy as np


class ExposTimer(QtCore.QThread):

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.expos_time = 60
        self.start_time = 0
        self.cur_time = 0.
        print 'in init'


    def set_expos_time (self, secs) :
        self.expos_time = secs
        print "in expos time"

    def get_current_etime (self) :
        return (self.cur_time)

    def run(self):
        print "thread called"
        start_time = time.time()
        print start_time
        self.cur_time = 0.
        while (self.cur_time < self.expos_time-1) :
            print self.cur_time
            self.cur_time = time.time() - start_time
            time.sleep (1)

        print 'exiting'


et = ExposTimer ()
et.set_expos_time (20)
et.start()


