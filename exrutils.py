import OpenEXR
import numpy as np

STD_HEADER = { 
    "compression" : OpenEXR.ZIP_COMPRESSION,
    "type" : OpenEXR.scanlineimage
}

v2i = tuple[int,int]

def v2i_add(a: v2i, b: v2i, c: v2i = (0,0)) -> v2i:
    return (a[0]+b[0]+c[0], a[1]+b[1]+c[1])

def v2i_max(a: v2i, b:v2i) -> v2i:
    return (max(a[0],b[0]), max(a[1],b[1]))

def v2i_min(a: v2i, b:v2i) -> v2i:
    return (min(a[0],b[0]), min(a[1],b[1]))

'''
rgb_pos:        (x,y)
thermal_pos:    (x,y)
'''
def write_dual_image(rgb_image: np.ndarray, thermal_image: np.ndarray, file_name: str, rgb_pos: tuple[int,int] = (0,0), thermal_pos: tuple[int,int] = (0,0), header:dict=STD_HEADER):
    # Change from (y,x,w) to (x,y)
    ris = rgb_image.shape[0:2][::-1]
    tis = thermal_image.shape[0:2][::-1]
    
    # This makes both images visible
    full_display = (
        v2i_min(rgb_pos, thermal_pos), # Upper left
        v2i_max(v2i_add(ris,rgb_pos,(-1,-1)), v2i_add(tis,thermal_pos,(-1,-1))) # Bottom right
    )

    rgb_header = header.copy()
    rgb_header["name"] = "visible"
    rgb_header["view"] = "visible"
    rgb_header["displayWindow"] = full_display
    rgb_header["dataWindow"] = (rgb_pos, v2i_add(rgb_pos,ris,(-1,-1)))
    rgb_part = OpenEXR.Part(rgb_header, {"RGB": rgb_image})

    thermal_header = header.copy()
    thermal_header["name"] = "infrared"
    thermal_header["view"] = "infrared"
    thermal_header["displayWindow"] = full_display
    thermal_header["dataWindow"] = (thermal_pos, v2i_add(thermal_pos,tis,(-1,-1)))
    thermal_part = OpenEXR.Part(thermal_header, {"T": thermal_image})

    with OpenEXR.File([rgb_part, thermal_part]) as outfile:
        print(thermal_image.shape)
        outfile.write(file_name)

def read_dual_image(file_name: str) -> tuple[np.ndarray, np.ndarray]:
    with OpenEXR.File(file_name) as infile:
        rgb_part = -1
        thermal_part = -1
        for part in infile.parts:
            if part.name() == "visible":
                rgb_part = part.part_index
            elif part.name() == "infrared":
                thermal_part = part.part_index
        return infile.channels(rgb_part)["RGB"].pixels, infile.channels(thermal_part)["T"].pixels

h,w = 100, 100

write_dual_image(np.random.rand(h, w*2, 3).astype('float32'), np.random.rand(h, w, 1).astype('float32'), "out/image.exr", (-100, 0))
visible, infra = read_dual_image("out/image.exr")
print(visible.shape, infra.shape)
# print(infra)