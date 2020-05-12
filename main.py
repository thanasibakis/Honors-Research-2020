from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

import numpy as np
from multiprocessing import Process, Queue
from queue import Empty
from datetime import datetime
import time

import sensor
import positioning

# Config options
WINDOW_TITLE = "MUGIC Plot"
HISTORY = 1000                  # number of observations to display
SAMPLE_SIZE = 30                # number of observations to fetch from sensor before integrating/filtering
PLOT_LOOP_INTERVAL = 0          # (ms) how often to plot new data
DEBUG_LEVEL = 1                 # Level 1: tracking movement of the data
                                # Level 2: also tracking GUI activity
assert HISTORY > SAMPLE_SIZE    # we make this assumption


# Metrics
metrics = {
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


def debug(level, *args):
    if DEBUG_LEVEL >= level:
        now = datetime.now()
        now_str = f"{now.hour:2d}:{now.minute:2d}:{now.second:2d}"

        print(now_str, *args)

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

def retrieve_new_data(data_queue, metrics_queue, stream):
    while True:
        start = time.time()
        raw_data = stream.readlines(n=SAMPLE_SIZE)
        elapsed = time.time() - start

        metrics["data_retrievals"]["sum_time_spent"] += elapsed
        metrics["data_retrievals"]["count"] += 1
        debug(1, "Retrieved data from stream,\t", round(elapsed, 3), "sec, \tavg", round(metrics["data_retrievals"]["sum_time_spent"] / metrics["data_retrievals"]["count"], 3), "sec")

        data_queue.put(raw_data)


def plot_loop():
    try:
        raw_data = data_queue.get_nowait()

        # TODO: run analyze on the last 160 samples... the 80 new ones and the 80 most recent old ones
        # bc the filter should see some overlap to anchor you
        start = time.time()
        new_data = analyze_data(raw_data)
        elapsed = time.time() - start

        metrics["data_analysis"]["sum_time_spent"] += elapsed
        metrics["data_analysis"]["count"] += 1
        debug(1, "Analyzed", len(raw_data), "observations,\t", round(elapsed, 3), "sec, \tavg",
              round(metrics["data_analysis"]["sum_time_spent"] / metrics["data_analysis"]["count"], 3), "sec")
        # then discard the first 80 to plot only the new ones

        # Plot x-axis correction, see the declaration of accumulated_data
        if (accumulated_data["needs_initializing"]):
            accumulated_data["time_sec"][:] = new_data["time_sec"][0]
            accumulated_data["needs_initializing"] = False

        accumulated_data["time_sec"] = np.roll(accumulated_data["time_sec"], -SAMPLE_SIZE)
        accumulated_data["time_sec"][-SAMPLE_SIZE: ] = new_data["time_sec"]

        accumulated_data["PC1"] = np.roll(accumulated_data["PC1"], -SAMPLE_SIZE)
        accumulated_data["PC1"][-SAMPLE_SIZE:] = new_data["PC1"]
        
        accumulated_data["projected_X"] = np.roll(accumulated_data["projected_X"], -SAMPLE_SIZE)
        accumulated_data["projected_X"][-SAMPLE_SIZE:] = new_data["projected_X"]

        accumulated_data["projected_Y"] = np.roll(accumulated_data["projected_Y"], -SAMPLE_SIZE)
        accumulated_data["projected_Y"][-SAMPLE_SIZE:] = new_data["projected_Y"]


        debug(2, "\t", "Updating plot with data from", new_data["time_sec"][0], "to", new_data["time_sec"][-1])
        curves[0].setData(accumulated_data["time_sec"], accumulated_data["PC1"])
        curves[1].setData(accumulated_data["projected_X"], accumulated_data["projected_Y"])
        app.processEvents()

        metrics["plot_updates"]["count"] += 1

    except Empty:
        # No more data is ready yet, let's not hold up the main UI
        debug(2, "\t", "No data available")
        pass

def close_app():
    ELAPSED_TIME = time.time() - START_TIME

    timer.stop()
    fetching_process.terminate()
    stream.close()

    debug(1, "Avg num plot updates per second:", round(metrics["plot_updates"]["count"] / ELAPSED_TIME, 3))

    
if __name__ == "__main__":
    accumulated_data = {
        "needs_initializing": True,                 # on the first data collection, we need to change all the 0s in time_sec to the first-seen timestamp value, or else the plot is no good until the time_sec buffer overwrites every 0
        "time_sec":     np.zeros((HISTORY,)),
        "PC1":          np.zeros((HISTORY,)),
        "projected_X":  np.zeros((HISTORY,)),
        "projected_Y": np.zeros((HISTORY,))
    }

    debug(2, "Creating data stream")
    stream = sensor.UDPStream() #sensor.SimulatedStream(delay_ms = 5)
    
    debug(2, "Starting data collection process")
    data_queue = Queue()
    metrics_queue = Queue()
    fetching_process = Process(target=retrieve_new_data, args=(data_queue, metrics_queue, stream))
    fetching_process.start()

    debug(2, "Creating GUI")
    app = QtGui.QApplication([])
    app.aboutToQuit.connect(close_app)
    window = pg.GraphicsWindow(title=WINDOW_TITLE)
    curves = [ window.addPlot().plot() for _ in range(2) ]

    timer=QtCore.QTimer()
    timer.timeout.connect(plot_loop)
    timer.start(PLOT_LOOP_INTERVAL)

    START_TIME = time.time()
     
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
