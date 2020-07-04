import pyqtgraph
from pyqtgraph import QtCore

import pandas as pd
from queue import Queue, Empty
from threading import Thread

import sensor
import positioning


# Config options
WINDOW_TITLE = "MUGIC Plot"
HISTORY = 1000                  # number of observations to display
SAMPLE_SIZE = 10                # number of observations to fetch from sensor before integrating/filtering (lower is smoother animated, but may lag)
REUSE_SIZE = 30                 # number of old samples to include when processing new data, for connectedness & boosted filter performance

# Validate config options
assert SAMPLE_SIZE < HISTORY
assert REUSE_SIZE < HISTORY


def process_data(samples):
    raw_acceleration = samples[["ax", "ay", "az"]]

    rotation_matrices = positioning.quaternions_as_rotation_matrix(samples.qw, samples.qx, samples.qy, samples.qz)
    linear_acceleration = positioning.rotate_each_row(raw_acceleration, rotation_matrices)

    # Get dataframe of x,y,z
    position = linear_acceleration \
        .apply(lambda col: positioning.filter_and_integrate(col, samples.time_sec)) \
        .apply(lambda col: positioning.filter_and_integrate(col, samples.time_sec))

    pca_matrix, pca_data = positioning.PCA(position)

    eig1 = pca_matrix[:, 0]
    new_points = positioning.project_3D_to_2D(position.to_numpy(), eig1)

    return pd.DataFrame({
        "time_sec":    samples.time_sec.values, # .values removes the pd index that throws off DataFrame()
        "PC1":         pca_data.PC1,
        "projected_X": new_points[:, 0],
        "projected_Y": new_points[:, 1]
    })


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

        # Storing accumulated data
        self.accumulated_raw = pd.DataFrame(columns=["time_sec", "ax", "ay", "az", "qw", "qx", "qy", "qz"])
        self.accumulated_processed = pd.DataFrame(columns=["time_sec", "PC1", "projected_X", "projected_Y"])

        # Application data
        self.data_queue = Queue()
        self.plots      = [ self.addPlot() for _ in range(2) ]
        self.curves     = [ plot.plot() for plot in self.plots ]
        self.timer      = QtCore.QTimer()
        self.stream     = stream

        # Start the data collection process
        fetching_thread = Thread(target=retrieve_new_data, args=(self.stream, self.data_queue))
        fetching_thread.start()

        # Start the plot loop
        self.timer.timeout.connect(self.plot_loop)
        self.timer.start(10)
    
    # Add the given data to the accumulated storage,
    # keeping at most the latest HISTORY number of samples
    def accumulate_raw_data(self, raw_data):
        self.accumulated_raw = self.accumulated_raw \
            .append(
                raw_data[self.accumulated_raw.columns],
                ignore_index = True
            ) \
            .tail(HISTORY) \
            .reset_index(drop=True) # pyqtgraph depends on an index starting at 0

    
    def accumulate_processed_data(self, processed_data):
        self.accumulated_processed = self.accumulated_processed \
            .append(
                processed_data[self.accumulated_processed.columns],
                ignore_index = True
            ) \
            .tail(HISTORY) \
            .reset_index(drop=True)




    def plot_loop(self):
        try: 
            raw_data = self.data_queue.get_nowait()
            samples = sensor.parse_bytes(raw_data)
            self.accumulate_raw_data(samples)

            # When integrating/filtering/etc, throw in some old data too...
            processed_data = process_data(self.accumulated_raw.tail(REUSE_SIZE + SAMPLE_SIZE))

            # ...but still only accumulate the new data
            self.accumulate_processed_data(processed_data.tail(SAMPLE_SIZE))
        
        except Empty:
            # No more data is ready yet, let's not hold up the main UI
            pass

        except Exception as ex:
            print(repr(ex)) # the padlen ValueError at the first sample is because we're too short on data to do a filter
        
    

        # We will get errors if we try plotting no data
        if len(self.accumulated_processed.time_sec) == 0:
            return

        self.curves[0].setData(self.accumulated_processed.time_sec, self.accumulated_processed.PC1)
        self.curves[1].setData(self.accumulated_processed.projected_X, self.accumulated_processed.projected_Y)

        self.plots[0].setYRange(
            min(-0.2, self.accumulated_processed.PC1.min()),
            max( 0.2, self.accumulated_processed.PC1.max())
        )

        self.plots[1].setXRange(
            min(-0.1, self.accumulated_processed.projected_X.min()),
            max( 0.1, self.accumulated_processed.projected_X.max())
        )

        self.plots[1].setYRange(
            min(-0.1, self.accumulated_processed.projected_Y.min()),
            max( 0.1, self.accumulated_processed.projected_Y.max())
        )

        
        
    
    def closeEvent(self, event):
        self.stream.close()
        event.accept()
