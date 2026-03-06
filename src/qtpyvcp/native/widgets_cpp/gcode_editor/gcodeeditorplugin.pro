# gcodeeditorplugin.pro
TEMPLATE = lib
CONFIG += plugin debug_and_release
QT += widgets designer core gui

CONFIG += plugin link_pkgconfig
PKGCONFIG += Qt6Widgets Qt6Core Qt6Gui


# Plugin information
TARGET = $$qtLibraryTarget(gcodeeditorplugin)
# DESTDIR = $$[QT_INSTALL_PLUGINS]/designer

# Source files
HEADERS += \
    gcodeeditor.h \
    gcodeeditorplugin.h \
    gcodehighlighter.h

SOURCES += \
    gcodeeditor.cpp \
    gcodehighlighter.cpp \
    gcodeeditorplugin.cpp

# For Linux/Mac installation
# unix {
#     target.path = $$[QT_INSTALL_PLUGINS]/designer
#     INSTALLS += target
# }

# Build settings
QMAKE_CXXFLAGS += -std=c++17
QMAKE_CXXFLAGS_RELEASE -= -O2
QMAKE_CXXFLAGS_RELEASE += -O3

# Disable warnings that might come from Qt headers
QMAKE_CXXFLAGS_WARN_ON -= -Wall
QMAKE_CXXFLAGS_WARN_ON -= -Wextra

# Additional include paths if needed
INCLUDEPATH += .

# For better debugging
CONFIG += debug
CONFIG += depend_includepath
CONFIG += no_include_pwd

LIBS += -L$$[QT_INSTALL_LIBS] -lQt6Widgets -lQt6Core -lQt6Gui
