import labjack.ljm as ljm

def set_fio0_high(handle):
    # Define the FIO addresses
    FIO0_ADDRESS = ljm.nameToAddress("FIO0")
    FIO1_ADDRESS = ljm.nameToAddress("FIO1")
    FIO2_ADDRESS = ljm.nameToAddress("FIO2")
    FIO3_ADDRESS = ljm.nameToAddress("FIO3")
    FIO4_ADDRESS = ljm.nameToAddress("FIO4")
    FIO5_ADDRESS = ljm.nameToAddress("FIO5")

    print("Writing high to FIO1 pin...")
    # Write high to the FIO0 pin
    ljm.eWriteName(handle, "FIO0", 1)
    ljm.eWriteName(handle, "FIO1", 1)
    ljm.eWriteName(handle, "FIO2", 1)
    ljm.eWriteName(handle, "FIO3", 0)
    ljm.eWriteName(handle, "FIO4", 0)
    ljm.eWriteName(handle, "FIO5", 0)

# Open the LabJack
print("Opening LabJack...")
handle = ljm.openS("ANY", "ANY", "ANY")

# Set FIO0 high
set_fio0_high(handle)

# Close the LabJack
print("Closing LabJack...")
ljm.close(handle)
