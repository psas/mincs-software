import labjack.ljm as ljm
import threading
from threading import Thread
import time
import queue

message_queue = queue.Queue()

class Network:
    def __init__(self):
        self.is_connected = False
        self.is_new_connection = False
        self.device_info = {}
        self.config = {
            "PIN_CONFIG": {
                "FIRE_BUTTON": "FIO6",
                "RESET_BUTTON": "FIO7",
                "SENSORS": {
                    "Pressure Sensor [1]": "AIN0",
                    "Pressure Sensor [2]": "AIN1",
                    "Pressure Sensor [3]": "AIN2",
                    "Pressure Sensor [4]": "AIN3",
                    "Temperature Sensor": "AIN4",
                    "Load Sensor [1]": "DAC0",
                    "Load Sensor [2]": "DAC1"
                },
                "ACTUATORS": {
                    "LOX Valve": "FIO0",
                    "N2 Purge Valve": "FIO1",
                    "N2 IPA Valve": "FIO2",
                    "N2 LOX Valve": "FIO3",
                    "IPA Valve": "FIO4",
                    "Ignition": "FIO5"
                },
            },
            "LABJACK_DEVICE_TYPE": "T7",
            "LABJACK_CONNECTION_TYPE": "ANY",
            "LABJACK_IDENTIFIER": "ANY"
        }
        
        try:
            self.handle = ljm.openS(self.config["LABJACK_DEVICE_TYPE"], self.config["LABJACK_CONNECTION_TYPE"], self.config["LABJACK_IDENTIFIER"])
        
        except ljm.LJMError:
            self.handle = None
            self.device_info = {
                "connection": "NO CONNECTION",
                "device_type": "NO CONNECTION",
                "serial_number": "NO CONNECTION",
                "firmware_version": "NO CONNECTION",
                "hardware_version": "NO CONNECTION",
                "ip_address": "NO CONNECTION",
                "subnet": "NO CONNECTION",
                "gateway": "NO CONNECTION",
        }
        
        self.read_lock = threading.Lock()
        self.write_lock = threading.Lock()
        
        refresh_thread = Thread(target=self.refresh_loop, args=(0.1,))  # 0.01 second interval
        refresh_thread.daemon = True  # Daemonize thread
        refresh_thread.start()

    def refresh_loop(self, interval):
        while True:
            self.refresh_connection()
            time.sleep(interval)

    def set_initial_pin_states(self):
        with self.write_lock:
            initial_pin_states = {
                "FIO0": 1,
                "FIO1": 0,
                "FIO2": 1,
                "FIO3": 1,
                "FIO4": 1,
                "FIO5": 1
            }

        for channel, state in initial_pin_states.items():
            ljm.eWriteName(self.handle, channel, state)

    def refresh_connection(self):
        with self.write_lock:
            try:
                self.handle = ljm.openS(self.config["LABJACK_DEVICE_TYPE"], self.config["LABJACK_CONNECTION_TYPE"], self.config["LABJACK_IDENTIFIER"])
                self.device_info = self.get_device_info()
                if not self.is_connected:
                    self.is_new_connection = True
                self.is_connected = True
                message_queue.put(self.device_info)
                
            except ljm.LJMError:
                self.is_connected = False
                self.is_new_connection = False
                self.handle = None
                self.device_info = {
                    "connection": "NO CONNECTION",
                    "device_type": "NO CONNECTION",
                    "serial_number": "NO CONNECTION",
                    "firmware_version": "NO CONNECTION",
                    "hardware_version": "NO CONNECTION",
                    "ip_address": "NO CONNECTION",
                    "subnet": "NO CONNECTION",
                    "gateway": "NO CONNECTION",
                }
                message_queue.put(self.device_info) 

    def get_device_info(self):
        with self.read_lock:
            try:
                if self.handle is not None:
                    device_info = {
                    "connection": "CONNECTED",
                    "device_type": self.config["LABJACK_DEVICE_TYPE"],
                    "serial_number": int(round(ljm.eReadName(self.handle, "SERIAL_NUMBER"))),
                    "firmware_version": round(ljm.eReadName(self.handle, "FIRMWARE_VERSION"), 2),
                    "hardware_version": round(ljm.eReadName(self.handle, "HARDWARE_VERSION"), 2),
                    "ip_address": ljm.eReadName(self.handle, "ETHERNET_IP"),
                    "subnet": int(round(ljm.eReadName(self.handle, "ETHERNET_SUBNET"))),
                    "gateway": int(round(ljm.eReadName(self.handle, "ETHERNET_GATEWAY"))),
                    }
                    return device_info
                else:
                    return self.device_info
            
            except ljm.LJMError as e:
                #print("Connection Failed!")
                return self.device_info

    def check_connection(self):
        return self.handle is not None

# Initialize Network and start threads
network = Network()