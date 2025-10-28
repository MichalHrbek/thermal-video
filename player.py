import os
from glob import glob
from typing import Optional, Callable
from pathlib import Path
import math

import cv2
import pygame as pg
import numpy as np

import exrutils, imageutils
from config import config

pg.init()

class Element:
    def __init__(self, rect: pg.Rect, surface: Optional[pg.Surface]):
        self.rect = rect
        if surface:
            self.surface = surface
        else:
            self.surface = pg.Surface(rect.size, pg.SRCALPHA)

    def handle_event(self, event: pg.event.Event):
        pass

    def update_surface(self, surface: pg.Surface):
        self.surface = surface
        self.rect.size = surface.get_size()
    
    def render(self, screen: pg.Surface):
        screen.blit(self.surface, self.rect)
    
    def tick(self):
        pass

class Label(Element):
    def __init__(self, rect: pg.Rect, surface: Optional[pg.Surface], text: str, font: Optional[pg.font.Font] = None, auto_rezise = True):
        super().__init__(rect, surface)
        self.auto_rezise = auto_rezise
        if font:
            self.font = font
        else:
            self.font = pg.font.SysFont('monospace', 32)
        self.update_text(text)
    
    def rerender_font(self):
        self.update_text(self._text)

    def update_text(self, text: str):
        self._text = text
        lines = text.split('\n')
        if self.auto_rezise:
            mh = self.font.get_linesize()*len(lines)+1 # (1 if self.font.underline else 0)
            mw = 0
            for i in lines:
                mw = max(mw, self.font.size(i)[0])
            
            if mh > self.surface.get_height() or mw > self.surface.get_width():
                self.update_surface(pg.Surface((mw,mh), pg.SRCALPHA))
            
            self.rect.size = (mw,mh)
        
        self.surface.fill((0,0,0,0))
        for i, line in enumerate(self._text.split('\n')):
            self.surface.blit(self.font.render(line, 1, "cornsilk"), (0,self.font.get_linesize()*i))

class Figure(Element):
    def __init__(self, rect: pg.Rect, surface: Optional[pg.Surface], text: str):
        super().__init__(rect, surface)
        self.label = Label(pg.Rect(self.rect.bottomleft, (0,0)), None, text)
        self.label.update_text(text)
    
    def render(self, screen: pg.Rect):
        super().render(screen)
        self.label.rect.topleft = self.rect.bottomleft
        self.label.render(screen)
    
    def handle_event(self, event):
        super().handle_event(event)

class Hoverable(Element):
    def __init__(self, rect, surface):
        super().__init__(rect, surface)
        self._is_hovered = False

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pg.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                if not self._is_hovered:
                    self.entered(event.pos, (event.pos[0]-self.rect.topleft[0], event.pos[1]-self.rect.topleft[1]))
                self.hovered(event.pos, (event.pos[0]-self.rect.topleft[0], event.pos[1]-self.rect.topleft[1]))
                self._is_hovered = True
            else:
                if self._is_hovered:
                    self.exited(event.pos, (event.pos[0]-self.rect.topleft[0], event.pos[1]-self.rect.topleft[1]))
                self._is_hovered = False

    def hovered(self, pos, local_pos):
        pass

    def entered(self, pos, local_pos):
        pass

    def exited(self, pos, local_pos):
        pass

class Clickable(Element):
    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pg.MOUSEBUTTONUP:
            if self.rect.collidepoint(event.pos):
                self.clicked(event.pos, (event.pos[0]-self.rect.topleft[0], event.pos[1]-self.rect.topleft[1]), event)

    def clicked(self, pos, local_pos, event: pg.event.Event):
        pass

class Button(Label, Hoverable, Clickable):
    def entered(self, pos, local_pos):
        self.font.underline = True
        self.rerender_font()
    
    def exited(self, pos, local_pos):
        self.font.underline = False
        self.rerender_font()

