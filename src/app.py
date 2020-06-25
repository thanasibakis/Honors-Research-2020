from pyqtgraph import QtGui
import traceback

from ConfigWindow import ConfigWindow
from PlotWindow import PlotWindow

class ErrorWindow(QtGui.QWidget):
    def __init__(self, error_message, traceback_string):
        super().__init__()

        self.message_box = QtGui.QMessageBox()

        self.message_box.setText("An error was encountered. Details can be found below.")
        self.message_box.setInformativeText(error_message)
        self.message_box.setWindowTitle("Error with MUGIC")
        self.message_box.setDetailedText(traceback_string)

        self.message_box.exec_()
        


if __name__ == "__main__":
    try:
        app = QtGui.QApplication([])

        config_window = ConfigWindow()
        stream = config_window.get_stream()

        if stream:
            plot_window = PlotWindow(stream)
            plot_window.show()

            app.exec_()
    
    except Exception as e:
        error_window = ErrorWindow(str(e), traceback.format_exc())

# TODO: no error being thrown when bad wifi config is given