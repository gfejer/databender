# databender
a Python script that manipulates images by converting them into NumPy arrays and directly editing pixel data to create unique glitch art effects.

## Getting Started

### GUI App
1. Go to the **[Releases](https://github.com/gfejer/databender/releases)** page.
2. Download the version for your OS (Windows, Mac (Intel/ARM), or Linux).
3. Run the executable.

### CLI Script
If you want to run the script manually:
1. Clone the repository.
2. Create a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the script:

```bash
python databender_cli.py
```

## Effects (for now)
- **Color Manipulation**: Adds a fixed integer value to all color channels (Red, Green, Blue).
- **Row Shifting**: Horizontally displaces rows of pixels by a random amount.
- **Chromatic Aberration**: Independent horizontal displacement of the Red, Green, and Blue color channels.
- **Pixel Sorting (lum / hue)**: Reorders pixels within specific intervals based on their mathematical properties.
- **Warping (normal / sin)**: Distorts the geometry of the image by shifting rows based on mathematical functions.
