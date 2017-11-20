from PyQt5 import QtWidgets, QtGui, QtCore

import pyqtgraph as pg
import numpy as np


class MyPlot (pg.PlotWidget):

    mousePos = QtCore.pyqtSignal(QtCore.QPointF)
    linePos = QtCore.pyqtSignal(float)

    def __init__(self, parent):
        pg.PlotWidget.__init__(self, parent)

        self.setXRange (0,1000)
        x = np.random.normal(size=1000)
        y = np.random.normal(size=1000)
        yy = np.random.normal(size=1000)
        self.plot(x, y, pen=(0,3), symbol='+')  ## setting pen=None disables line drawing
        self.plot (x, yy, pen=(1,3), symbol='+')
        self.autoFlag = False
        self.roi_disp = False
        #rois =[]
        #self.myroi = [(pg.RectROI([0,0],[1,1],pen=(0,9), movable=True, invertible=True, maxBounds=[0,0,1200,16000]))]
        self.myroi = [(pg.RectROI([0, 0], [20, 20], invertible=True, pen=(0, 9)))]

        self.setMouseEnabled (x=False, y=False)
        self.box_mode = -1


        self.setXRange (630,750)
        self.setYRange (0,1000)
        self.scene().sigMouseMoved.connect (self.mouseMoved)
        self.scene().sigMouseClicked.connect(self.mousePressed)
        self.myroi[0].sigRegionChangeFinished.connect (self.roi_done)
        #self.myroi[0].sigRegionChangeStarted.connect(self.roi_flux)


        self.maxLinePos = 700
        self.startX = 670
        self.endX = 750

        # first data if the flag to see if the spectrum has been displayed before or not,
        # if not use the data's x range to set the plot x axis
        self.first_data = True


        #self.vLine = pg.InfiniteLine (movable=True, angle=90)
        #self.vLine.setZValue(self.maxLinePos)
        #self.addItem(self.vLine, ignoreBounds=True)

    def resetView (self) :
        self.setXRange (self.startX, self.endX)


    def setBox (self) :
        self.box_mode = 1
        self.myroi[0].setPos(0,0)
        self.new_roi()
        self.addItem(self.myroi[0])
        self.roi_disp=True

    def setFirstData (self) :
        self.first_data = True


    def setMyData (self, x,y) :
        self.clear()
        if (self.roi_disp) :
            self.addItem(self.myroi[0])
        self.rx = x.copy ()
        self.ry = y.copy ()
        minv = x[0]
        maxv = x[len(x)-1]

        if (self.autoFlag or self.first_data ) :
            maxy = np.max(y)
            miny = np.min(y)
            self.setXRange (minv, maxv)
            self.setYRange (miny, maxy*1.5)
            if self.first_data :
                self.startX = minv
                self.endX = maxv
            self.first_data = False

        self.plot (x,y, pen=(0,3))
        maxarg = np.argmax (y)
        self.maxLinePos = x[maxarg]

        self.myLine = self.addLine (x=self.maxLinePos,movable=True)
        self.myLine.sigPositionChangeFinished.connect (self.draggedLine)
        self.linePos.emit(self.maxLinePos)


    def over_plot (self, y) :
        self.setMyData (self.rx, self.ry)
        self.plot (self.rx, y, pen=(1,3))


    def draggedLine (self) :
        self.maxLinePos = self.myLine.value()
        #print "Max line pos ", self.maxLinePos
        self.linePos.emit (self.maxLinePos)

    def mousePressed (self, evt) :
        if (self.box_mode != 1) :
            return
        xy = self.plotItem.vb.mapSceneToView(evt._scenePos)
        self.roi_disp = True
        self.myroi[0].setPos (xy)
        self.new_roi()

        self.box_mode = 2
        print xy



    def mouseMoved (self, evt) :
        #print evt
        #print self.plot.mapSceneToView(evt[0])

        xy= self.plotItem.vb.mapSceneToView(evt)
        xval = xy.x()
        yval = xy.y()

        xyval = QtCore.QPointF (xval,yval)
        self.mousePos.emit(xyval)



        return



    def roi_done (self, evt) :
        if (self.box_mode != 2) :
            return
        self.box_mode = -1
        self.roi_disp = False
        (x0, y0) = self.myroi[0].pos()
        (x1,y1) = self.myroi[0].size ()
        self.setXRange (x0, x1+x0)
        self.myroi[0].setPos(0,0)
        self.new_roi()
        self.removeItem (self.myroi[0])

    def new_roi (self) :

        self.myroi[0].setSize (5, 10)
