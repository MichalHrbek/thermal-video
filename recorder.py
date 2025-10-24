import time
from threading import Condition
from typing import Optional
from concurrent.futures import ProcessPoolExecutor

import cv2
import numpy as np
import pygame as pg
from seekcamera import (
    SeekCameraIOType,
    SeekCameraColorPalette,
    SeekCameraManager,
    SeekCameraManagerEvent,
    SeekCameraFrameFormat,
    SeekCameraFrame,
    SeekCameraError,
    SeekCamera,
    SeekFrame,
)

import exrutils
import player
from videocapture import BufferlessVideoCapture


class Renderer:
    def __init__(self):
        self.busy = False
        self.frame = SeekFrame()
        self.camera = SeekCamera()
        self.frame_condition = Condition()


def on_frame(_camera: SeekCamera, camera_frame: SeekCameraFrame, renderer: Renderer):
    print("Frame")
    with renderer.frame_condition:
        renderer.frame = camera_frame.thermography_float
        renderer.frame_condition.notify()


def on_event(camera: SeekCamera, event_type: SeekCameraManagerEvent, event_status: Optional[SeekCameraError], renderer: Renderer):
    print("{}: {}".format(str(event_type), camera.chipid))

    if event_type == SeekCameraManagerEvent.CONNECT:
        if renderer.busy:
            return

        renderer.busy = True
        renderer.camera = camera
        
        camera.color_palette = SeekCameraColorPalette.TYRIAN
        camera.register_frame_available_callback(on_frame, renderer)
        camera.capture_session_start(SeekCameraFrameFormat.THERMOGRAPHY_FLOAT)

    elif event_type == SeekCameraManagerEvent.DISCONNECT:
        if renderer.camera == camera:
            camera.capture_session_stop()
            renderer.camera = None
            renderer.frame = None
            renderer.busy = False

    elif event_type == SeekCameraManagerEvent.ERROR:
        print("{}: {}".format(str(event_status), camera.chipid))

    elif event_type == SeekCameraManagerEvent.READY_TO_PAIR:
        return


def bgr_white_hot(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor((img*255.0).astype(np.uint8), cv2.COLOR_GRAY2BGR)


def loop():
    cam = BufferlessVideoCapture(0)
    executor = ProcessPoolExecutor() # Image export is done in another process
    frame_counter = 1
    player.update_images(np.random.rand(480,640,3), np.linspace(20.0, 40.0, 240*320, dtype=np.float32).reshape(240, 320, 1), "No data found! Showing example data") # Generate random rgb data and temperature values from 20C to 40C

    screen = pg.display.set_mode((1280, 720), pg.RESIZABLE)
    clock = pg.time.Clock()
    running = True

    player.play_button.set_toggle(True)

    with SeekCameraManager(SeekCameraIOType.USB) as manager:
        renderer = Renderer()
        manager.register_event_callback(on_event, renderer)

        while running:
            with renderer.frame_condition:
                if renderer.frame_condition.wait(150.0 / 1000.0):
                    print("Render")
                    bgr_frame = cam.read()
                    rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB).astype('float32')/255.0
                    thermal_data = renderer.frame.data.astype('float32')
                    
                    file_name = "Not recording"
                    if player.play_button.is_toggled:
                        file_name = f"out/{int(time.time()*1000)}:{frame_counter:04}.exr"
                        executor.submit(exrutils.write_dual_image, rgb_frame, thermal_data, file_name)
                    else:
                        frame_counter = 0
                    player.update_images(rgb_frame, thermal_data, file_name)
                    frame_counter += 1

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                if event.type == pg.KEYUP:
                    if event.key == pg.K_q:
                        running = False
                for i in player.elements:
                    i.handle_event(event)

            for i in player.elements:
                i.tick()

            screen.fill("purple")

            for i in player.elements:
                i.render(screen)
            
            pg.display.flip()

            clock.tick(60)

    cam.close()
    pg.quit()


if __name__ == "__main__":
    loop()