class Toggle(Button):
    def __init__(self, rect, surface, text, font = None, auto_rezise = True, toggled = False):
        super().__init__(rect, surface, text, font, auto_rezise)
        self.is_toggled = toggled
        self.font.bold = toggled
        self.rerender_font()

    def clicked(self, pos, local_pos, event: pg.event.Event):
        self.set_toggle(not self.is_toggled)
    
    def set_toggle(self, value: bool):
        if self.is_toggled == value:
            return

        self.is_toggled = value
        self.toggled(self.is_toggled)

        self.font.bold = self.is_toggled
        self.rerender_font()
    
    def toggled(self, new_state: bool):
        pass

class ThermalPoint(Toggle):
    COLORS: list[pg.Color] = [pg.colordict.THECOLORS[i] for i in ["aqua", "darkgreen", "brown", "blueviolet", "yellow", "red", "blue"]]

    def __init__(self, pos: tuple[int,int] = (0,0),  name: str = "", deletable: bool = True, color_index: int = 0, self_updated: Callable[[],None] = lambda: None, self_destroyed: Callable[[],None] = lambda: None, font = None, toggled = True):
        self.pos = pos
        self.name = name
        self.deletable = deletable
        self.color_index = color_index
        self.temp = 0.0
        self.self_updated = self_updated
        self.self_destroyed = self_destroyed
        super().__init__(pg.Rect(0,0,0,0), None, "", font, True, toggled)
    
    def clicked(self, pos, local_pos, event):
        if event.button == pg.BUTTON_RIGHT:
            if self.deletable:
                self.self_destroyed()
        elif event.button == pg.BUTTON_WHEELDOWN:
            self.color_index = (self.color_index - 1) % len(ThermalPoint.COLORS)
            self.self_updated()
        elif event.button == pg.BUTTON_WHEELUP:
            self.color_index = (self.color_index + 1) % len(ThermalPoint.COLORS)
            self.self_updated()
        else:
            super().clicked(pos, local_pos, event)
    
    def toggled(self, new_state):
        super().toggled(new_state)
        self.self_updated()

    def update_temp(self, celsius_array: np.ndarray):
        self.temp = celsius_array[self.pos]
        mw = math.ceil(math.log10(celsius_array.shape[0]))+0
        mh = math.ceil(math.log10(celsius_array.shape[1]))+0
        self.update_text(((self.name + " ") if self.name else "") + f"({self.pos[0]:{mw}d}, {self.pos[1]:{mh}d}) = {self.temp[0]:.2f}")

