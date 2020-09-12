import pyqtgraph as pg
import pandas as pd

from datetime import datetime
from queue import Queue, Empty
from threading import Thread

import config, tools

# A widget to be added to a Qt interface.
# PlotWidget.update should be called on loop via a QTimer to keep the plots and data updated.
class PlotWidget(pg.GraphicsLayoutWidget):

    def __init__(self, sensor):
        pg.GraphicsLayoutWidget.__init__(self) # super() doesn't seem to work here

        self.plots       = { key: self.addPlot(title=key) for key in ("position", "velocity", "projection") }
        self.curves      = { key: plot.plot() for key, plot in self.plots.items() }
        self.sensor      = sensor


    # The widget's GUI loop. Should be called regularly to keep the sensor and plot up to date.
    def update(self):
        try: 
            # Always get and process new data, if available
            self.sensor.process_next_batch()

            # Update the plots with the new data, if we're recording
            #if(self.sensor.should_record):
            self._update_graphics()
        
        except Empty:
            # No more data is ready yet, let's not hold up the main UI
            pass

        except AssertionError:
            # We haven't collected enough data to begin analysis yet
            # (reuse_size > amount of accumulated data)
            print("Withholding data for calibration")

        except Exception as ex:
            # Anything else that could go wrong
            print(repr(ex))


    # Grab the latest accumulated data from the sensor and plot it
    def _update_graphics(self):
        self.curves["position"].setData(
            self.sensor.accumulated_processed.time_sec.tail(config.HISTORY).reset_index(drop = True), # pg depends on the first index being 0
            self.sensor.accumulated_processed.position.tail(config.HISTORY).reset_index(drop = True)
        )

        self.curves["velocity"].setData(
            self.sensor.accumulated_processed.time_sec.tail(config.HISTORY).reset_index(drop = True),
            self.sensor.accumulated_processed.velocity.tail(config.HISTORY).reset_index(drop = True)
        )

        self.curves["projection"].setData(
            self.sensor.accumulated_processed.projected_X.tail(config.HISTORY).reset_index(drop = True),
            self.sensor.accumulated_processed.projected_Y.tail(config.HISTORY).reset_index(drop = True)
        )

        self.plots["position"].setYRange(
            min(-0.2, self.sensor.accumulated_processed.position.min()),
            max( 0.2, self.sensor.accumulated_processed.position.max())
        )

        self.plots["velocity"].setYRange(
            min(-0.2, self.sensor.accumulated_processed.velocity.min()),
            max( 0.2, self.sensor.accumulated_processed.velocity.max())
        )

        self.plots["projection"].setXRange(
            min(-0.1, self.sensor.accumulated_processed.projected_X.min()),
            max( 0.1, self.sensor.accumulated_processed.projected_X.max())
        )

        self.plots["projection"].setYRange(
            min(-0.1, self.sensor.accumulated_processed.projected_Y.min()),
            max( 0.1, self.sensor.accumulated_processed.projected_Y.max())
        )