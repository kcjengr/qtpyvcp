#!/bin/bash

#   Copyright (c) 2018 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of QtPyVCP.
#
#   QtPyVCP is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   QtPyVCP is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with QtPyVCP.  If not, see <http://www.gnu.org/licenses/>.

# Description:
#   Sets up the environment and launches QtDesigner for editing screens .ui files.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

INI_FILE=$PWD/sim/xyz.ini
UI_FILE=$DIR/sim/xyz.ui
PLUGIN=

usage()
{
    echo 'Script for launching QtDesinger for editing QtPyVCP screens.'
    echo ''
    echo './launch_designer.sh'
    echo '    -h, --help                            display this help and exit'
    echo '    -i, --inifile=/path/to/machine.ini    path to the .ini file'
    echo '    -u, --uifile=/path/to/screen.ui       path to the .ui file to edit'
    echo '    -p, --plugin=/path/to/plugins         path to additional plug-ins'
    echo ''
}

while [ "$1" != "" ]; do
    PARAM=`echo $1 | awk -F= '{print $1}'`
    VALUE=`echo $1 | awk -F= '{print $2}'`
    case $PARAM in
        -h | --help)
            usage
            exit
            ;;
        --inifile | -i)
            INI_FILE=$VALUE
            ;;
        --uifile | -u)
            UI_FILE=$VALUE
            ;;
        --plugin | -p)
            PLUGIN:$PLUGIN=$VALUE
            ;;
        *)
            echo "ERROR: unknown parameter \"$PARAM\""
            usage
            exit 1
            ;;
    esac
    shift
done

# setup the environment
export INI_FILE_NAME=$INI_FILE
export CONFIG_DIR=$(dirname -- "$INI_FILE")
export PYTHONPATH=$DIR:$PYTHONPATH
export PYQTDESIGNERPATH=$DIR/QtPyVCP/widgets:$PLUGIN
export QT_SELECT=qt5

# QtDesigner sometimes reads old .pyc files, this ensures that it always recompiles
export PYTHONDONTWRITEBYTECODE=1

# launch the designer
designer $UI_FILE
