import threading
from pathlib import Path
import labjack.ljm as ljm
import tkinter as tk
from tkinter import Tk, ttk, StringVar, Canvas, Entry, Text, Button, PhotoImage, messagebox
from network import Network
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor
import queue
import time
from time import sleep
import datetime
import os
import csv
import numpy as np
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.ndimage import gaussian_filter1d
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
matplotlib.use("Agg")

network = Network()
data_lock = Lock()

# Initialize empty lists
pressure_data_1 = []
pressure_data_2 = []
pressure_data_3 = []
pressure_data_4 = []
temperature_data = []
load_data_1 = []
load_data_2 = []
time_data = []

pressure_data_raw_1 = []
pressure_data_raw_2 = []
pressure_data_raw_3 = []
pressure_data_raw_4 = []
temperature_data_raw = []
load_data_raw_1 = []
load_data_raw_2 = []

time_counter = 0

entry_widgets = {}
message_queue = queue.Queue()
device_info = network.get_device_info()
print("minCS is Connected")

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "minCS Assets"

icon_path = ASSETS_PATH / "minTS_logo.ico"

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

window = Tk()
window.geometry("1315x1000")
window.configure(bg = "#F0F0F0")
window.title("minCS")
#window.iconbitmap(icon_path)

style = ttk.Style(window)
style.theme_use("default")

fire_duration = None
ignition_duration = None 
purge_duration = None
cooldown_duration = None

correct_password = "test"
is_authenticated = False

data_logging = False
logging_thread = None
filename = None

canvas = Canvas(
    window,
    bg = "#F0F0F0",
    height = 1000,
    width = 1315,
    bd = 0,
    highlightthickness = 0,
    relief = "raised"
)

# ACTUATOR ENTRIES
#-------------------------------------------------------------------------------------------------------------------

entry_31 = Text(
    bd=0,
    font=("Roboto", 8, "bold"),
    fg="white",
    bg="red",
    borderwidth=1,
    highlightthickness=1
)
entry_31.place(
    x=1122.0,
    y=620,
    width=145.0,
    height=20.0
)

entry_32 = Text(
    bd=0,
    font=("Roboto", 8, "bold"),
    fg="white",
    bg="red",
    borderwidth=1,
    highlightthickness=1
)
entry_32.place(
    x=1122.0,
    y=684.0,
    width=145.0,
    height=20.0
)

entry_33 = Text(
    bd=0,
    font=("Roboto", 8, "bold"),
    fg="white",
    bg="red",
    borderwidth=1,
    highlightthickness=1
)
entry_33.place(
    x=1122.0,
    y=748.0,
    width=145.0,
    height=20.0
)

entry_34 = Text(
    bd=0,
    font=("Roboto", 8, "bold"),
    fg="white",
    bg="red",
    borderwidth=1,
    highlightthickness=1
)
entry_34.place(
    x=1122.0,
    y=812.0,
    width=145.0,
    height=20.0
)

entry_35 = Text(
    bd=0,
    font=("Roboto", 8, "bold"),
    fg="white",
    bg="red",
    borderwidth=1,
    highlightthickness=1
)
entry_35.place(
    x=1122.0,
    y=876.0,
    width=145.0,
    height=20.0
)

entry_36 = Text(
    bd=0,
    font=("Roboto", 8, "bold"),
    fg="white",
    bg="red",    
    borderwidth=1,
    highlightthickness=1
)
entry_36.place(
    x=1122.0,
    y=940.0,
    width=145.0,
    height=20.0
)

# REALTIME ENTRIES
#-------------------------------------------------------------------------------------------------------------------

entry_9 = Text(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    font=("Roboto", 8),
    borderwidth=1,
    highlightthickness=1
)
entry_9.place(
    x=474.0,
    y=173.0,
    width=145.0,
    height=20.0
)

entry_10 = Text(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    font=("Roboto", 8),
    borderwidth=1,
    highlightthickness=1
)
entry_10.place(
    x=474.0,
    y=236.0,
    width=145.0,
    height=20.0
)

entry_11 = Text(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    font=("Roboto", 8),
    borderwidth=1,
    highlightthickness=1
)
entry_11.place(
    x=474.0,
    y=299.0,
    width=145.0,
    height=20.0
)

entry_12 = Text(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    font=("Roboto", 8),
    borderwidth=1,
    highlightthickness=1
)
entry_12.place(
    x=474.0,
    y=364.0,
    width=145.0,
    height=20.0
)

entry_13 = Text(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    font=("Roboto", 8),
    borderwidth=1,
    highlightthickness=1
)
entry_13.place(
    x=474.0,
    y=428.0,
    width=145.0,
    height=20.0
)

entry_14 = Text(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    font=("Roboto", 8),
    borderwidth=1,
    highlightthickness=1
)
entry_14.place(
    x=474.0,
    y=492.0,
    width=145.0,
    height=20.0
)

entry_15 = Text(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    font=("Roboto", 8),
    borderwidth=1,
    highlightthickness=1
)
entry_15.place(
    x=474.0,
    y=556.0,
    width=145.0,
    height=20.0
)

# UPDATE STATUS
#-------------------------------------------------------------------------------------------------------------------

connection_status = False

def update_status():
    global network, connection_status
    while True:
        try:
            network.refresh_connection()
            device_info = network.get_device_info()

            if device_info['connection'] == 'NO CONNECTION':
                #print("No connection detected.")
                connection_status = False
                for entry in [entry_31, entry_32, entry_33, entry_34, entry_35, entry_36]:
                    pass
            else:
                if network.is_new_connection:
                    print("New connection detected. Setting initial pin states.")
                    connection_status = True
                    network.set_initial_pin_states()
                    network.is_new_connection = False
             
            message_queue.put(device_info)       
        
        except ljm.LJMError as e:
            #print("Connection Failed!")
            connection_status = False
        time.sleep(0.1)

prev_serial_number = None
has_been_disconnected = False

def check_for_reconnection():
    global prev_serial_number, has_been_disconnected
    serial_number = None

    try:
        serial_number = ljm.eReadName(network.handle, "SERIAL_NUMBER")
    except ljm.LJMError:
        has_been_disconnected = True

    if has_been_disconnected and serial_number is not None:
        print("LabJack Has Been Reconnected.")
        set_initial_pin_states(network.handle, entry_widgets)
        has_been_disconnected = False

reset_format = [entry_9, entry_10, entry_11, entry_12, entry_13, entry_14, entry_15]
ign_format = [entry_36]

# Function to set initial pin states
def set_initial_pin_states(network_handle, entry_widgets):
    if network_handle is None:
        print("No LabJack Connection Detected. Skipping Labjack Initialization.")        
        return

    initial_pin_states = {
        "FIO0": 1,
        "FIO1": 0,
        "FIO2": 1,
        "FIO3": 1,
        "FIO4": 1,
        "FIO5": 1
    }

    initial_mapping = {
        "FIO0": entry_32,
        "FIO1": entry_33,
        "FIO2": entry_34,
        "FIO3": entry_35,
        "FIO4": entry_31,
        "FIO5": entry_36
    }

    for pin, state in initial_pin_states.items():
        ljm.eWriteName(network_handle, pin, state)
     
        entry = initial_mapping[pin]
        entry.delete("1.0", "end")
 
        for e in reset_format:
            e.config(bg="white", fg="black", font=("Roboto", 8))
 
        if state == 1:
            entry.config(font=("Roboto", 8, "bold"))
            entry.insert("end", "   CLOSED")
            entry.config(bg="red")
        else:
            entry.config(font=("Roboto", 8, "bold"))
            entry.insert("end", "   CLOSED")
            entry.config(bg="red")       

        for e in ign_format:
            e.config(bg="red", fg="white", font=("Roboto", 8, "bold"))
            e.delete("1.0", "end")
            e.insert("1.0", "   OFF")

