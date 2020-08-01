from PySide2 import QtWidgets, QtCore, QtGui
from PlotDisplay import PlotDisplay

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, stream):
        QtWidgets.QMainWindow.__init__(self) # super doesn't seem to work here
        self.setWindowTitle("MUGIC Plot")
        self.window_widget = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QVBoxLayout()
        self.window_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.window_widget)
        self.setMinimumSize(1500, 500)
        
        self.stream = stream

        # Create the plot widget to use as the central widget
        self.plot_widget = PlotDisplay(self.stream)
        self.main_layout.addWidget(self.plot_widget)

        # Create the control panel
        self.control_widget = QtWidgets.QWidget(self)
        self.control_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addWidget(self.control_widget)
        self.control_widget.setLayout(self.control_layout)

        toggle_button = QtWidgets.QPushButton()
        toggle_button.setText("Toggle Recording")
        toggle_button.clicked.connect(self.plot_widget.toggle_recording)
        self.control_layout.addWidget(toggle_button)

        reset_button = QtWidgets.QPushButton()
        reset_button.setText("Reset")
        reset_button.clicked.connect(self.plot_widget.reset_recording)
        self.control_layout.addWidget(reset_button)

        export_button = QtWidgets.QPushButton()
        export_button.setText("Export")
        export_button.clicked.connect(self.export_csv)
        self.control_layout.addWidget(export_button)

        # Create the menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        run_menu = menu_bar.addMenu("Run")

        toggle_option = QtGui.QAction("Toggle recording", self)
        toggle_option.setShortcut("Ctrl+R")
        toggle_option.setStatusTip("Start/stop plotting data")
        toggle_option.triggered.connect(self.plot_widget.toggle_recording)
        run_menu.addAction(toggle_option)

        toggle_option = QtGui.QAction("Reset plots", self)
        toggle_option.setShortcut("Ctrl+Backspace")
        toggle_option.setStatusTip("Clear plotting data")
        toggle_option.triggered.connect(self.plot_widget.reset_recording)
        run_menu.addAction(toggle_option)
        
        export_option = QtGui.QAction("Export data...", self)
        export_option.setShortcut("Ctrl+S")
        export_option.setStatusTip("Export accumulated raw and processed data")
        export_option.triggered.connect(self.export_csv)
        file_menu.addAction(export_option)

        # Start the plot loop
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.plot_widget.update)
        self.timer.start(10)


    def export_csv(self):
        filename, _ = QtGui.QFileDialog.getSaveFileName(self, "Export data", "export.csv", "CSV files (*.csv)")

        if(filename):
            self.plot_widget.export_accumulated_data(filename)
    

    # Override to close stream safely
    def closeEvent(self, event):
        self.stream.close()
        event.accept()