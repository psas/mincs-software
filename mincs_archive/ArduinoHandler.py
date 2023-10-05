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

    def turn_on_led1(self):
        self.serial_port.write(b'1')

    def turn_off_led1(self):
        self.serial_port.write(b'0')

    def turn_on_led2(self):
        self.serial_port.write(b'2')

    def turn_off_led2(self):
        self.serial_port.write(b'3')

    def turn_on_led3(self):
        self.serial_port.write(b'4')

    def turn_off_led3(self):
        self.serial_port.write(b'5')

    def turn_on_led4(self):
        self.serial_port.write(b'6')

    def turn_off_led4(self):
        self.serial_port.write(b'7')

    def send_lcd_message(self, message):
        # print(f"Sending LCD message: {message}")
        if len(message) > 32:
            message = message[:32]
        self.serial_port.write(f"LCD:{message}\n".encode())
        # print("Message sent to Arduino")

    def read_serial_data(self):
        if self.serial_port.in_waiting:
            serial_data = self.serial_port.readline().decode("utf-8").strip()
            return serial_data
        else:
            return None

    def map_inputs_to_commands(self):
        serial_data = self.read_serial_data()

        if serial_data is not None:
            commands = []
            if "Fire Button Pressed" in serial_data:
                commands.append('FIRE')
            if "Reset Button Pressed" in serial_data:
                commands.append('RESET')
            return commands
        else:
            return []

    def set_control_panel_reference(self, control_panel_reference):
        self.control_panel_reference = control_panel_reference

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