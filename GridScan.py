###
# GridScan.py
# Top level python module to load the gridscan mainwindow and handle events
# generated by user interactions.nt
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from epics import caget, cainfo, caput
from MyCAEpics import *
import sys
import time

class gridscan(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = uic.loadUi("gridscan_mainwin.ui", self)
        #status = caput ("Dera:m3.VAL", 5.1)
        self.curAcqSecPBar.setRange(0, 20)
        # if status is not equal to 1 messagebox that info and exit
        if status != 1 :
            mbox = QtGui.QMessageBox ()
            mbox.setWindowTitle ("GridScan Problem : EPICS")
            mbox.setIcon (QtGui.QMessageBox.Critical)
            mbox.setText ("Problem with EPICS communication")
            mbox.setInformativeText("Start EPICS IOC")
            mbox.exec_()
            sys.exit (app.exit(-1))

        curval = caget ("Dera:m3.VAL")
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

        # set the data being sent to spectrometer for access to regularly plotting
        self.xdata = np.arange (0,2048,dtype=np.int64)
        self.ydata = np.zeros((2048), dtype=np.int64)
        self.ca.set_data (self.ydata)
        # link signals to slots
        #self.connect (self.ca, self.ca.update_position, self,
        #              QtCore.pyqtSlot(self.updateMotors))
        self.ca.update_position.connect (self.update_motors)
        self.ca.set_status.connect (self.set_status_label)
        self.ui.x_MoveButton.clicked.connect (self.move_x_motor)
        self.ui.browseButton.clicked.connect (self.browse_prefix)
        self.ui.StartScanButton.clicked.connect (self.start_scan)
        self.ui.exitButton.clicked.connect (self.closeup)
        self.ui.curAcqSecPBar.setRange (0, 20)
        self.ui.curAcqSecPBar.setValue (0)
        self.mytimer = QtCore.QTimer ()
        self.mytimer.timeout.connect (self.update_plot)
        self.mytimer.start(1000)



    def browse_prefix (self) :
        fname = QtGui.QFileDialog.getSaveFileName (self,"Output prefix name")
        self.ui.outprefLE.setText (fname)


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
        self.ui.acquisitionTimeLE.setText (acqStr)
        outprefix = self.ui.outprefLE.text()
        self.ca.set_acquisition_params (outprefix, acquisition_time)
        self.curAcqSecPBar.setValue(0)
        self.curAcqSecPBar.setRange (0, acquisition_time)
        self.ca.start ()


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
        print self.ydata[300:320]
        if self.ca.acquire_flag :
            asecs = self.ca.get_acq_time ()
            self.curAcqSecPBar.setValue (asecs)

    def closeup (self) :
        sys.exit(app.exit (0))



if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)
    GS = gridscan()
    GS.show()
    sys.exit(app.exec_())

