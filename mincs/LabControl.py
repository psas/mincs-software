import tkinter as tk
from tkinter import ttk
import json
from labjack import ljm
from LabJackHandler import LabJackHandler

class LabControl(tk.Tk):
    def __init__(self, labjack_handler, pin_config):
        print("minCS Testing Controller Loading...")
        super().__init__()

        self.labjack_handler = labjack_handler
        self.pin_config = pin_config
        self.actuator_pins = pin_config["ACTUATORS"]
        self.pin_states = {pin: True if label in ['Ignition', 'N2 Purge Valve'] else False for label, pin in self.actuator_pins.items()}  # Initial state for specific pins is True
        self.pin_labels = {pin: label for label, pin in self.actuator_pins.items()}  # Keep track of pin labels

        self.title("minCS Testing Controller")
        self.geometry("400x325")
        self.iconbitmap("C:/Users/ramir/minTS_logo.ico")
        self.resizable(False, False)

        self.main_frame = ttk.LabelFrame(self, text=" minCS Testing Application ", padding=10, relief='raised')
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Add these lines
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_widgets()
        
        self.show_alert_window("OPERATE WITH CAUTION")

    def create_widgets(self):
        style = ttk.Style()
        print("minCS Testing Controller Loaded")
        
        # Set the desired theme
        style.theme_use('winnative')

        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(pady=0)

        for idx, (label, pin) in enumerate(self.actuator_pins.items()):
            row, col = divmod(idx, 3)

            actuator_label = tk.Label(button_frame, text=label, font=("Helvetica", 9))
            actuator_label.grid(row=row * 2, column=col, padx=0, pady=0)

            # Determine initial button color and text
            button_initial_color = "green" if self.pin_states[pin] else "red"
            button_initial_text = "ON" if self.pin_states[pin] else "OFF"

            if label in ['Ignition', 'N2 Purge Valve']:
                # Set the color and text for these buttons to represent the reversed logic
                button_initial_color = "red" if self.pin_states[pin] else "green"
                button_initial_text = "OFF" if self.pin_states[pin] else "ON"

            button = tk.Button(
                button_frame, text=button_initial_text, bg=button_initial_color, relief="raised", width=10, height=2,
                command=lambda pin=pin: self.toggle_pin(pin)
            )
            button.grid(row=row * 2 + 1, column=col, padx=20, pady=20)
            button.pin = pin

    def toggle_pin(self, pin):
        self.pin_states[pin] = not self.pin_states[pin]
        ljm.eWriteName(self.labjack_handler.handle, pin, int(self.pin_states[pin]))  # Send the pin state as is to the LabJack device

        for widget in self.main_frame.winfo_children():
            if isinstance(widget, tk.Frame):  # buttons are placed in the frame, which is a child of main_frame
                for button in widget.winfo_children():
                    if hasattr(button, 'pin') and button.pin == pin:
                        label = self.pin_labels[button.pin]  # Get the label of the pin
                        if label in ['Ignition', 'N2 Purge Valve']:  # Check the button label
                            if self.pin_states[pin]:  # If pin state is True, button should display OFF
                                button.config(text="OFF", bg="red")
                            else:  # If pin state is False, button should display ON
                                button.config(text="ON", bg="green")
                        else:
                            if self.pin_states[pin]:  # For all other buttons, normal logic applies
                                button.config(text="ON", bg="green")
                            else:
                                button.config(text="OFF", bg="red")

    def show_alert_window(self, message):
        alert_window = tk.Toplevel()
        alert_window.title("minCS Warning: Read Me")
        alert_window.resizable(False, False)  # Make the window non-resizable
        alert_window.attributes("-toolwindow", 1)  # Add a tool window attribute to make it look cleaner
        alert_window.configure(bg="#f0f0f0")  # Set a background color for a cleaner look

        # Center the window on the screen
        alert_window.update_idletasks()
        width = 200  # Set the initial width of the window
        height = 160  # Set the initial height of the window
        x = (alert_window.winfo_screenwidth() // 2) - (width // 2)
        y = (alert_window.winfo_screenheight() // 2) - (height // 2)
        alert_window.geometry(f"{width}x{height}+{x}+{y}")

        alert_label = tk.Label(alert_window, text=message, wraplength=250, bg="#f0f0f0", fg="red", justify="center", font=("TkDefaultFont", 10, "bold"))
        alert_label.pack(padx=20, pady=10)

        personnel_label = tk.Label(alert_window, text="TRAINED PERSONNEL ONLY", bg="#f0f0f0", fg="red", justify="center", font=("TkDefaultFont", 9, "bold"))
        personnel_label.pack(padx=20, pady=(0, 5))

        personnel_label = tk.Label(alert_window, text="", bg="#f0f0f0", fg="red", justify="center", font=("TkDefaultFont", 9, "bold"))
        personnel_label.pack(padx=20, pady=(0, 5))

        ok_button = tk.Button(alert_window, text="OK I UNDERSTAND", command=alert_window.destroy)
        ok_button.pack(pady=(5, 20))

def main():
    # Read the config.json file
    with open('config.json', 'r') as f:
        config = json.load(f)

    # Retrieve the constants and pin configuration from the config
    LABJACK_DEVICE_TYPE = getattr(ljm.constants, config['LABJACK_DEVICE_TYPE'])
    LABJACK_CONNECTION_TYPE = getattr(ljm.constants, config['LABJACK_CONNECTION_TYPE'])
    LABJACK_IDENTIFIER = config['LABJACK_IDENTIFIER']
    pin_config = config['PIN_CONFIG']

    # Initialize the LabJack handler
    handle = ljm.openS(str(LABJACK_DEVICE_TYPE), str(LABJACK_CONNECTION_TYPE), str(LABJACK_IDENTIFIER))
    labjack_handler = LabJackHandler(handle, LABJACK_DEVICE_TYPE, pin_config)

    # Initialize the LabJack controller
    lab_control = LabControl(labjack_handler, pin_config)

    # Start the Tkinter main loop
    lab_control.mainloop()

if __name__ == "__main__":
    main()
