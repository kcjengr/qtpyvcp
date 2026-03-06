QT += designer widgets

HEADERS += \
    gcodeeditor.h \
    gcodehighlighter.h

SOURCES += \
    gcodeeditor.cpp \
    gcodehighlighter.cpp \
    gcodeeditorplugin.cpp

TARGET = $$qtLibraryTarget(gcodeeditorplugin)
DESTDIR = $$[QT_INSTALL_PLUGINS]/designer