initial_pin_states = {
    "FIO0": 1,
    "FIO1": 0,
    "FIO2": 1,
    "FIO3": 1,
    "FIO4": 1,
    "FIO5": 1
}

def reconnection_thread():
    while True:
        check_for_reconnection()
        time.sleep(0.1)

global is_testing
is_testing = False

global is_aborted
is_aborted = False

# REALTIME DATA TRACKING
#-------------------------------------------------------------------------------------------------------------------

image_image_8 = PhotoImage(
    file=relative_to_assets("image_8.png"))
image_8 = canvas.create_image(
    609.0,
    56.0,
    image=image_image_8
)

image_image_7 = PhotoImage(
    file=relative_to_assets("image_7.png"))
image_7 = canvas.create_image(
    546.0,
    803.0,
    image=image_image_7
)

canvas.place(x = 0, y = 0)
image_image_1 = PhotoImage(
    file=relative_to_assets("image_1.png"))
image_1 = canvas.create_image(
    114.0,
    357.0,
    image=image_image_1
)

image_image_2 = PhotoImage(
    file=relative_to_assets("image_2.png"))
image_2 = canvas.create_image(
    330.0,
    357.0,
    image=image_image_2
)

image_image_3 = PhotoImage(
    file=relative_to_assets("image_3.png"))
image_3 = canvas.create_image(
    546.0,
    357.0,
    image=image_image_3
)

image_image_4 = PhotoImage(
    file=relative_to_assets("image_4.png"))
image_4 = canvas.create_image(
    762.0,
    357.0,
    image=image_image_4
)

image_image_5 = PhotoImage(
    file=relative_to_assets("image_5.png"))
image_5 = canvas.create_image(
    978.0,
    357.0,
    image=image_image_5
)

image_image_6 = PhotoImage(
    file=relative_to_assets("image_6.png"))
image_6 = canvas.create_image(
    1194.0,
    549.0,
    image=image_image_6
)

def clear_entries():
    global fire_duration, ignition_duration, purge_duration, cooldown_duration
    fire_duration = ""
    ignition_duration = ""
    purge_duration = ""
    cooldown_duration = ""
    
    for entry in [entry_3, entry_4, entry_5, entry_6, entry_7, entry_8]:
        if isinstance(entry, tk.Entry):
            entry.delete(0, tk.END)
        elif isinstance(entry, tk.Text):
            entry.delete("1.0", tk.END)

button_image_3 = PhotoImage(file=relative_to_assets("button_3.png"))
button_3 = Button(
    window,
    image=button_image_3,
    text="CLEAR INPUTS             ",
    compound="center",
    font=("Roboto", 8, "bold"),
    borderwidth=2,
    highlightthickness=2,
    command=clear_entries  # Link to the function
)
button_3.pack()
button_3.place(x=258.0, y=556.0, width=145.0, height=20.0)

# TESTING CONTROLS
#-------------------------------------------------------------------------------------------------------------------

is_stages_running = False
fire_duration = 0
ignition_duration = 0
purge_duration = 0
cooldown_duration = 0

def reset_authenticate(buttons, button_texts, entries, network_handle, channels, initial_pin_states):
    global is_testing, is_stages_running
    is_testing = False
    for button, button_text, entry, channel in zip(buttons, button_texts, entries, channels):
        initial_state = initial_pin_states[channel]
        
        button.config(state="disabled", fg="white", bg="red", text="   OFF")
        button_10.config(state=tk.NORMAL)
        button_text.set("   OFF")
        
        insert_into_entries()
        
        if network_handle is not None:
            ljm.eWriteName(network_handle, channel, initial_state)

def authenticate(event):
    global is_authenticated, is_stages_running
    
    if is_stages_running:
        messagebox.showinfo('Warning', 'Testing Mode can\'t be used during Firing Mode.')
        return
    entered_password = entry_16.get()
    buttons = [button_4, button_5, button_6, button_7, button_8, button_9]
    button_texts = [button_text_4, button_text_5, button_text_6, button_text_7, button_text_8, button_text_9]
    entries = [entry_33, entry_36, entry_35, entry_34, entry_31, entry_32]
    channels = ["FIO1", "FIO5", "FIO3", "FIO2", "FIO4", "FIO0"]
    
    initial_pin_states = {"FIO1": 0, "FIO5": 1, "FIO3": 1, "FIO2": 1, "FIO4": 1, "FIO0": 1}
    if entered_password == correct_password:
        is_authenticated = True
        for button in buttons:
            button.config(state="normal")
            button_10.config(state=tk.DISABLED)
    else:
        is_authenticated = False
        reset_authenticate(buttons, button_texts, entries, network.handle, channels, initial_pin_states)

# Entry for authentication
entry_16 = Entry(bd=0, bg="#FFFFFF", fg="#000716", borderwidth=1, highlightthickness=1)
entry_16.place(x=690.0, y=173.0, width=145.0, height=20.0)
entry_16.bind('<Return>', authenticate)

def testing_toggle(button, button_text, entry, network_handle, channel, status_text):
    global is_testing
    entry.delete("1.0", tk.END)  # Clear existing text first
    if button_text.get() == "   OFF":
        is_testing = True
        button.config(fg="white", bg="green", text="   ON")
        button_text.set("   ON")
        if network_handle is not None:
            ljm.eWriteName(network_handle, channel, 0)
        entry.config(bg="green")
        entry.insert(tk.END, status_text[0])
    else:
        button.config(fg="white", bg="red", text="   OFF")
        button_text.set("   OFF")
        if network_handle is not None:
            ljm.eWriteName(network_handle, channel, 1)
        entry.config(bg="red")
        entry.insert(tk.END, status_text[1])

def toggle_button_4():
    testing_toggle(button_4, button_text_4, entry_36, network.handle, "FIO5", ["   ON", "   OFF"]) # IGNITION

def toggle_button_5():
    testing_toggle(button_5, button_text_5, entry_33, network.handle, "FIO1", ["   OPEN", "   CLOSED"]) # PURGE

def toggle_button_6():
    testing_toggle(button_6, button_text_6, entry_35, network.handle, "FIO3", ["   OPEN", "   CLOSED"]) # N2 LOX

def toggle_button_7():
    testing_toggle(button_7, button_text_7, entry_34, network.handle, "FIO2", ["   OPEN", "   CLOSED"]) # N2 IPA

def toggle_button_8():
    testing_toggle(button_8, button_text_8, entry_31, network.handle, "FIO4", ["   OPEN", "   CLOSED"]) # IPA

def toggle_button_9():
    testing_toggle(button_9, button_text_9, entry_32, network.handle, "FIO0", ["   OPEN", "   CLOSED"]) # LOX

button_text_4 = StringVar()
button_text_4.set("   OFF")

button_4 = Button(
    window,
    textvariable=button_text_4,
    compound="center",
    font=("Roboto", 8, "bold"),
    fg="white",
    bg="red",
    borderwidth=2,
    highlightthickness=2,
    anchor='w',  # Left justify the text
    command=toggle_button_4,
    state="disabled"
)
button_4.pack()

button_4.place(
    x=690.0,
    y=556.0,
    width=145.0,
    height=20.0
)

button_text_5 = StringVar()
button_text_5.set("   OFF")

button_5 = Button(
    window,
    textvariable=button_text_5,
    compound="center",
    font=("Roboto", 8, "bold"),
    fg="white",
    bg="red",
    borderwidth=2,
    highlightthickness=2,
    anchor='w',  # Left justify the text
    state="disabled",
    command=toggle_button_5
)
button_5.pack()

button_5.place(
    x=690.0,
    y=364.0,
    width=145.0,
    height=20.0
)

