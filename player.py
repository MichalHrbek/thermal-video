import pygame as pg
import exrutils, cvutils
import numpy as np
from typing import Optional

# rgb, thermal = exrutils.read_dual_image("out/image.exr")
rgb, thermal = (np.random.rand(480,640,3), np.linspace(20.0, 40.0, 240*320, dtype=np.float32).reshape(240, 320, 1)) # Generate random rgb data and temperature values from 20C to 40C

# Transpose and convert to RGB888
rgb = np.transpose(rgb, (1,0,2))
thermal = np.transpose(thermal, (1,0,2))
rgb_surface = pg.surfarray.make_surface((rgb * 255.0).astype(np.uint8))
thermal_surface = pg.surfarray.make_surface(np.repeat((cvutils.normalize(thermal)*255).astype(np.uint8), 3, axis=2))

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

class Label(Element):
    def __init__(self, rect: pg.Rect, surface: Optional[pg.Surface], text: str, font: Optional[pg.font.Font] = None):
        super().__init__(rect, surface)
        if font:
            self.font = font
        else:
            self.font = pg.font.SysFont('timesnewroman', 32)
        self.update_text(text)
    
    def update_text(self, text):
        self._text = text
        self.surface.fill((0,0,0,0))
        self.surface.blit(self.font.render(self._text, 1, "cornsilk"), (0,0))

class ThermalImage(Element):
    def __init__(self, rect: pg.Rect, surface: Optional[pg.Surface], celsius_array: np.ndarray, label: Optional[Label]):
        super().__init__(rect, surface)
        self.label = label
        self.celsius_array = celsius_array
    
    def handle_event(self, event: pg.event.Event):
        if event.type == pg.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                local_pos = (event.pos[0]-self.rect.topleft[0], event.pos[1]-self.rect.topleft[1])
                if self.label:
                    self.label.update_text(f"{self.celsius_array[local_pos][0]:.2f}")

# pg setup
screen = pg.display.set_mode((1280, 720), pg.RESIZABLE)
clock = pg.time.Clock()
running = True

celsius_label = Label(pg.Rect((640,240+32),(256,64)), None, "")
elements: list[Element] = [
    Element(pg.Rect((0,0),thermal_surface.get_size()), rgb_surface),
    ThermalImage(pg.Rect((640,0),thermal_surface.get_size()), thermal_surface, thermal, celsius_label),
    Label(pg.Rect((0,480),(256,64)), None, "Visible spectrum"),
    Label(pg.Rect((640,240),(256,64)), None, "IR spectrum"),
    celsius_label,
]

while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        for i in elements:
            i.handle_event(event)

    screen.fill("purple")

    for i in elements:
        screen.blit(i.surface, i.rect)
    
    pg.display.flip()

    clock.tick(60)

pg.quit()