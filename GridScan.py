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
        self.ui.x_customLE.setText (s)

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
        self.ui.y_customLE.setText(s)

        xval =1.
        yval =1.
        str = "%5.3f %5.3f" % (xval, yval)
        #mycoord = QtWidgets.QListWidgetItem (str, self.ui.coordLocationsWidget)
        #mycoord.setFlags (mycoord.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)
        #mycoord.setForeground (QtGui.QBrush(QtGui.QColor.black))
        #mycoord.setCheckState (QtCore.Qt.Checked)
        #mycoord.

        # get MyCAEpics instance
        self.ca = MyCAEpics()

        self.set_shutter_button (0)
        self.bclient = BrukerClient()
        self.bclient.connect()

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

        # set bc to ca
        self.ca.set_bruker_client(self.bclient)
        # link signals to slots
        #self.connect (self.ca, self.ca.update_position, self,
        #              QtCore.pyqtSlot(self.updateMotors))
        self.ca.update_position.connect (self.update_motors)
        self.ca.set_status.connect (self.set_status_label)
        self.ui.x_MoveButton.clicked.connect (self.move_x_motor)
        self.ui.y_MoveButton.clicked.connect(self.move_y_motor)
        self.ui.updateCenterButton.clicked.connect (self.set_center)
        self.ui.browseButton.clicked.connect (self.browse_prefix)
        self.ui.StartScanButton.clicked.connect (self.start_scan)
        self.ui.singleAcqButton.clicked.connect (self.single_take)
        self.ui.updateAnglesButton.clicked.connect (self.drive_bc_specified)
        self.ui.defaultAnglesButton.clicked.connect (self.drive_bc_default)
        self.ui.abortScanButton.clicked.connect (self.abort_scan)
        self.ui.actionLoad_mca_file.triggered.connect (self.load_mca)
        self.ui.exitButton.clicked.connect (self.closeup)
        self.ui.curAcqSecPBar.setRange (0, 20)
        self.ui.curAcqSecPBar.setValue (0)
        self.ui.curAcqSecPBar.setFormat ("%v")

        # signal - slot from the BIS Client (BrukerClient)
        self.bclient.shutter_state.connect (self.set_shutter_button)
        self.bclient.newangles.connect (self.bis_update)

        # custom scan - list widget based
        self.ui.add_current_button.clicked.connect (self.add_current_tolist)

        self.mytimer = QtCore.QTimer ()
        self.mytimer.timeout.connect (self.update_plot)
        self.mytimer.start(1000)
        #self.fulltime = 20


    def drive_bc_specified (self):
        dist = float(self.ui.distanceLE.text())
        theta = float(self.ui.twothetaLE.text())
        omega = float(self.ui.omegaLE.text())
        phi = float (self.ui.phiLE.text())
        self.bclient.drive_to_specified (dist, theta, omega, phi)
        
    def drive_bc_default (self) :
        self.bclient.drive_to_default ()

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
        #self.ui.plotInfoTE.setText (outText)

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
            self.ui.x_customLE.setText(s)
        if (mot_num==1) :
            self.ui.y_CurLocLE.setText (s)
            self.ui.y_customLE.setText(s)

        #if mot_num == 0 :

    def move_x_motor (self) :
        val = float(self.ui.x_MoveLocLE.text())
        print "move motor : "
        self.ca.move_motor (0, val)
        time.sleep (1)
        val = self.ca.get_position (0)
        s="%5.3f"%val
        self.ui.x_CurLocLE.setText(s)
        self.ui.x_customLE.setText(s)


    def move_y_motor (self) :
        val = float(self.ui.y_MoveLocLE.text())
        print "move motor : "
        self.ca.move_motor (1, val)
        time.sleep (1)
        val = self.ca.get_position (1)
        s="%5.3f"%val
        self.ui.y_CurLocLE.setText(s)
        self.ui.y_customLE.setText(s)

    def set_center (self) :
        xval = caget ("Dera:m3.VAL")
        s = "%5.3f"%xval
        self.ui.x_CenterLocLE.setText (s)
        yval = caget ("Dera:m2.VAL")
        s = "%5.3f"%yval
        self.ui.y_CenterLocLE.setText (s)

    def add_current_tolist (self) :
        xval = caget ("Dera:m3.VAL")
        yval = caget ("Dera:m2.VAL")
        s = "%5.3f %5.3f"%(xval,yval)
        mycoord = QtWidgets.QListWidgetItem(s, self.ui.coordLocationsWidget)
        mycoord.setFlags(mycoord.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)

        mycoord.setCheckState(QtCore.Qt.Checked)
        # mycoord.setForeground (QtGui.QBrush(QtGui.QColor.black))
        # mycoord.setCheckState (QtCore.Qt.Checked)


    def start_scan (self) :

        # Grid Scan
        if self.ui.ScanTypes.currentIndex() == 0 :
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
            #expos_secs = int (self.ui.instExposLE.text())
            self.ui.acquisitionTimeLE.setText (acqStr)
            outprefix = self.ui.outprefLE.text()
            self.ca.set_acquisition_params (outprefix, acquisition_time)
            #self.ca.set_expos_timer (expos_secs)
            self.curAcqSecPBar.setValue(0)
            self.curAcqSecPBar.setRange (0, acquisition_time)
            self.fulltime = acquisition_time
            self.ca.single_take = False
            self.ca.start ()
        # Scan locations
        if self.ui.ScanTypes.currentIndex()== 1 :
            acquisition_time = int(self.ui.acquisitionTimeLE.text())
            acqStr = "%4d" % (acquisition_time)
            # expos_secs = int (self.ui.instExposLE.text())
            self.ui.acquisitionTimeLE.setText(acqStr)
            outprefix = self.ui.outprefLE.text()
            self.ca.set_acquisition_params(outprefix, acquisition_time)
            # self.ca.set_expos_timer (expos_secs)
            self.curAcqSecPBar.setValue(0)
            self.curAcqSecPBar.setRange(0, acquisition_time)
            scanpositions=[]
            self.read_scan_locations (scanpositions)
            self.ca.set_listscan (scanpositions)
            self.ca.start ()

    # read the scan locations from the listwidget  with xy coords
    def read_scan_locations (self, loclist) :
        nlocs = self.ui.coordLocationsWidget.count()
        for i in range (nlocs) :
            myitem = self.ui.coordLocationsWidget.item(i)
            if myitem.checkState() == 2 :
                vals = myitem.text().split(' ')
                vals_x = float(vals[0])
                vals_y = float(vals[1])
                loclist.append((vals_x,vals_y))
        print loclist

    def abort_scan (self) :
        self.ca.abort_scan()

    # open shutter but do not move motors, take a single collection at current location
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
            #print asecs
            #str0 = "Scan file : \r\n%s"%self.ca.scanfile
            #str1 = "%s\r\nElapsed time : %d"%(str0,asecs)
            #print str1
            #self.ui.plotInfoTE.setText (str1)

    def bis_update (self) :
        vals = [0.,0.,0.,0.,0.,0.]
        self.bclient.get_values (vals)
        self.set_shutter_button (int(vals[0]))
        self.ui.distanceLE.setText ("%5.2f"%vals[5])
        self.ui.twothetaLE.setText ("%5.2f"%vals[1])
        self.ui.omegaLE.setText("%5.2f" % vals[2])
        self.ui.phiLE.setText("%5.2f" % vals[3])

    # called by bclient to update the shutter button
    def set_shutter_button (self, state) :
        p = self.ui.shutter_status_button.palette()
        
        print "called shutter button set ", state
        if state == 0 :
            self.ui.shutter_status_button.setText ("Shutter Closed")
            self.ui.shutter_status_button.setStyleSheet("background-color: white; color:black")
        if state == 1 :
            self.ui.shutter_status_button.setText ("Shutter Open")
            self.ui.shutter_status_button.setStyleSheet("background-color: yellow; color:red")
            

    def closeup (self) :
        self.bclient.close_shutter()
        sys.exit(app.exit (0))



if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)
    GS = gridscan()
    GS.show()
    sys.exit(app.exec_())

