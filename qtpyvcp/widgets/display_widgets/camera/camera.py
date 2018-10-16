#!/usr/bin/env python


#############################################################################
#
# Copyright (C) 2013 Riverbank Computing Limited.
# Copyright (C) 2013 Digia Plc and/or its subsidiary(-ies).
# All rights reserved.
#
# This file is part of the examples of PyQt.
#
# $QT_BEGIN_LICENSE:BSD$
# You may use this file under the terms of the BSD license as follows:
#
# "Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
#     the names of its contributors may be used to endorse or promote
#     products derived from this software without specific prior written
#     permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
# $QT_END_LICENSE$
#
#############################################################################

import os

from qtpy import uic

from qtpy.QtCore import QByteArray, Qt, QTimer
from qtpy.QtGui import QPalette, QPixmap
from qtpy.QtWidgets import (QAction, QActionGroup, QApplication,
                             QWidget, QMessageBox)

# Set up logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

multimedia_available = True
try:
    from qtpy.QtMultimedia import (QAudioEncoderSettings, QCamera,
                                    QCameraImageCapture, QImageEncoderSettings, QMediaMetaData,
                                    QMediaRecorder, QVideoEncoderSettings)

    # FixMe: PySide2 is missing QMediaMetaData bingings.
    #        https://wiki.qt.io/Qt_for_Python_Missing_Bindings

    from settings import Settings
except ImportError:
    multimedia_available = False
    LOG.error('Can\'t import QtMultimedia, is package "python-pyqt5.qtmultimedia" installed?')

WIDGET_PATH = os.path.dirname(os.path.abspath(__file__))

