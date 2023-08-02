import machine
import badger2040
import badger_os #https://github.com/pimoroni/badger2040/blob/main/firmware/PIMORONI_BADGER2040/lib/badger_os.py
import utime

#####################################
# Define functions
#####################################

def voltogetter(pin):
    # Create an ADC object
    adc = machine.ADC(machine.Pin(pin))  # Replace 26 with the appropriate ADC pin number

    # Read the ADC raw value
    adc_value = adc.read_u16()

    # Get the reference voltage (assuming 3.3V)
    reference_voltage = 3.3

    # Convert ADC value to voltage
    voltage = adc_value / 65535 * reference_voltage
    return voltage

def cls():
    display.set_pen(15)
    display.clear()
    display.set_pen(1)
    display.update()

#####################################
# Find values
#####################################

# Get the voltage values for all pins first
pin26 = round(voltogetter(26),2)
pin27 = round(voltogetter(27),2)
pin28 = round(voltogetter(28),2)
pin29 = round(voltogetter(29),2)

# Clear the screen
print("clearing screen")

#####################################
# Display stats
#####################################

# Initialise the badger screen
display = badger2040.Badger2040()
WIDTH = badger2040.WIDTH # 296
HEIGHT = badger2040.HEIGHT # 128
display.rectangle(0, 60, WIDTH, 25)
display.set_font("bitmap8")

batlevel = badger_os.get_battery_level()
print(f"battery: {batlevel}%")
diskusage = badger_os.get_disk_usage()
print(f"diskusage: {diskusage}%")
staterunning = badger_os.state_running()
print(f"staterunning: {staterunning}%")

while True:

    cls()
    # Update all the text values using the stored voltage values
    display.text(f"Voltage (ADC) | 26: {pin26} V | 27: {pin27} V | 28: {pin28} V 28: {pin28} V", 10, 10,WIDTH,1)
    display.text(f"Battery : {batlevel}%", 10, 30,WIDTH,1)
    display.text(f"disk | Total : {round(diskusage[0],2)} | Used : {round(diskusage[1],2)} | Free : {round(diskusage[2],2)}", 10, 50,WIDTH,1)
    display.text(f"Pin 28: {pin28} V", 10, 70,WIDTH,1)
    display.text(f"Pin 29: {pin29} V", 10, 90,WIDTH,1)
    
    display.update()
    badger2040.sleep_for(1)

# Add a short delay (e.g., 500 milliseconds)
# Update the display
