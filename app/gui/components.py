# -*- coding: utf-8 -*-
from functools import partial
from tkinter import Menu, Button, messagebox, Toplevel, Label
from tkinter import Frame, Text, GROOVE, END, Scrollbar
import datetime
from PIL import Image, ImageTk
import cv2
from gui.settings import display_settings_ui


def help_about():
    messagebox.showinfo(
        "Demographer", "Atoms was here."
    )


def do_nothing(root):
    filewin = Toplevel(root)
    button = Button(filewin, text="Do nothing button")
    button.pack()


def main_menu(root, end_command):

    menubar = Menu(root)
    root.config(menu=menubar)

    help_menu = Menu(menubar, tearoff=0)
    help_menu.add_command(label="Settings", command=partial(display_settings_ui, root))
    help_menu.add_command(label="About", command=help_about)
    menubar.add_cascade(label="Tools", menu=help_menu)
    help_menu.add_separator()
    help_menu.add_command(label="Exit", command=end_command)


class DisplayFrame(Frame):

    def __init__(self, parent, start_cmd):
        Frame.__init__(self, parent)
        self.root = parent
        self.display = None
        self.log_txt = None
        self.init_page()
        self.start_cmd = start_cmd

    def init_page(self):
        # create all of the main containers
        top_frame = Frame(self.root, width=450, height=50, pady=3)
        center = Frame(self.root, width=600, height=200, padx=3, pady=3)
        btm_frame = Frame(self.root, bg='white', width=600, height=45, pady=3)

        # layout all of the main containers
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        top_frame.grid(row=0, sticky="ew")
        center.grid(row=1, sticky="nsew")
        btm_frame.grid(row=3, sticky="ew")

        # create the center widgets
        center.grid_rowconfigure(0, weight=1)
        center.grid_columnconfigure(0, weight=3)
        center.grid_columnconfigure(1, weight=1)

        content_frame = Frame(self.root, borderwidth=5, relief=GROOVE, background="pink")
        log_frame = Frame(self.root, borderwidth=5, relief=GROOVE)
        # Aspect Ratio
        set_aspect(content_frame, log_frame, center, aspect_ratio=4.0/3.0)
        self.display = Label(content_frame, text="Display")
        self.display.grid(column=0, row=0, sticky="nsew")
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        log_lbl = Label(log_frame, text="Events")
        log_lbl.grid(column=0, row=0, sticky="nw")

        self.log_txt = Text(log_frame, state='disabled', width=10)
        # self.log_txt.tag_configure('bold_italics', font=('Arial', 8, 'bold', 'italic'))
        scroll = Scrollbar(log_frame, command=self.log_txt.yview)
        self.log_txt.grid(column=0, row=1, sticky="nsew")
        scroll.grid(column=1, row=1, sticky='nsew')
        self.log_txt['yscrollcommand'] = scroll.set

        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        # create the widgets for btm_frame
        btm_frame.grid_columnconfigure(0, weight=1)

        pack_btm_buttons = Frame(btm_frame)
        self.stop_btn = Button(pack_btm_buttons, text=u"◼ Stop", state="disabled", command=self.handle_stop)
        self.start_btn = Button(pack_btm_buttons, text="▶ Start", command=self.handle_start_btn)
        # self.detect = Button(pack_btm_buttons, text="⏺ Detect", command=self.handle_detection_btn, state="disabled")

        self.start_btn.pack(side="left", fill=None, expand=False)
        self.stop_btn.pack(side="left", fill=None, expand=False)

        pack_btm_buttons.grid(column=0, row=0, sticky="e")

    def handle_start_btn(self):
        self.start_btn.configure(state="disabled")
        self.start_cmd()
        self.stop_btn.configure(state="normal")

    def handle_stop(self):
        self.start_cmd(stop=True)
        self.start_btn.configure(state="normal")

    def update_content(self, imagearray):

        frame_resized = cv2.resize(imagearray,
                                   (self.display.winfo_width(), self.display.winfo_height()))
        cv2image = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGBA)
        current_image = Image.fromarray(cv2image)
        img_tk = ImageTk.PhotoImage(image=current_image)
        self.display.config(image=img_tk)  # show the image
        self.display.image = img_tk  # anchor imgtk so it does not be deleted by garbage-collector
        self.display.img_tk = img_tk
        self.display.config(image=img_tk)

    def update_event(self, event: str):
        self.log_txt.config(state='normal')
        now = datetime.datetime.now()
        self.log_txt.insert(END, "[" + now.strftime("%Y/%m/%d %H:%M:%S") + "] ")
        self.log_txt.insert(END, event + "\n")
        self.log_txt.config(state='disabled')
        self.log_txt.yview(END)


def set_aspect(content_frame, log_frame, pad_frame, aspect_ratio):
    # a function which places a frame within a containing frame, and
    # then forces the inner frame to keep a specific aspect ratio

    def enforce_aspect_ratio(event):
        # when the pad window resizes, fit the content into it,
        # either by fixing the width or the height and then
        # adjusting the height or width based on the aspect ratio.

        # start by using the width as the controlling dimension
        desired_width = event.width
        desired_height = int(event.width / aspect_ratio)

        # if the window is too tall to fit, use the height as
        # the controlling dimension
        if desired_height > event.height:
            desired_height = event.height
            desired_width = int(event.height * aspect_ratio)

        # place the window, giving it an explicit size
        x_pad_frame = 0
        log_width = event.width - desired_width

        if log_width > 600:
            x_pad_frame = (event.width - (desired_width + 600))/2
            log_width = 600

        content_frame.place(in_=pad_frame, x=x_pad_frame, y=0,
                            width=desired_width, height=desired_height)

        log_frame.place(in_=pad_frame, x=desired_width + x_pad_frame, y=0,
                        width=log_width, height=event.height)

    pad_frame.bind("<Configure>", enforce_aspect_ratio)
