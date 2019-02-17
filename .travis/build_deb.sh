#!/usr/bin/env bash

echo 'Installing fpm gem...'
gem install fpm

echo 'Creating debs dir'
mkdir debs

export DEB_BUILD=true

echo 'Building debian package in debs/...'
fpm -t deb \
    -p debs/ \
    -s python \
    -f \
    --license "GPLv2" \
    --vendor "KCJ Engineering" \
    --maintainer "'Kurt Jacobson <kcjengr@gmail.com>'" \
    --url "https://qtpyvcp.kcjengr.com" \
    --description "QtPyVCP - Qt and Python based Virtual Control Panel framework for LinuxCNC." \
    -d python-pip \
    -d python-pyqt5 \
    -d python-dbus.mainloop.pyqt5 \
    -d python-pyqt5.qtopengl \
    -d python-pyqt5.qsci \
    -d python-pyqt5.qtmultimedia \
    -d gstreamer1.0-plugins-bad \
    -d libqt5multimedia5-plugins \
    -d pyqt5-dev-tools \
    -d qttools5-dev-tools \
    --after-install .travis/after_install.sh \
    --after-remove .travis/after_remove.sh \
    --no-auto-depends \
    --verbose \
    setup.py

unset DEB_BUILD