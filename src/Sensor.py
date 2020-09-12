from queue import Queue, Empty
from datetime import datetime
from threading import Thread
import pandas as pd
import time

import config, tools


# An interface to the data coming in from the sensor.
# Anybody who would like to alter the way the positioning is calculated would
# want to modify Sensor.calculate_position, and perhaps Sensor.process_next_batch (which calls it)
class Sensor:
    def __init__(self, stream, batch_size = config.BATCH_SIZE, reuse_size = config.REUSE_SIZE):
        self.stream = stream
        self.batch_size = batch_size
        self.reuse_size = reuse_size
        self.data_queue = Queue()

        self.reset_recording()

        self.done_calibrating = False

        fetching_thread = Thread(target=retrieve_new_data, args=(self.stream, self.batch_size, self.data_queue))
        fetching_thread.start()


    # The positioning algorithm.
    # Given batches of raw samples, attempt to determine current velocity and position, as well as
    # the first principal components of those measurements and a projection of position onto the 
    # other two components. 
    def calculate_position(self, samples, integration_correction = True):
        raw_acceleration = samples[["ax", "ay", "az"]]

        rotation_matrices = tools.quaternions_as_rotation_matrix(samples.qw, samples.qx, samples.qy, samples.qz)
        linear_acceleration = tools.rotate_each_row(raw_acceleration, rotation_matrices)

        # Get dataframes of velocity and x,y,z
        velocity = linear_acceleration \
            .apply(lambda col: tools.filter_and_integrate(col, samples.time_sec))

        if integration_correction:
            mean_old_v = self.accumulated_processed \
                .tail(self.reuse_size - self.batch_size)[["vx", "vy", "vz"]] \
                .mean(axis = 0)

            mean_new_v = velocity \
                .head(self.reuse_size - self.batch_size) \
                .mean(axis = 0)

            offset = mean_old_v.to_numpy() - mean_new_v.to_numpy() # to numpy bc of the different colnames :(
            velocity = velocity.apply(lambda row: row + offset, axis = 1)

        position = velocity \
            .apply(lambda col: tools.filter_and_integrate(col, samples.time_sec))

        if integration_correction:
            mean_old_p = self.accumulated_processed \
                .tail(self.reuse_size - self.batch_size)[["x", "y", "z"]] \
                .mean(axis = 0)

            mean_new_p = position \
                .head(self.reuse_size - self.batch_size) \
                .mean(axis = 0)

            offset = mean_old_p.to_numpy() - mean_new_p.to_numpy()
            position = position.apply(lambda row: row + offset, axis = 1)

        _, velocity_PCs = tools.PCA(velocity)
        position_matrix, position_PCs = tools.PCA(position)

        eig1 = position_matrix[:, 0]
        new_points = tools.project_3D_to_2D(position.to_numpy(), eig1)

        return pd.DataFrame({
            "time_sec":    samples.time_sec.values, # .values removes the pd index that throws off DataFrame()
            "position":    position_PCs.PC1,
            "x":           position.ax,
            "y":           position.ay,
            "z":           position.az,
            "velocity":    velocity_PCs.PC1,
            "vx":          velocity.ax,
            "vy":          velocity.ay,
            "vz":          velocity.az,
            "projected_X": new_points[:, 0],
            "projected_Y": new_points[:, 1]
        })


    # Note that the data withheld for calibration won't have been processed, but will be exported    
    def export_accumulated_data(self, filename):
        log_message(2, "Exporting accumulated data")

        pd.merge(self.accumulated_raw, self.accumulated_processed, how = "outer", on = "time_sec") \
            .to_csv(filename)


    # Accumulates and analyzes the next batch of data. This is to be called reguarly from the GUI loop.
    def process_next_batch(self):
        samples = parse_bytes(self.data_queue.get_nowait())

        # Always collect data to keep the queue fresh, but throw it out if we don't want it
        if(self.should_record):
            self._accumulate_raw_data(samples)

            # Make sure we have enough data before we run any filters
            assert self.accumulated_raw.shape[0] >= self.reuse_size + self.batch_size

            # The first time we have enough data, we need to integrate the entire set of calibration batches,
            # so we have an initial reference to add to when integrating future data
            if not self.done_calibrating:
                calibrated_data = self.calculate_position(self.accumulated_raw, integration_correction=False)
                self._accumulate_processed_data(calibrated_data)

                self.done_calibrating = True

            else:
                # When integrating/filtering/etc, throw in some old data too... otherwise the batches are disconnected
                processed_data = self.calculate_position(self.accumulated_raw.tail(self.reuse_size + self.batch_size))

                # ...but still only accumulate the new data
                new_data = processed_data.tail(self.batch_size)
                self._accumulate_processed_data(new_data)


    # Clear out plots and accumulated data
    def reset_recording(self):
        self.should_record = False
        self.done_calibrating = False

        self.accumulated_raw = pd.DataFrame(columns=["time_sec", "ax", "ay", "az", "qw", "qx", "qy", "qz"])
        self.accumulated_processed = pd.DataFrame(columns=["time_sec", "vx", "vy", "vz", "x", "y", "z", "position", "velocity", "projected_X", "projected_Y"])


    # Toggle whether to accumulate and plot data. Either way, the fetching thread runs,
    # so when we toggle on, we pick up with the data that is new, not the data during the toggle off
    def toggle_recording(self):
        self.should_record = not self.should_record


    # Add the given data to the accumulated storage.
    # We save this so we have data to reuse when integrating
    def _accumulate_raw_data(self, raw_data):
        self.accumulated_raw = self.accumulated_raw.append(
            raw_data[self.accumulated_raw.columns],
            ignore_index = True
        )

    # Add the given data to the accumulated storage.
    # We save this both for plotting and for the integration correction in the analysis
    def _accumulate_processed_data(self, processed_data):
        self.accumulated_processed = self.accumulated_processed.append(
            processed_data[self.accumulated_processed.columns],
            ignore_index = True
        )


# Printing, but cooler
def log_message(error_level, msg):
    if(error_level <= config.DEBUG_LEVEL):
        print(datetime.now(), '\t', msg)


# An infinite loop to be run in a separate thread, so the sensor's stream is never blocked.
# Data can be retrieved at will from the given queue.
def retrieve_new_data(stream, n_lines, data_queue):
    try:
        while True:
            raw_data = stream.readlines(n_lines)
            data_queue.put(raw_data)

    except:  # the connection was closed, so this thread needs to end
        log_message(2, "Fetching has been halted.")


# Converts the raw output from the sensor to a Pandas data frame
def parse_bytes(raw_data: [bytes]) -> pd.DataFrame:
    rows = []

    for line in raw_data:
        try:
            line = line.decode("utf-8").strip()

            if line.startswith("mugicdata"): # Keep only lines with mugicdata prefix
                rows.append(line.split(' ')[1:])  # but lose that prefix
        
        except:
            print("A line of data was corrupt. This is likely because you are running on serial mode and read the data mid-line. This line will be thrown out and is probably nothing to worry about.")

    return pd.DataFrame(rows, dtype="double", columns = config.COLUMNS)