button_text_6 = StringVar()
button_text_6.set("   OFF")

button_6 = Button(
    window,
    textvariable=button_text_6,
    compound="center",
    font=("Roboto", 8, "bold"),
    fg="white",
    bg="red",
    borderwidth=2,
    highlightthickness=2,
    anchor='w',  # Left justify the text
    command=toggle_button_6,
    state="disabled"
)
button_6.pack()

button_6.place(
    x=690.0,
    y=492.0,
    width=145.0,
    height=20.0
)

button_text_7 = StringVar()
button_text_7.set("   OFF")

button_7 = Button(
    window,
    textvariable=button_text_7,
    compound="center",
    font=("Roboto", 8, "bold"),
    fg="white",
    bg="red",
    borderwidth=2,
    highlightthickness=2,
    anchor='w',  # Left justify the text
    command=toggle_button_7,
    state="disabled"
)
button_7.pack()

button_7.place(
    x=690.0,
    y=428.0,
    width=145.0,
    height=20.0
)

button_text_8 = StringVar()
button_text_8.set("   OFF")

button_8 = Button(
    window,
    textvariable=button_text_8,
    compound="center",
    font=("Roboto", 8, "bold"),
    fg="white",
    bg="red",
    borderwidth=2,
    highlightthickness=2,
    anchor='w',  # Left justify the text
    command=toggle_button_8,
    state="disabled"
)
button_8.pack()

button_8.place(
    x=690.0,
    y=236.0,
    width=145.0,
    height=20.0
)

button_text_9 = StringVar()
button_text_9.set("   OFF")

button_9 = Button(
    window,
    textvariable=button_text_9,
    compound="center",
    font=("Roboto", 8, "bold"),
    fg="white",
    bg="red",
    borderwidth=2,
    highlightthickness=2,
    anchor='w',
    command=toggle_button_9,
    state="disabled"
)
button_9.pack()

button_9.place(
    x=690.0,
    y=299.0,
    width=145.0,
    height=20.0
)

# LAUNCH CONTROLS
#-------------------------------------------------------------------------------------------------------------------

entry_1 = Text(
    bd=0,
    bg="yellow",
    fg="black",
    font=("Roboto", 8, "bold"),
    borderwidth=1,
    highlightthickness=1
)

entry_1.place(
    x=42.0,
    y=492.0,
    width=145.0,
    height=20.0
)
entry_1.insert("end", "   WAITING...")

entry_2 = Text(
    bd=0,
    bg="yellow",
    fg="black",
    font=("Roboto", 8, "bold"),
    borderwidth=1,
    highlightthickness=1
)
entry_2.place(
    x=42.0,
    y=557.0,
    width=145.0,
    height=20.0
)
entry_2.insert("end", "   WAITING...")

def fire_confirmation():
    user_response = messagebox.askokcancel("Confirmation", "Are you sure you want to fire the system?")
    
    if user_response:  # If the user clicks "OK"
        print("button_10 clicked")
        return True
    else:
        return False

button_image_10 = PhotoImage(file=relative_to_assets("button_10.png"))
button_10 = Button(
    window,
    image=button_image_10,
    text="FIRE",
    compound="center",
    font=("Roboto", 10, "bold"),
    borderwidth=2,
    highlightthickness=2,
    command=lambda: print("System Armed")
)
button_10.pack()

button_10.place(
    x=41.0,
    y=174.0,
    width=148.0,
    height=49.0
)

def abort_sequence():
    global is_aborted
    is_aborted = True
    entry_1.config(bg="red")
    entry_1.delete(1.0, "end")
    entry_1.insert("end", "   ABORTED...")
    print("System Abort!!")

button_image_11 = PhotoImage(file=relative_to_assets("button_11.png"))
button_11 = Button(
    window,
    image=button_image_11,
    text="ABORT",
    compound="center",
    font=("Roboto", 10, "bold"),
    fg="red",
    borderwidth=2,
    highlightthickness=2,
    command=abort_sequence
)
button_11.pack()

button_11.place(
    x=41.0,
    y=238.0,
    width=148.0,
    height=49.0
)

# CONFIGURATION
#-------------------------------------------------------------------------------------------------------------------

def validate_duration(value):
    # Check if the value is a positive integer
    try:
        val = int(value)
    except ValueError:
        return False
    
    # Check if value is over 10 seconds
    if val > 10:
        response = messagebox.askyesno("Critical Warning", "The duration you entered is over 10 seconds. Are you sure you want to override?")
        if not response:  # If user chooses 'No'
            return False
    
    # Check for valid range
    if val < 0 or val > 20:
        return False

    return True

def validate_voltage(value):
    # Check if the value is a positive integer
    try:
        val = int(value)
    except ValueError:
        return False
    
    # Check for valid range
    if val < 0 or val > 5:
        return False

    return True

def capture_fire_duration(event):
    global fire_duration
    fire_duration = entry_3.get()  # Get the value from entry_3
    if validate_duration(fire_duration):
        print(f"Captured Fire Duration (s): {fire_duration}")
    else:
        entry_3.delete(0, tk.END)

entry_3 = Entry(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    borderwidth=1,
    font=("Roboto", 8),
    highlightthickness=1
)
entry_3.place(
    x=258.0,
    y=173.0,
    width=145.0,
    height=20.0
)

entry_3.bind('<Return>', capture_fire_duration)

def capture_ignition_duration(event):
    global ignition_duration, fire_duration
    
    # Check if fire_duration is set
    try:
        int(fire_duration)
    except (ValueError, NameError):
        messagebox.showwarning("Duration Error", "Ignition duration cannot be greater than fire duration.\nPlease enter fire duration first.")
        entry_4.delete(0, tk.END)
        return
    
    ignition_duration = entry_4.get()
    try:
        if int(ignition_duration) > int(fire_duration):
            messagebox.showwarning("Duration Error", "Ignition duration cannot be greater than fire duration.\nPlease enter fire duration first.")
            entry_4.delete(0, tk.END)
            return
    except ValueError:
        pass

    if validate_duration(ignition_duration):
        print(f"Captured Ignition Duration (s): {ignition_duration}")
    else:
        entry_4.delete(0, tk.END)

entry_4 = Entry(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    borderwidth=1,
    font=("Roboto", 8),
    highlightthickness=1
)
entry_4.place(
    x=258.0,
    y=236.0,
    width=145.0,
    height=20.0
)
entry_4.bind('<Return>', capture_ignition_duration)

def capture_purge_duration(event):
    global purge_duration
    purge_duration = entry_5.get()
    if validate_duration(purge_duration):
        purge_duration = int(purge_duration)
        print(f"Captured Purge Duration (s): {purge_duration}")
    else:
        entry_5.delete(0, tk.END)

entry_5 = Entry(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    borderwidth=1,
    font=("Roboto", 8),
    highlightthickness=1
)
entry_5.place(
    x=258.0,
    y=299.0,
    width=145.0,
    height=20.0
)
entry_5.bind('<Return>', capture_purge_duration)

def capture_cooldown_duration(event):
    global cooldown_duration
    cooldown_duration = entry_6.get()
    if validate_duration(cooldown_duration):
        cooldown_duration = int(cooldown_duration)
        print(f"Captured Cooldown Duration (s): {cooldown_duration}")
    else:
        entry_6.delete(0, tk.END)

entry_6 = Entry(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    borderwidth=1,
    font=("Roboto", 8),
    highlightthickness=1
)
entry_6.place(
    x=258.0,
    y=364.0,
    width=145.0,
    height=20.0
)
entry_6.bind('<Return>', capture_cooldown_duration)

