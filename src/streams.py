import os, pickle, socket, sys, time
import serial  # pySerial package

# Template class
class _DataStream:
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

class SerialStream(_DataStream):
    def __init__(self, port, baud):
        self.connection = serial.Serial(port, int(baud))

    def readline(self):
        return self.connection.readline()

    def close(self):
        self.connection.close()

# Simulates a sensor from previously-saved raw data (a pickled list of bytes)
class SimulatedStream(_DataStream):
    def __init__(self, delay_ms=10):
        try:
            root_dir = sys._MEIPASS # if built with pyinstaller
        
        except AttributeError:
            root_dir = './src'


        with open(os.path.join(root_dir, "data", "simdata.pckl"), 'rb') as f:
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

class UDPStream(_DataStream):
    def __init__(self, ip, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.socket.bind((ip, int(port)))

    def readline(self):
        data, addr = self.socket.recvfrom(1024)

        return data

    def close(self):
        self.socket.close()
