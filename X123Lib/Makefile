
 
CC = g++
cc = gcc
CFLAGS = -Wall -g -Os
LD = ${CC}
SONAME = X123.dll
INCLUDES = -IDeviceIO
LIBS = -LDeviceIO -lusb-1.0


OBJS = x123.o  \
		ConsoleHelper.o \
		DeviceIO/DP5Protocol.o \
		DeviceIO/DP5Status.o \
		DeviceIO/DppLibUsb.o \
		DeviceIO/DppUtilities.o \
		DeviceIO/ParsePacket.o \
		DeviceIO/SendCommand.o \
		stringex.o 

${SONAME}: ${OBJS} 
	${CC} -shared -o ${SONAME} ${OBJS} ${LIBS}
	



# You don't even need to be explicit here,
# compiling C files is handled automagically by Make.
.c.o: 
	${CC} ${CFLAGS} ${INCLUDES} -c $^ -o $@
.cpp.o: 
	${CC} ${CFLAGS}  ${INCLUDES} -c $^ -o $@

