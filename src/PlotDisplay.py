import pyqtgraph as pg
import pandas as pd

from datetime import datetime
from queue import Queue, Empty
from threading import Thread

import config, tools


class PlotDisplay(pg.GraphicsLayoutWidget):

    def __init__(self, sensor):
        pg.GraphicsLayoutWidget.__init__(self) # super() doesn't seem to work here

        self.plots       = { key: self.addPlot(title=key) for key in ("position", "velocity", "projection") }
        self.curves      = { key: plot.plot() for key, plot in self.plots.items() }
        self.sensor      = sensor

        sensor.reset_recording()
        sensor.toggle_recording()



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
            min(-0.2, self.sensor.accumulated_processed.position.min()),
            max( 0.2, self.sensor.accumulated_processed.position.max())
        )

        self.plots["projection"].setXRange(
            min(-0.1, self.sensor.accumulated_processed.projected_X.min()),
            max( 0.1, self.sensor.accumulated_processed.projected_X.max())
        )

        self.plots["projection"].setYRange(
            min(-0.1, self.sensor.accumulated_processed.projected_Y.min()),
            max( 0.1, self.sensor.accumulated_processed.projected_Y.max())
        )

    

    # Plot loop
    def update(self):
        try: 
            # Get and process new data, if available
            self.sensor.fetch_data()

            # Update the plots with the new data
            if(self.sensor.should_record):
                self._update_graphics()
        
        except Empty:
            # No more data is ready yet, let's not hold up the main UI
            pass

        except AssertionError:
            # We haven't collected enough data to begin analysis yet
            # (reuse_size > amount of accumulated data)
            print("Withholding data for calibration")

        except Exception as ex:
            print(repr(ex))