class ThermalImage(Figure, Hoverable, Clickable):
    COLOR_PALLETES = [
        ("White hot",           imageutils.rgb_white_hot),
        ("Black hot",           imageutils.rgb_black_hot),
        ("CV2_AUTUMN",          lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_AUTUMN)),
        ("CV2_BONE",            lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_BONE)),
        ("CV2_JET",             lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_JET)),
        ("CV2_WINTER",          lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_WINTER)),
        ("CV2_RAINBOW",         lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_RAINBOW)),
        ("CV2_OCEAN",           lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_OCEAN)),
        ("CV2_SUMMER",          lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_SUMMER)),
        ("CV2_SPRING",          lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_SPRING)),
        ("CV2_COOL",            lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_COOL)),
        ("CV2_HSV",             lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_HSV)),
        ("CV2_PINK",            lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_PINK)),
        ("CV2_HOT",             lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_HOT)),
        ("CV2_PARULA",          lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_PARULA)),
        ("CV2_MAGMA",           lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_MAGMA)),
        ("CV2_INFERNO",         lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_INFERNO)),
        ("CV2_PLASMA",          lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_PLASMA)),
        ("CV2_VIRIDIS",         lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_VIRIDIS)),
        ("CV2_CIVIDIS",         lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_CIVIDIS)),
        ("CV2_TWILIGHT",        lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_TWILIGHT)),
        ("CV2_TWILIGHT_SHIFTED",lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_TWILIGHT_SHIFTED)),
        ("CV2_TURBO",           lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_TURBO)),
        ("CV2_DEEPGREEN",       lambda arr: imageutils.rgb_colormap_cv(arr, cv2.COLORMAP_DEEPGREEN)),
    ]

    def __init__(self, rect: pg.Rect, surface: Optional[pg.Surface], text: str, celsius_array: np.ndarray):
        super().__init__(rect, surface, text)
        self.initial_text = text
        self.celsius_array = celsius_array
        self.pallete_index = config["player"].getint("color_pallete")
        self.pallete_picker = Button(pg.Rect((0,0),(0,0)), None, ThermalImage.COLOR_PALLETES[self.pallete_index][0])
        self.pallete_picker.clicked = self.pallete_picker_clicked
        self.points = [ThermalPoint(name = "Min", deletable=False, color_index=-1, self_updated=self.colorize), ThermalPoint(name = "Max", deletable=False, color_index=-2, self_updated=self.colorize)]
        self.points_overlay = pg.Surface(self.rect.size, pg.SRCALPHA)

    def hovered(self, pos, local_pos):
        self.label.update_text(f"{self.initial_text}\n{self.celsius_array[local_pos][0]:.2f}°C")
    
    def colorize(self):
        self.update_surface(pg.surfarray.make_surface(ThermalImage.COLOR_PALLETES[self.pallete_index][1](self.celsius_array)))
        for i in self.points:
            if i.is_toggled:
                pg.draw.circle(self.surface, ThermalPoint.COLORS[i.color_index], i.pos, 2.0)

    def update_data(self, celsius_array: np.ndarray):
        self.celsius_array = celsius_array
        mini = np.unravel_index(celsius_array.argmin(), celsius_array.shape)
        maxi = np.unravel_index(celsius_array.argmax(), celsius_array.shape)
        self.points[0].pos = mini[0], mini[1]
        self.points[1].pos = maxi[0], maxi[1]
        for i in self.points:
            i.update_temp(self.celsius_array)
        self.colorize()
    
    def pallete_picker_clicked(self, pos, local_pos, event: pg.event.Event):
        delta = (1 if (event.button in [pg.BUTTON_LEFT, pg.BUTTON_WHEELUP]) else -1 if (event.button in [pg.BUTTON_RIGHT, pg.BUTTON_WHEELDOWN]) else 0)
        if not delta:
            return
        self.pallete_index = (self.pallete_index+delta)%len(ThermalImage.COLOR_PALLETES)
        self.pallete_picker.update_text(ThermalImage.COLOR_PALLETES[self.pallete_index][0])
        self.colorize()
    
    def render(self, screen):
        super().render(screen)
        rows = [self.pallete_picker] + self.points
        pos = self.label.rect.bottomleft
        for i in rows:
            i.rect.topleft = pos
            pos = i.rect.bottomleft
            i.render(screen)
    
    def handle_event(self, event):
        super().handle_event(event)
        for i in [self.pallete_picker] + self.points:
            i.handle_event(event)
    
    def clicked(self, pos, local_pos, event):
        self.points.append(ThermalPoint(local_pos, "", self_updated = self.colorize))
        self.points[-1].update_temp(self.celsius_array)
        self.colorize()

DynPos = Optional[Callable[[pg.Surface],tuple[float,float]]]
class Anchor(Element):
    def __init__(self, child: Element, topleft: DynPos = None, topright: DynPos = None, bottomleft: DynPos = None, bottomright: DynPos = None):
        super().__init__(pg.Rect((0,0),(0,0)), None)
        self.child = child
        self.topleft = topleft
        self.topright = topright
        self.bottomleft = bottomleft
        self.bottomright = bottomright
    
    def render(self, screen):
        super().render(screen)
        if self.topleft:
            self.child.rect.topleft = self.topleft(screen)
        if self.topright:
            self.child.rect.topright = self.topright(screen)
        if self.bottomleft:
            self.child.rect.bottomleft = self.bottomleft(screen)
        if self.bottomright:
            self.child.rect.bottomright = self.bottomright(screen)
        self.child.render(screen)
    
    def handle_event(self, event):
        super().handle_event(event)
        self.child.handle_event(event)
    
    def tick(self):
        super().tick()
        self.child.tick()

rgb_image_element = Figure(pg.Rect((0,0),(0,0)), None, "Visible")
thermal_image_element = ThermalImage(pg.Rect((0,0),(0,0)), None, "Temperature", None)
file_info_label = Label(pg.Rect((0,0),(0,0)), None, "No file loaded")
play_button = Toggle(pg.Rect((0,0),(0,0)), None, "Play/Pause", toggled=config["player"].getboolean("auto_play"))