def capture_voltage_DAC0(event):
    voltage_DAC0_str = entry_7.get()
    if validate_voltage(voltage_DAC0_str):
        voltage_DAC0 = float(voltage_DAC0_str)
        try:
            ljm.eWriteName(network.handle, "DAC0", voltage_DAC0)
            print(f"Written DAC0 voltage: {voltage_DAC0}")
        except ljm.LJMError:
            print("Error writing to DAC0")
    else:
        entry_7.delete(0, tk.END)

entry_7 = Entry(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    borderwidth=1,
    font=("Roboto", 8),
    highlightthickness=1
)
entry_7.place(x=258.0, y=428.0, width=145.0, height=20.0)
entry_7.bind('<Return>', capture_voltage_DAC0)

def capture_voltage_DAC1(event):
    voltage_DAC1_str = entry_8.get()
    if validate_voltage(voltage_DAC1_str):
        voltage_DAC1 = float(voltage_DAC1_str)
        try:
            ljm.eWriteName(network.handle, "DAC1", voltage_DAC1)
            print(f"Written DAC1 voltage: {voltage_DAC1}")
        except ljm.LJMError:
            print("Error writing to DAC1")
    else:
        entry_8.delete(0, tk.END)

entry_8 = Entry(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    borderwidth=1,
    font=("Roboto", 8),
    highlightthickness=1
)
entry_8.place(x=258.0, y=492.0, width=145.0, height=20.0)
entry_8.bind('<Return>', capture_voltage_DAC1)

entry_7.config(state="disabled")
entry_8.config(state="disabled")

#def add_space(event):
    #event.widget.delete(0, "end")
    #event.widget.insert(0, "   ")

#entry_3.bind("<FocusIn>", add_space)
#entry_4.bind("<FocusIn>", add_space)
#entry_5.bind("<FocusIn>", add_space)
#entry_6.bind("<FocusIn>", add_space)
#entry_7.bind("<FocusIn>", add_space)
#entry_8.bind("<FocusIn>", add_space)

# STAGES
#-------------------------------------------------------------------------------------------------------------------

def reset_to_initial_conditions():
    global is_terminated, is_stages_running
    print("Complete")
    for channel, state in initial_pin_states.items():
        ljm.eWriteName(network.handle, channel, state)

    button_10.config(state=tk.NORMAL)
    is_terminated = True
    is_stages_running = False

    entry_32.delete("1.0", "end")
    entry_32.insert("end", "   CLOSED")
    entry_32.config(font=("Roboto", 8, "bold"))
    entry_32.config(bg="red")        

    entry_33.delete("1.0", "end")
    entry_33.insert("end", "   CLOSED")
    entry_33.config(font=("Roboto", 8, "bold"))
    entry_33.config(bg="red")    

    entry_34.delete("1.0", "end")
    entry_34.insert("end", "   CLOSED")
    entry_34.config(font=("Roboto", 8, "bold"))
    entry_34.config(bg="red")  

    entry_35.delete("1.0", "end")
    entry_35.insert("end", "   CLOSED")
    entry_35.config(font=("Roboto", 8, "bold"))
    entry_35.config(bg="red") 

    entry_31.delete("1.0", "end")
    entry_31.insert("end", "   CLOSED")
    entry_31.config(font=("Roboto", 8, "bold"))
    entry_31.config(bg="red")
  
    entry_36.delete("1.0", "end")
    entry_36.insert("end", "   OFF")
    entry_36.config(font=("Roboto", 8, "bold"))
    entry_36.config(bg="red")  
 
    entry_3.delete(0, "end")     
    entry_4.delete(0, "end")
    entry_5.delete(0, "end")
    entry_6.delete(0, "end")
 
def sleep_with_abort_check(duration):
    step = 0.001  # 100 ms step
    steps = int(duration / step)
    for _ in range(steps):
        if is_aborted:
            return True
        time.sleep(step)
    return False

is_terminated = False
is_stages_running = False
is_aborted = False

def stages():
    global is_stages_running
    global fire_duration, ignition_duration, purge_duration, cooldown_duration, is_testing, is_aborted

    #is_testing = False
    is_aborted = False
    entry_1.config(bg="red")
    entry_1.config(fg="white")
    entry_1.delete(1.0, "end")
    entry_1.config(font=("Roboto", 8, "bold"))
    entry_1.insert("end", "   ARMED")
    
    #print(f'Is testing: {is_testing}')

    if is_testing:
        print("System is in testing mode. Aborting sequence.")
        entry_1.config(bg="blue")
        entry_1.config(fg="white")
        entry_1.delete(1.0, "end")
        entry_1.config(font=("Roboto", 8, "bold"))
        entry_1.insert("end", "   ERROR")
        return
    
    if not all([fire_duration, ignition_duration, purge_duration, cooldown_duration]):
        print("Error: Not all Durations are Entered. Aborting Sequence")
        entry_1.config(bg="blue")
        entry_1.config(fg="white")
        entry_1.delete(1.0, "end")
        entry_1.config(font=("Roboto", 8, "bold"))
        entry_1.insert("end", "   ERROR")
        return

    if not fire_confirmation():
        print("Error: User Did Not Confirm Firing the System. Aborting Sequence")
        # Any necessary actions if the user cancels.
        return

    button_10.config(state=tk.DISABLED)
    is_stages_running = True

    countdown_thread = threading.Thread(target=start_countdown)
    countdown_thread.start()
    
    entry_1.config(bg="green")
    entry_1.config(fg="white")
    entry_1.delete(1.0, "end")
    entry_1.config(font=("Roboto", 8, "bold"))
    entry_1.insert("end", "   RUNNING...")
    
    fire_duration_sec = float(fire_duration)
    ignition_duration_sec = float(ignition_duration)
    purge_duration_sec = float(purge_duration)
    cooldown_duration_sec = float(cooldown_duration)

    # Firing Stage
    print("Starting Firing Stage")

    if is_aborted: return reset_to_initial_conditions()
    
    entry_32.delete("1.0", "end")
    entry_32.insert("end", "   OPEN")
    entry_32.config(bg="green")        

    entry_33.delete("1.0", "end")
    entry_33.insert("end", "   CLOSED")
    entry_33.config(bg="red")    

    entry_34.delete("1.0", "end")
    entry_34.insert("end", "   OPEN")
    entry_34.config(bg="green")  

    entry_35.delete("1.0", "end")
    entry_35.insert("end", "   OPEN")
    entry_35.config(bg="green") 

    entry_31.delete("1.0", "end")
    entry_31.insert("end", "   OPEN")
    entry_31.config(bg="green")
    
    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO0", 0) # LOX

    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO1", 1) # N2 PURGE

    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO2", 0) # N2 IPA

    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO3", 1) # N2 LOX

    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO4", 0) # IPA

    # Write to FIO5 during the ignition duration
    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO5", 0)  # Set FIO5 to 1 (or any value you need)
    entry_36.delete("1.0", "end")
    entry_36.insert("end", "   ON")
    entry_36.config(bg="green")
    time.sleep(ignition_duration_sec)  # Delay specifically for ignition_duration_sec seconds
    if is_aborted: return reset_to_initial_conditions()

    # Reset FIO5 to 0 after ignition_duration_sec
    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO5", 1)  # Reset FIO5 to 0
    if is_aborted: return reset_to_initial_conditions()

    # Update Entry 36 to OFF and set background to red
    entry_36.delete("1.0", "end")
    entry_36.insert("end", "  OFF")
    entry_36.config(bg="red")

    # Complete the remaining fire duration if any
    if is_aborted: return reset_to_initial_conditions()
    remaining_fire_duration = fire_duration_sec - ignition_duration_sec
    if remaining_fire_duration > 0:
        time.sleep(remaining_fire_duration)
    if is_aborted: return reset_to_initial_conditions()
    
    # Purge Stage
    print("Starting Purge Stage")

    entry_32.delete("1.0", "end")
    entry_32.insert("end", "   CLOSED")
    entry_32.config(bg="red")        

    entry_33.delete("1.0", "end")
    entry_33.insert("end", "   OPEN")
    entry_33.config(bg="green")    

    entry_34.delete("1.0", "end")
    entry_34.insert("end", "   CLOSED")
    entry_34.config(bg="red")  

    entry_35.delete("1.0", "end")
    entry_35.insert("end", "   CLOSED")
    entry_35.config(bg="red") 

    entry_31.delete("1.0", "end")
    entry_31.insert("end", "   CLOSED")
    entry_31.config(bg="red")
  
    entry_36.delete("1.0", "end")
    entry_36.insert("end", "   OFF")
    entry_36.config(bg="red")   

    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO0", 1)

    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO1", 1)

    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO2", 1)

    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO3", 1)

    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO4", 1)

    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO5", 1)

    time.sleep(purge_duration_sec)
    
    if is_aborted: return reset_to_initial_conditions()

    # Cooldown Stage
    print("Starting Cooldown Stage")

    entry_32.delete("1.0", "end")
    entry_32.insert("end", "   CLOSED")
    entry_32.config(bg="red")        

    entry_33.delete("1.0", "end")
    entry_33.insert("end", "   CLOSED")
    entry_33.config(bg="red")    

    entry_34.delete("1.0", "end")
    entry_34.insert("end", "   CLOSED")
    entry_34.config(bg="red")  

    entry_35.delete("1.0", "end")
    entry_35.insert("end", "   CLOSED")
    entry_35.config(bg="red") 

    entry_31.delete("1.0", "end")
    entry_31.insert("end", "   CLOSED")
    entry_31.config(bg="red")
  
    entry_36.delete("1.0", "end")
    entry_36.insert("end", "   OFF")
    entry_36.config(bg="red")     

    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO0", 1)

    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO1", 0)

    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO2", 1)

    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO3", 1)

    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO4", 1)

    if is_aborted: return reset_to_initial_conditions()
    ljm.eWriteName(network.handle, "FIO5", 1)

    time.sleep(cooldown_duration_sec)

    # Update entry_1 to indicate completion
    entry_1.config(bg="green")
    entry_1.delete(1.0, "end")
    entry_1.config(fg="white")
    entry_1.insert("end", "   COMPLETE")

    reset_to_initial_conditions()
    is_stages_running = False

