import socket
import sys
import time
from PyQt5 import QtCore, QtGui


class BrukerClient (QtCore.QThread) :

    BSIZE = 1024
    serverip = '128.171.152.86'
    shutter_state = QtCore.pyqtSignal(bool)

    def __init__(self):
        QtCore.QThread.__init__(self)
        try :
            self.shutter_status = 0
            self.chi = 0
            self.omega = 0
            self.phi = 0
            self.chi = 0
            self.bcrun = False
            self.bcstatus= True
            self.distance = 0
            self.command_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.command_sock.settimeout(10.)
            #   command_sock.setblocking(0)
            self.file_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.file_sock.settimeout(10.)
            #file_sock.setblocking(0)
            self.status_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.status_sock.settimeout(10.)
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
            self.start()
            time.sleep (20)
            self.bcrun = False
        except socket.error, msg :
            print "Could not connect with socket : %s"%msg
            self.bcstatus = False


    def get_status (self):
        try :
            while (1):
                data = self.status_sock.recv(BrukerClient.BSIZE)
                print data
        except socket.error, msg:
            print "Shutter status error : %s" % msg

    def drive_to_default (self) :
        message = "[drive /distance=20 /2theta=-30 /omega=0 /phi=180 ]\n"
        try :
            print "sending message to bis"
            self.command_sock.send(message)
            time.sleep(1)
            while (1) :
                data = self.status_sock.recv (BrukerClient.BSIZE)
                print data
                if "[AXES" in data :
                    print "found message"
                    loc = data.find ("[AXES")
                    newstr = data[loc:]
                    print newstr

                #print data
        except socket.error, msg :
            print "Drive error : %s"%msg


    def open_shutter (self) :
        message = "[SHUTTER /STATUS=1]\n"
        try :
            print "sending message to bis"
            self.command_sock.send(message)
            time.sleep(1)
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
            print "Open shutter comm error : %s"%msg

    def close_shutter (self) :
        message = "[SHUTTER /STATUS=0]\n"
        try :
            print "sending message to bis"
            self.command_sock.send(message)
            time.sleep(1)
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

    def get_values (self, vals) :
        vals[0] = self.shutter_status
        vals[1] = self.twotheta
        vals[2] = self.omega
        vals[3] = self.phi
        vals[4] = self.chi
        vals[5] = self.distance

    def run (self) :
        self.bcrun = True
        while (self.bcrun) :
            data = self.status_sock.recv(BrukerClient.BSIZE)
            #print data
            if ("[SHUTTERSTATUS" in data) :
                startloc = data.find("[SHUTTERSTATUS")
                temp = data[startloc:]
                eqloc = temp.find('=')
                self.shutter_status  = int(temp[eqloc+1])
                print "**shutter is ** ", self.shutter_status
            if ("[ANGLESTATUS" in data) :
                print data
                startloc = data.find ("[ANGLESTATUS")
                temp = data [startloc:]
                eqsplit = temp.split('=')
                angles = eqsplit[1]
                subangles = angles.split(' ')
                print "ANGLES ARE 2theta ",subangles[0], ' omega : ',subangles[1], " phi : ", subangles[2], " chi : ", subangles[3]
                print "Distance is : ", eqsplit[2][0:eqsplit[2].find(']')]
                self.twotheta = float(subangles[0])
                self.phi=float(subangles[2])
                self.omega=float(subangles[1])
                self.distance=float (eqsplit[2][0:eqsplit[2].find(']')])

            if (len(data) == 0) :
                self.sleep (1)




bc = BrukerClient()
#bc.open_shutter()
#bc.close_shutter()
sys.exit(0)