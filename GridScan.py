###
# GridScan.py
# Top level python module to load the gridscan mainwindow and handle events
# generated by user interactions.nt
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from epics import caget, cainfo, caput
from MyCAEpics import *
from BrukerClient import *
import sys
import time

class gridscan(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = uic.loadUi("gridscan_mainwin.ui", self)
        curval = caget ("Dera:m3.VAL")
        self.curAcqSecPBar.setRange(0, 20)
        # if status is not equal to 1 messagebox that info and exit
        if curval == None :
            mbox = QtGui.QMessageBox ()
            mbox.setWindowTitle ("GridScan Problem : EPICS")
            mbox.setIcon (QtGui.QMessageBox.Critical)
            mbox.setText ("Problem with EPICS communication")
            mbox.setInformativeText("Start EPICS IOC")
            mbox.exec_()
            sys.exit (app.exit(-1))

        s="%7.4f"%(curval)
        print "M3 position is : ", s

        self.ui.x_CurLocLE.setText(s)
        self.ui.x_RangeLE.setText (".2")
        self.ui.x_CenterLocLE.setText(s)
        self.ui.x_NStepsLE.setText("10")
        self.ui.x_MoveLocLE.setText(s)

        self.ui.set_status_label ("Ready")

        # y motors
        curval = caget("Dera:m2.VAL")
        s = "%7.4f" % (curval)
        print "M2 position is : ", s

        self.ui.y_CurLocLE.setText(s)
        self.ui.y_RangeLE.setText(".2")
        self.ui.y_CenterLocLE.setText(s)
        self.ui.y_NStepsLE.setText("10")
        self.ui.y_MoveLocLE.setText(s)

        # get MyCAEpics instance
        self.ca = MyCAEpics()

        self.bclient = BrukerClient()
        if self.bclient.bcstatus == False :
            mbox = QtGui.QMessageBox()
            mbox.setWindowTitle("Bruker Comm Problem : BIS")
            mbox.setIcon(QtGui.QMessageBox.Critical)
            mbox.setText("Problem with Bruker communication")
            mbox.setInformativeText("Check network")
            mbox.exec_()
            sys.exit(app.exit(-1))



        # set the data being sent to spectrometer for access to regularly plotting
        self.xdata = np.arange (0,2048,dtype=np.int32)
        self.ydata = np.zeros((2048), dtype=np.int32)
        self.ca.set_data (self.ydata)
        # link signals to slots
        #self.connect (self.ca, self.ca.update_position, self,
        #              QtCore.pyqtSlot(self.updateMotors))
        self.ca.update_position.connect (self.update_motors)
        self.ca.set_status.connect (self.set_status_label)
        self.ui.x_MoveButton.clicked.connect (self.move_x_motor)
        self.ui.updateCenterButton.clicked.connect (self.set_center)
        self.ui.browseButton.clicked.connect (self.browse_prefix)
        self.ui.StartScanButton.clicked.connect (self.start_scan)
        self.ui.singleAcqButton.clicked.connect (self.single_take)
        self.ui.abortScanButton.clicked.connect (self.abort_scan)
        self.ui.actionLoad_mca_file.triggered.connect (self.load_mca)
        self.ui.exitButton.clicked.connect (self.closeup)
        self.ui.curAcqSecPBar.setRange (0, 20)
        self.ui.curAcqSecPBar.setValue (0)
        self.ui.curAcqSecPBar.setFormat ("%v")
        self.mytimer = QtCore.QTimer ()
        self.mytimer.timeout.connect (self.update_plot)
        self.mytimer.start(1000)
        self.fulltime = 20 



    def browse_prefix (self) :
        fname = QtGui.QFileDialog.getSaveFileName (self,"Output prefix name")
        self.ui.outprefLE.setText (fname)

    def load_mca (self) :
        fname = QtGui.QFileDialog.getOpenFileName(self, "Existing .mca file", "C:/X123Data")
        mcafile = fname[0]
        myvals = [0,0,0]
        print "MCA file to read is : ", mcafile
        self.readMCAFile (mcafile, self.ydata, myvals, 2048)
        self.ui.plotWidget.setMyData(self.xdata, self.ydata)
        outText = "Displayed MCA File : \r\n%s"%mcafile
        outText = "%s\r\nExposure Time : %f"%(outText, myvals[0])
        self.ui.plotInfoTE.setText (outText)

    def readMCAFile (self, fname, specdata, myvals, npts) :
        f = open (fname, 'r')
        count = -1
        for iline in f :
            if "DATA" in iline :
                count = 0
                continue
            if (count >= 0 and count < npts) :
                specdata[count] = int(iline)
                count += 1
            if "Accumulation" in iline :
                one,two = iline.split(":")
                print "exposure : ",two
                myvals[0]= (float (two))


    def update_motors (self, mot_num, pos) :

        s="%6.3f"%pos
        print "move motor : %d to position %f"%(mot_num, pos)
        if (mot_num==0) :
            self.ui.x_CurLocLE.setText(s)
        if (mot_num==1) :
            self.ui.y_CurLocLE.setText (s)
        #if mot_num == 0 :

    def move_x_motor (self) :
        val = self.ui.x_MoveLocLE.text().toFloat()[0]
        print "move motor : "
        self.ca.move_motor (0, val)
        time.sleep (1)
        val = self.ca.get_position (0)
        s="%5.3f"%val
        self.ui.x_CurLocLE.setText(s)


    def move_y_motor (self) :
        val = self.ui.y_MoveLocLE.text().toFloat()[0]
        print "move motor : "
        self.ca.move_motor (1, val)
        time.sleep (1)
        val = self.ca.get_position (1)
        s="%5.3f"%val
        self.ui.y_CurLocLE.setText(s)

    def set_center (self) :
        xval = caget ("Dera:m3.VAL")
        s = "%5.3f"%xval
        self.ui.x_CenterLocLE.setText (s)
        yval = caget ("Dera:m2.VAL")
        s = "%5.3f"%yval
        self.ui.y_CenterLocLE.setText (s)

    def start_scan (self) :
        #self.ca.set_pasfams ()
        x0 = float(self.ui.x_CenterLocLE.text())
        xsteps = int(self.ui.x_NStepsLE.text())
        xrange = float (self.ui.x_RangeLE.text())

        y0 = float(self.ui.y_CenterLocLE.text())
        yrange = float(self.ui.y_RangeLE.text())
        ysteps = int(self.ui.y_NStepsLE.text())

        self.ca.set_params( x0, xrange, xsteps, y0, yrange, ysteps)
        acquisition_time = int(self.ui.acquisitionTimeLE.text())
        acqStr = "%4d"%(acquisition_time)
        expos_secs = int (self.ui.instExposLE.text())
        self.ui.acquisitionTimeLE.setText (acqStr)
        outprefix = self.ui.outprefLE.text()
        self.ca.set_acquisition_params (outprefix, acquisition_time)
        self.ca.set_expos_timer (expos_secs)
        self.curAcqSecPBar.setValue(0)
        self.curAcqSecPBar.setRange (0, acquisition_time)
        self.fulltime = acquisition_time
        self.ca.single_take = False
        self.ca.start ()

    def abort_scan (self) :
        self.ca.abort_scan()

    def single_take (self) :
        acquisition_time = int(self.ui.acquisitionTimeLE.text())
        self.ca.set_acquisition_time(acquisition_time)
        self.curAcqSecPBar.setValue(0)
        self.curAcqSecPBar.setRange(0, acquisition_time)
        self.fulltime = acquisition_time
        self.ca.take_single() 
        


    def set_status_label (self, str, state=0) :
        p = self.ui.statusLE.palette()
        if (state == 1) :
            p.setColor (self.ui.statusLE.backgroundRole(), QtCore.Qt.yellow)
        if (state==0) :
            p.setColor(self.ui.statusLE.backgroundRole(), QtCore.Qt.white)
        self.ui.statusLE.setPalette (p)
        self.ui.statusLE.setText (str)

    def update_plot (self) :
        self.ui.plotWidget.setMyData (self.xdata, self.ydata)
        if self.ca.acquire_flag :
            asecs = self.ca.get_acq_time ()
            esecs = self.ca.get_cur_expos_time()
            if (asecs >= self.fulltime) :
                asecs = self.fulltime
            self.curAcqSecPBar.setValue(asecs)
            print asecs
            str0 = "Scan file : \r\n%s"%self.ca.scanfile
            str1 = "%s\r\nElapsed time : %d"%(str0,asecs)
            print str1
            self.ui.plotInfoTE.setText (str1)

    def closeup (self) :
        sys.exit(app.exit (0))



if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)
    GS = gridscan()
    GS.show()
    sys.exit(app.exec_())

