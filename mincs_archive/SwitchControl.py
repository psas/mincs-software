import sys
import os
import os.path
import time
import csv
import datetime
import subprocess
import openpyxl
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk, messagebox
from tkinter import ttk, Tk, StringVar, N, E, S, W, Button
import tkinter.messagebox as messagebox
from labjack import ljm
import labjack.ljm as ljm
import threading
import pyfirmata
from ArduinoHandler import ArduinoHandler
from LabJackHandler import LabJackHandler
import json
import queue

class SwitchControlWindow(tk.Toplevel):
    def __init__(self, labjack_handler, pin_config, control_panel_instance):
        super().__init__()

        self.labjack_handler = labjack_handler
        self.pin_config = pin_config
        self.control_panel_instance = control_panel_instance
        self.switch_tab_enabled = True

        self.title("Switch Control")
        self.geometry("400x300")

        self.create_switch_tab()
        self.protocol("WM_DELETE_WINDOW", self.quit_switch_control)

        self.control_panel_instance.switch_control_active = True

        # create a thread to handle the LabJack interaction
        self.thread_stop = False
        self.labjack_thread = threading.Thread(target=self.write_pin_states)
        self.labjack_thread.start()

    def create_switch_tab(self):
        pins = [
            "LOX Valve",
            "N2 IPA Valve",
            "N2 LOX Valve",
            "IPA Valve",
            "N2 Purge Valve",
            "Ignition",
        ]

        self.switch_frame = ttk.Frame(self, padding=10)
        self.switch_frame.pack()

        self.switch_title_label = ttk.Label(self.switch_frame, text="Advanced Configuration", font=('Helvetica', 10, 'bold'))
        self.switch_title_label.grid(row=0, column=0, columnspan=3, pady=10)

        self.pin_buttons = {}

        for i, pin_name in enumerate(pins):
            pin_label = ttk.Label(self.switch_frame, text=pin_name)
            pin_label.grid(row=(i // 3) * 3 + 1, column=i % 3, padx=20, pady=10)

            button = tk.Button(
                self.switch_frame,
                text="OFF",
                command=lambda pin=pin_name: self.toggle_pin(pin),
                width=8,
                height=2,
                bg='red'
            )
            button.grid(row=(i // 3) * 3 + 2, column=i % 3, padx=20, pady=10)
            self.pin_buttons[pin_name] = button
    
    def toggle_pin(self, pin_name):
        if not self.switch_tab_enabled:
            return

        button = self.pin_buttons[pin_name]
        current_state = button["text"]
        new_state = "ON" if current_state == "OFF" else "OFF"

        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"][pin_name], 1 if new_state == "ON" else 0)

        button["text"] = new_state
        button.config(bg='green' if new_state == "ON" else 'red')

    def write_pin_states(self):
        while not self.thread_stop:
            if not self.control_panel_instance.switch_control_active:
                return

            for pin_name, button in self.pin_buttons.items():
                pin_state = 1 if button["text"] == "ON" else 0
                ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"][pin_name], pin_state)

            time.sleep(0.01)

    def quit_switch_control(self):
        self.thread_stop = True
        self.control_panel_instance.switch_control_active = False
        self.destroy()