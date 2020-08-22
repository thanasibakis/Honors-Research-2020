from PySide2 import QtWidgets, QtCore, QtGui
from PlotWidget import PlotWidget
import sys

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, sensor):
        QtWidgets.QMainWindow.__init__(self) # super doesn't seem to work here
        self.setWindowTitle("MUGIC Plot")
        self.window_widget = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QVBoxLayout()
        self.window_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.window_widget)
        self.setMinimumSize(1500, 500)
        
        self.sensor = sensor

        # Create the plot widget to use as the central widget
        self.plot_widget = PlotWidget(sensor)
        self.main_layout.addWidget(self.plot_widget)

        # Create the control panel
        self.control_widget = QtWidgets.QWidget(self)
        self.control_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addWidget(self.control_widget)
        self.control_widget.setLayout(self.control_layout)

        self.toggle_button = QtWidgets.QPushButton()
        self.toggle_button.setText("Start Recording")
        self.toggle_button.clicked.connect(self.toggle_recording)
        self.control_layout.addWidget(self.toggle_button)

        reset_button = QtWidgets.QPushButton()
        reset_button.setText("Reset")
        reset_button.clicked.connect(self.reset_recording)
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
        toggle_option.triggered.connect(self.toggle_recording)
        run_menu.addAction(toggle_option)

        toggle_option = QtGui.QAction("Reset plots", self)
        toggle_option.setShortcut("Ctrl+Backspace")
        toggle_option.setStatusTip("Clear plotting data")
        toggle_option.triggered.connect(self.reset_recording)
        run_menu.addAction(toggle_option)
        
        export_option = QtGui.QAction("Export data...", self)
        export_option.setShortcut("Ctrl+S")
        export_option.setStatusTip("Export accumulated raw and processed data")
        export_option.triggered.connect(self.export_csv)
        file_menu.addAction(export_option)

        # Create the output console
        self.console = QtGui.QTextEdit()
        self.console.moveCursor(QtGui.QTextCursor.Start)
        self.console.ensureCursorVisible()
        self.main_layout.addWidget(self.console)

        # Hook up stdout to the console
        sys.stdout = TextStream()
        sys.stdout.signal.connect(self.update_text)

        # Start the plot loop
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.plot_widget.update_plot)
        self.timer.start(10)

    # https://stackoverflow.com/questions/44432276
    def update_text(self, text):
        cursor = self.console.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.console.setTextCursor(cursor)
        self.console.ensureCursorVisible()

    def toggle_recording(self):
        is_now_recording = self.sensor.toggle_recording()

        if is_now_recording:
            self.toggle_button.setText("Stop Recording")

        else:
            self.toggle_button.setText("Start Recording")

    def reset_recording(self):
        self.sensor.reset()
        self.toggle_button.setText("Start Recording")

    def export_csv(self):
        filename, _ = QtGui.QFileDialog.getSaveFileName(self, "Export data", "export.csv", "CSV files (*.csv)")

        if(filename):
            self.sensor.accumulated_data.to_csv(filename)
    

    # Override to close stream safely
    def closeEvent(self, event):
        self.sensor.close_stream()
        sys.stdout = sys.__stdout__

        event.accept()


# https://stackoverflow.com/questions/21071448
class TextStream(QtCore.QObject):
    signal = QtCore.Signal(str)

    def write(self, text):
        self.signal.emit(text)
