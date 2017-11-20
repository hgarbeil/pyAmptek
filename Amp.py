import ctypes
import numpy as np

amplib = ctypes.cdll.LoadLibrary(r"C:/Users/harold/workdir/pyAmptek/X123Lib/X123.dll")


class Amp(object):

    # constructor
    def __init__(self):
        amplib.X123_const.argtypes = []
        amplib.X123_const.restype = ctypes.c_void_p

        self.ampobj = amplib.X123_const()

        # set the data being sent to spectrometer for access to regularly plotting
        self.ydata = np.zeros ((2048),dtype=np.int64)
        amplib.X123_setData.argtypes=[ctypes.c_void_p,np.ctypeslib.ndpointer(np.int64, flags='C_CONTIGUOUS')]
        amplib.X123_setData.restypes= ctypes.c_void_p
        amplib.X123_setData (self.ampobj, self.ydata)

    #connect to usb spectrometer
    def connect(self):
        amplib.X123_connUSB.argtypes = [ ctypes.c_void_p]
        amplib.X123_connUSB.restype = ctypes.c_bool
        stat = amplib.X123_connUSB(self.ampobj)

        amplib.X123_clearSpec.argtypes = [ctypes.c_void_p]
        amplib.X123_clearSpec.restype = ctypes.c_void_p
        amplib.X123_clearSpec (self.ampobj)

        amplib.X123_readCFil.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        amplib.X123_readCFil.restypes = ctypes.c_void_p
        str = 'C:/configfile.txt'
        amplib.X123_readCFil (self.ampobj, str)

    #disconnect the spectrometer
    def disconnect(self):
        amplib.X123_disconnUSB.argtypes = [ ctypes.c_void_p]
        amplib.X123_disconnUSB.restype = ctypes.c_bool
        amplib.X123_disconnUSB(self.ampobj)

    # set spectrum file
    def set_spectrum_file (self, specfile) :
        amplib.X123_setSpecFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        amplib.X123_setSpecFile.restypes = ctypes.c_void_p
        amplib.X123_setSpecFile (self.ampobj, specfile)

    # set acquisition Time
    def set_acquisition_time (self, secs) :
        amplib.X123_setAcquisitonTime.argtypes = [ctypes.c_void_p, ctypes.c_int16]
        amplib.X123_setAcquisitionTime.restypes = ctypes.c_void_p
        amplib.X123_setAcquisitionTime (self.ampobj, secs)

    # start acquisition
    def start_acquisition (self) :
        amplib.X123_start_acquisition.argtypes = [ctypes.c_void_p]
        amplib.X123_start_acquisition.restypes = ctypes.c_void_p
        amplib.X123_start_acquisition(self.ampobj)



a = Amp()
status = a.connect()
a.disconnect()
print status
