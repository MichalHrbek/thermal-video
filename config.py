from configparser import ConfigParser
from pathlib import Path

DEFAULTS = {
    "recorder": {
        "camera": 0,
        "auto_record": False,
        "write_path": "out/",
    },
    "player": {
        "auto_play": False,
        "read_path": "out/",
        "color_pallete": 0,
    },
}

config = ConfigParser()
config.read(Path(__file__).resolve().parent / "config.ini")

for i in DEFAULTS:
    if not config.has_section(i):
        config.add_section(i) 
    
    for j in DEFAULTS[i]:
        if j not in config[i]:
            config[i][j] = str(DEFAULTS[i][j])