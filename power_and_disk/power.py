import machine
import badger2040
import badger_os #https://github.com/pimoroni/badger2040/blob/main/firmware/PIMORONI_BADGER2040/lib/badger_os.py
import utime
import network
from machine import ADC, Pin

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
    
def get_battery_info(full_battery=3.7, empty_battery=2.8):
    # Pico W voltage read function by darconeous on reddit: 
    # https://www.reddit.com/r/raspberrypipico/comments/xalach/comment/ipigfzu/

    # Initialize Variables
    conversion_factor = 3 * full_battery / 65535
    voltage=0
    percentage=0
    is_charge=False
    error_message=None
    
    # prep the network
    wlan = network.WLAN(network.STA_IF)
    wlan_active = wlan.active()

    try:
        # Don't use the WLAN chip for a moment.
        wlan.active(False)

        # Make sure pin 25 is high.
        Pin(25, mode=Pin.OUT, pull=Pin.PULL_DOWN).high()
        
        # Reconfigure pin 29 as an input.
        Pin(29, Pin.IN)
        
        vsys = ADC(29)
        
        # get the voltage
        voltage=vsys.read_u16() * conversion_factor
        
        # figure out the percentage of available battery
        if voltage:
            try:
                percentage = 100 * ((voltage - empty_battery) / (full_battery - empty_battery))
            except:
                percentage = 0
                
            if percentage > 100:
                percentage = 100.00
            elif percentage < 0:
                percentage = 0
                
            charging = Pin('WL_GPIO2', Pin.IN)  # reading this pin tells us whether or not USB power is connected
            is_charge = charging.value()
        
    except Exception as e:
        error_message=str(e)

    finally:
        # Restore the pin state and possibly reactivate WLAN
        Pin(29, Pin.ALT, pull=Pin.PULL_DOWN, alt=7)
        wlan.active(wlan_active)
    
    return {"error":error_message, "voltage":voltage, "percentage":percentage, "full_battery":full_battery, "empty_battery":empty_battery, "is_charge":is_charge}


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
#
# Initialise the badger screen
display = badger2040.Badger2040()
WIDTH = badger2040.WIDTH # 296
HEIGHT = badger2040.HEIGHT # 128

batlevel = get_battery_info()
print(f"battery: {batlevel}%")
diskusage = badger_os.get_disk_usage()
print(f"diskusage: {diskusage}%")
staterunning = badger_os.state_running()
print(f"staterunning: {staterunning}%")
print(get_battery_info())
print(f"Battery 2 :  {get_battery_info()}")
print(batlevel['voltage'])
# Get the CPU frequency
cpu_freq = round(machine.freq()/1000000,0)

cls()
# Draw a grid
# Vertical lines
display.line(85, 0, 85, 70, 3)
display.line(50, 70, 50, 150, 3)
display.line(200, 70, 200, 150, 3)

display.line(0, 40, 300, 40, 3)
display.line(0, 70, 300, 70, 3)

# Add voltage across various pins
display.text(f"Voltage ", 0, 15,WIDTH,2)
display.text(f"26: {pin26} V | 27: {pin27} V", 95, 5,WIDTH,2)
display.text(f"28: {pin28} V | 29: {pin28} V", 95, 20,WIDTH,2)

# Show the battery state
display.text(f"Battery ",0, 50,WIDTH,2)
display.text(f"{round(batlevel['voltage'],2)}V | {round(batlevel['percentage'],2)}%",95, 50,WIDTH,2)
    
# Show the disk space used/available    
display.text(f"Disk", 0, 90,WIDTH,2)
display.text(f" Total : {round(diskusage[0]/10000,2)}", 55, 75,WIDTH,2)
display.text(f" Used   : {round(diskusage[1],2)}", 55, 90,WIDTH,2)
display.text(f" Free   : {round(diskusage[2],2)}", 55, 105,WIDTH,2)
display.text(f" CPU", 205, 90,WIDTH,2)
display.text(f" {cpu_freq} MHz", 205, 110,WIDTH,2)

display.update()
#utime.sleep_ms(2000)
#badger_os.launch('launcher')

