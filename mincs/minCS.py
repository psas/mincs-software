import sys
import os
import time
import csv
import datetime
import threading
import serial
import tkinter as tk
from tkinter import ttk
from labjack import ljm
import labjack.ljm as ljm
import pyfirmata
from ControlPanel import ControlPanel
from ArduinoHandler import ArduinoHandler
from LabJackHandler import LabJackHandler
from loading import LoadingWindow
from itertools import cycle
import json

# Read the config.json file
with open('config.json', 'r') as f:
    config = json.load(f)

# Retrieve the constants and pin configuration from the config
LABJACK_DEVICE_TYPE = getattr(ljm.constants, config['LABJACK_DEVICE_TYPE'])
LABJACK_CONNECTION_TYPE = getattr(ljm.constants, config['LABJACK_CONNECTION_TYPE'])
LABJACK_IDENTIFIER = config['LABJACK_IDENTIFIER']
pin_config = config['PIN_CONFIG']

def initialize_system():
    # Close the socket before attempting to reconnect
    try:
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).close()
    except:
        pass

    def delayed_initialization():
        # Initialize the LabJack handler
        handle = ljm.openS(str(LABJACK_DEVICE_TYPE), str(LABJACK_CONNECTION_TYPE), str(LABJACK_IDENTIFIER))
        labjack_handler = LabJackHandler(handle, LABJACK_DEVICE_TYPE, pin_config)

        # Initialize the Arduino handler
        arduino_handler = ArduinoHandler()

        # Set initial pin states
        initial_pin_states = pin_config.get("INITIAL_PIN_STATES", {})
        if initial_pin_states:
            labjack_handler.write_pin_states(initial_pin_states)

        # Initialize the control panel
        control_panel = ControlPanel(arduino_handler, labjack_handler, pin_config, labjack_handler.initial_pin_values)

        # Turn on the second LED when the Python GUI is loaded
        arduino_handler.turn_on_led2()

        # Destroy the loading window
        loading_window.destroy()

        # Start the Tkinter minCS loop
        control_panel.minCSloop()

    # Schedule the delayed_initialization function to run in a separate thread after 5 seconds (5000ms)
    threading.Timer(5, delayed_initialization).start()

def minCS():
    print("System Loading...")

    # Create the loading window and display it
    loading_window = LoadingWindow()
    loading_window.update_idletasks()

    # Initialize control_panel variable
    control_panel = None

    def run_minCS_code():
        nonlocal control_panel
        # Initialize the LabJack handler
        handle = ljm.openS(str(LABJACK_DEVICE_TYPE), str(LABJACK_CONNECTION_TYPE), str(LABJACK_IDENTIFIER))
        labjack_handler = LabJackHandler(handle, LABJACK_DEVICE_TYPE, pin_config)

        # Initialize the Arduino handler
        arduino_handler = ArduinoHandler()

        # Set initial pin states
        initial_pin_states = pin_config.get("INITIAL_PIN_STATES", {})
        if initial_pin_states:
            labjack_handler.write_pin_states(initial_pin_states)

        # Initialize the control panel
        control_panel = ControlPanel(arduino_handler, labjack_handler, pin_config, labjack_handler.initial_pin_values, loading_window)

        # Start the Tkinter minCS loop
        control_panel.minCSloop()

        # Wait for a short delay before closing the loading window
        time.sleep(0.1)

    # Create a new thread to run the minCS code
    minCS_thread = threading.Thread(target=run_minCS_code)
    minCS_thread.start()

    # Run the Tkinter minCS loop for the loading window
    loading_window.minCSloop()

    # Join the minCS_thread to prevent the minCS thread from ending
    minCS_thread.join()

if __name__ == "__minCS__":
    minCS()
