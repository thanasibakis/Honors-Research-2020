# MUGIC Positioning

The [MUGIC device](http://www.marikimura.com/mugic-sensor.html) bridges what is audible with what is mobile, measuring the movement of the musician who wears it and enabling new methods of performance driven by data. Many various applications of this device have been developed, ranging from the alteration of instrumental sounds to the real-time synthesis of a musical track.

In this project, we leverage the device's capabilities as a metric of its wearer's instrumental technique, particularly in the case of a violinist. In having a violinist wear the device on the hand used for bowing, we can measure the motion of their bowing and assess the stability in which they play their instrument.

This project was supervised by [Prof. Mari Kimura](http://www.marikimura.com/) as an undergraduate research project for the UCI ICS Honors Program.

## Running

Tested on macOS Catalina and Windows 10. Requires Python 3. Works best with Python 3.7, not 3.8 (particuarly when it comes to building).

This application has been built into a Docker image (my first one!), based on the `python:3.7` image, to ensure that you can have all the correctly-functioning package versions. You can use `./run.sh` to run the program, once you have an X server running. (I recommend [X410](https://x410.dev/) for Windows 10 and [XQuartz](https://www.xquartz.org/) for macOS)

If you would like to use your own Python installation, the packages required can be installed with `pip install -r requirements.txt`.

Note that the Python distribution available on the Windows Store can cause sklearn to have issues with the PATH. You should install Python from the main website instead.

## Building to an Executable

The program can be built into an executable using pyinstaller:

```
pip install pyinstaller
make build-mac
```

The resulting executable will be in `build_resourcs/dist/`.