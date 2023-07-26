# badger2040w_code

I'm tinkering around with a badger2040w

**Clock_Stuff** contains a couple of scripts which explore how the RTC functions

It’s been unclear to me which of the various ways to call the time are actually calling to the clock which stays active on battery power when unplugged from the USB cable.

To call the time, I’ve typically used machine.RTC().datetime() and utime.localtime(), but neither of these seems to persist after the USB connection breaks or after the current script goes on to halt.

A bit of google work identified that I may need to access the pcf85063a rtc directly on the RPI2040W chip.
To explore this I made two separate scripts

cl1.py connects to wifi and uses ntptime to synchronise the clocks on the badger2040w.
It then calls machine.RTC().datetime(), utime.localtime() and the time on the pcf85063a rtc PCF85063A(i2c).datetime() sequentially. It displays the time on each clock on the screen of the badger.

Starting with the badger2040W disconnected, I attach a battery and run the cl1.py script.

![img/clk1.png]()


