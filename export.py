import os
import argparse
from typing import Optional
from pathlib import Path

import exrutils
import fsutils
from config import config

def export_values(files: list[str], point: Optional[tuple[int,int]], outpath: str, min=False, max=False):
    header = "timestamp, frame"
    if point: header += f", t({point[0]};{point[1]})"
    if min: header += ", min"
    if max: header += ", max"
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        f.write(header + "\n")
        for i in files:
            basename = os.path.basename(i)
            timestamp = int(basename.split(":")[0])
            frame_number = int(basename.split(":")[1].removesuffix(".exr"))
            _, thermal = exrutils.read_dual_image(i)
            line = f"{timestamp}, {frame_number}"
            if point:
                line += f", {thermal[point[1],point[0]]}" # I don't need to transpose since I swap coordinates here
            if min:
                line += f", {thermal.min()}"
            if max:
                line += f", {thermal.max()}"
            f.write(line + "\n")

def export_color(files: list[str], point: Optional[tuple[int,int]], outpath: str, color_palette: int, min=False, max=False):
    import pygame as pg
    import numpy as np
    import imageutils

    outpath = Path(outpath)

    os.makedirs(outpath, exist_ok=True)
    for i in files:
        _, thermal = exrutils.read_dual_image(i)
        thermal = thermal.reshape(thermal.shape[0], thermal.shape[1], 1).transpose((1,0,2))
        rgb = imageutils.COLOR_PALETTES[color_palette][1](imageutils.COLOR_SCALES[0][1](thermal))
        surface = pg.surfarray.make_surface(rgb)
        def draw_point(pos: tuple[int,int], color: pg.Color):
            pg.draw.circle(surface, color, pos, 2.0)
        if min:
            mini = np.unravel_index(thermal.argmin(), thermal.shape)
            draw_point((mini[0],mini[1]), pg.colordict.THECOLORS["blue"])
        if max:
            maxi = np.unravel_index(thermal.argmax(), thermal.shape)
            draw_point((maxi[0],maxi[1]), pg.colordict.THECOLORS["red"])
        if point:
            draw_point(point, pg.colordict.THECOLORS[config["export"]["point_color"]])
        pg.image.save(surface, outpath / (os.path.basename(i).removesuffix(".exr")+".png"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Exporter", description="This program exports thermal data from select points of a video into .csv format or creates a pseudo-colored png")
    parser.add_argument("type", choices=['csv', 'png'])
    parser.add_argument("start_path")
    parser.add_argument("end_path", nargs='?')
    parser.add_argument("-o", "--out")
    parser.add_argument("-p", "--point")
    parser.add_argument("--min", action="store_true")
    parser.add_argument("--max", action="store_true")
    parser.add_argument("-c", "--color", type=int, default=config["export"]["color_palette"])

    args = parser.parse_args()

    point = None
    if args.point:
        point = tuple(map(int, args.point.split(",")))

    if args.type == "csv":
        if not args.out:
            args.out = config["export"]["csv_path"]
        export_values(fsutils.file_range_sharp_start(args.start_path, args.end_path), point, args.out, args.min, args.max)

    elif args.type == "png":
        if not args.out:
            args.out = config["export"]["png_path"]
        export_color(fsutils.file_range_sharp_start(args.start_path, args.end_path), point, args.out, args.color, args.min, args.max)
