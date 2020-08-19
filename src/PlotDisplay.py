import pyqtgraph as pg

import config


class PlotDisplay(pg.GraphicsLayoutWidget):

    def __init__(self, sensor):
        pg.GraphicsLayoutWidget.__init__(self) # super() doesn't seem to work here

        self.plots       = { key: self.addPlot(title=key) for key in ("position", "velocity", "projection") }
        self.curves      = { key: plot.plot() for key, plot in self.plots.items() }
        self.sensor      = sensor
  

    # The plot loop, updating as often as the MainWindow timer is set to
    def update_plot(self):
        # Load new data, even if we aren't recording.
        # This way, when we do record, the data will be fresh
        self.sensor.accumulate_next_batch()

        # Update the plots with the new data
        data = self.sensor.get_latest_n_samples(config.HISTORY) \
            .reset_index(drop = False) # move time_sec to a column and reset the index to start at 0, which pg needs

        self.curves["position"].setData(data.time_sec, data.position)
        self.curves["velocity"].setData(data.time_sec, data.velocity)
        self.curves["projection"].setData(data.projected_X, data.projected_Y)

        self.plots["position"].setYRange(
            min(-0.2, data.position.min()),
            max( 0.2, data.position.max())
        )

        self.plots["velocity"].setYRange(
            min(-0.2, data.velocity.min()),
            max( 0.2, data.velocity.max())
        )

        self.plots["projection"].setXRange(
            min(-0.1, data.projected_X.min()),
            max( 0.1, data.projected_X.max())
        )

        self.plots["projection"].setYRange(
            min(-0.1, data.projected_Y.min()),
            max( 0.1, data.projected_Y.max())
        )