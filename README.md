# databender
a Python script that manipulates images and videos by converting them into NumPy arrays and directly editing pixel data to achieve unique glitch art effects.

## Getting Started

### GUI App
1. Go to the **[Releases](https://github.com/gfejer/databender/releases)** page.
2. Download the version for your OS (Windows, Mac (Intel/ARM), or Linux).
3. Run the executable.

> [!IMPORTANT]
> **Note for Mac Users:**  
macOS might flag this application as an unrecognized or dangerous file. To open the app safely, follow these steps:
> 1. Open **System Settings**.
> 2. Go to **Privacy & Security**.
> 3. Scroll down to the security section, locate the app (**databender**), and click **Open Anyway**.

> [!IMPORTANT]
> **Note for Windows Users:**  
Because this application is packaged using PyInstaller into a single executable, some antivirus software (like Windows Defender) might falsely flag it as a virus. This is a known **"false positive"** issue with Python packaging tools. You can safely tell your antivirus to allow the file, or inspect the open-source code and run it via Python directly!

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

## Features and effects (for now)
- **Region of Interest (ROI) mask:** Define a specific rectangular area by providing X, Y, width and height values to glitch only a targeted part of the image/video.

- **Color Manipulation:** Adds a fixed integer value to all color channels (Red, Green, Blue).
- **Row Shifting:** Horizontally displaces rows of pixels by a random amount.
- **Chromatic Aberration:** Independent horizontal displacement of the Red, Green, and Blue color channels.
- **Pixel Sorting (lum / hue):** Reorders pixels within specific intervals based on their mathematical properties.
- **Warping (normal / sin):** Distorts the geometry of the image/video by shifting rows based on mathematical functions.

## Example images

<p align="center">
    <img width="45%" height="45%" alt="havas" src="https://github.com/user-attachments/assets/c106d33e-33c2-4b1c-b7a5-75031ea18b66"/>
  &nbsp; &nbsp;
    <img width="45%" height="45%" alt="korszallo" src="https://github.com/user-attachments/assets/f0eb43c4-0668-4650-b88f-fccbb0c0e16b"/>
</p>

<p align="center">
    <img width="45%" height="45%" alt="homok" src="https://github.com/user-attachments/assets/4cdc1d67-3b26-4e58-9415-30effcf17549"/>
  &nbsp; &nbsp;
    <img width="45%" height="45%" alt="pozsony" src="https://github.com/user-attachments/assets/816c7c5d-4943-4b9c-ad63-7166ba1c8e51" />
</p>

## Example videos

<table align="center">
    <td width="50%">
      <video src="https://github.com/user-attachments/assets/2c1ebbf0-3cd1-42be-b878-d63cc2857c3b" width="100%" controls autoplay loop muted></video>
    </td>
    <td width="29.1%">
      <video src="https://github.com/user-attachments/assets/44576fff-bd24-4aa2-bc2a-3f3c8ff000b5" width="100%" controls autoplay loop muted></video>
    </td>
</table>
