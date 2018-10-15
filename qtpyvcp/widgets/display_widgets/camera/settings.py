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

from PyQt5 import uic

from PyQt5.QtCore import qFuzzyCompare
from PyQt5.QtMultimedia import QMultimedia
from PyQt5.QtWidgets import QDialog

WIDGET_PATH = os.path.dirname(os.path.abspath(__file__))


class Settings(QDialog):

    def __init__(self, mediaRecorder, imageCapture, parent=None):
        super(Settings, self).__init__(parent)

        self.imagecapture = imageCapture
        self.mediaRecorder = mediaRecorder

        self.ui = uic.loadUi(os.path.join(WIDGET_PATH, "settings.ui"), self)

        self.ui.imageCodecBox.addItem("Default image format", "")
        for codecName in self.imagecapture.supportedImageCodecs():
            description = self.imagecapture.imageCodecDescription(codecName)
            self.ui.imageCodecBox.addItem("{}: {}".format(codecName, description), codecName)

        self.ui.imageQualitySlider.setRange(0, QMultimedia.VeryHighQuality)

        self.ui.imageResolutionBox.addItem("Default resolution")
        supportedResolutions, _ = self.imagecapture.supportedResolutions()
        for resolution in supportedResolutions:
            self.ui.imageResolutionBox.addItem("{}x{}".format(resolution.width(), resolution.height()), resolution)

        self.ui.audioCodecBox.addItem("Default audio codec", "")
        for codecName in self.mediaRecorder.supportedAudioCodecs():
            description = self.mediaRecorder.audioCodecDescription(codecName)
            self.ui.audioCodecBox.addItem("{}: {}".format(codecName, description), codecName)

        supportedSampleRates, _ = self.mediaRecorder.supportedAudioSampleRates()
        for sampleRate in supportedSampleRates:
            self.ui.audioSampleRateBox.addItem(str(sampleRate), sampleRate)

        self.ui.audioQualitySlider.setRange(0, QMultimedia.VeryHighQuality)

        self.ui.videoCodecBox.addItem("Default video codec", "")
        for codecName in self.mediaRecorder.supportedVideoCodecs():
            description = self.mediaRecorder.videoCodecDescription(codecName)
            self.ui.videoCodecBox.addItem("{}: {}".format(codecName, description.encode("utf-8")), codecName)

        self.ui.videoQualitySlider.setRange(0, QMultimedia.VeryHighQuality)

        self.ui.videoResolutionBox.addItem("Default")
        supportedResolutions, _ = self.mediaRecorder.supportedResolutions()
        for resolution in supportedResolutions:
            self.ui.videoResolutionBox.addItem("{}x{}".format(resolution.width(), resolution.height()), resolution)

        self.ui.videoFramerateBox.addItem("Default")
        supportedFrameRates, _ = self.mediaRecorder.supportedFrameRates()
        for rate in supportedFrameRates:
            self.ui.videoFramerateBox.addItem("{}".format(rate), rate)

        self.ui.containerFormatBox.addItem("Default container", "")
        for format in self.mediaRecorder.supportedContainers():
            self.ui.containerFormatBox.addItem("{}: {}".format(format, self.mediaRecorder.containerDescription(format)),
                                               format)

    def imageSettings(self):
        settings = self.imagecapture.encodingSettings()
        settings.setCodec(self.boxValue(self.ui.imageCodecBox))
        settings.setQuality(
            QMultimedia.EncodingQuality(
                self.ui.imageQualitySlider.value()))

        resolution = self.boxValue(self.ui.imageResolutionBox)

        if resolution:
            settings.setResolution(resolution)

        return settings

    def setImageSettings(self, settings):

        self.selectComboBoxItem(self.ui.imageCodecBox, settings.codec())
        self.selectComboBoxItem(self.ui.imageResolutionBox, settings.resolution())
        self.ui.imageQualitySlider.setValue(settings.quality())

    def audioSettings(self):
        settings = self.mediaRecorder.audioSettings()
        settings.setCodec(self.boxValue(self.ui.audioCodecBox))
        settings.setQuality(
            QMultimedia.EncodingQuality(
                self.ui.audioQualitySlider.value()))

        if self.ui.audioSampleRateBox.count() > 1:
            sample_rate = self.boxValue(self.ui.audioSampleRateBox)
            settings.setSampleRate(sample_rate)

        return settings

    def setAudioSettings(self, settings):
        self.selectComboBoxItem(self.ui.audioCodecBox, settings.codec())
        self.selectComboBoxItem(self.ui.audioSampleRateBox, settings.sampleRate())
        self.ui.audioQualitySlider.setValue(settings.quality())

    def videoSettings(self):
        settings = self.mediaRecorder.videoSettings()
        settings.setCodec(self.boxValue(self.ui.videoCodecBox))
        settings.setQuality(QMultimedia.EncodingQuality(self.ui.videoQualitySlider.value()))

        if self.ui.videoResolutionBox.count() > 1 and self.ui.videoResolutionBox.currentIndex() != 0:
            settings.setResolution(self.boxValue(self.ui.videoResolutionBox))

        if self.ui.videoFramerateBox.count() > 1 and self.ui.videoFramerateBox.currentIndex() != 0:
            settings.setFrameRate(self.boxValue(self.ui.videoFramerateBox))

        return settings

    def setVideoSettings(self, settings):
        self.selectComboBoxItem(self.ui.videoCodecBox, settings.codec())
        self.selectComboBoxItem(self.ui.videoResolutionBox, settings.resolution())
        self.ui.videoQualitySlider.setValue(settings.quality())

        for i in range(1, self.ui.videoFramerateBox.count()):
            itemRate = self.ui.videoFramerateBox.itemData(i)
            if qFuzzyCompare(itemRate, settings.frameRate()):
                self.ui.videoFramerateBox.setCurrentIndex(i)
                break

    def format(self):
        return self.boxValue(self.ui.containerFormatBox)

    def setFormat(self, format):
        self.selectComboBoxItem(self.ui.containerFormatBox, format)

    @staticmethod
    def boxValue(box):
        idx = box.currentIndex()
        if idx == -1:
            return None

        return box.itemData(idx)

    @staticmethod
    def selectComboBoxItem(box, value):
        for i in range(box.count()):
            if box.itemData(i) == value:
                box.setCurrentIndex(i)
                break
