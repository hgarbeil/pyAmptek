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
        self.scantype=1 # default XRD scan
        QtWidgets.QMainWindow.__init__(self)
        self.ui = uic.loadUi("gridscan_mainwin.ui", self)
        curval = caget ("Dera:m1.VAL")
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
        print "M1 position is : ", s

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

        # z motor
        curval = caget("Dera:m3.VAL")
        s = "%7.4f" % (curval)
        print "M3 position is : ", s


        self.ui.z_customLE.setText(s)

        xval =1.
        yval =1.
        zval =1.

        str = "%5.3f %5.3f %5.3f" % (xval, yval, zval)
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

        self.bclient.get_gonio_position()
        self.bis_update()


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
        self.ui.abortScanButton.clicked.connect (self.abort_scan)
        self.ui.y_MoveButton.clicked.connect(self.move_y_motor)
        self.ui.updateCenterButton.clicked.connect (self.set_center)
        self.ui.browseButton.clicked.connect (self.browse_prefix)

        self.ui.xrdSelectRB.clicked.connect(self.change_scantype_to_XRD)
        self.ui.xrfSelectRB.clicked.connect(self.change_scantype_to_XRF)
        self.ui.bothSelectRB.clicked.connect(self.change_scantype_to_both)

        # on XRD Panel , these are the drive and drive to default buttons
        # updateAngles - drive button
        self.ui.updateAnglesButton.clicked.connect (self.drive_bc_specified)
        # defaultAngles - Drive Default
        self.ui.defaultAnglesButton.clicked.connect (self.drive_bc_default)
        # Omega position buttons
        self.ui.Omega_0_Button.clicked.connect (self.drive_omega_0)
        self.ui.Omega_60_Button.clicked.connect(self.drive_omega_60)
        self.ui.Omega_105_Button.clicked.connect(self.drive_omega_105)

        # collect XRD
        self.ui.collectXRDButton.clicked.connect (self.collect_XRD)

        self.ui.actionLoad_mca_file.triggered.connect (self.load_mca)

        # progress bar
        self.ui.curAcqSecPBar.setRange (0, 20)
        self.ui.curAcqSecPBar.setValue (0)
        self.ui.curAcqSecPBar.setFormat ("%v")

        # collect from the XRF side of the UI
        self.ui.StartScanButton.clicked.connect(self.start_scan)
        self.ui.singleAcqButton.clicked.connect(self.single_take)
        self.ui.abortScanButton.clicked.connect(self.abort_scan)
        # there is also a drive button but not sure what that is driving to?

        # signal - slot from the BIS Client (BrukerClient)
        self.bclient.shutter_state.connect (self.set_shutter_button)
        self.bclient.newangles.connect (self.bis_update)

        # custom scan - list widget based coordinates for xyz stage motion
        # user specifies each position to scan
        self.ui.add_current_button.clicked.connect (self.add_current_tolist)
        self.ui.restoreCoordsButton.clicked.connect (self.restore_coords)
        self.ui.delSelectedButton.clicked.connect (self.delete_selected)
        self.ui.move_sel_button.clicked.connect (self.move_selected)
        self.ui.saveCoordsButton.clicked.connect (self.save_coords)
        self.ui.clearCoordsButton.clicked.connect (self.clear_coords)

        self.mytimer = QtCore.QTimer ()
        self.mytimer.timeout.connect (self.update_plot)
        self.mytimer.start(1000)
        #self.fulltime = 20

        # close the application
        self.ui.exitButton.clicked.connect(self.closeup)

        # drive or drive_bc_specified, gets values from target LEs
    def drive_bc_specified (self):
        dist = float(self.ui.distanceLE.text())
        theta = float(self.ui.twothetaLE.text())
        omega = float(self.ui.omegaLE.text())
        if theta < -30 or theta > 30 :
            print 'theta out of bounds'
            self.exceed_twotheta()
            return
        phi = float (self.ui.phiLE.text())
        ######
        # note that there is a scan execute here
        #self.bclient.execute_scan(dist, theta, omega, phi)
        self.bclient.drive_to_specified (dist, theta, phi, omega)
        self.bclient.get_gonio_position()
        self.bclient.newangles.emit()
        #self.bis_update()

    def change_scantype_to_XRD (self):
        print "XRD scan selected"
        self.scantype=1

    def change_scantype_to_XRF (self):
        print "XRF scan selected"
        self.scantype=0

    def change_scantype_to_both (self):
        print "Both scans selected"
        self.scantype=2

    def drive_omega_0 (self) :
        dist = 20.
        theta = 0.
        omega = 0.
        phi = 0.
        self.bclient.drive_to_specified (dist, theta, phi, omega)
        self.bclient.get_gonio_position()
        self.bis_update()


    def drive_omega_60 (self) :
        print "omega 60"
        dist = 20
        theta = 0.
        omega = 60.
        phi = 0.
        self.bclient.drive_to_specified (dist, theta, phi, omega)
        self.bclient.get_gonio_position()
        self.bis_update()

    def drive_omega_105 (self) :
        dist = 20
        theta = 0.
        omega = 105.
        phi = 0.
        self.bclient.drive_to_specified (dist, theta, phi, omega)
        self.bclient.get_gonio_position()
        self.bis_update()


    # this is now used to reconnect to status socket and listen
    def drive_bc_default (self) :
        self.bclient.reconnect()
        self.bclient.drive_to_default ()

    def set_image_params(self, runnum):
        nscans = int(self.ui.nscansRunLE.text())
        secs = float(self.ui.timePerImageLE.text())
        width = float(self.ui.widthLE.text())
        #runnum = int(self.ui.runnumLE.text())
        self.bclient.set_image_params(runnum, nscans, secs, width)

    # collect with the XRD detector, first driving to the specified location
    def collect_XRD (self):
        # read the fields off the display and start the collect
        dist = float(self.ui.distanceLE.text())
        theta = float(self.ui.twothetaLE.text())
        omega = float(self.ui.omegaLE.text())
        phi = float(self.ui.phiLE.text())
        #self.drive_bc_specified()
        runnum = int(self.ui.runnumLE.text())
        self.set_image_params(runnum)
        outpref = self.ui.outprefLE.text()
        outfile = outpref + '_XRD_##_####.sfrm'
        # check if outfile exists
        # start the bclient thread which does the acquisition
        self.bclient.set_scan_type (2)
        self.bclient.set_scan_params (dist,theta, omega, phi, outfile)
        self.bclient.start()
    #    noresponse=self.bclient.execute_scan(dist,theta, omega, phi, outfile)


    def exceed_twotheta (self) :
        mbox = QtGui.QMessageBox()
        mbox.setWindowTitle("Invalid Parameter")
        mbox.setIcon(QtGui.QMessageBox.Critical)
        mbox.setText("Reenter Two Theta Value")
        mbox.setInformativeText("Abs (twotheta) >30")
        mbox.exec_()

    def exceed_distance (self) :
        mbox = QtGui.QMessageBox()
        mbox.setWindowTitle("Invalid Parameter")
        mbox.setIcon(QtGui.QMessageBox.Critical)
        mbox.setText("Reenter Distance")
        mbox.setInformativeText("7 <= Distance <= 20")
        mbox.exec_()

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
        if (mot_num==2) :
            self.ui.z_CurLocLE.setText (s)
            self.ui.z_customLE.setText(s)


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

    def move_z_motor(self):
        val = float(self.ui.z_MoveLocLE.text())
        print "move motor : "
        self.ca.move_motor(2, val)
        time.sleep(1)
        val = self.ca.get_position(2)
        s = "%5.3f" % val
        self.ui.z_CurLocLE.setText(s)
        self.ui.z_customLE.setText(s)

    def set_center (self) :
        xval = caget ("Dera:m3.VAL")
        s = "%5.3f"%xval
        self.ui.x_CenterLocLE.setText (s)
        yval = caget ("Dera:m2.VAL")
        s = "%5.3f"%yval
        self.ui.y_CenterLocLE.setText (s)

    def add_current_tolist (self) :
        xval = caget ("Dera:m1.VAL")
        yval = caget ("Dera:m2.VAL")
        zval = caget ("Dera:m3.VAL")
        s = "%5.3f %5.3f %5.3f"%(xval,yval,zval)
        mycoord = QtWidgets.QListWidgetItem(s, self.ui.coordLocationsWidget)
        mycoord.setFlags(mycoord.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)

        mycoord.setCheckState(QtCore.Qt.Checked)
        # mycoord.setForeground (QtGui.QBrush(QtGui.QColor.black))
        # mycoord.setCheckState (QtCore.Qt.Checked)

    def delete_selected (self) :
        nitems = self.ui.coordLocationsWidget.model().rowCount()
        print 'total items : ', nitems
        myrow = self.ui.coordLocationsWidget.currentRow()
        print myrow
        #self.ui.coordsLocationsWidget.takeItem(1)
        #for SelectedItem in self.coordLocationsWidget.selectedItems():
        #    myrow = self.ui.coordLocationsWidget.row(SelectedItem)
        self.ui.coordLocationsWidget.takeItem(myrow)

    def move_selected (self) :
        nitems = self.ui.coordLocationsWidget.model().rowCount()
        print 'total items : ', nitems
        mysel = self.ui.coordLocationsWidget.currentItem()
        print mysel
        curline = mysel.text()
        vals = curline.split(' ')
        xval = float (vals[0])
        yval = float(vals[1])
        zval = float(vals[2])
        self.ca.move_motor(0,xval)
        time.sleep (.5)
        self.ca.move_motor(1, yval)
        time.sleep(.5)
        self.ca.move_motor(2, zval)
        time.sleep(.5)
        xval = caget("Dera:m1.VAL")
        yval = caget("Dera:m2.VAL")
        zval = caget("Dera:m3.VAL")
        self.ui.x_customLE.setText ("%7.4f"%xval)
        self.ui.y_customLE.setText("%7.4f"%yval)
        self.ui.z_customLE.setText("%7.4f"%zval)

    # the start scan for XRF looks to see which tab widget is active, if in grid mode, reads params and starts the XRF Scan
    # if in


    def start_scan (self) :
        # we need a step here to drive to the Phi position to get the XRD out of the way,
      if self.scantype == 1:
        print "XRD scan"

        dist = float(self.ui.distanceLE.text())
        theta = float(self.ui.twothetaLE.text())
        omega = float(self.ui.omegaLE.text())
        phi = float(self.ui.phiLE.text())
        runnum = int(self.ui.runnumLE.text())

        outpref = self.ui.outprefLE.text()
        outfile = outpref + '_XRD_##_####.sfrm'
        # send the scan params to the bruker client
        self.bclient.set_scan_params(dist, theta, omega, phi, outfile)
        self.set_image_params(runnum)
        # get the scan positions
        scanpos = []
        self.read_scan_locations(scanpos)
        self.bclient.set_scan_positions(scanpos)
        self.bclient.set_scan_type (self.scantype)
        self.blient.set_motor_control (self.ca)
        self.bclient.start()
        # npos = len(scanpos)
        # nore=0
        # for i in range(npos):
        #     if nore == 0:
        #         xval = scanpos[i][0]
        #         yval = scanpos[i][1]
        #         zval = scanpos[i][2]
        #
        #         self.ca.move_motor(0, xval)
        #         self.ca.move_motor(1, yval)
        #         self.ca.move_motor(2, zval)
        #
        #         done = 0
        #         while done == 0:
        #             time.sleep(0.5)
        #             x = self.ca.get_position(0)
        #             y = self.ca.get_position(1)
        #             z = self.ca.get_position(2)
        #             if abs(x-xval) <0.001 and abs(y-yval)<0.001 and abs(z-zval)<0.001: done = 1
        #         runnum = runnum+1
        #         self.set_image_params(runnum)
        #         self.bclient.set_scan_params(dist, theta, omega, phi, outfile)
        #         nore=self.bclient.execute_scan(dist, theta, omega, phi, outfile)
        #         #self.bclient.start()
        #         print "--- position", i, "finished"
        #     else:
        #         print "Connection with BIS has been lost"


      else:
        if self.scantype == 0:
          print "XRF scan"
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
                vals_z = float(vals[2])
                loclist.append((vals_x,vals_y,vals_z))
        print loclist

    def save_coords (self) :
        # need to get a save file name
        fname = QtGui.QFileDialog.getSaveFileName (self, "Output ASCII Coord File","","*.txt")
        nlocs = self.ui.coordLocationsWidget.count()
        if (nlocs <1) :
            return
        try :
            fout = open(fname[0], "w")
            for i in range (nlocs) :
                myitem = self.ui.coordLocationsWidget.item(i)
                if myitem.checkState() < 2 :
                    continue
                fout.write (myitem.text()+"\n")
                print myitem.text()
                
        except IOError :
                print "could not write to : ", fname[0]
        fout.close()

    def clear_coords (self) :
        self.ui.coordLocationsWidget.clear()

    def restore_coords (self) :
        # need to get an existing file name
        fname = QtGui.QFileDialog.getOpenFileName(self, "Input ASCII Coord File", "", "*.txt")
        try :
            fin = open (fname[0], "r")

            
            #if npts <= 0 :
            #   print "file is empty "
            #   return
            #self.ui.coordLocationsWidget.clear()
			# read in one line at a time
            for lineval in fin :
                lineval = lineval.split("\n")[0]
                mycoord = QtWidgets.QListWidgetItem(lineval, self.ui.coordLocationsWidget)
                mycoord.setFlags(
                mycoord.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)

                mycoord.setCheckState(QtCore.Qt.Checked)
            fin.close()
        except IOError :
                print "problem with file : ", fname



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
        #print "position update", vals
        self.set_shutter_button (int(vals[0]))
        #self.ui.distanceLE.setText ("%5.2f"%vals[5])
        #self.ui.twothetaLE.setText ("%5.2f"%vals[1])
        #self.ui.omegaLE.setText("%5.2f" % vals[2])
        #self.ui.phiLE.setText("%5.2f" % vals[3])
        self.ui.curDistLE.setText ("%5.2f"%vals[5])
        self.ui.curTwothetaLE.setText("%5.2f"%vals[1])
        self.ui.curPhiLE.setText("%5.2f" % vals[3])
        self.ui.curOmegaLE.setText("%5.2f" % vals[2])

    def abort_scan (self) :
        self.bclient.set_abort(1)

    # called by bclient to update the shutter button
    def set_shutter_button (self, state) :
        p = self.ui.shutter_status_button.palette()
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

