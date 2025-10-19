import pygame as pg
import exrutils, cvutils
import numpy as np
from typing import Optional

# rgb, thermal = exrutils.read_dual_image("out/image.exr")
rgb, thermal = (np.random.rand(480,640,3), np.random.rand(240,320,1)*20.0+20.0)

# Transpose and convert to RGB888
rgb_surface = pg.surfarray.make_surface(np.transpose((rgb * 255.0).astype(np.uint8), (1,0,2)))
thermal_surface = pg.surfarray.make_surface(np.repeat(np.transpose((cvutils.normalize(thermal)*255).astype(np.uint8), (1,0,2)), 3, axis=2))

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
        self.surface.blit(self.font.render(self._text, 1, "cornsilk"), (0,0))

# pg setup
screen = pg.display.set_mode((1280, 720), pg.RESIZABLE)
clock = pg.time.Clock()
running = True
elements: list[Element] = [
    Element(pg.Rect((0,0),thermal_surface.get_size()), rgb_surface),
    Element(pg.Rect((640,0),thermal_surface.get_size()), thermal_surface),
    Label(pg.Rect((0,480),(256,64)), None, "Visible spectrum"),
    Label(pg.Rect((640,240),(256,64)), None, "IR spectrum"),
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