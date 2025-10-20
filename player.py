import pygame as pg
import exrutils, cvutils
import numpy as np
from typing import Optional
from glob import glob

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

celsius_label = Label(pg.Rect((640,240+32),(256,64)), None, "")
rgb_image_element = Element(pg.Rect((0,0),(0,0)), None)
thermal_image_element = ThermalImage(pg.Rect((640,0),(0,0)), None, None, celsius_label)
# celsius_array = np.linspace(20.0, 40.0, 240*320, dtype=np.float32).reshape(240, 320, 1)

def update_images(new_rgb_array, new_celsius_array):
    new_rgb_array = np.transpose(new_rgb_array, (1,0,2))
    new_celsius_array = np.transpose(new_celsius_array.reshape(240, 320, 1), (1,0,2))
    rgb_image_element.update_surface(pg.surfarray.make_surface((new_rgb_array * 255.0).astype(np.uint8)))
    thermal_image_element.update_surface(pg.surfarray.make_surface(np.repeat((cvutils.normalize(new_celsius_array)*255).astype(np.uint8), 3, axis=2)))
    thermal_image_element.celsius_array = new_celsius_array
    celsius_label.rect.topleft = thermal_image_element.rect.bottomleft

# update_images(*exrutils.read_dual_image(image_file_list[image_file_index]))
# update_images(np.random.rand(480,640,3), np.linspace(20.0, 40.0, 240*320, dtype=np.float32).reshape(240, 320, 1)) # Generate random rgb data and temperature values from 20C to 40C

elements: list[Element] = [
    rgb_image_element,
    thermal_image_element,
    celsius_label,
]

def loop():
    image_file_list = sorted(glob("out/*.exr"))
    image_file_index = 0
    update_images(*exrutils.read_dual_image(image_file_list[image_file_index]))

    screen = pg.display.set_mode((1280, 720), pg.RESIZABLE)
    clock = pg.time.Clock()
    running = True

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.KEYUP:
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
                image_file_index = min(max(image_file_index, 0), len(image_file_list)-1)
                if image_file_index != old:
                    update_images(*exrutils.read_dual_image(image_file_list[image_file_index]))

            for i in elements:
                i.handle_event(event)

        screen.fill("purple")

        for i in elements:
            screen.blit(i.surface, i.rect)
        
        pg.display.flip()

        clock.tick(60)

    pg.quit()

if __name__ == "__main__":
    loop()