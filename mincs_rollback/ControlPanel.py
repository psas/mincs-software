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
from ArduinoHandler import ArduinoHandler
from LabJackHandler import LabJackHandler
import matplotlib
matplotlib.use("Agg") # Set the matplotlib backend as Agg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import warnings
import pandas as pd
import numpy as np
from matplotlib.ticker import MaxNLocator
import json
import queue

# Filter out the specific warning
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.backends.backend_tkagg")

with open("config.json", "r") as file:
    config = json.load(file)

pin_config = config["PIN_CONFIG"]  # Read the PIN_CONFIG section from the config file

# Validation function for positive integers
def validate_integer_input(input_str):
    try:
        input_value = int(input_str)
        if input_value < 0:
            raise ValueError
        return True
    except ValueError:
        messagebox.showerror("Invalid Input", "PLEASE INPUT POSITIVE INTEGER ONLY")
        return False

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
        
        self.arduino_handler = arduino_handler
        self.labjack_handler = labjack_handler
        self.handle = labjack_handler.handle
        self.app_running = True
        self.destroying = False
        self.firing_sequence_executed = False  # Initialize the firing_sequence_executed attribute
        self.start_time = time.time()

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
        
        self.lock = threading.Lock() 

        # Create a flag to control the animation
        self.is_animating = True

        # create a thread for executing initial conditions
        self.initial_conditions = threading.Thread(target=self.initial_conditions_thread)
        self.initial_conditions.start()
        
        self.data_log_window = None

    def create_status_tab(self):
        print("Control Panel Loaded")
        self.status_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.status_tab, text="LabJack Status")

        # Leave Blank for Spacing Layout
        self.status_title_label = ttk.Label(self.controls_frame, text="", font=('Helvetica', 10, 'bold'))
        self.status_title_label.grid(row=2, column=0, columnspan=5, pady=10, sticky='w')

        # Add status bar to status tab
        self.status_bar = ttk.Frame(self.status_tab, relief='raised', borderwidth=10, height=30)
        self.status_bar.grid(row=3, column=0, columnspan=4, sticky='nsew')

        # Create a font color for the label
        self.status_label = ttk.Label(self.status_bar, text='INPUT DESIRED VOLTAGE AND PRESS ENTER', font=('Helvetica', 12, 'bold'), foreground='green', anchor='center')
        self.status_label.grid(row=0, column=0, columnspan=4, padx=(100, 0), pady=10, sticky='nsew')

        # Pin status
        self.pin_status_frames = {}
        self.pin_status_labels = {}
        for index, pin_type in enumerate(["FIO", "EIO", "CIO", "AIN"]):
            frame = ttk.LabelFrame(self.status_tab, text=f"{pin_type} Pins", padding=10)
            frame.grid(row=0, column=index, padx=10, pady=10, sticky='nsew')
            self.status_tab.columnconfigure(index, weight=1, minsize=145)

            labels = []
            for i in range(8):
                label = ttk.Label(frame, text=f"{pin_type}{i}: N/A")
                label.grid(row=i, column=0, sticky="w")
                labels.append(label)

            self.pin_status_frames[pin_type] = frame
            self.pin_status_labels[pin_type] = labels

        labjack_device_info = self.labjack_handler.get_device_info() if self.labjack_handler else {}
        labjack_device_info['labjack'] = bool(self.labjack_handler) # LabJack connection status
        labjack_device_info['arduino'] = bool(self.arduino_handler) # Arduino connection status
        self.update_device_info(labjack_device_info)

        # Create a frame for DAC settings
        dac_frame = ttk.Frame(self.status_tab, padding=5)
        dac_frame.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky='nsew')

        # Add Entry widgets for DAC0 and DAC1 voltages
        dac0_label = ttk.Label(dac_frame, text="DAC0 (V):")
        dac0_label.grid(row=0, column=0, padx=(0, 8), sticky='e')
        self.dac0_voltage_var = tk.StringVar(value="5.0")
        dac0_input = ttk.Entry(dac_frame, textvariable=self.dac0_voltage_var, width=9)
        dac0_input.grid(row=0, column=1, sticky='w')
        dac0_input.bind("<Return>", lambda event: (
            self.set_dac_voltages(),
            self.update_status_tab_status_bar("DAC0 VOLTAGE UPDATED", padx=185, foreground="green")
            if float(event.widget.get()) <= 10.0 else
            self.update_status_tab_status_bar("VOLTAGE INPUT TOO HIGH", padx=185, foreground="red")
            if float(event.widget.get()) > 10.0 else None,
            ljm.eWriteName(self.labjack_handler.handle, "DAC1", float(event.widget.get()))
        ))

        dac1_label = ttk.Label(dac_frame, text="DAC1 (V):")
        dac1_label.grid(row=1, column=0, padx=(0, 8), pady=(20, 98))
        self.dac1_voltage_var = tk.StringVar(value="5.0")
        dac1_input = ttk.Entry(dac_frame, textvariable=self.dac1_voltage_var, width=9)
        dac1_input.grid(row=1, column=1, pady=(20, 98))
        dac1_input.bind("<Return>", lambda event: (
            self.set_dac_voltages(),
            self.update_status_tab_status_bar("DAC1 VOLTAGE UPDATED", padx=185, foreground="green")
            if float(event.widget.get()) <= 10.0 else
            self.update_status_tab_status_bar("VOLTAGE INPUT TOO HIGH", padx=185, foreground="red")
            if float(event.widget.get()) > 10.0 else None,
            ljm.eWriteName(self.labjack_handler.handle, "DAC1", float(event.widget.get()))
        ))

        labjack_device_info = self.labjack_handler.get_device_info() if self.labjack_handler else {}
        labjack_device_info['labjack'] = bool(self.labjack_handler) # LabJack connection status
        labjack_device_info['arduino'] = bool(self.arduino_handler) # Arduino connection status
        self.update_device_info(labjack_device_info)

        self.update_gui()
        
    def set_dac_voltages(self):
        dac0_voltage = float(self.dac0_voltage_var.get())
        dac1_voltage = float(self.dac1_voltage_var.get())
        
        if dac0_voltage > 10.0 or dac1_voltage > 10.0:
            self.update_status_tab_status_bar("VOLTAGE INPUT TOO HIGH", padx=185, foreground="red")
        else:
            ljm.eWriteName(self.labjack_handler.handle, "DAC0", dac0_voltage)
            ljm.eWriteName(self.labjack_handler.handle, "DAC1", dac1_voltage)
            self.update_status_tab_status_bar("DAC VOLTAGES UPDATED", padx=185)

    def update_status_tab_status_bar(self, message="", padx=0, foreground="black"):
            self.status_label.config(text=message, foreground=foreground)
            self.status_label.grid_configure(padx=(padx, 0))
            self.status_label.update_idletasks()

    def create_device_info_tab(self):
        # Create the new tab
        device_info_tab = ttk.Frame(self.notebook)
        self.notebook.add(device_info_tab, text="Device Info")

        # Device info label frame
        device_info_frame = ttk.LabelFrame(device_info_tab, text="Device Information", padding=10)
        device_info_frame.pack(side='top', pady=10, padx=10, fill='both', expand=True)

        # Define the keys for the device info dictionary
        info_keys = [
            "labjack",
            "arduino",
            "device_type",
            "serial_number",
            "firmware_version",
            "hardware_version",
            "ip_address",
            "subnet",
            "gateway",
        ]

        # Add the labels to the device info frame
        self.device_info_labels = {}
        for index, key in enumerate(info_keys):
            label = ttk.Label(device_info_frame, text=f"{key.capitalize()}: N/A")
            label.grid(row=index, column=0, sticky='w', padx=10, pady=5)
            self.device_info_labels[key] = label

    def create_controls_tab(self):
        style = ttk.Style()

        # Set the desired theme
        style.theme_use('winnative')  # Replace 'clam' with the theme of your choice

        # Create a new style for the buttons
        style.configure('CPT.TButton', foreground='green', background='#90ee90', font=('Helvetica', 8, 'bold'), padding=(5, 5), width=10, focuscolor='#90ee90', highlightbackground='#90ee90', highlightthickness=10)
        style.configure('GB.TButton', foreground='green', background='#90ee90', font=('Helvetica', 8, 'bold'), padding=(5, 5), focuscolor='#90ee90', highlightbackground='#90ee90', highlightthickness=10)
        style.configure('Blue.TButton', foreground='blue', background='#2196F3', font=('Helvetica', 8, 'bold'), padding=(5, 5), width=10)
        style.configure('Red.TButton', foreground='red', background='#F44336', font=('Helvetica', 8, 'bold'), padding=(5, 5), width=10)
        style.map('CPT.TButton', background=[('active', '#66CD00'), ('disabled', '#C5E4C5'), ('pressed', '#8FBC8F')])
        style.map('GB.TButton', background=[('active', '#66CD00'), ('disabled', '#C5E4C5'), ('pressed', '#8FBC8F')])
        style.map('Red.TButton', background=[('active', '#FF0000'), ('disabled', '#FFC0CB'), ('pressed', '#FF6347')])

        self.controls_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.controls_tab, text="Control Panel")

        # Control Panel label frame
        controls_frame = ttk.LabelFrame(self.controls_tab, text=" Automatic System Control ", padding=10, relief='raised')
        controls_frame.pack(side='top', pady=10, padx=10, fill='both', expand=True)

        # Add status bar to controls tab
        self.status_bar = ttk.Frame(self.controls_tab, relief='raised', borderwidth=10, height=30)
        self.status_bar.pack(side='bottom', fill='x')

        # Create a font color for the label
        self.status_label = ttk.Label(self.status_bar, text='Welcome to minCS', font=('Helvetica', 12, 'bold'), foreground='black', anchor='center')
        self.status_label.pack(side='left', padx=10, pady=10, fill='both', expand=True)
        
        self.controls_frame = ttk.Frame(controls_frame, padding=10)
        self.controls_frame.pack()

        # Automatic Controls
        #self.controls_title_label = ttk.Label(self.controls_frame, text="Automatic System Control", font=('Helvetica', 10, 'bold'))
        #self.controls_title_label.grid(row=0, column=0, columnspan=5, pady=10, sticky='w')

        # Fire Button
        self.fire_button = ttk.Button(self.controls_frame, text="FIRE", command=self.gui_fire_button_pressed, style='CPT.TButton')
        self.fire_button.grid(row=1, column=0, padx=10, pady=10, columnspan=1, sticky="ns")

        # Reset Button
        self.reset_button = ttk.Button(self.controls_frame, text="RESET", command=self.restart_program, style='CPT.TButton')
        self.reset_button.grid(row=1, column=1, padx=10, pady=10, columnspan=1, sticky="ns")

        # Stop Button
        self.stop_button = ttk.Button(self.controls_frame, text='STOP', command=self.stop_system, style='Red.TButton')
        self.stop_button.grid(row=1, column=3, padx=10, pady=10, columnspan=1, sticky="ns")

        # Data Log Button
        self.log_data_button = ttk.Button(self.controls_frame, text="DATA LOG", command=self.toggle_data_logging, style='CPT.TButton')
        self.log_data_button.grid(row=1, column=2, padx=10, pady=10, columnspan=1, sticky="ns")
    
    def create_monitor_tab(self):
        self.monitor_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.monitor_tab, text="System Monitor")

        # Create a main frame to organize sensor frames and labels
        self.monitor_frame = ttk.LabelFrame(self.monitor_tab, text=" System Actuator and Sensor Monitoring ", padding=10, relief='raised')
        self.monitor_frame.pack(side='top', pady=10, padx=10, fill='both', expand=True)

        for i in range(3):
            self.monitor_frame.columnconfigure(i, weight=1)

        sensors = [
            "Pressure Sensor [1]", "Pressure Sensor [2]", "Pressure Sensor [3]", "Pressure Sensor [4]",
            "Temperature Sensor", "Load Sensor [1]", "Load Sensor [2]", "LOX Valve", "N2 Purge Valve",
            "N2 IPA Valve", "N2 LOX Valve", "IPA Valve", "Ignition"
        ]

        self.monitor_labels = {}
        self.indicators = {}

        for index, sensor in enumerate(sensors):
            if index < 4:
                col = 0
            elif 4 <= index < 7:
                col = 1
                index -= 4
            else:
                col = 2
                index -= 7

            row = index

            # Create a frame for each sensor
            sensor_frame = ttk.Frame(self.monitor_frame, borderwidth=1, relief="solid", padding=5)
            sensor_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            # Sensor label
            sensor_label = ttk.Label(sensor_frame, text=sensor, font=("Helvetica", 8, "bold"))
            sensor_label.pack(side=tk.TOP, pady=(0, 5))

            self.monitor_labels[sensor] = sensor_label

            # Indicator (red/green)
            indicator_frame = ttk.Frame(sensor_frame)
            indicator_frame.pack(side=tk.TOP)

            indicator = tk.Canvas(indicator_frame, width=10, height=10)
            indicator_light = indicator.create_rectangle(0, 0, 10, 10, fill="red")  # Create a rectangle and store its ID
            indicator.pack(side=tk.LEFT)

            indicator_label = ttk.Label(indicator_frame, text="OFF", font=("Helvetica", 8))
            indicator_label.pack(side=tk.LEFT)

            self.indicators[sensor] = (indicator, indicator_light, indicator_label)

        self.update_monitor_tab()

    def create_realtime_data_tab(self):
        style = ttk.Style()
        
        pressure_row = 0
        load_row = 0
        temperature_row = 0

        style.configure('CPT.TButton', foreground='green', background='#90ee90', font=('Helvetica', 8, 'bold'), padding=(5, 5), focuscolor='#90ee90', highlightbackground='#90ee90', highlightthickness=10)

        self.realtime_data_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.realtime_data_tab, text="Realtime Data")

        self.main_frame = ttk.LabelFrame(self.realtime_data_tab, text=" Realtime Data Monitoring System ", padding=10, relief='raised')
        self.main_frame.pack(side='top', pady=10, padx=10, fill='both', expand=True)

        self.realtime_canvas = tk.Canvas(self.main_frame, height=300)
        self.realtime_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.realtime_frame = ttk.Frame(self.realtime_canvas)
        self.realtime_frame.pack(fill=tk.BOTH, expand=True)

        self.realtime_canvas.create_window((0,0), window=self.realtime_frame, anchor=tk.NW)

        open_graph_button = ttk.Button(self.main_frame, text="Open minCS Graph", command=self.open_graph_window, style='GB.TButton')
        open_graph_button.place(relx=0.5, rely=1.0, anchor=tk.S, y=-10)  # Place the button in the center bottom with negative y-offset

        pressure_sensors = ["AIN0", "AIN1", "AIN2", "AIN3"]
        load_sensors = ["Load1", "Load2"]
        temperature_sensor = ["AIN4"]

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

        self.realtime_data_tab.after(1000, self.update_realtime_data_tab)

    def update_realtime_data_tab(self):
        for pin in range(0, 4):
            ain_value = self.labjack_handler.read_analog_input(pin)
            pressure = ain_value * 132.421875 - 62.5
            self.realtime_values[f"AIN{pin}"].config(text=f"{pressure:.2f} psi")

        # T-type thermocouple config
        ljm.eWriteName(self.handle, "AIN4_EF_INDEX", 24)
        ljm.eWriteName(self.handle, "AIN4_EF_CONFIG_A", 1)           # Output in degree C
        ljm.eWriteName(self.handle, "AIN4_EF_CONFIG_B", 60052)       # Using the internal temperature sensor for CJC
        ljm.eWriteName(self.handle, "AIN4_EF_CONFIG_D", 1)
        ljm.eWriteName(self.handle, "AIN4_EF_CONFIG_E", 0)
        ljm.eWriteName(self.handle, "AIN4_NEGATIVE_CH", 5)

        # Read the temperature from thermocouple
        temperature = ljm.eReadName(self.handle, "AIN4_EF_READ_A")
        self.realtime_values["AIN4"].config(text=f"{temperature:.2f} °C")

        # Set DAC0 and DAC1 to 4.1V
        ljm.eWriteName(self.handle, "DAC0", 4.1)
        ljm.eWriteName(self.handle, "DAC1", 4.1)

        # Set negative channels for AIN7 and AIN9
        ljm.eWriteName(self.handle, "AIN6_NEGATIVE_CH", 7)
        ljm.eWriteName(self.handle, "AIN8_NEGATIVE_CH", 9)

        # Take the tare weight
        tare_weight1 = self.labjack_handler.tare_weight1
        tare_weight2 = self.labjack_handler.tare_weight2

        # Read differential voltage from AIN6 (with reference to AIN10) and AIN8 (with reference to AIN11)
        voltage1 = self.labjack_handler.read_analog_input(6) - tare_weight1
        voltage2 = self.labjack_handler.read_analog_input(8) - tare_weight2

        excitation_voltage1 = ljm.eReadName(self.handle, "AIN10")
        excitation_voltage2 = ljm.eReadName(self.handle, "AIN11")

        # Calculate weight from voltage
        # Note: The weight value will depend on the exact load cell you're using
        # Here, we're assuming it's linear and the output is in pounds
        sensitivity = 0.02  # mV/V
        weight1 = (voltage1 / (sensitivity / 1000)) / excitation_voltage1
        weight2 = (voltage2 / (sensitivity / 1000)) / excitation_voltage2

        # Only display the weight if it's positive
        if weight1 > 0:
            self.realtime_values["Load1"].config(text=f"{weight1:.2f} lbs")
        else:
            self.realtime_values["Load1"].config(text="0.00 lbs")

        if weight2 > 0:
            self.realtime_values["Load2"].config(text=f"{weight2:.2f} lbs")
        else:
            self.realtime_values["Load2"].config(text="0.00 lbs")

        self.realtime_data_tab.after(100, self.update_realtime_data_tab) # 0.1 second update rate

    def open_graph_window(self):
        self.graph_window = tk.Toplevel()
        self.graph_window.wm_title("minCS Sensor Graphs")

        # Use a style with a darker background
        plt.style.use('dark_background')

        # Create 3 subplots
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, sharex=True)
        self.fig.subplots_adjust(hspace=0.5)
        self.fig.suptitle('minCS Sensor Data', fontsize=10, color='white', fontweight='bold')

        # Set titles and fonts
        self.ax1.set_title('Pressure', fontsize=9, color='white')
        self.ax2.set_title('Load', fontsize=9, color='white')
        self.ax3.set_title('Temperature', fontsize=9, color='white')

        # Create empty lines with different colors
        self.line1 = [self.ax1.plot([], [], color=color)[0] for color in ['red', 'green', 'magenta', 'yellow']]
        self.line2 = [self.ax2.plot([], [], color=color)[0] for color in ['red', 'green']]
        self.line3, = self.ax3.plot([], [], color='red')

        # Initialize data
        self.pressure_data = np.empty((4, 0))
        self.load_data = np.empty((2, 0))
        self.temperature_data = np.empty(0)

        # Set the canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_window)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Start the animation with save_count
        self.ani = self.fig.canvas.new_timer(interval=500)
        self.ani.add_callback(self.update_graph)
        self.ani.start()

    def open_graph_window(self):
        self.graph_window = tk.Toplevel(self.realtime_data_tab)
        self.graph_window.wm_title("minCS Sensor Graphs")

        # Use a style with a darker background
        plt.style.use('dark_background')

        # Create 3 subplots
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, sharex=True)
        self.fig.subplots_adjust(hspace=0.5)
        self.fig.suptitle('minCS Sensor Data', fontsize=10, color='white', fontweight='bold')

        # Set titles and fonts
        self.ax1.set_title('Pressure', fontsize=9, color='white')
        self.ax2.set_title('Load', fontsize=9, color='white')
        self.ax3.set_title('Temperature', fontsize=9, color='white')

        # Create empty lines with different colors
        self.line1 = [self.ax1.plot([], [], color=color)[0] for color in ['red', 'green', 'magenta', 'yellow']]
        self.line2 = [self.ax2.plot([], [], color=color)[0] for color in ['red', 'green']]
        self.line3, = self.ax3.plot([], [], color='red')

        # Initialize data
        self.pressure_data = [[] for _ in range(4)]
        self.load_data = [[] for _ in range(2)]
        self.temperature_data = []

        # Set the canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_window)  
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Start the window update thread
        window_thread = threading.Thread(target=self.update_window_thread)
        window_thread.start()

        # Start the animation with save_count
        self.ani = animation.FuncAnimation(self.fig, self.update_graph, interval=500, save_count=100) # 0.1 second update rate

    def update_window_thread(self):
        while self.is_animating:
            time.sleep(0.01)

    def update_graph(self, i):
        # Obtain the lock before updating the data
        with self.lock:
            # Append the new data to the lists
            for i in range(4):
                self.pressure_data[i].append(self.get_pressure_data(i))
            for i in range(2):
                self.load_data[i].append(self.get_load_data(i))
            self.temperature_data.append(self.get_temperature_data())

            # Calculate the moving averages with a window size of 5
            pressure_smooth = [np.convolve(data, np.ones(5) / 5, mode='valid') if len(data) >= 5 else [] for data in self.pressure_data]
            load_smooth = [np.convolve(data, np.ones(5) / 5, mode='valid') if len(data) >= 5 else [] for data in self.load_data]
            temperature_smooth = np.convolve(self.temperature_data, np.ones(5) / 5, mode='valid') if len(self.temperature_data) >= 5 else []

            # Set the new data
            for i, line in enumerate(self.line1):
                line.set_data(range(len(pressure_smooth[i])), pressure_smooth[i])
            for i, line in enumerate(self.line2):
                line.set_data(range(len(load_smooth[i])), load_smooth[i])
            self.line3.set_data(range(len(temperature_smooth)), temperature_smooth)

            # Adjust the plot limits
            self.ax1.set_xlim(0, max(1, len(self.pressure_data[0]) - 1))
            self.ax2.set_xlim(0, max(1, len(self.load_data[0]) - 1))
            self.ax3.set_xlim(0, max(1, len(self.temperature_data) - 1))
            
            max_pressure = max(max(data) if data else 1 for data in self.pressure_data)
            if max_pressure > self.ax1.get_ylim()[1]:
                self.ax1.set_ylim(0, max_pressure)

            max_load = max(max(data) if data else 1 for data in self.load_data)
            if max_load > self.ax2.get_ylim()[1]:
                self.ax2.set_ylim(0, max_load)

            max_temp = max(self.temperature_data) if self.temperature_data else 1
            if max_temp > self.ax3.get_ylim()[1]:
                self.ax3.set_ylim(0, max_temp)

            # Draw the new data
            self.fig.canvas.draw()

            # Update the x-axis to integer values
            self.ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
            self.ax2.xaxis.set_major_locator(MaxNLocator(integer=True))
            self.ax3.xaxis.set_major_locator(MaxNLocator(integer=True))

            # Set the color and width of the spines (borders)
            for ax in [self.ax1, self.ax2, self.ax3]:
                for spine in ax.spines.values():
                    spine.set_edgecolor('white')
                    spine.set_linewidth(2)

                # Set the color of the labels
                ax.xaxis.label.set_color('white')
                ax.yaxis.label.set_color('white')

                # Set the color of the tick labels
                ax.tick_params(colors='white')

                # Set the color and width of the grid
                ax.grid(color='white', linewidth=0.5)

            # Add a legend to each subplot
            self.ax1.legend(["Pressure Sensor [1]", "Pressure Sensor [2]", "Pressure Sensor [3]", "Pressure Sensor [4]"], loc="upper left", fontsize=8, frameon=True, shadow=True)
            self.ax2.legend(["Load Sensor [1]", "Load Sensor [2]"], loc="upper left", fontsize=8, frameon=True, shadow=True)
            self.ax3.legend(["Temperature Sensor"], loc="upper left", fontsize=8, frameon=True, shadow=True)

            # Set the axis labels
            self.ax1.set_ylabel('Pressure(psi)', fontsize=8, color='white')
            self.ax2.set_ylabel('Load (lbs)', fontsize=8, color='white')
            self.ax3.set_xlabel('Time (s)', fontsize=8, color='white')
            self.ax3.set_ylabel('Temperature (C°)', fontsize=8, color='white')

    def stop_animation(self):
        # Set the flag to stop the animation
        self.is_animating = False

        # Wait for the window update thread to finish
        window_thread.join()

    def get_pressure_data(self, i):
        # Pull value directly from the label
        pressure = float(self.realtime_values[f"AIN{i}"].cget("text").split()[0])
        return pressure

    def get_load_data(self, i):
        # Pull value directly from the label
        load = float(self.realtime_values[f"Load{i+1}"].cget("text").split()[0])
        return load

    def get_temperature_data(self):
        # Pull value directly from the label
        temperature = float(self.realtime_values["AIN4"].cget("text").split()[0])
        return temperature

    def create_test_tab(self):
        # Create the new tab
        test_tab = ttk.Frame(self.notebook)
        self.notebook.add(test_tab, text="Configuration")

        # Test label frame
        test_frame = ttk.LabelFrame(test_tab, text=" Sequence Duration Settings ", padding=10)
        test_frame.pack(side='top', pady=10, padx=10, fill='both', expand=True)

        self.style = ttk.Style()
        self.style.configure('Raised.TButton', relief='raised')

        # Firing Sequence duration input box
        firing_sequence_frame = ttk.Frame(test_frame)
        firing_sequence_frame.pack(side=tk.TOP, pady=(10, 0), padx=10, fill=tk.X)

        firing_sequence_label = ttk.Label(firing_sequence_frame, text="Firing Sequence Duration (sec):", font=("TkDefaultFont", 8, "bold"))
        firing_sequence_label.pack(side=tk.LEFT)

        self.firing_sequence_var = tk.StringVar(value="")
        firing_sequence_input = ttk.Entry(firing_sequence_frame, textvariable=self.firing_sequence_var)
        firing_sequence_input.pack(side=tk.RIGHT)
        firing_sequence_input.bind("<Return>", lambda event: (
            setattr(self, "firing_sequence_time", float(event.widget.get())),
            self.update_test_status_bar("FIRING SEQUENCE DURATION UPDATED"),
            self.update_button_states()
        ) if validate_integer_input(event.widget.get()) else None)

        # Ignition Sequence duration input box
        ignition_sequence_frame = ttk.Frame(test_frame)
        ignition_sequence_frame.pack(side=tk.TOP, pady=(10, 0), padx=10, fill=tk.X)

        ignition_sequence_label = ttk.Label(ignition_sequence_frame, text="Ignition Sequence Duration (sec):", font=("TkDefaultFont", 8, "bold"))
        ignition_sequence_label.pack(side=tk.LEFT)

        self.ignition_sequence_var = tk.StringVar(value="")
        ignition_sequence_input = ttk.Entry(ignition_sequence_frame, textvariable=self.ignition_sequence_var)
        ignition_sequence_input.pack(side=tk.RIGHT)
        ignition_sequence_input.bind("<Return>", lambda event: (
            setattr(self, "ignition_sequence_time", float(event.widget.get())),
            self.update_test_status_bar("IGNITION SEQUENCE DURATION UPDATED"),
            self.update_button_states()
        ) if validate_integer_input(event.widget.get()) else None)

        # Final Cooling Sequence duration input box
        final_cooling_frame = ttk.Frame(test_frame)
        final_cooling_frame.pack(side=tk.TOP, pady=(10, 0), padx=10, fill=tk.X)

        final_cooling_label = ttk.Label(final_cooling_frame, text="Purge Sequence Duration (sec):", font=("TkDefaultFont", 8, "bold"))
        final_cooling_label.pack(side=tk.LEFT)

        self.final_cooling_var = tk.StringVar(value="")
        final_cooling_sequence_input = ttk.Entry(final_cooling_frame, textvariable=self.final_cooling_var)
        final_cooling_sequence_input.pack(side=tk.RIGHT)
        final_cooling_sequence_input.bind("<Return>", lambda event: (
            setattr(self, "final_cooling_sequence_time", float(event.widget.get())),
            self.update_test_status_bar("PURGE SEQUENCE DURATION UPDATED"),
            self.update_button_states()
        ) if validate_integer_input(event.widget.get()) else None)

        # Cooldown Sequence duration input box
        cooldown_sequence_frame = ttk.Frame(test_frame)
        cooldown_sequence_frame.pack(side=tk.TOP, pady=(10, 0), padx=10, fill=tk.X)

        cooldown_sequence_label = ttk.Label(cooldown_sequence_frame, text="Shutdown Sequence Duration (sec):", font=("TkDefaultFont", 8, "bold"))
        cooldown_sequence_label.pack(side=tk.LEFT)

        self.cooldown_sequence_var = tk.StringVar(value="")
        cooldown_sequence_input = ttk.Entry(cooldown_sequence_frame, textvariable=self.cooldown_sequence_var)
        cooldown_sequence_input.pack(side=tk.RIGHT)
        cooldown_sequence_input.bind("<Return>", lambda event: (
            setattr(self, "cooldown_sequence_time", float(event.widget.get())),
            self.update_test_status_bar("SHUTDOWN SEQUENCE DURATION UPDATED"),
            self.update_button_states()
        ) if validate_integer_input(event.widget.get()) else None)

        # Reset button to clear all inputs
        reset_button = ttk.Button(test_frame, text="Reset Inputs", command=self.reset_test_inputs)
        reset_button.pack(side=tk.BOTTOM, pady=(10, 30), padx=10)

        # Add status bar to test tab
        test_status_bar = ttk.Frame(test_tab, relief='raised', borderwidth=10, height=30)
        test_status_bar.pack(side='bottom', fill='x')

        # Create a font color for the label
        self.test_status_label = ttk.Label(test_status_bar, text='PLEASE INPUT DESIRED DURATION AND PRESS ENTER', font=('Helvetica', 12, 'bold'), foreground='green', anchor='center')
        self.test_status_label.pack(side='left', padx=10, pady=10, fill='both', expand=True)

    def check_inputs(self):
        if (not self.firing_sequence_var.get() or not self.ignition_sequence_var.get() or
                not self.final_cooling_var.get() or not self.cooldown_sequence_var.get()):
            return False
        return True

    def update_button_states(self):
        all_values_set = self.check_inputs()

        if all_values_set:
            state = 'enable'
        else:
            state = 'disable'

        self.fire_button.configure(state=state)
        self.reset_button.configure(state=state)
        self.stop_button.configure(state=state)
        self.log_data_button.configure(state=state)

    def show_alert_window(self, message):
        alert_window = tk.Toplevel()
        alert_window.title("minCS Warning: Read Me")
        alert_window.resizable(False, False)  # Make the window non-resizable
        alert_window.attributes("-toolwindow", 1)  # Add a tool window attribute to make it look cleaner
        alert_window.configure(bg="#f0f0f0")  # Set a background color for a cleaner look

        # Center the window on the screen
        alert_window.update_idletasks()
        width = 300  # Set the initial width of the window
        height = 150  # Set the initial height of the window
        x = (alert_window.winfo_screenwidth() // 2) - (width // 2)
        y = (alert_window.winfo_screenheight() // 2) - (height // 2)
        alert_window.geometry(f"{width}x{height}+{x}+{y}")

        alert_label = tk.Label(alert_window, text=message, wraplength=250, bg="#f0f0f0", fg="red", justify="center", font=("TkDefaultFont", 10, "bold"))
        alert_label.pack(padx=20, pady=20)

        ok_button = tk.Button(alert_window, text="OK I UNDERSTAND", command=alert_window.destroy)
        ok_button.pack(pady=(0, 20))
    
    def update_test_status_bar(self, message=""):
        self.test_status_label.config(text=message)
        self.test_status_label.update_idletasks()

    def reset_test_inputs(self):
        self.firing_sequence_var.set("")
        self.ignition_sequence_var.set("")
        self.final_cooling_var.set("")
        self.cooldown_sequence_var.set("")
        self.update_test_status_bar("ALL USER INPUTS RESET")
        time.sleep(2)
        self.update_test_status_bar("PLEASE INPUT DESIRED DURATION AND PRESS ENTER")

    def toggle_data_logging(self):
        if self.data_logging:
            self.stop_data_logging()
            self.log_data_button.config(text="Start Data Logging")
        else:
            self.start_data_logging()
            self.log_data_button.config(text="Stop Data Logging")

    def update_gui(self):
        if not self.app_running:
            return
        device_info = self.labjack_handler.get_device_info()
        self.update_device_info(device_info)

        fio_status = self.labjack_handler.read_pin_status('FIO')
        self.update_pin_status('FIO', fio_status)

        eio_status = self.labjack_handler.read_pin_status('EIO')
        self.update_pin_status('EIO', eio_status)

        cio_status = self.labjack_handler.read_pin_status('CIO')
        self.update_pin_status('CIO', cio_status)

        ain_status = self.labjack_handler.read_pin_status('AIN')
        self.update_pin_status('AIN', ain_status)

        if self.app_running:
            self.id_update_gui = self.after(100, self.update_gui)
            self.id_update_idletasks = self.after_idle(self.update_idletasks)

    def main_loop(self):
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
            time.sleep(0.0001)
        
        # Restart the program if the reset button was pressed
        if self.resetting:
            print("Resetting system...")
            self.message_queue.put(("Resetting system...", "black", ("Helvetica", 12, "bold")))
            self.restart_program()
            time.sleep(2)  # Give some time for the application to close

    def process_queue(self):
        try:
            while not self.message_queue.empty():
                message = self.message_queue.get()

                if isinstance(message, tuple) and len(message) == 3:
                    msg_type, msg_data = message[0], message[1:]
                    if msg_type == "device_info":
                        self.update_device_info(text=msg_data, foreground=message[2] if len(message) > 2 else "black", font=message[3] if len(message) > 3 else ("Helvetica", 10))
                    elif msg_type == "pin_status":
                        self.update_pin_status(text=msg_data, foreground=message[2] if len(message) > 2 else "black", font=message[3] if len(message) > 3 else ("Helvetica", 10))
                    elif msg_type == "status":
                        self.status_label.config(text=msg_data, foreground=message[2] if len(message) > 2 else "black", font=message[3] if len(message) > 3 else ("Helvetica", 10))
                    elif msg_type == "welcome":
                        self.status_label.config(text=msg_data, foreground=message[2] if len(message) > 2 else "black", font=message[3] if len(message) > 3 else ("Helvetica", 10))
                    else:
                        self.status_label.config(text=msg_type)
                        # print(message)

            while not self.firing_sequence_queue.empty():
                self.firing_sequence_executed = True
                self.check_fire_button()

        except queue.Empty:
            pass

        self.after(100, self.process_queue)  

    def check_fire_button(self):
        # print("Check Fire Button")
        fire_button_pin = self.pin_config["FIRE_BUTTON"]
        fire_button_address = ljm.nameToAddress(fire_button_pin)[0]
        fire_button_state = ljm.eReadAddress(self.labjack_handler.handle, fire_button_address, ljm.constants.FLOAT32)

        if fire_button_state == 1 and not self.firing_sequence_executed:
            self.firing_sequence_executed = True
            self.execute_firing_sequence()  # Call the firing sequence function
            self.fire_button.config(state=tk.DISABLED)
            self.after(10000, lambda: self.fire_button.config(state=tk.NORMAL))

    def gui_fire_button_pressed(self):
        print("GUI Fire Button Pressed")
        self.status_label.config(text="", foreground="black", font=("Helvetica", 12, "bold"))
        confirmation = messagebox.askokcancel("Confirm Firing", "Are you sure you want to execute the firing sequence?")
        if confirmation and not self.firing_sequence_executed:
            self.firing_sequence_executed = True
            self.execute_firing_sequence()
            self.fire_button.config(state=tk.DISABLED)
            self.after(10000, lambda: self.fire_button.config(state=tk.NORMAL))

    def set_valve(self, valve_name, state):
        print("Set Values")
        # Set the valve state and update the actuator_addresses dictionary
        actuators = self.pin_config["ACTUATORS"]
        actuator_addresses = {k: ljm.nameToAddress(v)[0] for k, v in actuators.items()}
        ljm.eWriteAddress(self.labjack_handler.handle, actuator_addresses[valve_name], ljm.constants.FLOAT32, state)

        # Update the indicators dictionary with the new valve state
        indicator_canvas, _, indicator_label = self.indicators[valve_name]
        self.indicators[valve_name] = (indicator_canvas, state, indicator_label)

    def set_fio_pins(self, state_dict):
        print("Set FIO Pins")
        # Set the state of specific FIO pins
        for pin_name, state in state_dict.items():
            pin_address = ljm.nameToAddress(pin_name)[0]
            ljm.eWriteAddress(self.labjack_handler.handle, pin_address, ljm.constants.FLOAT32, state)

    def execute_firing_sequence(self):
        print("Execute Firing Sequence")
        if self.firing_sequence_running:
            return
        self.firing_sequence_running = True
        threading.Thread(target=self.firing_sequence_thread).start()

    def firing_sequence_thread(self):
        print("Firing Sequence Thread")
        self.message_queue.put(("EXECUTING FIRING SEQUENCE...", "black", ("Helvetica", 12, "bold")))

        # Store the current state of the FIO pins
        lox_valve_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["LOX Valve"])
        n2_ipa_valve_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 IPA Valve"])
        n2_lox_valve_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 LOX Valve"])
        ipa_valve_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["IPA Valve"])
        n2_purge_valve_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 Purge Valve"])
        ignition_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["Ignition"])

        # Set the state of specific FIO pins during fire
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["LOX Valve"], 0)
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 IPA Valve"], 0)
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 LOX Valve"], 1)
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["IPA Valve"], 0)
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 Purge Valve"], 1)
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["Ignition"], 0)

        # Update the indicators based on the FIO pin states
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["LOX Valve"][3:]), 0)
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["N2 IPA Valve"][3:]), 0)
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["N2 LOX Valve"][3:]), 1)
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["IPA Valve"][3:]), 0)
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["N2 Purge Valve"][3:]), 1)
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["Ignition"][3:]), 0)
        
        self.message_queue.put(("ENGINE FIRING", "black", ("Helvetica", 12, "bold")))

        # Wait for x seconds without letting the pins change state
        start_time = time.time()
        while time.time() - start_time < self.firing_sequence_time:
            # print("Ignition ON")
            if time.time() - start_time < self.ignition_sequence_time:
                ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["Ignition"], 0)
            else:
                ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["Ignition"], 1)
                # print("IGNITION OFF")
            # Write the pins again to make sure their state doesn't change
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["LOX Valve"], 0)
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 IPA Valve"], 0)
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 LOX Valve"], 1)
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["IPA Valve"], 0)
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 Purge Valve"], 1)
            time.sleep(0.0001)

        # Call the shutdown function
        time.sleep(0.1)
        self.cooling_thread()
        self.firing_sequence_running = False
    
    def cooling_thread(self):
        print("Cooling Thread")
        time.sleep(0.1)
        self.message_queue.put(("ENGINE COOLING...", "black", ("Helvetica", 12, "bold")))
        
        # Store the current state of the FIO pins
        lox_valve_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["LOX Valve"])
        n2_ipa_valve_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 IPA Valve"])
        n2_lox_valve_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 LOX Valve"])
        ipa_valve_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["IPA Valve"])
        n2_purge_valve_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 Purge Valve"])
        ignition_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["Ignition"])
        
        # Set the state of specific FIO pins during shutdown
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["LOX Valve"], 1)
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 IPA Valve"], 1)
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 LOX Valve"], 1)
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["IPA Valve"], 1)
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 Purge Valve"], 1)
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["Ignition"], 1)

        # Update the indicators based on the FIO pin states
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["LOX Valve"][3:]), 1)
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["N2 IPA Valve"][3:]), 1)
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["N2 LOX Valve"][3:]), 1)
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["IPA Valve"][3:]), 1)
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["N2 Purge Valve"][3:]), 1)
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["Ignition"][3:]), 1)

        start_time = time.time()
        while time.time() - start_time < self.final_cooling_sequence_time:
            # Write the pins again to make sure their state doesn't change
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["LOX Valve"], 1)
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 IPA Valve"], 1)
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 LOX Valve"], 1)
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["IPA Valve"], 1)
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 Purge Valve"], 1)
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["Ignition"], 1)
            time.sleep(0.0001)          

        time.sleep(0.1)
        self.shutdown_thread()     
    
    def shutdown_thread(self):
        print("Shutdown Thread")
        time.sleep(0.1)
        self.message_queue.put(("ENGINE STOPPED", "black", ("Helvetica", 12, "bold")))

        # Store the current state of the FIO pins
        lox_valve_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["LOX Valve"])
        n2_ipa_valve_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 IPA Valve"])
        n2_lox_valve_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 LOX Valve"])
        ipa_valve_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["IPA Valve"])
        n2_purge_valve_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 Purge Valve"])
        ignition_state = ljm.eReadName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["Ignition"])
        
        # Set the state of specific FIO pins during shutdown
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["LOX Valve"], 1)
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 IPA Valve"], 1)
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 LOX Valve"], 1)
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["IPA Valve"], 1)
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 Purge Valve"], 0)
        ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["Ignition"], 1)

        # Update the indicators based on the FIO pin states
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["LOX Valve"][3:]), 1)
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["N2 IPA Valve"][3:]), 1)
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["N2 LOX Valve"][3:]), 1)
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["IPA Valve"][3:]), 1)
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["N2 Purge Valve"][3:]), 0)
        self.update_control_indicator("FIO", int(self.pin_config["ACTUATORS"]["Ignition"][3:]), 1)

        start_time = time.time()
        while time.time() - start_time < self.cooldown_sequence_time:
            # Write the pins again to make sure their state doesn't change
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["LOX Valve"], 1)
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 IPA Valve"], 1)
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 LOX Valve"], 1)
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["IPA Valve"], 1)
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 Purge Valve"], 0)
            ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["Ignition"], 1)
            time.sleep(0.0001)         
        
        self.message_queue.put(("minCS Ready to Fire", "black", ("Helvetica", 12, "bold")))
        
        # Reset the firing_sequence_executed flag
        self.firing_sequence_executed = False
        self.firing_sequence_running = False
        self.pin_states_set = False
           
        # Restore the initial pin states
        self.initial_conditions_thread()          

    def restore_initial_pin_states(self):
        with self.pin_lock:
            if not self.firing_sequence_executed:
                ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["LOX Valve"], 1)
                ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 IPA Valve"], 1)
                ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 LOX Valve"], 1)
                ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["IPA Valve"], 1)
                ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 Purge Valve"], 0)
                ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["Ignition"], 1)
            else:
                ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["LOX Valve"], 1)
                ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 IPA Valve"], 1)
                ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 LOX Valve"], 1)
                ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["IPA Valve"], 1)
                ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["N2 Purge Valve"], 0)
                ljm.eWriteName(self.labjack_handler.handle, self.pin_config["ACTUATORS"]["Ignition"], 1)
   
    def initial_conditions_thread(self):
        print("Initial Conditions Set")

        while not self.firing_sequence_running:
            # Maintain the initial pin states until the firing sequence sequence starts
            self.restore_initial_pin_states()

        all_values_set = self.check_inputs()

        if all_values_set:
            state = 'normal'
        else:
            state = 'disabled'

        self.fire_button.configure(state=state)
        self.reset_button.configure(state=state)
        self.stop_button.configure(state=state)
        self.log_data_button.configure(state=state)

    def update_device_info(self, device_info):
        for key, value in device_info.items():
            if key == 'labjack':
                if value:
                    self.device_info_labels['labjack'].config(text=f"LabJack: Connected")
                else:
                    self.device_info_labels['labjack'].config(text=f"LabJack: Not Connected")
            elif key == 'arduino':
                if value:
                    self.device_info_labels['arduino'].config(text=f"Arduino: Connected")
                else:
                    self.device_info_labels['arduino'].config(text=f"Arduino: Not Connected")
            elif key == 'device_type':
                self.device_info_labels['device_type'].config(text=f"Device Type: {value}")
            elif key == 'serial_number':
                self.device_info_labels['serial_number'].config(text=f"Serial Number: {value}")
            elif key == 'firmware_version':
                self.device_info_labels['firmware_version'].config(text=f"Firmware Version: {value}")
            elif key == 'hardware_version':
                self.device_info_labels['hardware_version'].config(text=f"Hardware Version: {value}")
            elif key == 'ip_address':
                if value == 0:
                    value = "N/A"
                self.device_info_labels['ip_address'].config(text=f"IP Address: {value}")
            elif key == 'subnet':
                self.device_info_labels['subnet'].config(text=f"Subnet: {value}")
            elif key == 'gateway':
                self.device_info_labels['gateway'].config(text=f"Gateway: {value}")

    def update_pin_status(self, pin_type, pin_status):
        for index, status in enumerate(pin_status):
            if pin_type == "FIO":
                if index < len(self.pin_config["ACTUATORS"]):
                    sensor_name = list(self.pin_config["ACTUATORS"].keys())[index]
                    if sensor_name in ["LOX Valve", "N2 IPA Valve", "N2 LOX Valve", "IPA Valve", "Ignition"]:
                        status_text = "ON" if status == 0 else "OFF"
                    elif sensor_name in ["N2 Purge Valve"]:
                        status_text = "OFF" if status == 1 else "ON"
                elif index in [6, 7]:
                    status_text = "OFF" if status == 0 else "ON"
                else:
                    status_text = f"{status:.2f}"
            elif pin_type == "AIN" and index in range(len(self.pin_config["SENSORS"])):
                status_text = "OFF" if status == 0 else "ON"
            elif pin_type in ["EIO", "CIO"]:
                status_text = "OFF" if status == 1 else "ON"
            else:
                status_text = f"{status:.2f}"

            self.pin_status_labels[pin_type][index].config(text=f"{pin_type}{index}: {status_text}")

    def update_monitor_tab(self):
        actuator_statuses = self.labjack_handler.get_actuator_statuses()
        sensor_statuses = self.labjack_handler.get_sensor_statuses()

        for actuator, status in actuator_statuses.items():
            self.update_indicator(actuator, status)

        for sensor, status in sensor_statuses.items():
            self.update_indicator(sensor, status)

        self.monitor_frame.after(1000, self.update_monitor_tab)

    def update_control_indicator(self, pin_type, pin_number, status):
        # print(f"pin_type: {pin_type}, pin_number: {pin_number}")

        if pin_type == "FIO":
            index = pin_number
        elif pin_type == "EIO":
            index = 8 + pin_number
        elif pin_type == "CIO":
            index = 16 + pin_number
        else:
            return

        if index >= len(self.indicators):
            return

        # print(f"index: {index}")
        # print(f"self.indicators: {self.indicators}")

        # Update the color of the indicator based on the status
        if status == 0:
            color = "red"
        else:
            color = "green"

        if index in self.indicators:
            self.indicators[index][0].itemconfig(self.indicators[index][0], fill=color)
            self.indicators[index][2].config(text="ON" if status == 0 else "OFF")

    def update_indicator(self, sensor, status):
        if sensor in self.pin_config["ACTUATORS"]:
            if sensor in ["LOX Valve", "N2 IPA Valve", "N2 LOX Valve", "IPA Valve"]:
                status_text = "ON" if status == 0 else "OFF"
                color = "green" if status == 0 else "red"
            elif sensor in ["N2 Purge Valve"]:
                status_text = "OFF" if status == 0 else "ON"
                color = "red" if status == 0 else "green"
            elif sensor == "Ignition":
                status_text = "OFF" if status > 3 else "ON"
                color = "red" if status > 3 else "green"
        else:  # Assuming it is a sensor
            status_text = "OFF" if status == 1 else "ON"
            color = "red" if status == 1 else "green"

        # print(f"Updating indicator for {sensor}: status={status}, status_text={status_text}, color={color}")  # Debugging print statement

        self.monitor_labels[sensor].config(text=f"{sensor}")
        indicator, indicator_light, indicator_label = self.indicators[sensor]
        indicator.itemconfig(indicator_light, fill=color)
        indicator_label.config(text=status_text)  # Update the text of the indicator_label

    def close(self):
        ljm.close(self.labjack_handler)

    def restart_program(self):
        confirm = messagebox.askyesno("Reset System", "Are you sure you want to reset the system?")
        if confirm:
            self.message_queue.put(("Resetting system...", "black", ("Helvetica", 12, "bold")))
            time.sleep(2)
            self.stop_system()
            time.sleep(2)  # Give some time for the application to close

            # Close the socket before attempting to reconnect
            try:
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).close()
            except:
                pass

            os.execl(sys.executable, sys.executable, *sys.argv)

    def restart_program(self):
            confirm = messagebox.askyesno("Reset Confirmation", "Are you sure you want to reset the system?")
            if confirm:
                self.message_queue.put(("Resetting system...", "black", ("Helvetica", 12, "bold")))
                time.sleep(2)
                self.stop_system()
                time.sleep(2)  # Give some time for the application to close

                # Close the socket before attempting to reconnect
                try:
                    socket.socket(socket.AF_INET, socket.SOCK_STREAM).close()
                except:
                    pass

                os.execl(sys.executable, sys.executable, *sys.argv)

    def shutdown(self):
        print("System Shutdown")
        
        # Reset the firing_sequence_executed flag
        self.firing_sequence_executed = False
        self.firing_sequence_running = False
           
        # Restore the initial pin states
        self.initial_conditions_thread()          

    def stop_system(self):
        self.status_label.config(text="ENGINE STOPPED", foreground="black", font=("Helvetica", 12, "bold"))
        print("Stop button pressed. Initiating shutdown...")
        threading.Thread(target=self.shutdown).start()
        self.update_pin_status('FIO', self.labjack_handler.read_pin_status('FIO'))

    def stop(self): # Only use if you want to close program after the stop button is pressed
        print("minCS Program Terminated")
        self.destroy()

    def start_data_logging(self):
        self.data_logging = True

        # Generate a unique filename based on the current timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        os.makedirs("data_logs", exist_ok=True)  # Create the folder if it doesn't exist
        self.filename = os.path.join(os.getcwd(), "data_logs", f"minTS_data_log_{timestamp}.csv")

        # Create a new CSV file and write the header
        with open(self.filename, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Timestamp", "Load 1", "Load 2", "Pressure 1", "Pressure 2", "Pressure 3", "Pressure 4", "Temperature"])

        # Create a new window to display "DATA LOG RUNNING..." and a "STOP" button
        self.logging_window = tk.Toplevel(self.controls_tab)
        self.logging_window.title("minCS Data Log")
        self.logging_window.geometry("300x100")
        self.logging_window.resizable(False, False)
        self.logging_window.protocol("WM_DELETE_WINDOW", self.stop_data_logging)

        logging_label = ttk.Label(self.logging_window, text="DATA LOG RUNNING...", foreground="red", font=('Helvetica', 10, 'bold'))
        logging_label.pack(padx=10, pady=10)

        logging_stop_button = ttk.Button(self.logging_window, text="STOP", command=self.stop_data_logging)
        logging_stop_button.pack(padx=10, pady=10)

        # Start logging data
        self.logging_thread = threading.Thread(target=self.log_data, args=(self.filename,))
        self.logging_thread.start()
   
    def log_data(self, filename):
        # Record the start time
        start_time = time.time()
        elapsed_time = 0.0

        while self.data_logging:
            # Read the pressure, load cell, and temperature
            pressures = [self.get_pressure_data(i) for i in range(4)]
            load1 = self.get_load_data(0)
            load2 = self.get_load_data(1)
            temperature = self.get_temperature_data()

            # Generate the current time string
            current_time = "{:.2f}".format(elapsed_time)

            # Log data to CSV file
            with open(filename, 'a', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow([current_time, load1, load2, *pressures, temperature])

            # Wait for 0.1 seconds before logging the next set of data
            time.sleep(0.1)

            # Increment elapsed_time by 0.1 seconds
            elapsed_time += 0.1

    def toggle_data_logging(self):
        if self.data_logging:
            confirm = messagebox.askyesno("Stop Data Logging", "Are you sure you want to stop data logging?")
            if confirm:
                self.stop_data_logging()
                self.log_data_button.config(text="DATA LOG")

                # Change status label to indicate data logging has stopped
                self.status_label.config(text="DATA LOG STOPPED", foreground="black", font=("Helvetica", 10, "bold"))

                # Destroy the data logging window if it exists
                if self.data_log_window is not None:
                    self.data_log_window.destroy()
                    self.data_log_window = None

        else:
            confirm = messagebox.askyesno("Start Data Logging", "Are you sure you want to start data logging?")
            if confirm:
                self.start_data_logging()
                self.log_data_button.config(text="DATA LOGGING")

                # Change status label to indicate data logging has started
                self.status_label.config(text="DATA LOGGING STARTED", foreground="black", font=("Helvetica", 12, "bold"))

    def stop_data_logging(self):
        self.data_logging = False

        # Close the logging window
        if hasattr(self, 'logging_window'):
            self.logging_window.destroy()

if __name__ == "__main__":
    # Initialize the Arduino handler
    arduino_handler = ArduinoHandler(config["ARDUINO_PORT"])

    # Initialize the LabJack handler
    handle, device_type = ljm.openS(config["LABJACK_DEVICE_TYPE"], config["LABJACK_CONNECTION_TYPE"], config["LABJACK_IDENTIFIER"])
    labjack_handler = LabJackHandler(handle, device_type, config["PIN_CONFIG"])

    # Initialize the Control Panel and start the main loop
    control_panel = ControlPanel(arduino_handler, labjack_handler, pin_config)
    control_panel.main_loop()
