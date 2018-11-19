#!/usr/bin/env python

"""QCompile - compile .ui and .qrc files to Python

    Recursively compiles all Qt .ui and .qrc files in the
    specified package(s).

Usage:
  qcompile <package> ...
  qcompile -h

Example::

  $ qcompile .
  $ qcompile package1 package2/subpackage
"""

import os
import sys
import fnmatch
import subprocess

pyrcc = 'pyrcc5'
pyuic = 'pyuic5'

ok = "\033[32mok\033[0m"
error = "\033[31mERROR - unable to call {}\033[0m"


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
            print "Compiling .ui files in package '{}':".format(package)

            for infile in files:
                outfile = infile.replace('.ui', '_ui.py')

                sys.stdout.write("  {} => {} ... "
                                 .format(os.path.basename(infile),
                                         os.path.basename(outfile))
                                 )
                sys.stdout.flush()

                try:
                    ret = subprocess.call([pyuic, '-o', outfile, infile])
                except OSError:
                    print error.format(pyuic)
                    break
                if ret == 0:
                    print ok

        # Compile Qt resource files
        files = [os.path.join(dirpath, f)
                 for dirpath, dirnames, files in os.walk(package_path)
                 for f in files if f.endswith('.qrc')]

        if len(files) > 0:
            print "\nCompiling .qrc files in package '{}':".format(package)

            for infile in files:
                outfile = infile.replace('.qrc', '_rc.py')

                sys.stdout.write("  {} => {} ... " \
                                 .format(os.path.basename(infile),
                                         os.path.basename(outfile))
                                 )
                sys.stdout.flush()

                try:
                    ret = subprocess.call([pyrcc, '-o', outfile, infile])
                except OSError:
                    print error.format(pyrcc)
                    break
                if ret == 0:
                    print ok


def main():
    packages = sys.argv[1:]
    if len(packages) == 0 or '-h' in packages:
        print __doc__
    else:
        compile(packages=sys.argv[1:])


if __name__ == '__main__':
    main()
