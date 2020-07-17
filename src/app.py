from PySide2 import QtCore, QtWidgets, QtGui
import sys, traceback

from ConfigWindow import ConfigWindow
from MainWindow import MainWindow
from ErrorWindow import ErrorWindow
        


if __name__ == "__main__":
    try:
        app = QtWidgets.QApplication([])

        config_window = ConfigWindow()
        stream = config_window.get_stream()

        if stream:
            main_window = MainWindow(stream)
            main_window.show()

            sys.exit(app.exec_())
    
    except Exception as e:
        error_window = ErrorWindow(str(e), traceback.format_exc())

# TODO: no error being thrown when bad wifi config is given