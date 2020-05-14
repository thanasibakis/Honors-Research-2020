from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

import numpy as np
from threading import Thread
from queue import Queue, Empty
from datetime import datetime
import time
import sys

from . import sensor
from . import positioning

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

# Storing the data we collect
accumulated_data = {
    # on the first data collection, we need to change all the 0s in time_sec to the first-seen timestamp value, or else the plot is no good until the time_sec buffer overwrites every 0
    "needs_initializing": True,
    "time_sec":     np.zeros((HISTORY,)),
    "PC1":          np.zeros((HISTORY,)),
    "projected_X":  np.zeros((HISTORY,)),
    "projected_Y": np.zeros((HISTORY,))
}

# Application data
app_data = {
    "data_queue": Queue(),
    "stream": None,
    "curves": [],
    "timer": None,
    "START_TIME": None
}



def debug(level, *args):
    if DEBUG_LEVEL >= level:
        now = datetime.now()
        now_str = f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}"

        print(now_str, *args)

def analyze_data(raw_data):
    # TODO: exponential moving average?

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
            start = time.time()
            raw_data = stream.readlines(n=SAMPLE_SIZE)
            elapsed = time.time() - start

            metrics["data_retrievals"]["sum_time_spent"] += elapsed
            metrics["data_retrievals"]["count"] += 1
            debug(1, "Retrieved data from stream,\t", round(elapsed, 3), "sec, \tavg", round(metrics["data_retrievals"]["sum_time_spent"] / metrics["data_retrievals"]["count"], 3), "sec")

            data_queue.put(raw_data)

    except:  # the connection was closed, so this thread needs to end
        pass



def plot_loop():
    try:
        raw_data = app_data["data_queue"].get_nowait()

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

        # Usually, this size == SAMPLE_SIZE, but occasionally, we read the serial data mid-line and throw that line out,
        # so we need to account for that
        sample_size = len(new_data["time_sec"])

        accumulated_data["time_sec"] = np.roll(accumulated_data["time_sec"], -sample_size)
        accumulated_data["time_sec"][-sample_size:] = new_data["time_sec"]

        accumulated_data["PC1"] = np.roll(accumulated_data["PC1"], -sample_size)
        accumulated_data["PC1"][-sample_size:] = new_data["PC1"]
        
        accumulated_data["projected_X"] = np.roll(accumulated_data["projected_X"], -sample_size)
        accumulated_data["projected_X"][-sample_size:] = new_data["projected_X"]

        accumulated_data["projected_Y"] = np.roll(accumulated_data["projected_Y"], -sample_size)
        accumulated_data["projected_Y"][-sample_size:] = new_data["projected_Y"]


        debug(2, "\t", "Updating plot with data from", new_data["time_sec"][0], "to", new_data["time_sec"][-1])
        app_data["curves"][0].setData(accumulated_data["time_sec"], accumulated_data["PC1"])
        app_data["curves"][1].setData(accumulated_data["projected_X"], accumulated_data["projected_Y"])
        #app.processEvents()

        metrics["plot_updates"]["count"] += 1

    except Empty:
        # No more data is ready yet, let's not hold up the main UI
        debug(2, "\t", "No data available")
        pass

def close_app():
    ELAPSED_TIME = time.time() - app_data["START_TIME"]

    app_data["timer"].stop()
    app_data["stream"].close()

    debug(1, "Avg num plot updates per second:", round(metrics["plot_updates"]["count"] / ELAPSED_TIME, 3))

    
def run_app():
    global sys
    
    debug(2, "Creating data stream")
    if len(sys.argv) > 1 and sys.argv[1] == "usb":
        app_data["stream"] = sensor.SerialStream() # TODO: not sure how well this works on Macs, it seems like they keep spinning up random serial connections
    elif len(sys.argv) > 1 and sys.argv[1] == "simulate":
        app_data["stream"] = sensor.SimulatedStream(delay_ms=5)
    elif len(sys.argv) == 1 or sys.argv[1] == "wifi": # TODO: bad connection is still spinning up a GUI and not printing an error
        app_data["stream"] = sensor.UDPStream()
    else:
        print(f"Unknown mode '{sys.argv[1]}'. Try 'wifi', 'usb', or 'simulate'.")
        sys.exit()
    
    debug(2, "Starting data collection process")
    fetching_thread = Thread(target=retrieve_new_data, args=(app_data["stream"], app_data["data_queue"]))
    fetching_thread.start()

    debug(2, "Creating GUI")
    app = QtGui.QApplication([])
    app.aboutToQuit.connect(close_app)
    window = pg.GraphicsWindow(title=WINDOW_TITLE)
    app_data["curves"] = [ window.addPlot().plot() for _ in range(2) ]

    app_data["timer"] = QtCore.QTimer()
    app_data["timer"].timeout.connect(plot_loop)
    app_data["timer"].start(PLOT_LOOP_INTERVAL)

    app_data["START_TIME"] = time.time()
     
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()


if __name__ == "__main__":
    run_app()