import json
import tkinter as tk
from functools import partial
from tkinter import Frame, Label, Entry, Button, filedialog, StringVar, IntVar
from tkinter import Menu, Toplevel

from lib import config


def openfile(master, fn=None):
    filename = filedialog.askopenfilename(parent=master,
                                          title="Select file",
                                          filetypes=(("zip files", "*.zip"), ("all files", "*.*")))
    print(filename)
    if fn is not None:
        fn(filename)


def save_settings(top, **kwargs):
    if kwargs is not None:
        settings = {ke: va.get() for ke, va in kwargs.items()}

        for key, value in settings.items():
            print("%s : %s" % (key, value))

        json_txt = json.dumps(settings)
        with open(config.SETTINGS_FILE, 'w') as file:
            file.write(json_txt)
            top.destroy()
            top.update()
        config.SETTINGS.refresh_data()


def display_settings_ui(master):
    top = Toplevel(master)
    top.resizable(width=False, height=False)

    body = Frame(top, width=400, height=150)

    Label(body, text="Model:").grid(row=0, column=0, sticky="e")
    Label(body, text="Hostname:").grid(row=1, column=0, sticky="e")
    Label(body, text="URL Post:").grid(row=2, column=0, sticky="e")
    Label(body, text="Video capture:").grid(row=3, column=0, sticky="e")
    Label(body, text="Post by minute:").grid(row=4, column=0, sticky="e")

    model = Entry(body)
    model.grid(row=0, column=1, sticky="we", padx=2, pady=2)

    inputs = {
        "modelPath": StringVar(),
        "hostname": StringVar(),
        "urlPost": StringVar(),
        "videoCapture": StringVar(),
        "postByMinute": IntVar(),
    }

    row = 0
    inputs["modelPath"].set(config.SETTINGS.model_path)
    inputs["hostname"].set(config.SETTINGS.hostname)
    inputs["urlPost"].set(config.SETTINGS.url_post)
    inputs["videoCapture"].set(config.SETTINGS.video_capture)
    inputs["postByMinute"].set(config.SETTINGS.post_by_minute)

    for k, var in inputs.items():
        Entry(body, textvariable=var).grid(row=row, column=1, sticky="we", padx=2, pady=2)
        row += 1

    Button(body, text="...",
           command=partial(openfile, master, handle_file(inputs["modelPath"]))) \
        .grid(row=0, column=2, sticky="we", padx=2, pady=2)

    pack_btm_buttons = Frame(body)

    start = Button(pack_btm_buttons, text="Save",
                   command=partial(save_settings, top, **inputs))
    start.pack(side="left", fill=None, expand=False)

    pack_btm_buttons.grid(row=6, column=1, columnspan=2, sticky="e", padx=2, pady=2)

    body.grid(row=0, column=0, padx=5)
    body.grid_propagate(0)

    body.grid_rowconfigure(0, weight=1)

    body.grid_columnconfigure(1, weight=1)
    body.grid_columnconfigure(1, weight=1)


def handle_file(modelpath):
    def update_variable(filename):
        modelpath.set(filename)

    return update_variable


if __name__ == "__main__":
    root = tk.Tk()

    menubar = Menu(root)
    root.config(menu=menubar)

    help_menu = Menu(menubar, tearoff=0)
    help_menu.add_command(label="Settings", command=partial(display_settings_ui, root))

    menubar.add_cascade(label="Tools", menu=help_menu)

    root.mainloop()
