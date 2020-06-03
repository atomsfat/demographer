# -*- coding: utf-8 -*-
import logging
from tkinter import FALSE

import cv2

from lib.payload import Payload
from gui.components import main_menu, DisplayFrame
from lib import config

LOGGER = logging.getLogger(__name__)


class MainFrame:
    def __init__(self, master, queue, start_cmd, end_command):
        self.queue = queue

        self.root = master
        self.end_command = end_command

        # Tk stuff
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.option_add('*tearOff', FALSE)

        # Components
        main_menu(self.root, end_command)
        self.current_frame = DisplayFrame(self.root, start_cmd)

        self.cvframe = None
        self.payload = None

    def update_img(self):
        if self.cvframe is not None:
            self.current_frame.update_content(self.cvframe)

    def draw_prediction(self, class_id, confidence, x, y, x_plus_w, y_plus_h):

        label = str(config.CLASSES[class_id]) + " " + confidence
        color = config.COLORS[class_id]
        cv2.rectangle(self.cvframe, (x, y), (x_plus_w, y_plus_h), color, 2)
        cv2.putText(self.cvframe, label, (x-10, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def show_frame(self):

        if self.cvframe.any() and self.payload:
            detected = []
            for i in self.payload.indices:

                i = i[0]
                box = self.payload.boxes[i]
                # pylint: disable=invalid-name
                x = box[0]
                y = box[1]
                w = box[2]
                h = box[3]
                confidence = '{0:.2f}'.format(100 * self.payload.confidences[i])

                label = config.CLASSES[self.payload.class_ids[i]]

                detected.append(f"{label}:{confidence}%")
                self.draw_prediction(self.payload.class_ids[i],
                                     confidence,
                                     round(x), round(y), round(x+w), round(y+h))
            # print(",".join(detected))
            if detected:
                detected = ",".join(detected)
                LOGGER.info(detected)
                self.current_frame.update_event(detected)
        self.update_img()

    def process_incoming(self):

        # LOGGER.debug("processIncoming %s", str(self.queue.qsize()))
        if self.queue.qsize():
            msg = self.queue.get(0)
            # LOGGER.debug("processIncoming %s", type(msg))
            if msg is None:  # Empty the payload
                self.payload = None
                return

            if isinstance(msg, Payload):
                self.payload = msg

            else:
                self.cvframe = msg

            self.show_frame()

    def close(self):
        LOGGER.debug('received stop signal, cancelling tasks...')
        self.end_command()
        self.root.destroy()
