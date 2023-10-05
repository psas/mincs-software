import labjack.ljm as ljm  # import the labjack_ljm module
import time

# Open the first found LabJack
handle = ljm.openS("ANY", "ANY", "ANY")

# Set DAC0 and DAC1 to 4.1V
ljm.eWriteName(handle, "DAC0", 4.1)
ljm.eWriteName(handle, "DAC1", 4.1)

# Set negative channels for AIN6 and AIN8
ljm.eWriteName(handle, "AIN6_NEGATIVE_CH", 7)
ljm.eWriteName(handle, "AIN8_NEGATIVE_CH", 9)

# Assuming sensitivity of load cell is 0.02mV/V and excitation voltage is 5V
sensitivity = 0.02  # mV/V
excitation_voltage = 5.0  # V

# Take the tare weight
tare_weight1 = ljm.eReadName(handle, "AIN6")
tare_weight2 = ljm.eReadName(handle, "AIN8")

try:
    while True:
        # Read differential voltage from AIN6 (with reference to AIN10) and AIN8 (with reference to AIN11)
        voltage1 = ljm.eReadName(handle, "AIN6") - tare_weight1
        voltage2 = ljm.eReadName(handle, "AIN8") - tare_weight2

        excitation_voltage1 = ljm.eReadName(handle, "AIN10")
        excitation_voltage2 = ljm.eReadName(handle, "AIN11")

        # Calculate weight from voltage
        # Note: The weight value will depend on the exact load cell you're using
        # Here, we're assuming it's linear and the output is in pounds
        weight1 = (voltage1 / (sensitivity / 1000)) / excitation_voltage1
        weight2 = (voltage2 / (sensitivity / 1000)) / excitation_voltage2

        # Print only if weight is positive
        if weight1 >= 0:
            print("Weight Reading 1: ", weight1, " lbs")
        if weight2 >= 0:
            print("Weight Reading 2: ", weight2, " lbs")

        time.sleep(1)  # sleep for 1 second before the next reading
except KeyboardInterrupt:
    # User has pressed Ctrl+C, close the handle and exit
    print("Stopping...")
finally:
    # Close the device
    ljm.close(handle)
