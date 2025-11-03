import os
import zipfile
import tempfile
from typing import Optional
from pathlib import Path
from glob import glob

temp_handle: Optional[tempfile.TemporaryDirectory] = None

def zip_range(file_name: str) -> list[str]:
    global temp_handle
    paths = []
    temp_handle = tempfile.TemporaryDirectory()
    temp_dir = temp_handle.name
    with zipfile.ZipFile(file_name, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            if file.endswith(".exr"):
                paths.append(os.path.join(root, file))
    
    return sorted(paths)

def file_range(start: str, end: Optional[str] = None) -> tuple[list[str], int]:
    startpath = None
    if os.path.isfile(start):
        startpath = Path(start).resolve()
        if start.endswith(".zip"):
            return zip_range(start), 0
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
    
    return file_list[:end_index+1], start_index

def file_range_sharp_start(start: str, end: Optional[str] = None) -> list[str]:
    paths, index = file_range(start, end)
    return paths[index:]