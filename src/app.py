# The program entrypoint: python3 src/app.py

from PySide2 import QtCore, QtWidgets, QtGui
import sys, traceback

from ConfigWindow import ConfigWindow
from MainWindow import MainWindow
from ErrorWindow import ErrorWindow
from Sensor import Sensor
import config


if __name__ == "__main__":
    try:
        app = QtWidgets.QApplication([])

        config_window = ConfigWindow()
        setup = config_window.get_setup()

        if setup:
            stream, batch_size, reuse_size = setup

            assert batch_size < config.HISTORY

            sensor = Sensor(stream, batch_size, reuse_size)

            main_window = MainWindow(sensor)
            main_window.show()

            sys.exit(app.exec_())
    
    except Exception as e:
        error_window = ErrorWindow(str(e), traceback.format_exc())

# TODO: no error being thrown when bad wifi config is given