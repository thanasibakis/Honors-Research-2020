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

## Building to an Executable

The program can be built into an macOS executable using pyinstaller:

```
pip install pyinstaller
make build-mac
```

The resulting executable will be in `build_resourcs/dist/`.