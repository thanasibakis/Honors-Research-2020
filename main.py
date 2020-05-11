from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
from pyqtgraph.ptime import time

import numpy as np
from multiprocessing import Process, Queue
from queue import Empty
from datetime import datetime

import sensor
import positioning

HISTORY = 1000              # number of observations to display
SAMPLE_SIZE = 50            # number of observations to fetch from sensor before integrating/filtering
PLOT_LOOP_INTERVAL = 100    # (ms) how often to plot new data

def debug(*args):
    now = datetime.now()
    now_str = f"{now.hour}:{now.minute}:{now.second}"

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

def retrieve_new_data(queue, stream):
   while True:
       debug("Retrieving data from stream")
       raw_data = stream.readlines(n=SAMPLE_SIZE)

       # keep track of rate of arrival

       debug("\t", "Sending data to queue")
       queue.put(raw_data)


def plot_loop():
    try:
        debug("Retrieving data from queue")
        raw_data = data_queue.get_nowait()

        # run analyze on the last 160 samples... the 80 new ones and the 80 most recent old ones
        # bc the filter should see some overlap to anchor you
        debug("\t", "Analyzing", len(raw_data), "observations")
        new_data = analyze_data(raw_data)
        # then discard the first 80 to plot only the new ones

        accumulated_data["time_sec"] = np.append(accumulated_data["time_sec"], new_data["time_sec"])[-HISTORY:] # only keep last 1000
        accumulated_data["PC1"] = np.append(accumulated_data["PC1"], new_data["PC1"])[-HISTORY:]
        accumulated_data["projected_X"] = np.append(accumulated_data["projected_X"], new_data["projected_X"])[-HISTORY:]
        accumulated_data["projected_Y"] = np.append(accumulated_data["projected_Y"], new_data["projected_Y"])[-HISTORY:]

        debug("\t", "Updating plot with data from", new_data["time_sec"][0], "to", new_data["time_sec"][-1])

        #curve.setData(accumulated_data["PC1"]) # curve = window.plot()
        #app.processEvents()
        window.plot(accumulated_data["time_sec"], accumulated_data["PC1"], clear=True)

    except Empty:
        # No more data is ready yet, let's not hold up the main UI
        debug("\t", "No data available")
        pass

def close_app():
    timer.stop()
    fetching_process.terminate()
    stream.close()

    
if __name__ == "__main__":
    accumulated_data = {
        "time_sec": np.array([]),
        "PC1": np.array([]),
        "projected_X": np.array([]),
        "projected_Y": np.array([])
    }

    debug("Creating data stream")
    stream = sensor.SimulatedStream("mari-bowing-data/variable-speed.csv")  # UDPStream()
    
    debug("Starting data collection process")
    data_queue = Queue()
    fetching_process = Process(target=retrieve_new_data, args=(data_queue,stream))
    fetching_process.start()

    debug("Creating GUI")
    app = QtGui.QApplication([])
    app.aboutToQuit.connect(close_app)
    window = pg.plot(title="Interesting Title")

    timer=QtCore.QTimer()
    timer.timeout.connect(plot_loop)
    timer.start(PLOT_LOOP_INTERVAL)
     
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
