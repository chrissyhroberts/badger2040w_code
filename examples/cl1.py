import machine
import badger2040
import time
import utime
import ntptime
from pcf85063a import PCF85063A
import badger_os

badger = badger2040.Badger2040()

badger.set_pen(15)
badger.clear()
badger.set_pen(1)

badger.connect()

if badger.isconnected():
    # Synchronize with the NTP server to get the current time
    ntptime.settime()


badger.set_pen(15)
badger.clear()
badger.set_pen(1)
badger.update()
time.sleep(0.05)

# Set the time on the Pico's onboard RTC
def set_pico_time():
    rtc = machine.RTC()
    now = utime.localtime()
    rtc.datetime((now[0], now[1], now[2], now[6], now[3], now[4], now[5], 0))

# Set the time on the external PCF85063A RTC
def set_pcf85063a_time():
    now = utime.localtime()
    i2c = machine.I2C(0, scl=machine.Pin(5), sda=machine.Pin(4))
    rtc_pcf85063a = PCF85063A(i2c)
    rtc_pcf85063a.datetime(now)

# Set the time on the Pico's onboard RTC
set_pico_time()

# Set the time on the external PCF85063A RTC
set_pcf85063a_time()

# Get the time after setting the RTCs

badger.text(f"Pico_RTC: {ut}", 80, 0, 1)
badger.text(f"PCF_RTC: {ut2}", 200, 0, 1)
badger.update()
time.sleep(0.05)

print("Pico RTC:", utime.localtime())
print("PCF85063A RTC:", str(machine.RTC().datetime()))
while True:
    badger.keepalive()
    badger.halt()

