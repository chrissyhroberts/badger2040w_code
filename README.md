# badger2040w_code

I'm tinkering around with a badger2040w

## 3d_print_case

This is an openscad model and STL file for a really simple backplate for the badger2040W. You can screw your badger on to this with some small screws. It has a space for the USB socket and also ample room in the back for a li-on battery pack. I used a 1200 mAh PKCELL from Pimoroni. 


## Clock_Stuff

contains a couple of scripts which explore how the RTC functions

It’s been unclear to me which of the various ways to call the time are actually calling to the clock which stays active on battery power when unplugged from the USB cable.

To call the time, I’ve typically used machine.RTC().datetime() and utime.localtime(), but neither of these seems to persist after the USB connection breaks or after the current script goes on to halt.

A bit of google work identified that I may need to access the pcf85063a rtc directly on the RPI2040W chip.
To explore this I made two separate scripts

cl1.py connects to wifi and uses ntptime to synchronise the clocks on the badger2040w.
It then calls machine.RTC().datetime(), utime.localtime() and the time on the pcf85063a rtc PCF85063A(i2c).datetime() sequentially. It displays the time on each clock on the screen of the badger.

Starting with the badger2040W disconnected, I attach a battery and run the cl1.py script.

![/img/clk1.png](/img/clk1.png)

In this image you can see that all three clock interfaces are null, having been reset when the battery was disconnected.

I then killed the cl1.py script and ran cl2.py

The big difference here is that cl2.py doesn’t connect to ntptime. It just asks for the time from each of the three clock systems.

Here’s what it returns

![/img/clk2.png](/img/clk2.png)

As you can see, the only method of the three which actually keeps the time inbetween two different scripts being run on the badger2040W is the pcf85063a method.

My take home from this is that you should use the pcf85063a to establish any rtc link to the badger.

The minimal code needed to pull time from the RTC is

```
from pcf85063a import PCF85063A
# Create PCF85063A RTC instance
i2c = machine.I2C(0, scl=machine.Pin(5), sda=machine.Pin(4))
rtc_pcf85063a = PCF85063A(i2c)
print(rtc_pcf85063a.datetime())
```

I’ve tested that this method works both for a li-on 3.7 V battery plugged in to the batt socket on the back, and also for a badger running on a USB cable connected to a mobile phone charger pack. The RTC keeps running on both, even though I had to push the button on the charger pack to start pushing buttons. It seems that the buttons on the badger can’t trigger the activation of the generic mobile charger, but the RTC can keep running.

## Weather 

This is an updated version of the example weather app for the Badger2040W. I fiddled around with the calls to the open-meteo API, adding a bunch of new functions and data outputs. This now adds info about pollen levels, particulates in the air, rainfall level and probability, UV index, winds, sunrise and sunset. It also adds a 2 day forecast. 

![/img/weather.png](/img/weather.png)