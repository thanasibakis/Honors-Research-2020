from PySide2 import QtWidgets, QtCore, QtGui
from PlotDisplay import PlotDisplay

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, stream):
        QtWidgets.QMainWindow.__init__(self) # super doesn't seem to work here
        self.setWindowTitle("MUGIC Plot")
        self.stream = stream

        # Create the plot widget to use as the central widget
        self.plot_widget = PlotDisplay(self.stream)
        self.setCentralWidget(self.plot_widget)

        # Start the plot loop
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.plot_widget.update)
        self.timer.start(10)

        # Configure the menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('File')
        export_button = QtGui.QAction('Export data...', self)
        export_button.setShortcut('Ctrl+S')
        export_button.setStatusTip('Export accumulated raw and processed data')
        export_button.triggered.connect(self.export_csv)
        file_menu.addAction(export_button)


    def export_csv(self):
        filename, _ = QtGui.QFileDialog.getSaveFileName(self, "Export data", "export.csv", "CSV files (*.csv)")

        if(filename):
            self.plot_widget.export_accumulated_data(filename)
    

    # Override to close stream safely
    def closeEvent(self, event):
        self.stream.close()
        event.accept()