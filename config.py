from configparser import ConfigParser
from pathlib import Path

DEFAULTS = {
    # Recorder
    "camera": 0,
    "auto_record": False,
    "write_path": "out/",
    # Player
    "auto_play": False,
    "read_path": "out/*.exr",
    "color_pallete": 0,
}

config = ConfigParser(defaults=DEFAULTS)
config.read(Path(__file__).resolve().parent / "config.ini")