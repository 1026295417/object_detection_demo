""" ref:
https://github.com/ECI-Robotics/opencv_remote_streaming_processing/
"""

import cv2
import detection
import os
import sys
from logging import getLogger, basicConfig, DEBUG, INFO

logger = getLogger(__name__)

basicConfig(
    level=INFO,
    format="%(asctime)s %(levelname)s %(name)s %(funcName)s(): %(message)s")

frame_prop = (640, 480)


class VideoCamera(object):
    def __init__(self, input, model_xml, model_bin, device, prob_threshold,
                 cpu_extention, is_async_mode, flip_code, no_v4l):
        self.flip_code = flip_code

        if input == 'cam':
            self.input_stream = 0
            if no_v4l:
                self.cap = cv2.VideoCapture(self.input_stream)
            else:
                # for Picamera, added VideoCaptureAPIs(cv2.CAP_V4L)
                try:
                    self.cap = cv2.VideoCapture(self.input_stream, cv2.CAP_V4L)
                except:
                    logger.error(
                        "cv2.VideoCapture() does not need v4l option. Try to start with --no_v4l option."
                    )
                    sys.exit(1)
        else:
            self.input_stream = input
            assert os.path.isfile(input), "Specified input file doesn't exist"
            self.cap = cv2.VideoCapture(self.input_stream)

        ret, self.frame = self.cap.read()
        cap_prop = self._get_cap_prop()
        logger.info("cap_pop:{}, frame_prop:{}".format(cap_prop, frame_prop))

        if ret:
            self.detection = detection.ObjectDetection(
                frame_prop, model_xml, model_bin, device, prob_threshold,
                cpu_extention, is_async_mode)

    def __del__(self):
        self.cap.release()

    def _get_cap_prop(self):
        return self.cap.get(cv2.CAP_PROP_FRAME_WIDTH), self.cap.get(
            cv2.CAP_PROP_FRAME_HEIGHT), self.cap.get(cv2.CAP_PROP_FPS)

    def get_frame(self, is_async_mode, flip_code):
        self.flip_code = flip_code

        if is_async_mode:
            ret, next_frame = self.cap.read()
            next_frame = cv2.resize(next_frame, frame_prop)
            if self.input_stream == 0 and self.flip_code is not None:
                next_frame = cv2.flip(next_frame, int(self.flip_code))
        else:
            ret, self.frame = self.cap.read()
            self.frame = cv2.resize(self.frame, frame_prop)
            next_frame = None
            if self.input_stream == 0 and self.flip_code is not None:
                self.frame = cv2.flip(self.frame, int(self.flip_code))
        if not ret:
            return

        frame = self.detection.start_inference(self.frame, next_frame,
                                               is_async_mode)
        ret, jpeg = cv2.imencode('1.jpg', frame)

        if is_async_mode:
            self.frame = next_frame

        return jpeg.tostring()