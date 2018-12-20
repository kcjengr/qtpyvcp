#!/bin/bash

libpath="/usr/lib/x86_64-linux-gnu/qt5/plugins/designer"

oldlib=$libpath/"libpyqt5.so"
if [ -f "$oldlib" ]
then
    echo "renaming existing libpyqt5.so to libpyqt5.so.old"
    mv "$oldlib" "$oldlib.old"
fi

echo "copying libpyqt5_py2.so to $libpath"
cp  $PWD/libpyqt5_py2.so $libpath

echo "copying libpyqt5_py3.so to $libpath"
cp  $PWD/libpyqt5_py3.so $libpath
