#-------------------------------------------------
#
# Project created by QtCreator 2017-11-15T11:29:56
#
#-------------------------------------------------

QT       -= core gui

TARGET = X123Lib
TEMPLATE = lib

DEFINES += X123LIB_LIBRARY

# The following define makes your compiler emit warnings if you use
# any feature of Qt which as been marked as deprecated (the exact warnings
# depend on your compiler). Please consult the documentation of the
# deprecated API in order to know how to port your code away from it.
DEFINES += QT_DEPRECATED_WARNINGS

# You can also make your code fail to compile if you use deprecated APIs.
# In order to do so, uncomment the following line.
# You can also select to disable deprecated APIs only up to a certain version of Qt.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0

SOURCES += \
    DeviceIO/DP5Protocol.cpp \
    DeviceIO/DP5Status.cpp \
    DeviceIO/DppLibUsb.cpp \
    DeviceIO/DppUtilities.cpp \
    DeviceIO/ParsePacket.cpp \
    DeviceIO/SendCommand.cpp \
    ConsoleHelper.cpp \
    stringex.cpp \
    x123.cpp

HEADERS += \
    DeviceIO/DP5Protocol.h \
    DeviceIO/DP5Status.h \
    DeviceIO/DppConst.h \
    DeviceIO/DppLibUsb.h \
    DeviceIO/DppUtilities.h \
    DeviceIO/libusb.h \
    DeviceIO/ParsePacket.h \
    DeviceIO/SendCommand.h \
    DeviceIO/stringex.h \
    ConsoleHelper.h \
    stringex.h \
    stringSplit.h \
    x123.h

INCLUDEPATH += ./DeviceIO ./
LIBS += -L../X123Lib/DeviceIO -lstdc++ -lm ../X123Lib/DeviceIO/libusb.lib

unix {
    target.path = /usr/lib
    INSTALLS += target
}
