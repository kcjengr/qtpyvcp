from led_widget import LEDWidget

from PySide2.QtGui import QIcon
from PySide2.QtDesigner import (QExtensionManager,
    QDesignerCustomWidgetInterface)


DOM_XML = """
<ui language='c++'>
    <widget class='LEDWidget' name='ledWidget'>
        <property name='geometry'>
            <rect>
                <x>0</x>
                <y>0</y>
                <width>200</width>
                <height>200</height>
            </rect>
        </property>
        <property name='state'>
            <string>-X-XO----</string>
        </property>
    </widget>
</ui>
"""


class LEDWidgetPlugin(QDesignerCustomWidgetInterface):
    def __init__(self):
        super().__init__()
        self._form_editor = None

    def createWidget(self, parent):
        t = LEDWidget(parent)
        return t

    def domXml(self):
        return DOM_XML

    def group(self):
        return ''

    def icon(self):
        return QIcon()

    def includeFile(self):
        return 'ledwidget'

    def initialize(self, form_editor):
        self._form_editor = form_editor
        manager = form_editor.extensionManager()
        # iid = TicTacToeTaskMenuFactory.task_menu_iid()
        # manager.registerExtensions(TicTacToeTaskMenuFactory(manager), iid)

    def isContainer(self):
        return False

    def isInitialized(self):
        return self._form_editor is not None

    def name(self):
        return 'LEDWidget'

    def toolTip(self):
        return 'LEDWidget Example, demonstrating class QDesignerTaskMenuExtension (Python)'

    def whatsThis(self):
        return self.toolTip()
