import time
import sys
import labjack.ljm as ljm

# Open a connection to any LabJack T7 device
handle = ljm.openS("T7", "ANY", "ANY")

# Load cell 1 configuration
ljm.eWriteName(handle, "AIN1_NEGATIVE_CH", 0)

# Read load cell 1 values
while True:
    try:
        # Read load cell voltages
        load_readings = [
            ljm.eReadName(handle, "AIN1"),
            ljm.eReadName(handle, "AIN2"),
        ]
        
        # Define the calibration equation parameters
        sensitivity = 1.0  # load cell sensitivity (mV/V)
        excitation_voltage = 5.0  # load cell excitation voltage (V)
        bridge_resistance = 1000.0  # load cell bridge resistance (Ohms)
        capacity = 20.0  # load cell capacity (kg)
        calibration_factor = capacity * sensitivity * excitation_voltage / bridge_resistance  # calibration factor (g/mV)

        # Convert load readings to weights
        weights = [load_readings[i] * calibration_factor for i in range(len(load_readings))]
        
        # Print load cell weights
        print(f"Load Cell 1: {weights[0]:.2f} kg")
        print(f"Load Cell 2: {weights[1]:.2f} kg")
        
        time.sleep(0.5)
    
    except KeyboardInterrupt:
        # Close the connection on Ctrl-C
        ljm.close(handle)
        sys.exit()