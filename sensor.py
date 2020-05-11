import pandas as pd
import serial  # pySerial package
import serial.tools.list_ports
import subprocess
import time
import sys
import socket
from datetime import datetime


IP = "192.168.4.2"
UDP_PORT = 4000
SER_PORT = "COM3" # serial.tools.list_ports.comports()[0].device
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
        self.socket.bind((ip, port))

    def readline(self):
        return self.socket.recvfrom(1024)

    def close(self):
        self.socket.close()


class SerialStream(DataStream):
    def __init__(self, port=SER_PORT):
        self.connection = serial.Serial(port, BAUD)

    def readline(self):
        return self.connection.readline()

    def close(self):
        self.connection.close()

# Simulates a sensor from an already-processed CSV output
class SimulatedStream(DataStream):
    def __init__(self, csvpath): 
        self.data = pd.read_csv(csvpath)[COLUMNS]
        self.row_index = 0

    def readline(self):
        time.sleep(0.010) # seconds

        row = self.data.iloc[self.row_index,:]
        self.row_index = (self.row_index + 1) % self.data.shape[0]

        return str("mugicdata " + ' '.join(row.values.astype(str))).encode("utf-8")


def raw_to_dataframe(raw_data: list) -> pd.DataFrame:
    decoded_output = [line.decode("utf-8").strip() for line in raw_data]

    # Keep only lines with mugicdataprefix, but lose the prefix
    dataMatrix = [ line.split(' ')[1:] for line in decoded_output if line.startswith("mugicdata") ]

    return pd.DataFrame(dataMatrix, dtype="double", columns = COLUMNS)



if __name__ == "__main__":
    
    outfile = str(datetime.now()).replace(':', '.') + ".csv"
    
    stream = UDPStream()

    raw = stream.read_for_time(seconds = 1)
    raw_to_dataframe(raw).to_csv(outfile)

    stream.close()
