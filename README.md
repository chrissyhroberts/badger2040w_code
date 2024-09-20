# Badger 2040W code resources

This repo consolidates a bunch of code for the Pimoroni Badger2040 and Badger2040W

NB : There's an issue with Mac version of Thonny which means it sometimes can't find the badger. Killing the internal library with `rm -rf ~/Library/Thonny` can fix this. 

## App provisioning [examples/apps.py](examples/apps.py) and [examples/icon-apps.jpg](examples/icon-apps.jpg) 

Using Thonny to copy your code and apps on to the badger2040W can be a bit of a pain. This functionality allows a user to provision a list of apps to the device remotely. The main function here is that you can write an app and stick it in an 'examples' folder on a github repo or other source. The 'apps' app then consults a json file which maintains a list of the apps that you currently want on your badger2040W. It downloads the apps from your repo, then restarts the launcher to update the badgeros homepage.

You'll need to make a new file `provisioning_manifest.json`.

The contents are two lists `folders_to_clean` and `files`

`folders_to_clean` tells the provisioning app to delete the contents of folders specified here. This has the effect of cleaning out things that are not on the list
`files` provides [a] the path (on github) and filename of files you want to add and [b] the target folder on the badger 2040W. 

```
{
  "folders_to_clean": ["examples", "icons","data"],
  "files": [
    { "path": "examples/apps.py",		"folder": "examples"},
    { "path": "examples/icon-apps.jpg",	"folder": "examples"},    
    { "path": "examples/weather.py",		"folder": "examples"},
    { "path": "examples/icon-weather.jpg",	"folder": "examples"},
    { "path": "examples/space.py",			"folder": "examples"},
    { "path": "examples/icon-space.jpg",   	"folder": "examples"},
    { "path": "examples/power.py",		    "folder": "examples"},
    { "path": "examples/icon-power.jpg",    "folder": "examples"},
    { "path": "data/data.csv",		    	"folder": "data"},
    { "path": "data/data2.csv",		    	"folder": "data"},
    { "path": "icons/icon-sun.jpg",		    "folder": "icons"},
    { "path": "icons/icon-snow.jpg",	    "folder": "icons"},
    { "path": "icons/icon-storm.jpg",       "folder": "icons"},
    { "path": "icons/icon-rain.jpg",       "folder": "icons"},
    { "path": "icons/icon-cloud.jpg",       "folder": "icons"}
  ]
}
```

Ensure that you always have the `apps.py` and `icon-apps.jpg` on this list, or you'll immediately lose the provisioning functionality

Don't forget to add an icon for each app in the `examples` folder, or the system will freeze. 

The first time you want to run the provisioning app, you'll need to manually install it with thonny. 
You'll also need the `WIFI_CONFIG.py` to be configured.

Finally, you'll need to set the target for the repo. 

Change the line `github_repo_url = "https://raw.githubusercontent.com/chrissyhroberts/badger2040w_code/main/"`
to match your own target. Put the `provisioning_manifest.json` file in the root of the repo. 


After the first install you won't _need_ Thonny anymore.

![/img/clk1.png](/img/apps_provision_01.jpg)
![/img/clk1.png](/img/apps_provision_02.jpg)




## [Charts](charts/heatmap.py)

These scripts add some basic data visualisation methods to the badger. These can be used in projects that perform data logging across time, or any context where a dataset is pulled from an onboard or remote data source. There's limits on how big a table can be ingested, which probably simply relate to (a) the limited storage capacity and (b) the available RAM.

![/img/clk1.png](/img/barchart.jpg)
![/img/clk1.png](/img/heatmap_matrix.jpg)
![/img/clk1.png](/img/heatmap_summary.jpg)

## [Clock_Stuff](Clock_Stuff)

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

## Dashboard Calendar, TOTP and Clock [examples/dash.py](examples/dash.py)

This pulls together some code from the clock and TOTP apps to build a simple dashboard. The main new feature here is the ability to read in a calendar .ics feed and to display current and next meetings, along with date, clock and current TOTP code. Refreshes every minute, so you might want to change to 30s if you want TOTPs showing correctly all the time. Pressing A will update TOTP, Pressing B updates both TOTP and Calendar events (it is consequentially slower to update) and button C puts the device to sleep or wakes it from sleep. 

There's built in colour switching between dark and light modes, which aims to minimise screen-burn, but my guess is that once you've used this dashboard for a while, you might well get ghosting thanks to the many refreshes you'll be doing. 

