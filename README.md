# Databender
a Python script that manipulates images by converting them into NumPy arrays and directly editing pixel data to create unique glitch art effects.

## Installation
Mac, Windows and Linux apps available in releases.  
For the cli version: simply create a Python venv and install the required packages by running 

```bash
pip install -r requirements.txt
```

## Effects (for now)
- Color Manipulation (Adds a fixed integer value to all color channels (Red, Green, Blue).)
- Row Shifting (Horizontally displaces rows of pixels by a random amount.)
- Chromatic Aberration (Independent horizontal displacement of the Red, Green, and Blue color channels.)
- Pixel Sorting (lum / hue) (Reorders pixels within specific intervals based on their mathematical properties.)
- Warping (normal / sin) (Distorts the geometry of the image by shifting rows based on mathematical functions.)
