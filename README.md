# MUGIC Positioning

The [MUGIC device](http://www.marikimura.com/mugic-sensor.html) bridges what is audible with what is mobile, measuring the movement of the musician who wears it and enabling new methods of performance driven by data. Many various applications of this device have been developed, ranging from the alteration of instrumental sounds to the real-time synthesis of a musical track.

In this project, we leverage the device's capabilities as a metric of its wearer's instrumental technique, particularly in the case of a violinist. In having a violinist wear the device on the hand used for bowing, we can measure the motion of their bowing and assess the stability in which they play their instrument.

This project was supervised by [Prof. Mari Kimura](http://www.marikimura.com/) as an undergraduate research project for the UCI ICS Honors Program.

## Troubleshooting

Requires Python 3. Works best with Python 3.7, not 3.8.

Dependencies: pandas, pyinstaller (to package), PySide2, pyqtgraph, pyserial, sklearn

You should not use the pyqtgraph release available from PyPI. Instead, use:

`pip install --upgrade git+http://github.com/pyqtgraph/pyqtgraph.git`

Note that pyinstaller does not support Python 3.8, so if you are trying to package the application, consider using a supported version.

Note that pyinstaller has issues with sklearn, so we have included the troublesome dll file for Windows users in lib/.

Note that the Python distribution available on the Windows Store can cause sklearn to have issues with the PATH.
You should install Python from the main website instead.
