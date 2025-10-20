#!/usr/bin/env python3
# Copyright 2021 Seek Thermal Inc.
#
# Original author: Michael S. Mead <mmead@thermal.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Modified from original which can be found at https://github.com/seekthermal/seekcamera-python/blob/3b056f94225a17190d4fd78bb59a690baa5946a9/examples/seekcamera-opencv.py

from threading import Condition, Thread
from typing import Optional
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import cv2
import cvutils, exrutils
import numpy as np
import time
from videocapture import BufferlessVideoCapture

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


def main():
    window_name = "Video"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cam = BufferlessVideoCapture(0)
    frame_counter = 1

    with SeekCameraManager(SeekCameraIOType.USB) as manager:
        # Start listening for events.
        renderer = Renderer()
        manager.register_event_callback(on_event, renderer)

        while True:
            # Wait a maximum of 150ms for each frame to be received.
            # A condition variable is used to synchronize the access to the renderer;
            # it will be notified by the user defined frame available callback thread.
            with renderer.frame_condition:
                if renderer.frame_condition.wait(150.0 / 1000.0):
                    print("Render")
                    # Render the image to the window.
                    bgr_frame = cam.read()
                    thermal_frame_processed = cv2.resize(cvutils.bgr_white_hot(cvutils.normalize(renderer.frame.data)), (bgr_frame.shape[1],bgr_frame.shape[0]))
                    cv2.imshow(window_name, np.concatenate((bgr_frame,thermal_frame_processed), axis=1))
                    
                    # Export image
                    rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB).astype('float16')/255.0
                    # with ProcessPoolExecutor() as executor:
                        # future = executor.submit(exrutils.write_dual_image, rgb_frame, renderer.frame.data.astype('float32'), "out/image.exr")
                    t = Thread(target=exrutils.write_dual_image, args=(rgb_frame, renderer.frame.data.astype('float16'), f"out/{int(time.time()*1000)}:{frame_counter:04}.exr"))
                    frame_counter += 1
                    t.start()

            # Process key events.
            key = cv2.waitKey(1)
            if key == ord("q"):
                break

            # Check if the window has been closed manually.
            if not cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE):
                break

    # cam.release()
    cv2.destroyWindow(window_name)


if __name__ == "__main__":
    main()