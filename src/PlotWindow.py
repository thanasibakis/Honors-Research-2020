import pyqtgraph
from pyqtgraph import QtCore

import numpy as np
from queue import Queue, Empty
from threading import Thread

import sensor
import positioning


# Config options
WINDOW_TITLE = "MUGIC Plot"
HISTORY = 1000                  # number of observations to display
SAMPLE_SIZE = 30                # number of observations to fetch from sensor before integrating/filtering
PLOT_LOOP_INTERVAL = 0          # (ms) how often to plot new data
assert HISTORY > SAMPLE_SIZE    # we make this assumption


def analyze_data(raw_data):
    data = sensor.raw_to_dataframe(raw_data) \
        .pipe(positioning.prepare_data)

    pca_matrix, pca_data = positioning.PCA(data, "x", "y", "z")
    PC1 = pca_data[["time_sec", "PC1"]].to_numpy()

    eig1 = pca_matrix[:, 0]
    xyz = data[["x", "y", "z"]].to_numpy()
    new_points = positioning.project_3D_to_2D(xyz, eig1)

    new_data = {
        "time_sec": PC1[:, 0],
        "PC1": PC1[:, 1],
        "projected_X": new_points[:, 0],
        "projected_Y": new_points[:, 1]
    }

    return new_data


def retrieve_new_data(stream, data_queue):
        try:
            while True:
                raw_data = stream.readlines(n=SAMPLE_SIZE)
                data_queue.put(raw_data)

        except:  # the connection was closed, so this thread needs to end
            pass


class PlotWindow(pyqtgraph.GraphicsWindow):
    def __init__(self, stream):
        super().__init__(title=WINDOW_TITLE)

        # Metrics
        self.metrics = {
            "data_retrievals": {
                "sum_time_spent": 0,
                "count": 0
            },

            "plot_updates": {
                "count": 0
            },

            "data_analysis": {
                "sum_time_spent": 0,
                "count": 0
            }
        }

        # Storing the data we collect
        self.accumulated_data = {
            # on the first data collection, we need to change all the 0s in time_sec to the first-seen timestamp value, or else the plot is no good until the time_sec buffer overwrites every 0
            "needs_initializing": True,
            "time_sec":     np.zeros((HISTORY,)),
            "PC1":          np.zeros((HISTORY,)),
            "projected_X":  np.zeros((HISTORY,)),
            "projected_Y":  np.zeros((HISTORY,))
        }

        # Application data
        self.data_queue = Queue()
        self.curves     = [ self.addPlot().plot() for _ in range(2) ]
        self.timer      = QtCore.QTimer()
        self.stream     = stream

        # Start the data collection process
        fetching_thread = Thread(target=retrieve_new_data, args=(self.stream, self.data_queue))
        fetching_thread.start()

        # Start the plot loop
        self.timer.timeout.connect(self.plot_loop)
        self.timer.start(PLOT_LOOP_INTERVAL)


    def plot_loop(self):
        try:
            raw_data = self.data_queue.get_nowait()
            new_data = analyze_data(raw_data)

           # Plot x-axis correction, see the declaration of accumulated_data
            if (self.accumulated_data["needs_initializing"]):
                self.accumulated_data["time_sec"][:] = new_data["time_sec"][0]
                self.accumulated_data["needs_initializing"] = False

            # Usually, this size == SAMPLE_SIZE, but occasionally, we read the serial data mid-line and throw that line out,
            # so we need to account for that
            sample_size = len(new_data["time_sec"])

            self.accumulated_data["time_sec"] = np.roll(self.accumulated_data["time_sec"], -sample_size)
            self.accumulated_data["time_sec"][-sample_size:] = new_data["time_sec"]

            self.accumulated_data["PC1"] = np.roll(self.accumulated_data["PC1"], -sample_size)
            self.accumulated_data["PC1"][-sample_size:] = new_data["PC1"]
            
            self.accumulated_data["projected_X"] = np.roll(self.accumulated_data["projected_X"], -sample_size)
            self.accumulated_data["projected_X"][-sample_size:] = new_data["projected_X"]

            self.accumulated_data["projected_Y"] = np.roll(self.accumulated_data["projected_Y"], -sample_size)
            self.accumulated_data["projected_Y"][-sample_size:] = new_data["projected_Y"]

            self.curves[0].setData(self.accumulated_data["time_sec"], self.accumulated_data["PC1"])
            self.curves[1].setData(self.accumulated_data["projected_X"], self.accumulated_data["projected_Y"])

        except Empty:
            # No more data is ready yet, let's not hold up the main UI
            pass
        
    
    def closeEvent(self, event):
        self.stream.close()
        event.accept()
