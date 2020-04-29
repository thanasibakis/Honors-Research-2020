import numpy as np
import serial  # pySerial package
import serial.tools.list_ports
import subprocess
import time
import sys
import socket
from datetime import datetime

BAUD = 115200
COLUMNS = ["ax", "ay", "az", "ex", "ey", "ez", "gx", "gy", "gz", "mx", "my", "mz", "qw", "qx", "qy", "qz", 
           "BatteryPercent", "SystemStatus", "GyroStatus", "AccelStatus", "MagStatus", "Timestamp", "SequenceNum"]

# Returns the serial output on the given port seen over the given length of time
def readSerialFor(port, seconds):
    output = []
    seconds = int(seconds)
    startTime = time.time()

    with serial.Serial(port, BAUD) as ser:
        while time.time() - startTime < seconds:
            output.append(ser.readline())

    return map(lambda line: line.decode("utf-8").strip(), output[1:]) # lose the first line in case we read it mid-broadcast

# Returns the serial output on the given port seen over the given length of time
def readUDPFor(ip, port, seconds):
    output = []
    seconds = int(seconds)
    startTime = time.time()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))

    while time.time() - startTime < seconds:
        data, _ = sock.recvfrom(1024)
        output.append(data)

    return map(lambda line: line.decode("utf-8").strip(), output)



# Filters out the non-data rows and converts to a numpy array
def rawToArray(output: list) -> np.array:
    selectData = lambda line: line.startswith("mugicdata")
    extractData = lambda line: line.split(' ')[1:]  # lose the MugicData prefix
    dataMatrix = map(extractData, filter(selectData, output))

    return np.array(list(dataMatrix), dtype="double")

# Writes the numpy array and its column headers to a CSV of the given name
def writeToCSV(arr: np.array, filename: str):
    with open(filename, 'w') as f:
        f.write(','.join(COLUMNS) + '\n')
        np.savetxt(f, arr, delimiter=',', fmt="%.6f")

# Usage:
#   read_data.py <ip> <port> <seconds>
if __name__ == "__main__":
    
    ip      = sys.argv[1] # "192.168.4.2"
    port    = int(sys.argv[2]) # 4000
    seconds = int(sys.argv[3])
    outfile = str(datetime.now()).replace(':', '.') + ".csv"
    
    #port    = serial.tools.list_ports.comports()[0].device
    #raw = readSerialFor(port, seconds)
    raw = readUDPFor(ip, port, seconds)
        
    writeToCSV(rawToArray(raw), outfile)