# Update button to start the sequence in a new thread
button_10.config(command=lambda: threading.Thread(target=stages).start())

entries = {}
entries[3] = entry_3
entries[4] = entry_4
entries[5] = entry_5
entries[6] = entry_6

is_terminated = False  # Initialize global flag

def start_countdown():
    global is_terminated
    global is_aborted  # Include the abort flag
    if is_stages_running:
        try:
            fire_duration_int = int(fire_duration)
            ignition_duration_int = int(ignition_duration)
            purge_duration_int = int(purge_duration)
            cooldown_duration_int = int(cooldown_duration)
        except ValueError:
            return

        is_terminated = False  # Reset the flag

        countdown_thread_3 = threading.Thread(target=countdown, args=(3, fire_duration_int))
        countdown_thread_4 = threading.Thread(target=countdown, args=(4, ignition_duration_int))

        countdown_thread_3.start()
        countdown_thread_4.start()

        while countdown_thread_3.is_alive() or countdown_thread_4.is_alive():
            if is_terminated or is_aborted:  # Check for the abort flag
                return reset_to_initial_conditions()  # Reset if aborted
            sleep(0.1)

        if not is_terminated and not is_aborted:  # Check for the abort flag
            countdown(5, purge_duration_int)
            countdown(6, cooldown_duration_int)
    else:
        is_terminated = True
        clear_entries()

def countdown(entry_num, duration):
    for i in range(duration, 0, -1):
        if is_terminated or is_aborted:  # Check for the abort flag
            return reset_to_initial_conditions() 
        entries[entry_num].delete(0, tk.END)
        entries[entry_num].insert(0, str(i))
        window.update()
        sleep(1)
    if not is_terminated:
        entries[entry_num].delete(0, tk.END)
        entries[entry_num].insert(0, "DONE")

# SYSTEM STATUS
#-------------------------------------------------------------------------------------------------------------------

entry_24 = Text(
    bd=0,
    bg="#D9D9D9",
    fg="white",
    font=("Roboto", 8, "bold"),
    borderwidth=1,
    highlightthickness=1
)
entry_24.place(
    x=1122.0,
    y=173.0,
    width=145.0,
    height=20.0
)

entry_25 = Text(
    bd=0,
    bg="#D9D9D9",
    fg="white",
    font=("Roboto", 8, "bold"),
    borderwidth=1,
    highlightthickness=1
)
entry_25.place(
    x=1122.0,
    y=236.0,
    width=145.0,
    height=20.0
)

entry_26 = Text(
    bd=0,
    bg="#D9D9D9",
    fg="white",
    font=("Roboto", 8, "bold"),
    borderwidth=1,
    highlightthickness=1
)
entry_26.place(
    x=1122.0,
    y=299.0,
    width=145.0,
    height=20.0
)

entry_27 = Text(
    bd=0,
    bg="#D9D9D9",
    fg="white",
    font=("Roboto", 8, "bold"),
    borderwidth=1,
    highlightthickness=1
)
entry_27.place(
    x=1122.0,
    y=364.0,
    width=145.0,
    height=20.0
)

entry_28 = Text(
    bd=0,
    bg="#D9D9D9",
    fg="white",
    font=("Roboto", 8, "bold"),
    borderwidth=1,
    highlightthickness=1
)
entry_28.place(
    x=1122.0,
    y=428.0,
    width=145.0,
    height=20.0
)

entry_29 = Text(
    bd=0,
    bg="#D9D9D9",
    fg="white",
    font=("Roboto", 8, "bold"),
    borderwidth=1,
    highlightthickness=1
)
entry_29.place(
    x=1122.0,
    y=492.0,
    width=145.0,
    height=20.0
)

entry_30 = Text(
    bd=0,
    bg="#D9D9D9",
    fg="white",
    font=("Roboto", 8, "bold"),
    borderwidth=1,
    highlightthickness=1
)
entry_30.place(
    x=1122.0,
    y=556.0,
    width=145.0,
    height=20.0
)

# REALTIME DATA COLLECTION
#-------------------------------------------------------------------------------------------------------------------
all_sensors_ok = True
blink_flag = False

def reset_plot_data():
    time_data.clear()
    pressure_data_1.clear()
    pressure_data_2.clear()
    pressure_data_3.clear()
    pressure_data_4.clear()
    load_data_1.clear()
    load_data_2.clear()
    temperature_data.clear()

def update_realtime():
    with ThreadPoolExecutor() as executor:
        global connection_status
        #print(f"TIME: {np.shape(time_data)}, P1: {np.shape(pressure_data_1)}, P2: {np.shape(pressure_data_2)}, P3: {np.shape(pressure_data_3)}, P4: {np.shape(pressure_data_4)}, L1: {np.shape(load_data_1)}, L2: {np.shape(load_data_2)}, T1: {np.shape(temperature_data)}")
        try:
            if connection_status:
                update_sensors()
            update_plots()

        except ValueError as e:
            #print(f"Data mismatch error")
            reset_plot_data()

        # Schedule the update_realtime function to run again after 10 ms
        window.after(100, update_realtime)

def schedule_reset():
    reset_plot_data()
    window.after(60000, schedule_reset)

schedule_reset()

# Set the size for all subsequent plots
plt.figure().set_figheight(2)
plt.figure().set_figwidth(15)

