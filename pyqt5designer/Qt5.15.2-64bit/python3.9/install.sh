#!/bin/bash

SCRIPT_PATH=$(dirname "$(realpath -s "$0")")
LIB_PATH="/usr/lib/x86_64-linux-gnu/qt5/plugins/designer"

OLD_LIB=$LIB_PATH/"libpyqt5.so"
if [ -f "$OLD_LIB" ]
then
    echo "renaming existing libpyqt5.so to libpyqt5.so.old"
    mv "$OLD_LIB" "$OLD_LIB.old"
fi

echo "copying libpyqt5.so for python 3.9 to $LIB_PATH"
cp  $SCRIPT_PATH/libpyqt5.so $LIB_PATH
