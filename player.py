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
    
    def render(self, screen: pg.Surface):
        screen.blit(self.surface, self.rect)
    
    def tick(self):
        pass

class Label(Element):
    def __init__(self, rect: pg.Rect, surface: Optional[pg.Surface], text: str, font: Optional[pg.font.Font] = None):
        super().__init__(rect, surface)
        if font:
            self.font = font
        else:
            self.font = pg.font.SysFont('timesnewroman', 32)
        self.update_text(text)
    
    def update_text(self, text: str):
        self._text = text
        self.surface.fill((0,0,0,0))
        for i, line in enumerate(text.split('\n')):
            self.surface.blit(self.font.render(line, 1, "cornsilk"), (0,self.font.get_linesize()*i))

class Figure(Element):
    def __init__(self, rect: pg.Rect, surface: Optional[pg.Surface], label: Optional[Label], text: str):
        super().__init__(rect, surface)
        if label:
            self.label = label
        else:
            self.label = Label(pg.Rect(self.rect.bottomleft, (512,128)), None, text)
            self.label.update_text(text)
    
    def render(self, screen: pg.Rect):
        super().render(screen)
        self.label.rect.topleft = self.rect.bottomleft
        self.label.render(screen)

class Hoverable(Element):
    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pg.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.hovered(event.pos, (event.pos[0]-self.rect.topleft[0], event.pos[1]-self.rect.topleft[1]))

    def hovered(self, pos, local_pos):
        pass

class Clickable(Element):
    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pg.MOUSEBUTTONUP:
            if self.rect.collidepoint(event.pos):
                self.clicked(event.pos, (event.pos[0]-self.rect.topleft[0], event.pos[1]-self.rect.topleft[1]))

    def clicked(self, pos, local_pos):
        pass

class ThermalImage(Figure, Hoverable):
    def __init__(self, rect: pg.Rect, surface: Optional[pg.Surface], label: Optional[Label], text: str, celsius_array: np.ndarray):
        super().__init__(rect, surface, label, text)
        self.initial_text = text
        self.celsius_array = celsius_array

    def hovered(self, pos, local_pos):
        self.label.update_text(f"{self.initial_text}\n{self.celsius_array[local_pos][0]:.2f}°C")

rgb_image_element = Figure(pg.Rect((0,0),(0,0)), None, None, "Visible")
thermal_image_element = ThermalImage(pg.Rect((0,0),(0,0)), None, None, "Temperature", None)
file_info_label = Label(pg.Rect((0,0),(512,64)), None, "No file loaded")

def update_images(new_rgb_array, new_celsius_array, filename):
    new_rgb_array = np.transpose(new_rgb_array, (1,0,2))
    new_celsius_array = np.transpose(new_celsius_array.reshape(240, 320, 1), (1,0,2))
    rgb_image_element.update_surface(pg.surfarray.make_surface((new_rgb_array * 255.0).astype(np.uint8)))
    thermal_image_element.update_surface(pg.surfarray.make_surface(np.repeat((cvutils.normalize(new_celsius_array)*255).astype(np.uint8), 3, axis=2)))
    thermal_image_element.celsius_array = new_celsius_array
    thermal_image_element.rect.topleft = rgb_image_element.rect.topright
    file_info_label.update_text(filename)
    file_info_label.rect.topleft = thermal_image_element.rect.topright

# update_images(*exrutils.read_dual_image(image_file_list[image_file_index]))
# update_images(np.random.rand(480,640,3), np.linspace(20.0, 40.0, 240*320, dtype=np.float32).reshape(240, 320, 1)) # Generate random rgb data and temperature values from 20C to 40C

elements: list[Element] = [
    rgb_image_element,
    thermal_image_element,
    file_info_label,
]

def loop():
    image_file_list = sorted(glob("out/*.exr"))
    image_file_index = 0
    update_images(*exrutils.read_dual_image(image_file_list[image_file_index]), image_file_list[image_file_index])

    screen = pg.display.set_mode((1280, 720), pg.RESIZABLE)
    clock = pg.time.Clock()
    running = True

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.KEYUP:
                if event.key == pg.K_q:
                    running = False

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