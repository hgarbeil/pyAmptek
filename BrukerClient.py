import socket
import sys
import time
from PyQt5 import QtCore, QtGui


class BrukerClient (QtCore.QThread) :

    BSIZE = 1024
	#Change to Bruker Computer IP Address
    serverip = '128.171.152.86'
    shutter_state = QtCore.pyqtSignal(int)
    newangles = QtCore.pyqtSignal ()

    def __init__(self):
        QtCore.QThread.__init__(self)


    def connect (self) :
        try :
            self.shutter_status = 0
            self.chi = 0
            self.omega = 0
            self.phi = 0
            self.chi = 0
            self.bcrun = False
            self.bcstatus= True
            self.distance = 0
            self.scansinrun = 5 #scans per run
            self.scantime = 5 #secs per image
            self.width = 1 #angular width for each image
            self.runnumber = 1

            self.command_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.command_sock.settimeout(30.)
            #   command_sock.setblocking(0)
            self.file_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.file_sock.settimeout(30.)
            #file_sock.setblocking(0)
            self.status_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.status_sock.settimeout(120.)
            #status_sock.setblocking(0)
            server_address = (BrukerClient.serverip, 49153)
            print >> sys.stderr, 'connecting to %s port %s'%server_address
            self.command_sock.connect (server_address)

            server_address = (BrukerClient.serverip, 49154)
            print >> sys.stderr, 'connecting to %s port %s'%server_address
            self.file_sock.connect (server_address)
            server_address = (BrukerClient.serverip, 49155)
            print >> sys.stderr, 'connecting to %s port %s'%server_address
            self.status_sock.connect (server_address)
            #self.get_status()
            #time.sleep (20)
            self.start()

            self.bcrun = False
        except socket.error, msg :
            print "Could not connect with socket : %s"%msg
            self.bcstatus = False


    def reconnect (self) :
        try :
            print "--Attempting to reconnect with BIS"
            self.command_sock.close()
            self.file_sock.close()
            self.status_sock.close()
            time.sleep(1.0)

            self.command_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.command_sock.settimeout(30.)
            self.file_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.file_sock.settimeout(30.)
            self.status_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.status_sock.settimeout(120.)

            server_address = (self.serverip, 49153)
            print >> sys.stderr, 'connecting to %s port %s'%server_address
            self.command_sock.connect (server_address)

            server_address = (self.serverip, 49154)
            print >> sys.stderr, 'connecting to %s port %s'%server_address
            self.file_sock.connect (server_address)

            server_address = (self.serverip, 49155)
            print >> sys.stderr, 'connecting to %s port %s'%server_address
            self.status_sock.connect (server_address)

            self.bcstatus= True
        except socket.error, msg :
            print "Could not reconnect with BIS: %s"%msg
            self.bcstatus = False



    def get_status (self):
        try :
            while (1):
                data = self.status_sock.recv(BrukerClient.BSIZE)
                print data
        except socket.error, msg:
            print "Shutter status error : %s" % msg

    # drive to position of 200mm, 2theta= -30 omega=0 and phi=180
    def drive_to_default (self) :
        try :
            for i in range (1):
                time.sleep(0.5)
                data = self.status_sock.recv(1024)
                print "----", data

        except socket.error, msg:
            print "Drive error : %s" % msg
        else:
            print "Status socket readout complete"

    def drive_to_specified (self, dist, theta, phi, omega) :
        self.get_gonio_position
        if abs(self.twotheta-theta) <0.05 and  abs(self.omega-omega)<0.05 and abs(self.distance-dist)<0.05 :
            print "goniometer is aleady at target position"
        else:
            message = "[drive /distance=%f /2theta=%f /omega=%f /phi=%f]"%(dist,theta,omega,phi)
            try :
                print "sending move message to bis"
                self.command_sock.send(message)
                complete = 0
                while complete == 0 :
                    time.sleep(0.5)
                    data = self.status_sock.recv (1024)
                    # print data
                    if ("[ANGLESTATUS" in data):
                        angles = self.parse_anglestatus(data)
                        self.set_angles(angles)
                        self.newangles.emit()
                        complete = 1
            except socket.error, msg :
                print "Drive error : %s"%msg
            else: print "--- Motion completed without exception"

    def set_image_params (self, runnum, nscans, scansec, w) :
        self.runnumber = runnum
        self.scansinrun = nscans
        self.scantime = scansec
        self.width = w

    def execute_scan(self, dist, theta, omega, phi, outfile):
        self.drive_to_specified(dist, theta, phi, omega)
        fname_template=outfile
        rownumber = 1
        #runnumber = 56 # need
        firstimagenumber = 1
        rotaxis = 2

        print "--- AddRun"

        me = "[addrun /RowNumber=%d /RunNumber=%d /FirstImageNumber=%d  /RotAxis=%d  /scansInRun=%d" \
        "/scanTime=%f /Width=%f]"%(rownumber,self.runnumber,firstimagenumber,rotaxis,self.scansinrun,self.scantime,self.width)
        print "sending AddRun message to bis"
        self.command_sock.send(me)
        time.sleep(0.5)
        message = "[scans /FilenameTemplate=%s /Fast=%d]" % (fname_template, 1)
        print message
        try:
            print "sending message to bis"
            self.command_sock.send(message)
            time.sleep(1)
            completed = 0
            noresponse=0
            while completed == 0 and noresponse <10:
                time.sleep(1.0)
                data = self.status_sock.recv(1024)
                #print data
                if not data:
                    print "--no response", noresponse
                    noresponse = noresponse + 1
                    time.sleep(2.0)
                    if noresponse >2:
                        self.reconnect()
                else:
                    noresponse = 0
                    if "[SCAN_YES /RUNNUMBER=" in data:
                        num = data.find("/RUNNUMBER")
                        print data[num:num+30]
                    if "[SCAN(S)DONE]" in data:
                        print "------------- scan is complete"
                        completed=1

                    if ("[ANGLESTATUS" in data):
                        angles = self.parse_anglestatus(data)
                        self.set_angles(angles)
                        self.newangles.emit()
        except socket.error, msg:
            print "Scans error : %s" % msg
        return noresponse
    # open the shutter
    def open_shutter (self) :
        message = "[SHUTTER /STATUS=1]\n"
        try :
            print "sending message to bis"
            self.command_sock.send(message)
            time.sleep(1)
            self.shutter_state.emit(1)

            while (1) :
                data = self.status_sock.recv (BrukerClient.BSIZE)
                print data
                if "[SHUTTERSTATUS" in data :
                    print "SHUTTER status string : "
                    loc = data.find ("[SHUTTER")
                    newstr = data[loc:]
                    print newstr
            

                #print data
        except socket.error, msg :
            print "Open shutter comm error : %s"%msg

    # close the shutter
    def close_shutter (self) :
        message = "[SHUTTER /STATUS=0]\n"
        try :
            print "sending message to bis"
            self.command_sock.send(message)
            time.sleep(1)
            self.shutter_state.emit(0)
            while (1) :
                data = self.status_sock.recv (BrukerClient.BSIZE)
                print data
                if "[SHUTTERSTATUS" in data :
                    print "found message"
                    loc = data.find ("[SHUTTER")
                    newstr = data[loc:]
                    print newstr
                
                

                #print data
        except socket.error, msg :
            print "Close shutter comm error : %s"%msg

    # called by other classes to get BIS values
    def get_values (self, vals) :
        vals[0] = self.shutter_status
        vals[1] = self.twotheta
        vals[2] = self.omega
        vals[3] = self.phi
        vals[4] = self.chi
        vals[5] = self.distance

    def get_gonio_position (self) :
        print "--- gonio position check"
        message = "[GetAxesPositions]"
        self.command_sock.send(message)
        completed = 0
        while completed == 0:
            try:
                time.sleep(0.5)
                data = self.status_sock.recv(1024)
            except socket.error, msg:
                print  "socket error"
            else :
                if ("[ANGLESTATUS" in data):
                    angles=self.parse_anglestatus(data)
                    self.set_angles(angles)
                    self.newangles.emit()
                    completed = 1

    def set_angles (self, angles):
            self.distance = angles[1]
            self.twotheta = angles[2]
            self.omega = angles[3]
            self.phi = angles[4]

    # thread method to check the status socket for any updates.
    def parse_anglestatus (self, text):
        if ("[ANGLESTATUS" in text):
            # print data
            startloc = text.find("[ANGLESTATUS")
            temp = text[startloc:]
            eqsplit = temp.split('=')
            angles = eqsplit[1]
            subangles = angles.split(' ')
            #dist, theta, omega, phi
            return [0,float(eqsplit[2][0:eqsplit[2].find(']')]),float(subangles[0]),float(subangles[1]),float(subangles[2]),float(subangles[3])]
        else: return [-1,0,0,0,0,0] # return -1 if text does not contain "[ANGLESTATUS"

    def run (self) :
        self.bcrun = False # PD changed to false om 5/5/20
        while (self.bcrun) :
            self.newangles.emit()
            self.sleep (2)




#bc = BrukerClient()
#bc.open_shutter()
#bc.close_shutter()
#sys.exit(0)