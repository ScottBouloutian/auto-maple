"""The central program that ties all the modules together."""

import os

os.add_dll_directory("C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v11.2/bin")

import time
from bot import Bot
from capture import Capture
from listener import Listener
from gui import GUI


bot = Bot()
bot.start()
while not bot.ready:
    time.sleep(0.01)

cap = Capture()
cap.start()
while not cap.ready:
    time.sleep(0.01)

listener = Listener()
listener.start()
while not listener.ready:
    time.sleep(0.01)

print('\n[~] Successfully initialized Auto Maple.')

gui = GUI()
gui.start()
