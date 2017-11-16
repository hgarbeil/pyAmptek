#ifndef X123LIB_GLOBAL_H
#define X123LIB_GLOBAL_H

#include <QtCore/qglobal.h>

#if defined(X123LIB_LIBRARY)
#  define X123LIBSHARED_EXPORT Q_DECL_EXPORT
#else
#  define X123LIBSHARED_EXPORT Q_DECL_IMPORT
#endif

#endif // X123LIB_GLOBAL_H
