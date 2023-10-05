import sys
import os
import time
import csv
import datetime
import threading
import tkinter as tk
from tkinter import ttk
import labjack.ljm as ljm  # import ljm module from labjack package
import pyfirmata
import json
import numpy as np

with open("config.json", "r") as file:
    config = json.load(file)
# print(config)

class LabJackHandler:
    def __init__(self, handle, device_type, pin_config):
        print("LabJack Connected")
        self.handle = handle
        self.device_type = device_type
        self.pin_config = pin_config
        self.initial_pin_values = self.read_pin_values()
        assert "FIRE_BUTTON" in self.pin_config
        self.tare_weight1 = ljm.eReadName(self.handle, "AIN6")
        self.tare_weight2 = ljm.eReadName(self.handle, "AIN8")

    def write_pin_states(self, pin_states):
        fio_states = pin_states["FIO"]
        for i, state in enumerate(fio_states):
            ljm.eWriteName(self.handle, f"FIO{i}", state)

    def read_pin_values(self):
        valid_pin_types = ["FIO", "EIO", "CIO", "AIN"]
        pin_values = {}
        for pin_type in self.pin_config.keys():
            if pin_type in valid_pin_types:
                pin_values[pin_type] = self.read_pin_status(pin_type)

        return pin_values

    def read_pin_status(self, pin_type):
        # Read the status of FIO, EIO, CIO, and AIN pins
        pin_status = []

        if pin_type in ["FIO", "EIO", "CIO"]:
            num_pins = 8
        elif pin_type == "AIN":
            num_pins = 4
        else:
            raise ValueError("Invalid pin type specified.")

        for pin in range(num_pins):
            try:
                pin_status.append(ljm.eReadName(self.handle, f"{pin_type}{pin}"))
            except ljm.LJMError:
                break

        return pin_status

    def get_device_info(self):
        device_info = {
            "device_type": self.device_type,
            "serial_number": int(round(ljm.eReadName(self.handle, "SERIAL_NUMBER"))),
            "firmware_version": round(ljm.eReadName(self.handle, "FIRMWARE_VERSION"), 2),
            "hardware_version": round(ljm.eReadName(self.handle, "HARDWARE_VERSION"), 2),
            "ip_address": ljm.eReadName(self.handle, "ETHERNET_IP"),
            "subnet": int(round(ljm.eReadName(self.handle, "ETHERNET_SUBNET"))),
            "gateway": int(round(ljm.eReadName(self.handle, "ETHERNET_GATEWAY"))),
        }
        return device_info

    def get_actuator_statuses(self):
        actuator_statuses = {
            "LOX Valve": ljm.eReadName(self.handle, "FIO6"),
            "N2 Purge Valve": ljm.eReadName(self.handle, "FIO7"),
            "N2 IPA Valve": ljm.eReadName(self.handle, "MIO0"),
            "N2 LOX Valve": ljm.eReadName(self.handle, "MIO1"),
            "IPA Valve": ljm.eReadName(self.handle, "MIO2"),
            "Ignition": ljm.eReadName(self.handle, "AIN12"),
        }
        return actuator_statuses

    def get_sensor_statuses(self):
        # print("Reading sensor values...")
        sensor_statuses = {
            "Pressure Sensor [1]": ljm.eReadName(self.handle, "AIN0") * 132.421875 - 62.5,
            "Pressure Sensor [2]": ljm.eReadName(self.handle, "AIN1") * 132.421875 - 62.5,
            "Pressure Sensor [3]": ljm.eReadName(self.handle, "AIN2") * 132.421875 - 62.5,
            "Pressure Sensor [4]": ljm.eReadName(self.handle, "AIN3") * 132.421875 - 62.5,
            "Temperature Sensor": ljm.eReadName(self.handle, "AIN4"),
            "Load Sensor [1]": ljm.eReadName(self.handle, "DAC0"),
            "Load Sensor [2]": ljm.eReadName(self.handle, "DAC1"),
        }
        #for key, value in sensor_statuses.items():
            #print(key + ": " + str(value))
        return sensor_statuses

    def read_analog_input(self, ain_pin):
        if 0 <= ain_pin <= 14:
            return ljm.eReadName(self.handle, f"AIN{ain_pin}")
        else:
            raise ValueError("Invalid AIN pin number. It must be between 0 and 14.")

    def close(self):
        if hasattr(self, 'board'):
            self.board.exit()
        elif hasattr(self, 'handle'):
            ljm.close(self.handle)
        else:
            raise ValueError('Cannot close object: no board or handle attribute found.')

        if 'labjack' not in self.device_info_labels:
            print("Error: device_info_labels dictionary doesn't have 'labjack' key")
            return

