from Sensor import Sensor
from streams import SerialStream
from time import sleep

sensor = Sensor(SerialStream("COM3", 115200))
sensor.toggle_recording()

while True:
    sleep(0.1)

    sensor.process_next_batch()
    #print(sensor.get_latest_n_samples(1).vx)