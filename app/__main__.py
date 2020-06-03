import tkinter as tk
import logging.config
import yaml
from lib.threads import ThreadWrapper
from lib import config


with open('logconfig.yaml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger(__name__)

logger.debug(config.PWD)

ROOT = tk.Tk()
ThreadWrapper(ROOT)
ROOT.mainloop()  # Starts GUI

