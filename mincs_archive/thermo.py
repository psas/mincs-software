import time
import sys
from labjack import ljm

# Open first found LabJack
handle = ljm.open(ljm.constants.dtANY, ljm.constants.ctANY, "ANY")

try:
    # T-type thermocouple config
    ljm.eWriteName(handle, "AIN4_EF_INDEX", 24)
    ljm.eWriteName(handle, "AIN4_EF_CONFIG_A", 1)           # Output in degree C
    ljm.eWriteName(handle, "AIN4_EF_CONFIG_B", 60052)       # Using the internal temperature sensor for CJC
    ljm.eWriteName(handle, "AIN4_EF_CONFIG_D", 1)
    ljm.eWriteName(handle, "AIN4_EF_CONFIG_E", 0)
    ljm.eWriteName(handle, "AIN4_NEGATIVE_CH", 5)

    while True:
        # Check temperature on thermocouple
        tempC = ljm.eReadName(handle, "AIN4_EF_READ_A")
        print(f'Temperature: {tempC} \u00b0C')
        
        # Wait for 1 second
        time.sleep(1)
        
except KeyboardInterrupt:
    # User has pressed Ctrl+C, close the LabJack
    ljm.close(handle)
    sys.exit()