# Create a Figure with larger dimensions
fig = Figure(figsize=(20, 20), dpi=70, facecolor=(238/255, 238/255, 238/255))

# Create 3 subplots side by side
ax1 = fig.add_subplot(1, 3, 1)
ax2 = fig.add_subplot(1, 3, 2)
ax3 = fig.add_subplot(1, 3, 3)

ax1.grid(True, color='#888888')
ax2.grid(True, color='#888888')
ax3.grid(True, color='#888888')

#ax3.set_ylim(0, 30)

# Adjust the vertical spacing
fig.subplots_adjust(left=0.05, bottom=0.175, right=0.975, top=0.95, hspace=0.20, wspace=0.30)

# Adjust ticks for each subplot
for ax in [ax1, ax2, ax3]:
    ax.xaxis.set_major_locator(MaxNLocator(nbins=10, integer=True))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=10, integer=True))
    ax.yaxis.set_minor_locator(MaxNLocator(nbins=10, integer=True))
    
# Set custom y-axis labels and axis limits
y_labels = ['Pressure (psi)', 'Temperature (°C)', 'Thrust (N)']

for ax, y_label in zip([ax1, ax2, ax3], y_labels):
    ax.set_xlabel('Time (s)', weight='bold')
    ax.set_ylabel(y_label, weight='bold')

# Create 7 lines with different colors for each subplot
colors = ['#FF0000', '#FFB600', '#22CA00', '#0061FF', '#A300DB', '#FD95FF', '#59FFFF']
labels = ['Pressure Sensor [1]', 'Pressure Sensor [2]', 'Pressure Sensor [3]', 'Pressure Sensor [4]', 'Temperature Sensor', 'Load Cell [1]', 'Load Cell [2]']
line_width = 2.0  # Set the desired line width

line1, = ax1.plot(time_data, pressure_data_1, linewidth=line_width)
line2, = ax1.plot(time_data, pressure_data_2, linewidth=line_width)
line3, = ax1.plot(time_data, pressure_data_3, linewidth=line_width)
line4, = ax1.plot(time_data, pressure_data_4, linewidth=line_width)
line5, = ax2.plot(time_data, temperature_data, linewidth=line_width)
line6, = ax3.plot(time_data, load_data_1, linewidth=line_width)
line7, = ax3.plot(time_data, load_data_2, linewidth=line_width)

lines = [line1, line2, line3, line4, line5, line6, line7]
for line, color in zip(lines, colors):
    line.set_color(color)

# Create a legend
legend = fig.legend(lines[:7], labels, loc='upper center', bbox_to_anchor=(0.5, 0.075), ncol=7, frameon=False)
for text in legend.get_texts():
    text.set_color("black")

# Embed the figure in Tkinter
canvas_plot = FigureCanvasTkAgg(fig, master=window)
canvas_plot.get_tk_widget().config(bg='white')  # Set the background color to match the figure
canvas_plot.draw()

# Position the plot on the canvas with larger dimensions
canvas_plot.get_tk_widget().place(x=20, y=631.5, width=1055, height=350)

entry_mapping = {
    "Pressure Sensor [1]": entry_9,
    "Pressure Sensor [2]": entry_10,
    "Pressure Sensor [3]": entry_11,
    "Pressure Sensor [4]": entry_12,
    "Temperature Sensor": entry_13,
    "Load Sensor [1]": entry_14,
    "Load Sensor [2]": entry_15
}

temperature_entries = [entry_13]
load_cell_entries = [entry_14, entry_15]
pressure_entries = [entry_9, entry_10, entry_11, entry_12]
ready_entries = [entry_24, entry_25, entry_26, entry_27, entry_28, entry_29, entry_30]
sensor_entries = [entry_9, entry_10, entry_11, entry_12, entry_13, entry_14, entry_15]
error_entries = [entry_9, entry_10, entry_11, entry_12, entry_13, entry_14, entry_15, entry_24, entry_25, entry_26, entry_27, entry_28, entry_29, entry_30]

def update_sensors():
    with ThreadPoolExecutor() as executor:
        global time_counter
        global data_logging, filename
        global all_sensors_ok
        all_sensors_ok = True

        with data_lock:
            time_data.append(time_counter)
            time_counter += 0.1

            for sensor, entry in entry_mapping.items():
                channel = network.config["PIN_CONFIG"]["SENSORS"][sensor]
                try:
                    if entry in pressure_entries:
                        channel = network.config["PIN_CONFIG"]["SENSORS"][sensor]
                        raw_value = ljm.eReadName(network.handle, channel)
                        
                        if sensor == "Pressure Sensor [1]":
                            pressure_data_1.append(round(raw_value * 132.421875 - 62.5 - 2, 5))
                            pressure_data_raw_1.append(raw_value)
                            value = pressure_data_1[-1]
                            
                        elif sensor == "Pressure Sensor [2]":
                            pressure_data_2.append(round(raw_value * 132.421875 - 62.5 - 2, 5))
                            pressure_data_raw_2.append(raw_value)
                            value = pressure_data_2[-1]
                            
                        elif sensor == "Pressure Sensor [3]":
                            pressure_data_3.append(round(raw_value * 132.421875 - 62.5, 5))
                            pressure_data_raw_3.append(raw_value)
                            value = pressure_data_3[-1]
                            
                        elif sensor == "Pressure Sensor [4]":
                            pressure_data_4.append(round(raw_value * 132.421875 - 62.5 - 1, 5))
                            pressure_data_raw_4.append(raw_value)
                            value = pressure_data_4[-1]

                        entry.delete("1.0", "end")
                        entry.insert("end", f"   {value:.2f} psi")      
                    
                    elif entry in temperature_entries:
                        # Initialize moving average and threshold variables if they don't exist
                        if not hasattr(network, 'last_n_temp_values'):
                            network.last_n_temp_values = []
 
                        moving_avg_n_temp = 5  # Number of last temperature readings to average
                        threshold_temp = 3  # Set this to a suitable value that filters out noise
 
                        # Thermocouple Configuration
                        ljm.eWriteName(network.handle, "AIN4_EF_INDEX", 24)
                        ljm.eWriteName(network.handle, "AIN4_EF_CONFIG_A", 1)
                        ljm.eWriteName(network.handle, "AIN4_EF_CONFIG_B", 60052)
                        ljm.eWriteName(network.handle, "AIN4_EF_CONFIG_D", 1)
                        ljm.eWriteName(network.handle, "AIN4_EF_CONFIG_E", 0)
                        ljm.eWriteName(network.handle, "AIN4_NEGATIVE_CH", 5)                
                        #value = round(ljm.eReadName(network.handle, "AIN4_EF_READ_A"), 5)

                        value = round(ljm.eReadName(network.handle, "AIN4_EF_READ_A"), 5)

                        temperature_data_raw.append(ljm.eReadName(network.handle, "AIN4_EF_READ_A"))
                        temperature_data.append(value)
                        
                        # Apply threshold
                        if abs(value) < threshold_temp:
                            value = 0
                        
                        network.last_n_temp_values.append(value)
                        
                        # Keep only the last 'moving_avg_n_temp' readings
                        if len(network.last_n_temp_values) > moving_avg_n_temp:
                            network.last_n_temp_values.pop(0)
                        
                        # Calculate average temperature
                        avg_value_temp = sum(network.last_n_temp_values) / len(network.last_n_temp_values)
                        
                        # Convert average value to Fahrenheit
                        conversion_factor_C_to_F = 9 / 5
                        avg_value_temp_F = avg_value_temp * conversion_factor_C_to_F + 32
                        
                        if avg_value_temp > -1000:
                            entry.delete("1.0", "end")
                            entry.insert("end", f"   {avg_value_temp:.2f} °C / {avg_value_temp_F:.2f} °F")
                        else:
                            entry.delete("1.0", "end")
                            entry.insert("end", "   ERROR")

                        continue           
                    
                    elif entry in load_cell_entries:
                        # Read Tare Weights

                        ljm.eWriteName(network.handle, "DAC0", 4.1)  # Setting DAC0 to 5V
                        ljm.eWriteName(network.handle, "DAC1", 4.1)  # Setting DAC1 to 5V

                        ljm.eWriteName(network.handle, "AIN6_NEGATIVE_CH", 7)
                        ljm.eWriteName(network.handle, "AIN8_NEGATIVE_CH", 9)
                        
                        # Initialize other variables and arrays
                        moving_avg_n = 5
                        last_n_values_1 = []
                        last_n_values_2 = []

                        # Read tare weights
                        tare_weight1 = ljm.eReadName(network.handle, "AIN6")
                        tare_weight2 = ljm.eReadName(network.handle, "AIN8")

                        # Read voltage with reference to the negative channel
                        voltage = ljm.eReadName(network.handle, channel) - (tare_weight1 if entry == entry_14 else tare_weight2)

                        # Read excitation voltage from reference channels
                        excitation_voltage = ljm.eReadName(network.handle, "AIN10" if entry == entry_14 else "AIN11")

                        # Additional code for sensitivity and calculations
                        sensitivity = 0.1
                        
                        threshold = 20
                        
                        if abs(value) < threshold:
                            value = 0                        
                        
                        if sensor == "Load Sensor [1]":
                            K1 = 101666
                            K3 = 10
                            value = ((-((voltage / (sensitivity / 1000)) / excitation_voltage)) * K3) + K1
                            last_n_values_1.append(value)
                            if len(last_n_values_1) > moving_avg_n:
                                last_n_values_1.pop(0)
                            avg_value_1 = sum(last_n_values_1) / len(last_n_values_1)
                            load_data_1.append(avg_value_1)
                            load_data_raw_1.append(tare_weight1)
                        
                        elif sensor == "Load Sensor [2]":
                            K2 = 101663
                            K4 = 10
                            value = ((-((voltage / (sensitivity / 1000)) / excitation_voltage)) * K4) + K2
                            last_n_values_2.append(value)
                            if len(last_n_values_2) > moving_avg_n:
                                last_n_values_2.pop(0)
                            avg_value_2 = sum(last_n_values_2) / len(last_n_values_2)
                            load_data_2.append(avg_value_2)
                            load_data_raw_2.append(tare_weight2)
                        
                        entry.delete("1.0", "end")
                        conversion_factor = 0.2248  # 1 N = 0.2248 lbs
                        if sensor == "Load Sensor [1]":
                            weight_in_lbs = avg_value_1 * conversion_factor
                            entry.insert("end", f"   {avg_value_1:.2f} N / {weight_in_lbs:.2f} lbs")
                        elif sensor == "Load Sensor [2]":
                            weight_in_lbs = avg_value_2 * conversion_factor
                            entry.insert("end", f"   {avg_value_2:.2f} N / {weight_in_lbs:.2f} lbs")

                        continue
                    
                    else:
                        value = int(round(ljm.eReadName(network.handle, channel), 0))


                    entry.config(font=("Roboto", 8), fg="black", bg="white")
                
                except ljm.LJMError:
                    all_sensors_ok = False

        # Update the ready entries based on all_sensors_ok flag
        for ready_entry in ready_entries:
            ready_entry.delete("1.0", "end")
            if all_sensors_ok:
                ready_entry.insert("end", "   READY")
                ready_entry.config(font=("Roboto", 8, "bold"))
                ready_entry.config(bg="green")
                ready_entry.config(fg="white")
                update_plots()
            
            else:
                ready_entry.insert("end", "   ERROR")

