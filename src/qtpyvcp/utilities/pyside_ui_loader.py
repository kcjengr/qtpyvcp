#import pydevd; pydevd.settrace()

import subprocess
import xml.etree.ElementTree as xml
class PySide6Ui:
    """
        class to load .ui files to memory or
        convert them to .py files

        based on:
        http://stackoverflow.com/a/14195313/3781327

        usage:
        PySide6Ui('myUi.ui').toPy('myUi.py')
        PySide6Ui('myUi.ui').toPy()

        PySide6Ui('myUi.ui').load()
    """
    def __init__(self, ui_file):
        self.__ui_file = ui_file

    def __getUi(self):
        return subprocess.check_output(['pyside6-uic', self.__ui_file])

    def toPy(self, py_file=None):
        py_file = py_file or self.__ui_file.replace('.ui','.py')
        uipy = self.__getUi()
        try:
            # Write the file
            with open(py_file, 'w') as f:
                f.write(uipy.decode("utf-8"))
            return True
        except:
            return False

    def load(self):
        uipy = self.__getUi()
        parsed = xml.parse(self.__ui_file)
        widget_class = parsed.find('widget').get('class')
        form_class = parsed.find('class').text
        pyc = compile(uipy, '<string>', 'exec')
        frame = {}
        exec(pyc, frame)
        form_class = frame['Ui_%s'%form_class]
        # Base class does not seem to be needed within qtpyvcp.  It also errors
        # when dealing with QDialog classes even though they are QWidget derived.
        # So setting to None until firther investigation is done.
        #base_class = eval('%s'%widget_class)# 'QMainWindow' or 'QWidget'
        base_class = None
        return form_class, base_class
