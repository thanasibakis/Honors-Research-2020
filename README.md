# MUGIC Positioning

The [MUGIC device](http://www.marikimura.com/mugic-sensor.html) bridges what is audible with what is mobile, measuring the movement of the musician who wears it and enabling new methods of performance driven by data. Many various applications of this device have been developed, ranging from the alteration of instrumental sounds to the real-time synthesis of a musical track.

In this project, we attempt to track the absolute position of the device, to use as a metric of its wearer's instrumental technique (particularly in the case of a violinist). In having a violinist wear the device on the hand used for bowing, we can measure the motion of their bowing and assess the stability in which they play their instrument.

This project was supervised by [Prof. Mari Kimura](http://www.marikimura.com/) as an undergraduate research project for the UCI ICS Honors Program.

## Running

### With Docker and an X server

This application has been built into a Docker image (my first ever one!), based on the `python:3.7` image, to ensure that you can have all the correctly-functioning package versions.

```
./run.sh # or run.bat on Windows
```

For the X server, I recommend [X410](https://x410.dev/) for Windows 10 and [XQuartz](https://www.xquartz.org/) for macOS.

### With a local Python installation

```
pip install -r requirements.txt
python src/app.py
```

Tested on macOS Catalina and Windows 10. Requires Python 3. Works best with Python 3.7, not 3.8. Note that the Python distribution available on the Windows Store can cause sklearn to have issues with the PATH. You should install Python from the main website instead.

## Building to an executable

The program can be built into an macOS executable using pyinstaller:

```
pip install pyinstaller
make build-mac
```

The resulting executable will be in `build_resourcs/dist/`.

## About the program

## The positioning algorithm

While the sensor outputs acceleration samples one at a time, this program reads them in batches of 20. Each time we obtain a new batch, we first temporarily combine it with the 10 previous batches. We rotate the raw acceleration measurements using the quaternions outputted by the sensor to obtain linear acceleration measurements. We then perform a highpass filter (due to the sensor's drift) and integration. To obtain true velocity, we perform an "integration correction" by adding a constant to the integration results such that the average of the velocity measured equals the average of the velocity of the previous set of batches (the ones used to integrate the previous batch). We then repeat to obtain position from velocity. All the numerical configurations listed here (20 samples per batch, previous 10 batches, etc.) are defined in `config.py` and can be changed.

We then perform analysis specific to the case of the sensor on a violin bow. We perform principal component analysis on the position measurements to find one signal that represents the musician's bowing motion. We also project the measurements onto the plane defined by the other two components, as a measure of the musician's "bowing stability". 

### The codebase

The file `app.py` is the main entrypoint. Due to the structure of the code and data, you should run it from the project's root directory, ie. `python src/app.py`. The entrypoint will use `ConfigWindow.py` and perhaps (but hopefully not!) `ErrorWindow.py` to determine how you are trying to access the device and use the program.

Finally, `MainWindow.py` will generate an interface with a menu bar, plot area, and message console. The plot area is contained within a widget defined in `PlotWidget.py`. Every time this widget updates, it communicates with the sensor via an interface object defined in `Sensor.py`. This interface spawns a thread to constantly fetch data from the sensor, and provides a `process_next_batch` method to analyze and store this data on demand. (Typically, the demand is the GUI loop.)

If you're really curious, the `Sensor.py` interface uses `streams.py` as an abstraction to the various ways the sensor can connect (WiFi, USB). The `tools.py` file just provides helpful functions when doing position analysis.