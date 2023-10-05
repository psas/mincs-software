import sys
import os
import time
import csv
import serial
from serial.tools import list_ports
import datetime
import threading
import tkinter as tk
from tkinter import ttk
import labjack.ljm as ljm  # import ljm module from labjack package
import pyfirmata

class ArduinoHandler:
    def __init__(self):
        print("Searching for Arduino...")
        self.serial_port = self.find_and_connect_arduino()

    def find_and_connect_arduino(self):
        print("Arduino Connected")
        arduino_ports = [
            p.device
            for p in list_ports.comports()
            if 'Arduino' in p.description
        ]
        if not arduino_ports:
            raise IOError("No Arduino found")
        if len(arduino_ports) > 1:
            print('Multiple Arduinos found - using the first one')

        ser = serial.Serial(arduino_ports[0], 9600)
        time.sleep(2)  # Give the connection some time to establish
        return ser

    def main():
        arduino_handler = ArduinoHandler()
        control_panel = ControlPanel(arduino_handler, labjack_handler, pin_config, initial_pin_values)
        arduino_handler.set_control_panel_reference(control_panel)

    def close(self):
        if hasattr(self, 'serial_port'):
            self.serial_port.close()
        elif hasattr(self, 'handle'):
            ljm.close(self.handle)
        else:
            raise ValueError('Cannot close object: no serial port or handle attribute found.')