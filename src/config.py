HISTORY = 1000                  # number of observations to display
BATCH_SIZE = 20                 # number of observations to fetch from sensor before integrating/filtering (lower is smoother animated, but may lag)
REUSE_SIZE = 200                # number of old samples to include when processing new data, for connectedness & boosted filter performance
DEBUG_LEVEL = 1                 # flag to print messages to console (0: off, 1: errors only, 2: all)

IP = "192.168.4.2"
UDP_PORT = 4000
BAUD = 115200
COLUMNS = ["ax", "ay", "az", "ex", "ey", "ez", "gx", "gy", "gz", "mx", "my", "mz", "qw", "qx", "qy", "qz", 
           "BatteryPercent", "SystemStatus", "GyroStatus", "AccelStatus", "MagStatus", "time_sec", "SequenceNum"]
ACCUMULATED_COLUMNS = ["time_sec", "ax", "ay", "az", "lax", "lay", "laz", "qw", "qx", "qy", "qz", "vx", "vy", "vz",
                        "x", "y", "z", "position", "velocity", "projected_X", "projected_Y"]