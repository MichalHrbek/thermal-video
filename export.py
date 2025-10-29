import os
import argparse
from typing import Optional
from pathlib import Path
from glob import glob

import exrutils
import config

def file_range(start: str, end: Optional[str] = None) -> list[str]:
    startpath = None
    if os.path.isfile(start):
        startpath = Path(start).resolve()
        dirpath = startpath.parent

    elif os.path.isdir(start):
        dirpath = Path(start).resolve()
    
    else:
        raise ValueError(f"{start} is not a valid path")
    
    file_list = sorted(glob(str(dirpath / "*.exr")))

    start_index = 0
    if startpath:
        if str(startpath) in file_list:
            start_index = file_list.index(str(startpath))

    end_index = len(file_list)
    if end:
        if os.path.isfile(end):
            endpath = Path(end).resolve()
            if str(endpath) in file_list:
                end_index = file_list.index(str(endpath))

        else:
            raise ValueError(f"{end} is not a valid *file* path")
    
    return file_list[start_index:end_index+1]


def export_values(files: list[str], point: Optional[tuple[int,int]], outpath: str, min=False, max=False):
    header = "timestamp, frame"
    if point: header += f", t({point[0]};{point[1]})"
    if min: header += ", min"
    if max: header += ", max"
    with open(outpath, "w") as f:
        f.write(header + "\n")
        for i in files:
            basename = os.path.basename(i)
            timestamp = int(basename.split(":")[0])
            frame_number = int(basename.split(":")[1].removesuffix(".exr"))
            _, thermal = exrutils.read_dual_image(i)
            # thermal = np.transpose(thermal.reshape(thermal.shape[0], thermal.shape[1], 1), (1,0,2))
            line = f"{timestamp}, {frame_number}"
            if point:
                line += f", {thermal[point[1],point[0]]}"
            if min:
                line += f", {thermal.min()}"
            if max:
                line += f", {thermal.max()}"
            f.write(line + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Exporter", description="This program exports thermal data from select points of a video into .csv format")
    parser.add_argument("start_path")
    parser.add_argument("end_path", nargs='?')
    parser.add_argument("-o", "--out", default=config.config["export"]["csv_path"])
    parser.add_argument("-p", "--point")
    parser.add_argument("--min", action="store_true")
    parser.add_argument("--max", action="store_true")
    args = parser.parse_args()
    
    point = None
    if args.point:
        point = tuple(map(int, args.point.split(",")))

    export_values(file_range(args.start_path, args.end_path), point, args.out, args.min, args.max)
