# Thermal video
I made this tool for IYPT 2026 problem number 4. I plan to measure the flow of oil on a thermal gradient using this tool.

A set of utils for thermal video recording and playback. The thermal data is stored as float16 or float32 in degrees celsius. A visible spectrum image is stored along the thermal image in a single .exr file.

The video is made up of separate exr frames.

#### `recorder.py`
Implements video recording for all cameras compatible with the seek thermal sdk.

#### `player.py`
Plays back the frames.

#### `export.py`
A tool for exporting thermal values in csv.

#### `exrutils.py`
`write_dual_image()` and `read_dual_image()` for reading and writing the data to a file.

#### `imageutils.py`
Helper functions for image manipulation.

#### `fsutils.py`
Helper functions for file ranges.

#### `videocapture.py`
A helper class for reading the latest frame from a webcam.