def update_images(new_rgb_array: np.ndarray, new_celsius_array: np.ndarray, filename: str):
    new_rgb_array = np.transpose(new_rgb_array, (1,0,2))
    new_celsius_array = np.transpose(new_celsius_array.reshape(240, 320, 1), (1,0,2))
    rgb_image_element.update_surface(pg.surfarray.make_surface((new_rgb_array * 255.0).astype(np.uint8)))
    thermal_image_element.update_data(new_celsius_array)
    thermal_image_element.rect.topleft = rgb_image_element.rect.topright
    file_info_label.update_text(filename)
    file_info_label.rect.topleft = thermal_image_element.rect.topright

elements: list[Element] = [
    rgb_image_element,
    thermal_image_element,
    Anchor(file_info_label, bottomright=lambda screen: (screen.get_width(), screen.get_height())),
    Anchor(play_button, bottomleft=lambda screen: (0, screen.get_height())),
]

def loop():
    image_file_list: list[str] = []
    image_file_index: int = 0

    def open_path(path: str):
        nonlocal image_file_list, image_file_index
        dirpath = Path(path).resolve()
        filepath = None
        if os.path.isfile(path):
            filepath = Path(path).resolve()
            dirpath = filepath.parent

        elif os.path.isdir(path):
            dirpath = Path(path).resolve()
        
        image_file_list = sorted(glob(str(dirpath / "*.exr")))
        
        image_file_index = 0
        if str(filepath) in image_file_list:
            image_file_index = image_file_list.index(str(filepath))

        if image_file_list:
            update_images(*exrutils.read_dual_image(image_file_list[image_file_index]), image_file_list[image_file_index])
        else:
            update_images(np.random.rand(480,640,3), np.linspace(20.0, 40.0, 240*320, dtype=np.float32).reshape(240, 320, 1), "No files found! Showing example data") # Generate random rgb data and temperature values from 20C to 40C

    open_path(config["player"].get("read_path"))
    
    screen = pg.display.set_mode((1280, 720), pg.RESIZABLE)
    clock = pg.time.Clock()
    running = True
    tof = 0

    while running:
        if play_button.is_toggled:
            if image_file_index >= len(image_file_list)-1:
                play_button.set_toggle(False)
            else:
                tof += clock.get_time()
                try:
                    t1 = int(os.path.basename(image_file_list[image_file_index]).split(":")[0])
                    t2 = int(os.path.basename(image_file_list[image_file_index+1]).split(":")[0])
                    if tof > t2-t1:
                        tof -= t2-t1
                        image_file_index += 1
                        update_images(*exrutils.read_dual_image(image_file_list[image_file_index]), image_file_list[image_file_index])
                except ValueError:
                    print(f"Invalid file name: {image_file_list[image_file_index]}")
                    play_button.set_toggle(False)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.DROPFILE:
                open_path(event.file)
            if event.type == pg.KEYUP:
                if event.key == pg.K_q:
                    running = False
                
                if event.key == pg.K_SPACE:
                    play_button.set_toggle(not play_button.is_toggled)

                old = image_file_index
                if event.key == pg.K_RIGHT:
                    image_file_index += 1
                elif event.key == pg.K_LEFT:
                    image_file_index -= 1
                elif event.key == pg.K_UP:
                    image_file_index += 5
                elif event.key == pg.K_DOWN:
                    image_file_index -= 5
                elif event.key == pg.K_END:
                    image_file_index = len(image_file_list)-1
                elif event.key == pg.K_HOME:
                    image_file_index = 0
                image_file_index = min(max(image_file_index, 0), max(len(image_file_list)-1, 0))
                if image_file_index != old:
                    tof = 0
                    update_images(*exrutils.read_dual_image(image_file_list[image_file_index]), image_file_list[image_file_index])

            for i in elements:
                i.handle_event(event)

        for i in elements:
            i.tick()

        screen.fill("purple")

        for i in elements:
            i.render(screen)
        
        pg.display.flip()

        clock.tick(60)

    pg.quit()

if __name__ == "__main__":
    loop()