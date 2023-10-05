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
from tkinter import ttk, Tk, StringVar, N, E, S, W, Button, Toplevel
import tkinter.messagebox as messagebox
from labjack import ljm
import labjack.ljm as ljm
import threading
import pyfirmata
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ArduinoHandler import ArduinoHandler
from LabJackHandler import LabJackHandler
import json
import queue

with open("config.json", "r") as file:
    config = json.load(file)

pin_config = config["PIN_CONFIG"]  # Read the PIN_CONFIG section from the config file

class ControlPanel(tk.Tk):
    def __init__(self, arduino_handler, labjack_handler, pin_config, initial_pin_values, loading_window):
        print("Control Panel Loading...")
        super().__init__()
        
        self.pin_config = pin_config  # Save the pin_config parameter as an instance variable
        
        # Read and save the initial pin states
        self.pin_config = pin_config
        self.initial_pin_states = {}
        valid_pin_types = ["FIO", "EIO", "CIO", "AIN"]
        for pin_type in self.pin_config.keys():
            if pin_type in valid_pin_types:
                self.initial_pin_states[pin_type] = self.labjack_handler.read_pin_status(pin_type)
        
        self.root = tk.Tk()
        self.arduino_handler = arduino_handler
        self.labjack_handler = labjack_handler
        self.handle = labjack_handler.handle
        self.app_running = True
        self.destroying = False
        self.firing_sequence_executed = False  # Initialize the firing_sequence_executed attribute
        self.start_time = time.time()

        self.manual_firing_sequence_running = False
        self.manual_firing_sequence_executed = False
        
        self.manual_ignition_sequence_running = False
        self.manual_ignition_sequence_executed = False
        
        self.manual_purge_sequence_running = False
        self.manual_purge_sequence_executed = False
        
        self.manual_cooling_sequence_running = False
        self.manual_cooling_sequence_executed = False
        
        self.manual_controls_executed = False

        self.message_queue = queue.Queue()
        self.firing_sequence_queue = queue.Queue()
        self.firing_sequence_running = False
        self.switch_tab_enabled = True
        
        self.title("minCS ")
        self.resizable(width=False, height=False)
        self.geometry("600x480")  # set the size of the window

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill=tk.BOTH)
        
        # Add this line to initialize the pin states dictionary
        #self.pin_states = {pin: 0 for pin in self.pin_config["ACTUATORS"]}

        # Add this line to start a thread for continuously writing pin states
        #self.write_pin_states_thread = threading.Thread(target=self.write_pin_states, daemon=True)
        #self.write_pin_states_thread.start()

        self.progress_bars = {}    
        self.realtime_values = {}
        self.value_labels = {}

        self.create_controls_tab()
        self.create_test_tab()
        #self.create_switch_tab()        
        self.create_monitor_tab()
        self.create_realtime_data_tab()
        self.create_device_info_tab()
        self.create_status_tab() 

        self.update_button_states()        
        self.show_alert_window("PLEASE ENTER YOUR DESIRED TIME BEFORE RUNNING THE SYSTEM")
        
        self.process_queue()  # Call process_queue after creating the tabs
        
        self.update_gui()

        self.id_update_gui = None
        self.id_update_idletasks = None
        self.check_fire_button()
        self.pin_lock = threading.Lock()

        # create a thread for executing initial conditions
        self.initial_conditions = threading.Thread(target=self.initial_conditions_thread)
        self.initial_conditions.start()
        
        self.data_log_window = None

    def create_realtime_data_tab(self):
        pressure_row = 0
        load_row = 0
        temperature_row = 0

        self.realtime_data_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.realtime_data_tab, text="Realtime Data")

        self.realtime_canvas = tk.Canvas(self.realtime_data_tab, height=300)
        self.realtime_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.realtime_frame = ttk.Frame(self.realtime_canvas)
        self.realtime_frame.pack(fill=tk.BOTH, expand=True)

        self.realtime_canvas.create_window((0,0), window=self.realtime_frame, anchor=tk.NW)

        pressure_sensors = ["AIN0", "AIN1", "AIN2", "AIN3"]
        load_sensors = ["Load1", "Load2"]
        temperature_sensor = ["AIN4"]
        
        graph_button = ttk.Button(self.realtime_data_tab, text="Open Graph", command=self.create_graph_window)
        graph_button.pack(side=tk.BOTTOM)
        
        for i in range(3):
            self.realtime_frame.columnconfigure(i, weight=1, uniform="col")
            self.realtime_frame.columnconfigure(i, minsize=100)
            
            self.realtime_labels = {
                "Pressure Sensor [1]": "AIN0",
                "Pressure Sensor [2]": "AIN1",
                "Pressure Sensor [3]": "AIN2",
                "Pressure Sensor [4]": "AIN3",
                "Temperature Sensor": "AIN4",
                "Load Sensor [1]": "Load1",
                "Load Sensor [2]": "Load2",
            }

        for label, pin in self.realtime_labels.items():
            if pin in pressure_sensors:
                row = pressure_row
                col = 0
                pressure_row += 1
            elif pin in load_sensors:
                row = load_row
                col = 1
                load_row += 1
            elif pin in temperature_sensor:
                row = temperature_row
                col = 2
                temperature_row += 1

            # Create a frame for each level
            level_frame = ttk.Frame(self.realtime_frame, borderwidth=1, relief="solid", padding=5)
            level_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            # Level label
            level_label = ttk.Label(level_frame, text=label, font=("Helvetica", 8, "bold"))
            level_label.pack(side=tk.TOP, pady=(0, 5))

            # Level value
            level_value = ttk.Label(level_frame, text="0.0", font=("Helvetica", 8))
            level_value.pack(side=tk.TOP, pady=(0, 5))

            self.realtime_labels[label] = level_label
            self.realtime_values[pin] = level_value

    def create_graph_window(self):
        self.graph_window = tk.Toplevel(self.root)
        self.graph_window.title("Realtime Data Graphs")

        self.figure = plt.Figure(figsize=(5, 5), dpi=100)
        self.pressure_plot = self.figure.add_subplot(311)
        self.load_plot = self.figure.add_subplot(312)
        self.temp_plot = self.figure.add_subplot(313)

        self.pressure_plot.set_title("Pressure Reading")
        self.load_plot.set_title("Load Cells Reading")
        self.temp_plot.set_title("Temperature Reading")

        self.canvas = FigureCanvasTkAgg(self.figure, self.graph_window)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def update_realtime_data_tab(self):
        for pin in range(0, 4):
            ain_value = self.labjack_handler.read_analog_input(pin)
            pressure = ain_value * 132.421875 - 62.5
            self.realtime_values[f"AIN{pin}"].config(text=f"{pressure:.2f} psi")

        # Read the temperature using the get_temperature() method
        temperature = self.labjack_handler.get_temperature()
        self.realtime_values["Temperature Sensor"].config(text=f"{temperature:.2f} °C")

        # Set DAC0 and DAC1 to 4.1V
        ljm.eWriteName(self.labjack_handler.handle, "DAC0", 4.1)
        ljm.eWriteName(self.labjack_handler.handle, "DAC1", 4.1)

        # Set negative channels for AIN7 and AIN9
        ljm.eWriteName(self.labjack_handler.handle, "AIN6_NEGATIVE_CH", 7)
        ljm.eWriteName(self.labjack_handler.handle, "AIN8_NEGATIVE_CH", 9)

        # Take the tare weight
        tare_weight1 = self.labjack_handler.tare_weight1
        tare_weight2 = self.labjack_handler.tare_weight2

        # Read differential voltage from AIN6 (with reference to AIN10) and AIN8 (with reference to AIN11)
        voltage1 = self.labjack_handler.read_analog_input(6) - tare_weight1
        voltage2 = self.labjack_handler.read_analog_input(8) - tare_weight2

        excitation_voltage1 = ljm.eReadName(self.labjack_handler.handle, "AIN10")
        excitation_voltage2 = ljm.eReadName(self.labjack_handler.handle, "AIN11")

        # Calculate weight from voltage
        # Note: The weight value will depend on the exact load cell you're using
        # Here, we're assuming it's linear and the output is in pounds
        sensitivity = 0.02  # mV/V
        weight1 = (voltage1 / (sensitivity / 1000)) / excitation_voltage1
        weight2 = (voltage2 / (sensitivity / 1000)) / excitation_voltage2

        # Only display the weight if it's positive
        if weight1 > 0:
            self.realtime_values["Load Sensor [1]"].config(text=f"{weight1:.2f} lbs")
        else:
            self.realtime_values["Load Sensor [1]"].config(text="0.00 lbs")

        if weight2 > 0:
            self.realtime_values["Load Sensor [2]"].config(text=f"{weight2:.2f} lbs")
        else:
            self.realtime_values["Load Sensor [2]"].config(text="0.00 lbs")

        # Pressure plot
        self.pressure_plot.clear()
        self.pressure_plot.plot([f"AIN{pin}" for pin in range(4)], [self.labjack_handler.read_analog_input(pin) for pin in range(4)])
        self.pressure_plot.set_title("Pressure Reading")

        # Load cells plot
        self.load_plot.clear()
        self.load_plot.plot(["Load Sensor [1]", "Load Sensor [2]"], [weight1, weight2])
        self.load_plot.set_title("Load Cells Reading")

        # Temperature plot
        self.temp_plot.clear()
        self.temp_plot.plot(["Temperature Sensor"], [self.labjack_handler.get_temperature()])
        self.temp_plot.set_title("Temperature Reading")

        self.canvas.draw()

        # Update plots only if the graph window has been created
        if hasattr(self, 'graph_window'):
            # Pressure plot
            self.pressure_plot.clear()
            self.pressure_plot.plot([f"AIN{pin}" for pin in range(4)], [self.labjack_handler.read_analog_input(pin) for pin in range(4)])
            self.pressure_plot.set_title("Pressure Reading")

            # Load cells plot
            self.load_plot.clear()
            self.load_plot.plot(["Load Sensor [1]", "Load Sensor [2]"], [weight1, weight2])
            self.load_plot.set_title("Load Cells Reading")

            # Temperature plot
            self.temp_plot.clear()
            self.temp_plot.plot(["Temperature Sensor"], [self.labjack_handler.get_temperature()])
            self.temp_plot.set_title("Temperature Reading")

            self.canvas.draw()

        self.realtime_data_tab.after(1000, self.update_realtime_data_tab)

    def main_loop(self):
        self.root.mainloop()
        # Set the initial pin states
        initial_pin_states = self.config["PIN_CONFIG"]["INITIAL_PIN_STATES"]
        self.labjack_handler.write_pin_states(initial_pin_states)

        # Update the GUI with the initial pin states
        self.update_gui()

        while self.running:
            # Read inputs from the Arduino
            power_switch, fire_button, reset_button = self.arduino_handler.read_inputs()

            # Control the solenoids based on the inputs
            if fire_button:
                self.labjack_handler.control_solenoids('FIRE', self.config["PIN_CONFIG"]["FIRE_BUTTON"])
            elif reset_button:
                self.labjack_handler.control_solenoids('RESET', self.config["PIN_CONFIG"]["RESET_BUTTON"])

            # Read data from the sensors
            pressure_values, temperature_value, load_values = self.labjack_handler.read_sensors(self.config["PIN_CONFIG"]["SENSORS"])

            # Update the GUI with the latest information
            self.update_gui(pressure_values, temperature_value, load_values)

            # Handle the events and refresh the GUI
            self.update_idletasks()
            self.update()

            # Add a delay to avoid high CPU usage
            time.sleep(0.000001)
        
        # Restart the program if the reset button was pressed
        if self.resetting:
            print("Resetting system...")
            self.message_queue.put(("Resetting system...", "black", ("Helvetica", 12, "bold")))
            self.restart_program()
            time.sleep(5)  # Give some time for the application to close

if __name__ == "__main__":
    # Initialize the Arduino handler
    arduino_handler = ArduinoHandler(config["ARDUINO_PORT"])

    # Initialize the LabJack handler
    handle, device_type = ljm.openS(config["LABJACK_DEVICE_TYPE"], config["LABJACK_CONNECTION_TYPE"], config["LABJACK_IDENTIFIER"])
    labjack_handler = LabJackHandler(handle, device_type, config["PIN_CONFIG"])

    # Initialize the Control Panel and start the main loop
    control_panel = ControlPanel(arduino_handler, labjack_handler, pin_config)
    control_panel.main_loop()