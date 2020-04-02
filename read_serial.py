import numpy as np
import serial  # pySerial package
import subprocess
import time
import sys
import socket

BAUD = 115200
COLUMNS = ["ax", "ay", "az", "ex", "ey", "ez", "gx", "gy", "gz", "qw", "qx", "qy", "qz", "mx", "my", "mz",
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

# Returns the WiFi UDP output on the given port seen over the given length of time
# TODO: THIS HAS NOT BEEN TESTED
def readUDPfor(seconds):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 4000))
    
    output = []
    seconds = int(seconds)
    startTime = time.time()
    
    while time.time() - startTime < seconds:
        data, addr = sock.recvfrom(512)
        output.append(data)
    
    sock.close()
    
    return map(lambda line: line.decode("utf-8").strip(), output[1:])

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
#   read_serial.py ip <ipaddr> <port> <seconds> <outfile>
#   read_serial.py com <port> <seconds> <outfile>
if __name__ == "__main__":
    mode = sys.argv[1]
    
    if mode == "ip":
        ip = sys.argv[2]
        port = sys.argv[3]
        seconds = sys.argv[4]
        outfile = sys.argv[5]
        
        raw = readUDPfor(seconds)
    
    elif mode == "com":
        port = sys.argv[2] 
        seconds = sys.argv[3]
        outfile = sys.argv[4]
        
        raw = readSerialFor(port, seconds)
        
    writeToCSV(rawToArray(raw), outfile)

### Tips ###
# Get COM port num: "powershell.exe [System.IO.Ports.SerialPort]::getportnames()"
# Get IP address: arp -a