def gaussian_smooth(data, sigma = 5):  # Higher sigma for more smoothing
    return gaussian_filter1d(data, sigma)

def update_plots():
    with ThreadPoolExecutor() as executor:
        # Calculate moving averages
        avg_pressure_data_1 = gaussian_smooth(pressure_data_1)
        avg_pressure_data_2 = gaussian_smooth(pressure_data_2)
        avg_pressure_data_3 = gaussian_smooth(pressure_data_3)
        avg_pressure_data_4 = gaussian_smooth(pressure_data_4)
        avg_temperature_data = gaussian_smooth(temperature_data)
        avg_load_data_1 = gaussian_smooth(load_data_1)
        avg_load_data_2 = gaussian_smooth(load_data_2)
        avg_time_data = gaussian_smooth(time_data)

        line1.set_data(avg_time_data, avg_pressure_data_1)
        line2.set_data(avg_time_data, avg_pressure_data_2)
        line3.set_data(avg_time_data, avg_pressure_data_3)
        line4.set_data(avg_time_data, avg_pressure_data_4)
        line5.set_data(avg_time_data, avg_temperature_data)
        line6.set_data(avg_time_data, avg_load_data_1)
        line7.set_data(avg_time_data, avg_load_data_2)

        # Rescale axes
        for ax in [ax1, ax2, ax3]:
            ax.relim()
            ax.autoscale_view()

        # Redraw the plot
        fig.canvas.draw_idle()

def blink_error_entries():
    global blink_flag
    global all_sensors_ok
    if not all_sensors_ok:
        for error_entry in error_entries:
            error_entry.delete("1.0", "end")
            if blink_flag:
                error_entry.config(bg="blue")
                error_entry.config(fg="white")
                error_entry.insert("end", "   ERROR")
                error_entry.config(font=("Roboto", 8, "bold"))
            else:
                error_entry.config(bg="white")
                #error_entry.config(fg="black")
                error_entry.insert("end", "")
        
        blink_flag = not blink_flag
    window.after(500, blink_error_entries)

# DEVICE INFRORMATION
#-------------------------------------------------------------------------------------------------------------------

entry_17 = Text(
    bd=0,
    bg="#D9D9D9",
    fg="#000716",
    font=("Roboto", 8),
    borderwidth=1,
    highlightthickness=1
)
entry_17.place(
    x=906.0,
    y=173.0,
    width=145.0,
    height=20.0
)

entry_18 = Text(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    font=("Roboto", 8),
    borderwidth=1,
    highlightthickness=1
)
entry_18.place(
    x=906.0,
    y=236.0,
    width=145.0,
    height=20.0
)

entry_19 = Text(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    font=("Roboto", 8),
    borderwidth=1,
    highlightthickness=1
)
entry_19.place(
    x=906.0,
    y=299.0,
    width=145.0,
    height=20.0
)

entry_20 = Text(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    font=("Roboto", 8),
    borderwidth=1,
    highlightthickness=1
)
entry_20.place(
    x=906.0,
    y=364.0,
    width=145.0,
    height=20.0
)

entry_21 = Text(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    font=("Roboto", 8),
    borderwidth=1,
    highlightthickness=1
)
entry_21.place(
    x=906.0,
    y=428.0,
    width=145.0,
    height=20.0
)

entry_22 = Text(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    font=("Roboto", 8),
    borderwidth=1,
    highlightthickness=1
)
entry_22.place(
    x=906.0,
    y=492.0,
    width=145.0,
    height=20.0
)

entry_23 = Text(
    bd=0,
    bg="#FFFFFF",
    fg="#000716",
    font=("Roboto", 8),
    borderwidth=1,
    highlightthickness=1
)
entry_23.place(
    x=906.0,
    y=556.0,
    width=145.0,
    height=20.0
)

# ACTUATOR STATUS
#-------------------------------------------------------------------------------------------------------------------

# Entry widget mapping
entry_widgets = {
    "FIO0": entry_32,
    "FIO1": entry_33,
    "FIO2": entry_34,
    "FIO3": entry_35,
    "FIO4": entry_31,
    "FIO5": entry_36
}

