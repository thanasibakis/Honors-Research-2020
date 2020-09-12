# Configurations for this program
BATCH_SIZE  = 20                 # number of observations to fetch from sensor before integrating/filtering (lower is smoother animated, but may lag)
REUSE_SIZE  = 10 * BATCH_SIZE    # number of old samples to include when processing new data, for connectedness & boosted filter performance
HISTORY     = 50 * BATCH_SIZE    # number of observations to display

DEBUG_LEVEL = 1                  # flag to print messages to console (0: off, 1: errors only, 2: all)

# Configurations set by the MUGIC firmware
IP          = "192.168.4.2"
UDP_PORT    = 4000
BAUD        = 115200
# The columns of the raw data outputted by the device
COLUMNS     = ["ax", "ay", "az", "ex", "ey", "ez", "gx", "gy", "gz", "mx", "my", "mz", "qw", "qx", "qy", "qz", 
               "BatteryPercent", "SystemStatus", "GyroStatus", "AccelStatus", "MagStatus", "time_sec", "SequenceNum"]