![/img/dash.jpeg](/img/dash.jpeg)


## Space Weather [examples/space.py](examples/space.py) and [examples/icon-space.jpg](examples/icon-space.jpg)

The space app adds functions to display a variety of data that can be useful to HAM radio / Amateur radio enthusiasts. 
The data that populate this app come from the excellent resources at at https://www.hamqsl.com/solarxml.php

**NOTE: Please respect the request of the maintainers of www.hamqsl.com that you don't put too much strain on their resource. Downloading data more than once an hour is pointless and could harm their ability to continue to provide the data. If you value this, please donate to Paul L Herrman (N0NBH) who maintains it : [Donate here via PayPal](https://www.paypal.com/donate?token=PGsbxxaNxFueJmdq1fgPek22o4yU0UR6tybC7O1mUM66rCnWMDxZjvQtmFIAISSAwA2GZXfBMNPVzMTY)**

**NOTE 2 : Because this project relies on the efforts and goodwill of the maintainers of www.hamqsl.com, the design of this app comes with a potential single point of failure (SPOF) risk. I don't know where the data really comes from and I'm sure that there's a more sustainable and lower risk route to getting this data through an API somewhere. If you know what the source is, then I'd appreciate it if you could share this info via the issues**

In order for the local weather to be properly displayed, you should change the latitude and longitude in the script to match your location. 

![/img/clk2.png](/img/space.jpeg)

## Temperature and Humidity Logger (AHT20 unit) [examples/weather.py](examples/logger.py) and [examples/icon-weather.jpg](examples/icon-logger.jpg) and [lib/ahtx0.py](lib/ahtx0.py)

The [AHT20](https://learn.adafruit.com/adafruit-aht20/overview) connects to the QWIIC socket on the badger2040W and provides a rough temperature and humidity measurement on a schedule of your choice. It is controlled through the i2c protocol using a [library obtained here](https://raw.githubusercontent.com/targetblank/micropython_ahtx0/master/ahtx0.py) and copied to the [lib](lib) folder of this repo. 

The logger has basic functions to (a) collect, (b) visualise and (c) store to file, a set of measurements from the AHT20. This provides a framework for other types of environmental sensor connected via QWIIC. 

![/img/logger_1.jpeg](/img/logger_1.jpeg)
![/img/logger_2.jpeg](/img/logger_2.jpeg)


## Terrestrial Weather [examples/weather.py](examples/weather.py) and [examples/icon-weather.jpg](examples/icon-weather.jpg)

This is an updated version of the example weather app for the Badger2040W. I fiddled around with the calls to the open-meteo API, adding a bunch of new functions and data outputs. This now adds info about pollen levels, particulates in the air, rainfall level and probability, UV index, winds, sunrise and sunset. It also adds a 2 day forecast. 

![/img/weather.png](/img/weather.png)

## TOTP Authenticator [examples/totp.py](examples/totp.py) and [examples/icon-totp.jpg](examples/icon-totp.jpg)

This app provides the functionality of a TOTP authenticator. It is tested against Google Authenticator and creates identical codes, on the same time step. 
When launched, the app connects to the web and synchronises the system clock via `ntptime` server. Currently unclear if it automatically handles timezones. I think so but will check after October 31^st^
To add you keys, you need to get the secret keys from your service provider and add them to the [data/totp_keys.json](data/totp_keys.json) file.
You should be able to add 30 keys to the same screen. Best to have this plugged in, as battery will drain faster with 30s updates.

![/img/authenticator.png](/img/authenticator.jpg)

A lot of the code comes from this project by Edd Mann [https://github.com/eddmann/pico-2fa-totp](https://github.com/eddmann/pico-2fa-totp)

## TOTP Authenticator 2 [examples/totp2.py](examples/totp2.py) and [examples/icon-totp2.jpg](examples/icon-totp2.jpg)

The exact same thing as totp, except it only updates the screen when you press a button.

## [3D Printable Badger2040 / Badger2040W case](3d_print_case)

This is an openscad model and STL file for a really simple backplate for the badger2040W. You can screw your badger on to this with some small screws. It has a space for the USB socket and also ample room in the back for a li-on battery pack. I used a 1200 mAh PKCELL from Pimoroni. 

![/img/3d_print_case.png](/img/3d_print_case.png)
![/img/3d_print_case_2.jpeg](/img/3d_print_case_2.jpeg)


## Support this project

If you would like to support this project, please feel free to pay what you want https://t.co/GpUNwewruR
