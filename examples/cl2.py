import machine
import badger2040
import utime
from pcf85063a import PCF85063A

# Create Badger2040 instance
display = badger2040.Badger2040()

# Create Pico's RTC instance
rtc = machine.RTC()

# Create PCF85063A RTC instance
i2c = machine.I2C(0, scl=machine.Pin(5), sda=machine.Pin(4))
rtc_pcf85063a = PCF85063A(i2c)

# Clear screen
display.set_pen(15)
display.clear()
display.set_pen(1)

# Display system's time
display.text(f"system_time: {utime.localtime()}", 10, 0, 1)
display.update()
utime.sleep(0.02)

# Display Pico's RTC
display.set_pen(15)
display.clear()
display.set_pen(1)
display.text(f"pico_RTC: {rtc.datetime()}", 10, 0, 1)
display.update()
utime.sleep(0.02)

# Display PCF85063A's RTC
display.set_pen(15)
display.clear()
display.set_pen(1)
display.text(f"PCF_RTC: {rtc_pcf85063a.datetime()}", 10, 0, 1)
display.update()
utime.sleep(0.02)

while True:
    display.keepalive()
    display.halt()