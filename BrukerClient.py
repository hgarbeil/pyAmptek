import socket
import sys
import time


class BrukerClient :

    BSIZE = 1024
    serverip = '128.171.152.86'

    def __init__(self):
        try :
            self.bcstatus= True
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
            self.get_status()
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
        message = "[drive /distance=20 /2theta=30 /omega=0 /phi=180 ]\n"
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


bc = BrukerClient()
bc.open_shutter()
bc.close_shutter()