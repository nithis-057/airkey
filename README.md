# AirKey

A hand-tracking virtual keyboard that allows typing through air gestures using computer vision.

## Overview

AirKey creates a transparent overlay displaying a virtual keyboard that responds to hand movements captured through your webcam. Users can type by pointing their index finger at keys, making it useful for touchless input scenarios.

## Installation

```bash
git clone https://github.com/nithis-057/airkey.git
cd airkey
pip install opencv-python mediapipe PySide6 pynput pygame
```

**Windows users:** `pip install pywin32`  
**macOS users:** `pip install PyObjC`

Add a `click.wav` audio file to the project directory for key press feedback.

## Usage

Run `python airkey.py` and point your index finger at the on-screen keyboard. Hold over keys for 0.5 seconds to activate them. The application creates a click-through overlay that won't interfere with other programs.

## Controls

- Point and hold to press keys
- "Shift" toggles case
- "ClearAll" requires 2-second hold
- Click "Exit" button to close

## Requirements

- Python 3.7+
- Webcam
- Windows or macOS

## Technical Details

The application uses MediaPipe for hand landmark detection and native OS APIs to create a transparent, click-through window overlay. Hand positions are mapped to virtual keyboard coordinates with visual feedback indicating key activation states.

## Configuration

Key dimensions, timing thresholds, and layout can be modified in the constants section of `airkey.py`.

## Troubleshooting

- Ensure camera permissions are granted
- Check lighting conditions for hand tracking
- Verify audio file exists for sound feedback
- Run with administrator privileges if overlay doesn't appear