# Call the function after entry widgets are defined
set_initial_pin_states(network.handle, entry_widgets)

# UPDATE SYSTEM
#-------------------------------------------------------------------------------------------------------------------

def insert_no_connection():
    for entry in [entry_31, entry_32, entry_33, entry_34, entry_35, entry_36]:
        entry.delete("1.0", tk.END)
        entry.insert(tk.END, "   NO CONNECTION")
        entry.config(font=("Roboto", 8, "bold"))
        entry.config(bg="red")
        entry.config(fg="white")

def update_device_entries():
    with data_lock:
        try:
            # Attempt to read a simple value from LabJack
            serial_number = ljm.eReadName(network.handle, "SERIAL_NUMBER")

            # If successful, update as normal
            device_info = message_queue.get()
            entry_17.delete(1.0, "end")
            entry_17.insert("end", "   " + device_info["connection"])
            entry_17.configure(bg="green", fg="white", font=("Roboto", 8, 'bold'))

            for entry, key in zip([entry_18, entry_19, entry_20, entry_21, entry_22, entry_23], 
                                  ["device_type", "serial_number", "firmware_version", "hardware_version", "subnet", "gateway"]):
                entry.delete(1.0, "end")
                entry.configure(bg="white", fg="black", font=("Roboto", 8))
                entry.insert("end", "   " + str(device_info[key]))
        except (ljm.LJMError, queue.Empty):
            # If reading fails, set to NO CONNECTION
            insert_no_connection()
            for entry in [entry_17, entry_18, entry_19, entry_20, entry_21, entry_22, entry_23]:
                entry.delete(1.0, "end")
                entry.configure(bg="red", fg="white", font=("Roboto", 8, 'bold'))
                entry.insert("end", "   NO CONNECTION")

    window.after(500, update_device_entries)

def insert_into_entries():
    global entry_31, entry_32, entry_33, entry_34, entry_35, entry_36

    entry_31.delete("1.0", tk.END)
    entry_31.insert(tk.END, "   CLOSED")
    entry_31.config(font=("Roboto", 8, "bold"), bg="red", fg="white")

    entry_32.delete("1.0", tk.END)
    entry_32.insert(tk.END, "   CLOSED")
    entry_32.config(font=("Roboto", 8, "bold"), bg="red", fg="white")
    
    entry_33.delete("1.0", tk.END)
    entry_33.insert(tk.END, "   CLOSED")
    entry_33.config(font=("Roboto", 8, "bold"), bg="red", fg="white")
    
    entry_34.delete("1.0", tk.END)
    entry_34.insert(tk.END, "   CLOSED")
    entry_34.config(font=("Roboto", 8, "bold"), bg="red", fg="white")
    
    entry_35.delete("1.0", tk.END)
    entry_35.insert(tk.END, "   CLOSED")
    entry_35.config(font=("Roboto", 8, "bold"), bg="red", fg="white")
    
    entry_36.delete("1.0", tk.END)
    entry_36.insert(tk.END, "   OFF")
    entry_36.config(font=("Roboto", 8, "bold"), bg="red", fg="white")

# SYSTEM RECORDING
#-------------------------------------------------------------------------------------------------------------------

def start_recording():
    entry_2.config(bg="green")
    entry_2.config(fg="white")
    entry_2.delete(1.0, "end")
    entry_2.insert("end", "   RUNNING...")


def stop_recording():
    entry_2.config(bg="yellow")
    entry_2.config(fg="black")
    entry_2.delete(1.0, "end")
    entry_2.insert("end", "   WAITING...")


button_image_1 = PhotoImage(file=relative_to_assets("button_1.png"))
button_1 = Button(
    window,
    image=button_image_1,
    text="RECORD",
    compound="center",
    font=("Roboto", 10, "bold"),
    borderwidth=2,
    highlightthickness=2,
    command=lambda: print("Record Button Pressed. Data Collection Started")
)
button_1.pack()
button_1.config(command=start_recording)

button_1.place(
    x=41.0,
    y=334.0,
    width=148.0,
    height=49.0
)

button_image_2 = PhotoImage(file=relative_to_assets("button_2.png"))
button_2 = Button(
    window,
    image=button_image_2,
    text="STOP",
    compound="center",
    font=("Roboto", 10, "bold"),
    borderwidth=2,
    highlightthickness=2,
    command=lambda: print("Data Collection Stopped")
)
button_2.pack()
button_2.config(command=stop_recording)

button_2.place(
    x=41.0,
    y=398.0,
    width=148.0,
    height=49.0
)

def start_data_logging():
    global data_logging, filename
    if data_logging:  # If already logging, return without doing anything.
        return

    button_2.config(state=tk.NORMAL)
    button_1.config(state=tk.DISABLED)

    data_logging = True
    timestamp = datetime.datetime.now().strftime("%m-%d-%Y (%H hrs %M min %S sec)")
    os.makedirs("minCS Data Log", exist_ok=True)
    filename = os.path.join(os.getcwd(), "minCS Data Log", f"minCS Data Log {timestamp}.csv")
    
    with open(filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Timestamp", "Pressure 1", "Pressure 2", "Pressure 3", "Pressure 4", "Temperature", "Load 1", "Load 2", "", "Pressure 1 (V)", "Pressure 2 (V)", "Pressure 3 (V)", "Pressure 4 (V)", "Temperature (V)", "Load 1 (V)", "Load 2 (V)"])

    entry_2.config(bg="green")
    entry_2.config(fg="white")
    entry_2.delete(1.0, "end")
    entry_2.insert("end", "   RUNNING...")

    logging_thread = threading.Thread(target=log_data, args=(filename,))
    logging_thread.start()

def log_data(filename):
    global data_logging
    log_time = 0

    while data_logging:
        current_time = "{:.2f}".format(log_time)
        current_datetime = datetime.datetime.now().strftime("%m-%d-%Y %H-%M-%S")
        
        with open(filename, 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow([current_datetime, current_time,
                                 *pressure_data_1[-1:], 
                                 *pressure_data_2[-1:], 
                                 *pressure_data_3[-1:], 
                                 *pressure_data_4[-1:], 
                                 *temperature_data[-1:], 
                                 *load_data_1[-1:], 
                                 *load_data_2[-1:],
                                 "",
                                 *pressure_data_raw_1[-1:], 
                                 *pressure_data_raw_2[-1:], 
                                 *pressure_data_raw_3[-1:], 
                                 *pressure_data_raw_4[-1:], 
                                 *temperature_data_raw[-1:], 
                                 *load_data_raw_1[-1:], 
                                 *load_data_raw_2[-1:]])

        log_time += 0.5  # Increment by 0.5 seconds for each data point
        time.sleep(0.5)  # Sleep for 0.5 seconds before the next data acquisition

def stop_data_logging():
    global data_logging
    data_logging = False

    button_1.config(state=tk.NORMAL)
    button_2.config(state=tk.DISABLED)

    entry_2.config(bg="yellow")
    entry_2.config(fg="black")
    entry_2.delete(1.0, "end")
    entry_2.insert("end", "   WAITING...")

button_1.config(command=start_data_logging)
button_2.config(command=stop_data_logging)

thread1 = Thread(target=update_status)
thread1.daemon = True
thread1.start()

thread2 = Thread(target=update_realtime)
thread2.daemon = True
thread2.start()

thread3 = Thread(target=update_device_entries)
thread3.daemon = True
thread3.start()

thread4 = Thread(target=blink_error_entries)
thread4.daemon = True
thread4.start()

thread5 = Thread(target=reconnection_thread)
thread5.daemon = True
thread5.start()

window.resizable(False, False)
window.mainloop()
