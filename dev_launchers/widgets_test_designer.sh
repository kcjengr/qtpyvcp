#!/bin/bash

source /home/g0704/Dev/venv/bin/activate
cd /home/g0704/Dev/qtpyvcp/src/video_tests/widgets_test
editvcp --ui-file mainwindow.ui --yaml-file config.yml 2>&1 | tee /tmp/widgets_designer.log
