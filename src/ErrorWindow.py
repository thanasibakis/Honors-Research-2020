from PySide2 import QtWidgets

class ErrorWindow(QtWidgets.QWidget):
    def __init__(self, error_message, traceback_string):
        super().__init__()

        self.message_box = QtWidgets.QMessageBox()

        self.message_box.setText("An error was encountered. Details can be found below.")
        self.message_box.setInformativeText(error_message)
        self.message_box.setWindowTitle("Error with MUGIC")
        self.message_box.setDetailedText(traceback_string)

        self.message_box.exec_()