class Camera(QWidget):

    def __init__(self, parent=None, standalone=False):
        super(Camera, self).__init__(parent)

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None and not standalone:
            return

        if not multimedia_available:
            return

        self.ui = uic.loadUi(os.path.join(WIDGET_PATH, "camera.ui"), self)

        self.camera = None
        self.imageCapture = None
        self.mediaRecorder = None
        self.isCapturingImage = False
        self.applicationExiting = False

        self.imageSettings = QImageEncoderSettings()
        self.audioSettings = QAudioEncoderSettings()
        self.videoSettings = QVideoEncoderSettings()
        self.videoContainerFormat = ''

        camera_device = QByteArray()

        videoDevicesGroup = QActionGroup(self)

        videoDevicesGroup.setExclusive(True)

        if not QCamera.availableDevices():
            self.ui.devicesCombo.addItem("No Device")
        else:
            for deviceName in QCamera.availableDevices():
                description = QCamera.deviceDescription(deviceName)
                self.ui.devicesCombo.addItem(description)

                videoDeviceAction = QAction(description, videoDevicesGroup)
                videoDeviceAction.setCheckable(True)
                videoDeviceAction.setData(deviceName)

                if camera_device.isEmpty():
                    cameraDevice = deviceName
                    videoDeviceAction.setChecked(True)

                self.ui.devicesCombo.addAction(videoDeviceAction)

        videoDevicesGroup.triggered.connect(self.updateCameraDevice)

        self.ui.captureWidget.currentChanged.connect(self.updateCaptureMode)

        self.ui.devicesCombo.currentIndexChanged.connect(self.get_device_action)

        self.ui.lockButton.hide()

        # Start camera 2s after the UI has loaded
        QTimer.singleShot(2000, lambda: self.setCamera(camera_device))

    def setCamera(self, cameraDevice):
        try:
            if cameraDevice.isEmpty():
                self.camera = QCamera()
            else:
                self.camera = QCamera(cameraDevice)

            self.camera.stateChanged.connect(self.updateCameraState)
            self.camera.error.connect(self.displayCameraError)

            self.mediaRecorder = QMediaRecorder(self.camera)
            self.mediaRecorder.stateChanged.connect(self.updateRecorderState)

            self.imageCapture = QCameraImageCapture(self.camera)

            self.mediaRecorder.durationChanged.connect(self.updateRecordTime)
            self.mediaRecorder.error.connect(self.displayRecorderError)

            self.mediaRecorder.setMetaData(QMediaMetaData.Title, "Camera Widget")

            self.ui.exposureCompensation.valueChanged.connect(
                self.setExposureCompensation)

            self.camera.setViewfinder(self.ui.viewfinder)

            self.updateCameraState(self.camera.state())
            self.updateLockStatus(self.camera.lockStatus(), QCamera.UserRequest)
            self.updateRecorderState(self.mediaRecorder.state())

            self.imageCapture.readyForCaptureChanged.connect(self.readyForCapture)
            self.imageCapture.imageCaptured.connect(self.processCapturedImage)
            self.imageCapture.imageSaved.connect(self.imageSaved)

            self.camera.lockStatusChanged.connect(self.updateLockStatus)

            self.ui.captureWidget.setTabEnabled(0, self.camera.isCaptureModeSupported(QCamera.CaptureStillImage))
            self.ui.captureWidget.setTabEnabled(1, self.camera.isCaptureModeSupported(QCamera.CaptureVideo))

            self.updateCaptureMode()
            self.camera.start()
        except:
            pass

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return

        if event.key() == Qt.Key_CameraFocus:
            self.displayViewfinder()
            self.camera.searchAndLock()
            event.accept()
        elif event.key() == Qt.Key_Camera:
            if self.camera.captureMode() == QCamera.CaptureStillImage:
                self.takeImage()
            elif self.mediaRecorder.state() == QMediaRecorder.RecordingState:
                self.stop()
            else:
                self.record()

            event.accept()
        else:
            super(Camera, self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return

        if event.key() == Qt.Key_CameraFocus:
            self.camera.unlock()
        else:
            super(Camera, self).keyReleaseEvent(event)

    def updateRecordTime(self):
        msg = "Recorded {} sec".format(self.mediaRecorder.duration())
        self.ui.timeLabel.text = msg
        print(msg)

    def processCapturedImage(self, requestId, img):
        scaledImage = img.scaled(self.ui.viewfinder.size(), Qt.KeepAspectRatio,
                                 Qt.SmoothTransformation)

        self.ui.lastImagePreviewLabel.setPixmap(QPixmap.fromImage(scaledImage))

        self.displayCapturedImage()
        QTimer.singleShot(4000, self.displayViewfinder)

    def configureSettings(self):

        settings_dialog = Settings(self.mediaRecorder, self.imageCapture)

        settings_dialog.setImageSettings(self.imageSettings)
        settings_dialog.setAudioSettings(self.audioSettings)
        settings_dialog.setVideoSettings(self.videoSettings)

        settings_dialog.setFormat(self.videoContainerFormat)
        # settings_dialog.setStreamingSettings(self.streamingSettings)

        if settings_dialog.exec_():
            self.imageSettings = settings_dialog.imageSettings()
            self.audioSettings = settings_dialog.audioSettings()
            self.videoSettings = settings_dialog.videoSettings()
            self.videoContainerFormat = settings_dialog.format()

            self.imageCapture.setEncodingSettings(self.imageSettings)
            self.mediaRecorder.setEncodingSettings(self.audioSettings, self.videoSettings, self.videoContainerFormat)

    def record(self):
        self.mediaRecorder.record()
        self.updateRecordTime()

    def pause(self):
        self.mediaRecorder.pause()

    def stop(self):
        self.mediaRecorder.stop()

    def setMuted(self, muted):
        self.mediaRecorder.setMuted(muted)

    def toggleLock(self):
        if self.camera.lockStatus() in (QCamera.Searching, QCamera.Locked):
            self.camera.unlock()
        elif self.camera.lockStatus() == QCamera.Unlocked:
            self.camera.searchAndLock()

    def updateLockStatus(self, status, reason):
        indicationColor = Qt.black

        if status == QCamera.Searching:
            self.ui.statusbar.showMessage("Focusing...")
            self.ui.lockButton.setText("Focusing...")
            indicationColor = Qt.yellow
        elif status == QCamera.Locked:
            self.ui.lockButton.setText("Unlock")
            self.ui.statusbar.showMessage("Focused", 2000)
            indicationColor = Qt.darkGreen
        elif status == QCamera.Unlocked:
            self.ui.lockButton.setText("Focus")

            if reason == QCamera.LockFailed:
                self.ui.statusbar.showMessage("Focus Failed", 2000)
                indicationColor = Qt.red

        palette = self.ui.lockButton.palette()
        palette.setColor(QPalette.ButtonText, indicationColor)
        self.ui.lockButton.setPalette(palette)

    def takeImage(self):
        self.isCapturingImage = True
        self.imageCapture.capture()

    def startCamera(self):
        self.camera.start()

    def stopCamera(self):
        self.camera.stop()


    def updateCaptureMode(self):
        tabIndex = self.ui.captureWidget.currentIndex()
        captureMode = QCamera.CaptureStillImage if tabIndex == 0 else QCamera.CaptureVideo

        if self.camera.isCaptureModeSupported(captureMode):
            self.camera.setCaptureMode(captureMode)

    def updateCameraState(self, state):
        if state == QCamera.ActiveState:
            self.ui.actionStartCamera.setEnabled(False)
            self.ui.actionStopCamera.setEnabled(True)
            self.ui.captureWidget.setEnabled(True)
            self.ui.actionSettings.setEnabled(True)
        elif state in (QCamera.UnloadedState, QCamera.LoadedState):
            self.ui.actionStartCamera.setEnabled(True)
            self.ui.actionStopCamera.setEnabled(False)
            self.ui.captureWidget.setEnabled(False)
            self.ui.actionSettings.setEnabled(False)

    def updateRecorderState(self, state):
        if state == QMediaRecorder.StoppedState:
            self.ui.recordButton.setEnabled(True)
            self.ui.pauseButton.setEnabled(True)
            self.ui.stopButton.setEnabled(False)
        elif state == QMediaRecorder.PausedState:
            self.ui.recordButton.setEnabled(True)
            self.ui.pauseButton.setEnabled(False)
            self.ui.stopButton.setEnabled(True)
        elif state == QMediaRecorder.RecordingState:
            self.ui.recordButton.setEnabled(False)
            self.ui.pauseButton.setEnabled(True)
            self.ui.stopButton.setEnabled(True)

    def setExposureCompensation(self, index):
        self.camera.exposure().setExposureCompensation(index * 0.5)

    def displayRecorderError(self):
        QMessageBox.warning(self, "Capture error",
                            self.mediaRecorder.errorString())

    def displayCameraError(self):
        QMessageBox.warning(self, "Camera error", self.camera.errorString())

    def get_device_action(self, index):
        self.ui.devicesCombo.actions()[index].trigger()

    def updateCameraDevice(self, action):
        self.setCamera(action.data())

    def displayViewfinder(self):
        self.ui.stackedWidget.setCurrentIndex(0)

    def displayCapturedImage(self):
        self.ui.stackedWidget.setCurrentIndex(1)

    def readyForCapture(self, ready):
        self.ui.takeImageButton.setEnabled(ready)

    def imageSaved(self, id, fileName):
        self.isCapturingImage = False

        if self.applicationExiting:
            self.close()

    def closeEvent(self, event):
        if self.isCapturingImage:
            self.setEnabled(False)
            self.applicationExiting = True
            event.ignore()
        else:
            event.accept()


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    camera = Camera(standalone=True)
    camera.show()

    sys.exit(app.exec_())
