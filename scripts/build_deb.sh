echo 'Installing fpm gem...'
gem install fpm

echo 'Building debian package...'
fpm -s python \
    -p debs/ \
    -d python-pyqt5 \
    -d python-dbus.mainloop.pyqt5 \
    -d python-pyqt5.qtopengl \
    -d python-pyqt5.qsci \
    -d python-pyqt5.qtmultimedia \
    -d gstreamer1.0-plugins-bad \
    -d libqt5multimedia5-plugins \
    -d pyqt5-dev-tools \
    -f \
    -m "Kurt Jacobson" \
    -t deb setup.py
