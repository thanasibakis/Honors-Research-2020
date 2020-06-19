import os
import pandas as pd
import pickle
import serial  # pySerial package
import serial.tools.list_ports
import socket
import subprocess
import sys
import time
from datetime import datetime

import mugic


IP = "192.168.4.2"
UDP_PORT = 4000
BAUD = 115200
COLUMNS = ["ax", "ay", "az", "ex", "ey", "ez", "gx", "gy", "gz", "mx", "my", "mz", "qw", "qx", "qy", "qz", 
           "BatteryPercent", "SystemStatus", "GyroStatus", "AccelStatus", "MagStatus", "Timestamp", "SequenceNum"]


# Template class
class DataStream:
    def readline(self):
        pass

    def readlines(self, n):
        return [self.readline() for _ in range(n)]

    def read_for_time(self, seconds):
        output = []
        start_time = time.time()

        while time.time() - start_time < seconds:
            output.append(self.readline())

        return output # you strip the first line if this is serial, in case we read it mid-broadcast
        
    def close(self):
        pass

class UDPStream(DataStream):
    def __init__(self, ip=IP, port=UDP_PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            self.socket.bind((ip, port))

        except OSError:
            print("Could not find the device.")
            sys.exit()

    def readline(self):
        data, addr = self.socket.recvfrom(1024)

        return data

    def close(self):
        self.socket.close()


class SerialStream(DataStream):
    def __init__(self, port=None):
        if not port:
            print("Please unplug your device, if it is plugged in. Then press ENTER...", end='')
            input()
            old_ports = serial.tools.list_ports.comports()
            print("Now plug in your device, and press ENTER...", end='')
            input()
            new_ports = serial.tools.list_ports.comports()

            if (len(old_ports) == len(new_ports)):
                print("Could not find the device.")
                sys.exit()
            
            port = [port for port in new_ports if port not in old_ports][0].device
            print("Connected to", port)

        self.connection = serial.Serial(port, BAUD)

    def readline(self):
        return self.connection.readline()

    def close(self):
        self.connection.close()

# Simulates a sensor from previously-saved raw data (a pickled list of bytes)
class SimulatedStream(DataStream):
    def __init__(self, delay_ms=10):
        with open(os.path.join(os.path.dirname(mugic.__file__), "simdata.pckl"), 'rb') as f:
            self.data = pickle.load(f)
        
        self.row_index = 0
        self.delay_sec = delay_ms / 1000

    def readline(self):
        time.sleep(self.delay_sec)

        row = self.data[self.row_index]
        self.row_index = (self.row_index + 1) % len(self.data)

        return row
    
    def close(self):
        # We need to do something that will cause readline to throw an exception, killing the data fetching thread
        self.data = None

# Converts the raw output from the sensor to a Pandas data frame
def raw_to_dataframe(raw_data: [bytes]) -> pd.DataFrame:
    rows = []

    for line in raw_data:
        try:
            line = line.decode("utf-8").strip()

            if line.startswith("mugicdata"): # Keep only lines with mugicdata prefix
                rows.append(line.split(' ')[1:])  # but lose that prefix
        
        except:
            print("A line of data was corrupt. This is likely because you are running on serial mode and read the data mid-line. This line will be thrown out and is probably nothing to worry about.")

    return pd.DataFrame(rows, dtype="double", columns = COLUMNS)



if __name__ == "__main__":
    
    outfile = str(datetime.now()).replace(':', '.') + ".csv"
    
    stream = UDPStream()

    raw = stream.read_for_time(seconds = 1)
    raw_to_dataframe(raw).to_csv(outfile)

    stream.close()
