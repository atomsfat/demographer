import numpy as np
import os
import getpass
import socket
import json

SLEEP_BETWEEN_DETECT = 0.2
CLASSES = None

TITLE = "Demographer"
VERSION = "0.0.1"

PWD = os.getcwd()

SETTINGS_FILE = PWD + "/.demographer-config.json"

YOLO_WEIGHTS = PWD + "/models/yolo/yolov3.weights"
YOLO_CONFIG = PWD + "/models/yolo/yolov3.cfg"
YOLO_CLASSES = PWD + "/models/yolo/yolov3.txt"

FRONTFACE = PWD + "/models/haarcascades/haarcascade_frontalface_default.xml"

with open(YOLO_CLASSES) as file_classes:
    CLASSES = [line.strip() for line in file_classes.readlines()]

COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))


class _Settings:

    def __init__(self):
        self.model_path = ""
        self.hostname = "{}@{}".format(getpass.getuser(), socket.gethostname())
        self.url_post = "https://localhost:5000/input"
        self.video_capture = "0"
        self.post_by_minute = 0
        self.refresh_data()

    def refresh_data(self):
        data = self.read_settings()
        if data is not None:
            self.model_path = data['modelPath']
            self.hostname = data['hostname']
            self.url_post = data['urlPost']
            try:
                self.video_capture = int(data['videoCapture'])
            except ValueError:
                self.video_capture = data['videoCapture']
            self.post_by_minute = data['postByMinute']

    def read_settings(self):
        data = None
        print("READING " + SETTINGS_FILE)
        filename = SETTINGS_FILE
        if os.path.exists(filename):
            with open(filename, 'r') as json_file:
                try:
                    print(json_file)
                    data = json.load(json_file)
                    print(data)
                except IOError:
                    print("Could not open/read file:")
        return data


SETTINGS = _Settings()

