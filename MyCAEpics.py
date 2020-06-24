from epics import caput, caget, cainfo
from BrukerClient import *
from PyQt5 import QtCore, QtGui
from time import localtime
import numpy as np
import os
import sys
import subprocess
from Amp import *
#from ExposTimer import *

class MyCAEpics (QtCore.QThread):

    update_position = QtCore.pyqtSignal(int, float)
    set_status = QtCore.pyqtSignal(str, int)
    prep_xrf = QtCore.pyqtSignal()

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.gridFlag = True
        self.x_start = 0.
        self.y_start = 0.
        self.y_nsteps = 10
        self.x_nsteps = 10
        self.x_inc = 0.01
        self.y_inc = 0.01
        self.prog_fraction = 0.
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
        #self.mytimer = ExposTimer()
        #self.expos_secs = 0


    def abort_scan (self) :
        self.abort_flag = True

    def set_data (self, ydat) :
        self.amptek.set_data(ydat)

    def set_bruker_client (self, bc) :
        self.bclient = bc

    def set_listscan (self, coordlist) :
        self.gridFlag = False
        self.scanpos_list = coordlist

    def set_params (self, x0, xrange, xsteps, y0, yrange, ysteps) :
        self.x_start = x0 - xrange
        self.x_inc = xrange * 2 / xsteps
        self.x_nsteps = xsteps

        self.y_start = y0 - yrange
        self.y_inc = yrange * 2 / ysteps
        self.y_nsteps = ysteps
        self.gridFlag = True

    def set_expos_timer (self, nsecs) :
        self.expos_secs = 300

    def get_position (self, mot_num) :
        if (mot_num == 0) :
            return caget('Dera:m1.VAL')
        if (mot_num == 1) :
            return caget('Dera:m2.VAL')
        if (mot_num == 2) :
            return caget('Dera:m3.VAL')


    # add "2" motor move
    # changed motor numbers x,y,z is 1,2,3 was 3,2,1
    def move_motor (self, mot_num, loc) :
        if (mot_num == 0) :
            caput('Dera:m1.VAL',loc)
        if (mot_num == 1) :
            caput ('Dera:m2.VAL', loc)
        if (mot_num == 2) :
            caput ('Dera:m3.VAL', loc)

    def set_acquisition_params (self, ofil, atime) :
        self.outpref = ofil
        self.acqtime = atime

    def set_acquisition_time (self,  atime) :
        self.acqtime = atime

    def get_acq_time (self) :
        isec = self.amptek.get_elapsed_secs()
        return isec

    def get_prog_fraction (self) :
        return self.prog_fraction
    
    def get_cur_expos_time (self) :
        isec = self.amptek.get_elapsed_secs()
        return isec

    def take_single (self) :
        acqstring = "Acquiring single scan"
        self.set_status.emit(acqstring, 1)
        self.amptek.set_acquisition_time(self.acqtime)
        self.acquire_flag = True
        self.single_take = True
        self.gridFlag = True
        self.start()
        


    def run (self) :
        count = 0
        print "Opening the shutter"
        self.bclient.open_shutter()
        print "Finished opening the shutter"
        self.abort_flag = False

        # XRF LIST SCAN - with positions in the scanpos_list
        # if working from listflag
        if (self.gridFlag == False) :
            self.acquire_flag = True;
            xval = caget('Dera:m1.VAL')
            count = 0
            yval = caget('Dera:m2.VAL')
            zval = caget('Dera:m3.VAL')
            ltime = localtime()
            timestring = "%4d%02d%02d%02d%02d" % (ltime.tm_year, ltime.tm_mon, ltime.tm_mday,
                                                  ltime.tm_hour, ltime.tm_min)
            posfile = open("%s_position.txt" % (self.outpref), 'w')
            npos = len(self.scanpos_list)
            for i in range (npos) :
                self.prog_fraction = float(i)/float(npos)
                xval = self.scanpos_list[i][0]
                yval = self.scanpos_list[i][1]
                zval = self.scanpos_list[i][2]

                # prepare by doing the xrf_prep
                self.prep_xrf.emit()
                QtCore.QThread.sleep(2)

                # move the x, y, z motors
                self.move_motor(1,yval)
                self.update_position.emit(1, yval)

                self.move_motor(0,xval)
                self.update_position.emit(0, xval)

                self.move_motor(2, zval)
                self.update_position.emit(2, zval)

                if (self.abort_flag== True) :
                    break
                outstr = '%d\t%f\t%f\t%f\r\n' % (i, xval, yval, zval)
                posfile.write(outstr)
                filstring = "%s_%04d.mca" % (self.outpref, i)
                self.acquire_flag = True;
                acqstring = "Acquiring %05d" % (i)
                print "Scanning... file will be : ", filstring
                self.set_status.emit(acqstring, 1)
                self.amptek.set_spectrum_file(filstring)
                self.amptek.set_acquisition_time(self.acqtime)
                self.amptek.start_acquisition()

            self.bclient.close_shutter()
            self.set_status.emit("Ready", 0)
            self.acquire_flag = False
            posfile.close()
            self.prog_fraction = 0
            return


        #if a gridscan or single scan
        # In The if - set up for grid scan
        if (self.single_take == False) :
            xval = caget ('Dera:m1.VAL')
            count = 0
            yval = caget ('Dera:m2.VAL')
            ltime = localtime()
            timestring = "%4d%02d%02d%02d%02d"%(ltime.tm_year,ltime.tm_mon, ltime.tm_mday,
                ltime.tm_hour, ltime.tm_min)
            posfile = open ("%s_position.txt"%(self.outpref), 'w')
            # start the instrument exposure time timer....
            #if (self.expos_secs > 0) :
            #    self.mytimer.set_expos_time (self.expos_secs)
            #    self.mytimer.start()
        # if not grid but signle take
        else :
            posfile = open("%s_position.txt" % (self.outpref), 'w')
            self.y_nsteps = 1
            self.x_nsteps = 1
            self.prog_fraction = 0
        # start the scan single or otherwise
        for i in range (self.y_nsteps) :
            if (self.abort_flag == True):
                break
            yval = self.y_start + i * self.y_inc
            #caput ('Dera:m2.VAL', yval)
            if (self.single_take == False) :
                self.move_motor (1, yval)
                self.update_position.emit (1, yval)
                # QtCore.QThread.sleep (2)
            iy = int (yval * 1000)
            for j in range (self.x_nsteps) :
                self.prog_fraction = float(count) / float(self.x_nsteps * self.y_nsteps)
                count = count + 1
                # for each scan - do an xrf_prep
                self.prep_xrf.emit()
                QtCore.QThread.sleep(2)
                if (self.abort_flag== True) :
                    break
                if (self.single_take == False) :
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
                    #if (self.single_take == False) :
                else :
                    filstring = "%s_single.mca"%(self.outpref)
                    self.amptek.set_spectrum_file (filstring)

                self.amptek.set_acquisition_time (self.acqtime)
                self.amptek.start_acquisition()


        self.bclient.close_shutter()
        self.set_status.emit("Ready", 0)
        self.acquire_flag = False
        # posfile is written when grid scan
        if (self.single_take == False) :
            posfile.close()
        self.singleTake = False
        self.prog_fraction = 0.