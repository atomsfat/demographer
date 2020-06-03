# -*- coding: utf-8 -*-
import logging
import time
import threading
import queue
import sys

import cv2
import numpy as np

from lib.payload import Payload
from lib import config

from gui.tkapp import MainFrame

LOGGER = logging.getLogger(__name__)


def get_output_layers(net):
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    return output_layers


class ThreadWrapper:

    def __init__(self, master):

        LOGGER.debug('This is a debug message')
        logging.debug('help')
        self.master = master
        self.master.winfo_toplevel().title(config.TITLE + " Video capture: " + str(config.SETTINGS.video_capture))
        self.queue = queue.Queue()

        # Set up the GUI part
        self.gui = MainFrame(master, self.queue, self.start, self.end_application)
        # Set up the thread to do asynchronous I/O
        # More threads can also be created and used, if necessary
        self.running = True
        self.threads = {
            'capture': {
                'thread': None,
                'running': False
            },
            'detect': {
                'thread': None,
                'running': False
            }
        }

        self.cvframe = None
        self.cap = None

        # Start the periodic call in the GUI to check if the queue contains
        # anything
        self.periodic_call()

    def periodic_call(self):
        self.gui.process_incoming()
        if not self.running:
            # This is the brutal stop of the system. You may want to do
            # some cleanup before actually shutting it down.
            sys.exit(1)
        self.master.after(41, self.periodic_call)

    def end_application(self):
        print("endApplication")
        self.running = False
        self.threads["capture"]['running'] = False
        self.threads["detect"]['running'] = False

    def start(self, stop=False):

        if stop:
            self.threads["capture"]['running'] = False
            self.threads["detect"]['running'] = False
            if self.cap:
                self.cap.release()
            self.cap = None
            self.cvframe = None

            return

        self.master.winfo_toplevel().title(config.TITLE + " Video capture: " + str(config.SETTINGS.video_capture))

        LOGGER.debug("starting video")
        self.threads["capture"]['running'] = True
        self.threads["capture"]['thread'] = threading.Thread(target=self.video_capture_thread)
        self.threads["capture"]['thread'].start()

        LOGGER.debug("starting detection")
        self.threads["detect"]['running'] = True
        self.threads["detect"]['thread'] = threading.Thread(target=self.detection_thread)
        # self.threads["detect"]['thread'] = threading.Thread(target=self.detection_from_caffee)
        self.threads["detect"]['thread'].start()

    def video_capture_thread(self):

        if self.cap is None:
            LOGGER.debug("Openning video capture: %s", config.SETTINGS.video_capture)
            self.cap = cv2.VideoCapture(config.SETTINGS.video_capture)

        while self.threads["capture"]['running']:
            _, frame = self.cap.read()
            frame = cv2.flip(frame, 1)
            self.cvframe = frame
            self.queue.put(self.cvframe)

            time.sleep(config.SLEEP_BETWEEN_DETECT)

    def detection_thread(self):
        LOGGER.debug("Init NET CV")
        # read pre-trained model and config file
        net = cv2.dnn.readNet(config.YOLO_WEIGHTS, config.YOLO_CONFIG)
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_OPENCL)

        scale = 0.00392

        while self.threads["detect"]['running']:
            payload = None
            if self.cvframe is not None and self.cvframe.any():

                blob = cv2.dnn.blobFromImage(self.cvframe, scale, (416, 416), (0, 0, 0), True, crop=False)
                width = self.cvframe.shape[1]
                height = self.cvframe.shape[0]

                net.setInput(blob)
                outs = net.forward(get_output_layers(net))

                class_ids = []
                confidences = []
                boxes = []

                conf_threshold = 0.5
                nms_threshold = 0.4

                for out in outs:
                    for detection in out:

                        scores = detection[5:]
                        class_id = np.argmax(scores)
                        confidence = scores[class_id]

                        if confidence > 0.5:
                            center_x = int(detection[0] * width)
                            center_y = int(detection[1] * height)
                            # pylint: disable=invalid-name
                            w = int(detection[2] * width)
                            h = int(detection[3] * height)
                            x = center_x - w / 2
                            y = center_y - h / 2

                            class_ids.append(class_id)
                            confidences.append(float(confidence))
                            boxes.append([x, y, w, h])

                    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

                    payload = Payload(indices, class_ids, confidences, boxes)

                    LOGGER.debug("detected:  %s", len(indices))

            self.queue.put(payload)
            time.sleep(config.SLEEP_BETWEEN_DETECT)

    # https://itywik.org/2018/03/26/age-and-gender-detection-with-opencv-on-the-raspberry-pi/
    def detection_from_caffee(self):
        LOGGER.debug("Init detection_from_caffee")
        model_mean_values = (78.4263377603, 87.7689143744, 114.895847746)
        age_list = ['(0, 2)', '(4, 6)', '(8, 12)', '(15, 20)', '(25, 32)', '(38, 43)', '(48, 53)', '(60, 100)']
        gender_list = ['Male', 'Female']

        age_net = cv2.dnn.readNetFromCaffe(
            config.PWD + "/models/caffee/deploy_age.prototxt",
            config.PWD + "/models/caffee/age_net.caffemodel")

        gender_net = cv2.dnn.readNetFromCaffe(
            config.PWD + "/models/caffee/deploy_gender.prototxt",
            config.PWD + "/models/caffee/gender_net.caffemodel")

        while self.threads["detect"]['running']:

            if self.cvframe is not None and self.cvframe.any():
                face_cascade = cv2.CascadeClassifier(config.FRONTFACE)
                gray = cv2.cvtColor(self.cvframe, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 5)
                LOGGER.debug("Found " + str(len(faces)) + " face(s)")
                for (x, y, w, h) in faces:
                    # cv2.rectangle(self.cvframe, (x, y), (x+w, y+h), (255, 255, 0), 2)
                    face_img = self.cvframe[y:y + h, x:x + w].copy()
                    blob = cv2.dnn.blobFromImage(face_img, 1, (227, 227), model_mean_values, swapRB=False)

                    # Predict gender
                    gender_net.setInput(blob)
                    gender_preds = gender_net.forward()
                    LOGGER.debug(gender_preds)
                    gender = gender_list[gender_preds[0].argmax()]

                    # Predict age
                    age_net.setInput(blob)
                    age_preds = age_net.forward()
                    LOGGER.debug(age_preds)
                    age = age_list[age_preds[0].argmax()]

                    overlay_text = "%s, %s" % (gender, age)
                    LOGGER.debug("overlay_text" + overlay_text)
                    # payload = Payload(indices, class_ids, confidences, faces)
                    # cv2.putText(image, overlay_text ,(x,y), font, 2,(255,255,255),2,cv2.LINE_AA)
