from epics import caput, caget, cainfo
from PyQt5 import QtCore, QtGui
from time import localtime
import numpy as np
import os
import sys
import subprocess
from Amp import *
from ExposTimer import *

class MyCAEpics (QtCore.QThread):

    update_position = QtCore.pyqtSignal (int, float)
    set_status = QtCore.pyqtSignal(str, int)

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.x_start = 0.
        self.y_start = 0.
        self.y_nsteps = 10
        self.x_nsteps = 10
        self.x_inc = 0.01
        self.y_inc = 0.01
        self.acquire_flag = False ;
        self.abort_flag = False
        # amptek
        self.amptek = Amp()
        status = self.amptek.connect()
        if status == False  :
            print 'could not open spectrometer'
            mbox = QtGui.QMessageBox()
            mbox.setWindowTitle("GridScan Problem : Amptek")
            mbox.setIcon(QtGui.QMessageBox.Critical)
            mbox.setText("Problem with Amptek USB communication")
            mbox.setInformativeText("Check spectrometer")
            mbox.exec_()
            #sys.exit(app.exit(-1))
        
        self.single_take = False 
        self.scanfile = ""
        self.mytimer = ExposTimer()
        self.expos_secs = 0


    def abort_scan (self) :
        self.abort_flag = True

    def set_data (self, ydat) :
        self.amptek.set_data(ydat)

    def set_params (self, x0, xrange, xsteps, y0, yrange, ysteps) :
        self.x_start = x0 - xrange
        self.x_inc = xrange * 2 / xsteps
        self.x_nsteps = xsteps

        self.y_start = y0 - yrange
        self.y_inc = yrange * 2 / ysteps
        self.y_nsteps = ysteps

    def set_expos_timer (self, nsecs) :
        self.expos_secs = 300

    def get_position (self, mot_num) :
        if (mot_num == 0) :
            return caget('Dera:m3.VAL')
        if (mot_num == 1) :
            return caget('Dera:m2.VAL')



    def move_motor (self, mot_num, loc) :
        if (mot_num == 0) :
            caput('Dera:m3.VAL',loc)
        if (mot_num == 1) :
            caput ('Dera:m2.VAL', loc)

    def set_acquisition_params (self, ofil, atime) :
        self.outpref = ofil
        self.acqtime = atime

    def set_acquisition_time (self,  atime) :
        self.acqtime = atime

    def get_acq_time (self) :
        isec = self.amptek.get_elapsed_secs()
        return isec

    def take_single (self) :
        acqstring = "Acquiring single scan"
        self.set_status.emit(acqstring, 1)
        self.amptek.set_acquisition_time(self.acqtime)
        self.acquire_flag = True;
        self.single_take = True
        self.start()
        


    def run (self) :
        self.abort_flag = False
        if (self.single_take == False) :
            xval = caget ('Dera:m3.VAL')
            count = 0
            yval = caget ('Dera:m2.VAL')
            ltime = localtime()
            timestring = "%4d%02d%02d%02d%02d"%(ltime.tm_year,ltime.tm_mon, ltime.tm_mday,
                ltime.tm_hour, ltime.tm_min)
            posfile = open ("%s_position.txt"%(self.outpref), 'w')
            # start the instrument exposure time timer....
            if (self.expos_secs > 0) :
                self.mytimer.set_expos_time (self.expos_secs)
                self.mytimer.start()
        else :
            self.y_nsteps = 1
            self.x_nsteps = 1
        for i in range (self.y_nsteps) :
            if (self.abort_flag == True):
                break
            yval = self.y_start + i * self.y_inc
            #caput ('Dera:m2.VAL', yval)
            if (self.single_take == False) :
                self.move_motor (1, yval)
                self.update_position.emit (1, yval)
                QtCore.QThread.sleep (2)
            iy = int (yval * 1000)
            for j in range (self.x_nsteps) :
                if (self.abort_flag== True) :
                    break
                if (self.single_take == False) :
                    # get the amount of exposure time remaining on the instrument
                    cur_etime = self.mytimer.get_current_etime ()
                    # need to pause for acquisition
                    if (self.acqtime >= cur_etime) :
                        self.mytimer.stopclock()
                        mmb = QtGui.QMessageBox.warning (self,'pyAmptek Exposure', 'Re-start exposure', QtGui.QMessageBox.O)
                        self.mytimer.start()



                    xval = self.x_start + j * self.x_inc
                    outstr = '%d\t%f\t%f\r\n'%(count,xval,yval)
                    posfile.write (outstr)
                    #caput ('Dera:m3.VAL', xval)
                    self.update_position.emit (0, xval)
                    QtCore.QThread.sleep (2)
                    self.move_motor (0, xval)
                    ix = int (xval * 1000)
                # now do the scan
                #filstring = "%s_%s_%05d_%05d.mca"%(self.outpref, timestring, ix, iy)
                    filstring = "%s_%04d.mca"%(self.outpref,count)
                    count = count + 1
                #cmdstring = "C:/Users/przem/workdir/X123/build-X123_cmd-Desktop_Qt_5_9_0_MinGW_32bit-Release/release/X123.exe"
                #fullstring = "%s %s %d"%(cmdstring, filstring, self.acqtime)
                    self.acquire_flag = True ;
                    acqstring = "Acquiring %05d %05d" % (ix, iy)
                    print "Scanning... file will be : ", filstring
                    self.set_status.emit(acqstring, 1)
                    self.amptek.set_spectrum_file (filstring)
                if (self.single_take == False) :
    					self.scanfile = filstring
                self.amptek.set_acquisition_time (self.acqtime)
                self.amptek.start_acquisition()
                
                #os.system(fullstring)
                #news = [cmdstring, filstring, "%d"%(self.acqtime)]
                #p = subprocess.Popen (news)
                #p.wait()


        self.set_status.emit("Ready", 0)
        self.acquire_flag = False
        if (self.single_take == False) :
            posfile.close()
        self.singleTake = False 