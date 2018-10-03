#!/usr/bin/env python

"""Compile Qt UI and resource files.

Usage:
    To recursively compile all .ui and .qrc files in the current working
    directory and its children run::
        $ ./compile_qt.py .

    You can also specify specific packages to compile::
        $ ./compile_qt.py package1 package2/sub-package ...
"""

import os
import sys
import fnmatch
import subprocess

pyrcc = 'pyrcc5'
pyuic = 'pyuic5'

def compile(packages=['.',]):
    for package in packages:
        package_path = os.path.abspath(package)
        if not os.path.isdir(package_path):
            raise ValueError('Package "{}" not found!'.format(package))

        # Compile Qt UI files

        files = [os.path.join(dirpath, f)
            for dirpath, dirnames, files in os.walk(package_path)
            for f in files if f.endswith('.ui')]

        if len(files) > 0:
            print "Compiling Qt UI files in package '{}':".format(package)

            for infile in files:
                outfile = infile.replace('.ui', '_ui.py')

                sys.stdout.write("  {} => {} ... " \
                                .format(os.path.basename(infile),
                                os.path.basename(outfile))
                                )
                sys.stdout.flush()

                ret = subprocess.call([pyuic, '-o', outfile, infile])
                if ret == 0:
                    print 'OK'


        # Compile Qt resource files

        files = [os.path.join(dirpath, f)
            for dirpath, dirnames, files in os.walk(package_path)
            for f in files if f.endswith('.qrc')]

        if len(files) > 0:
            print "\nCompiling Qt resource files in package '{}':".format(package)

            for infile in files:
                outfile = infile.replace('.qrc', '_rc.py')

                sys.stdout.write("  {} => {} ... " \
                                .format(os.path.basename(infile),
                                os.path.basename(outfile))
                                )
                sys.stdout.flush()

                ret = subprocess.call([pyrcc, '-o', outfile, infile])
                if ret == 0:
                    print 'OK'

if __name__ == '__main__':
    packages = sys.argv[1:]
    if len(packages) == 0 or '-h' in packages:
        print __doc__
    else:
        compile(packages=sys.argv[1:])
