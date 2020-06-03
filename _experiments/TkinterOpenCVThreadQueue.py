import numpy as np
import cv2
import tkinter as tk
from PIL import Image, ImageTk
import time
import threading
import random
import queue
import requests
from io import BytesIO
from urllib.request import urlopen
from Payload import Payload

# generate different colors for different classes
classes = None

#https://github.com/arunponnusamy/object-detection-opencv
with open("./_models/yolov3.txt") as file:
    classes = [line.strip() for line in file.readlines()]
COLORS = np.random.uniform(0, 255, size=(len(classes), 3))

class GuiPart:
    def __init__(self, master, queue, endCommand):
        self.queue = queue

        self.root = master
        #Graphics window
        self.imageFrame = tk.Frame(master, width=600, height=500)
        self.imageFrame.grid(row=0, column=0, padx=10, pady=2)

        #Capture video frames
        self.lmain = tk.Label(self.imageFrame)
        self.lmain.grid(row=0, column=0)
        self.openCVFrame = None

        # self.cap = cv2.VideoCapture(0)
        self.payload = None
        self.show_frame2()

    def draw_prediction(self, class_id, confidence, x, y, x_plus_w, y_plus_h):

        label = str(classes[class_id])
        color = COLORS[class_id]
        cv2.rectangle(self.openCVFrame, (x,y), (x_plus_w,y_plus_h), color, 2)
        cv2.putText(self.openCVFrame, label, (x-10,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def show_frame2(self):


        if self.openCVFrame is not None and self.payload:
            for i in self.payload.indices:

                i = i[0]
                box = self.payload.boxes[i]
                x = box[0]
                y = box[1]
                w = box[2]
                h = box[3]

                self.draw_prediction(self.payload.class_ids[i], self.payload.confidences[i], round(x), round(y), round(x+w), round(y+h))


        if self.openCVFrame is not None:

            cv2image = cv2.cvtColor(self.openCVFrame, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2image)

            imgtk = ImageTk.PhotoImage(image=img)

            self.lmain.imgtk = imgtk
            self.lmain.config(image=imgtk)


        self.root.after(25, self.show_frame2)

    def processIncoming(self):

        # print("processIncoming " + str(self.queue.qsize()))

        if self.queue.qsize():
            msg = self.queue.get(0)
            # Check contents of message and do whatever is needed. As a
            # simple test, print it (in real life, you would
            # suitably update the GUI's display in a richer fashion).
            # print("MSG", msg)
            # img_tk = ImageTk.PhotoImage(image=msg)
            # self.lmain.image = img_tk  # anchor imgtk so it does not be deleted by garbage-collector

            if type(msg) == Payload:
                print("FAAAAAAAATTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT")
                self.payload = msg
            else:
                self.openCVFrame = msg



class ThreadedClient:

    def __init__(self, master):

        self.master = master

        self.queue = queue.Queue(  )

        # Set up the GUI part
        self.gui = GuiPart(master, self.queue, self.endApplication)

        # Set up the thread to do asynchronous I/O
        # More threads can also be created and used, if necessary
        self.running = 2
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread2 = threading.Thread(target=self.workerThread2)

        self.cap = cv2.VideoCapture(0)
        self.frame = None
        self.thread1.start( )
        # self.thread2.start( )



        # Start the periodic call in the GUI to check if the queue contains
        # anything
        self.periodicCall(  )

    def periodicCall(self):
        """
        Check every 200 ms if there is something new in the queue.
        """
        self.gui.processIncoming( )
        if not self.running:
            # This is the brutal stop of the system. You may want to do
            # some cleanup before actually shutting it down.

            self.cap.release()


            import sys
            sys.exit(1)
        self.master.after(41, self.periodicCall)

    def workerThread1(self):
        """
        This is where we handle the asynchronous I/O. For example, it may be
        a 'select(  )'. One important thing to remember is that the thread has
        to yield control pretty regularly, by select or otherwise.
        """

        while self.running:

            _, frame = self.cap.read()
            frame = cv2.flip(frame, 1)
            self.frame = frame



            self.queue.put(self.frame)

            time.sleep(.1)


    def get_output_layers(self, net):

        layer_names = net.getLayerNames()
        output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

        return output_layers

    def workerThread2(self):

        print("net working")

        # read pre-trained model and config file
        net = cv2.dnn.readNet("./_models/yolov3.weights", "./_models/yolov3.cfg")
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_OPENCL)


        scale = 0.00392
        """
        This is where we handle the asynchronous I/O. For example, it may be
        a 'select(  )'. One important thing to remember is that the thread has
        to yield control pretty regularly, by select or otherwise.
        """
        while self.running:


                blob = cv2.dnn.blobFromImage(self.frame, scale, (416,416), (0,0,0), True, crop=False)
                # To simulate asynchronous I/O, we create a random number at
                # random intervals. Replace the following two lines with the real
                # thing.

                Width = self.frame.shape[1]
                Height = self.frame.shape[0]

                net.setInput(blob)
                outs = net.forward(self.get_output_layers(net))
                print("outs " + str(len(outs)) + str(type(outs)))


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

                            center_x = int(detection[0] * Width)
                            center_y = int(detection[1] * Height)
                            w = int(detection[2] * Width)
                            h = int(detection[3] * Height)
                            x = center_x - w / 2
                            y = center_y - h / 2

                            class_ids.append(class_id)
                            confidences.append(float(confidence))
                            boxes.append([x, y, w, h])

                indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

                payload = Payload(indices, class_ids, confidences, boxes)

                print("outs " + str(len(outs)) + str(type(indices)))

                time.sleep(.5)

                # msg = rand.random( )
                # print("put", msg)
                self.queue.put(payload)

    def endApplication(self):
        self.running = 0




rand = random.Random(  )
root = tk.Tk(  )

client = ThreadedClient(root)
root.mainloop()  #Starts GUI
