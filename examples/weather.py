# This example grabs current weather details from Open Meteo and displays them on Badger 2040 W.
# Find out more about the Open Meteo API at https://open-meteo.com
#
#
# V3.0 changes
# Adds new method to prevent screenburn which inverts colours each time the screen refreshes
import badger2040
from badger2040 import WIDTH
import urequests
import jpegdec
import machine

rtc = machine.RTC()

# Set your latitude/longitude here (find yours by right clicking in Google Maps!)
LAT = 52.104
LNG = -0.0227
TIMEZONE = "auto"  # determines time zone from lat/long

URL = "https://api.open-meteo.com/v1/forecast?latitude=" + str(LAT) + "&longitude=" + str(LNG) + "&current_weather=true&daily=weathercode,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,precipitation_sum,precipitation_probability_max,winddirection_10m_dominant&timezone=" + TIMEZONE
URL2 = "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=" + str(LAT) + "&longitude=" + str(LNG) + "&hourly=pm10,pm2_5,uv_index,alder_pollen,birch_pollen,grass_pollen,mugwort_pollen,olive_pollen,ragweed_pollen"

# Define foreground and background variable for color mode
fg = 15  # Start with normal colors
bg = 0

# Display Setup
display = badger2040.Badger2040()


display.led(128)
display.set_update_speed(2)

jpeg = jpegdec.JPEG(display.display)



def get_data():
    global weathercode, temperature, windspeed, winddirection, date, time, day_weathercode, apparent_temperature_max, apparent_temperature_min, sunrise, sunset, precipitation_sum, precipitation_probability_max, winddirection_10m_dominant
    print(f"Requesting URL: {URL}")
    r = urequests.get(URL)
    # open the json data
    j = r.json()
    print("Data obtained!")
    print(j)

    # parse relevant data from JSON
    current = j["current_weather"]
    temperature = current["temperature"]
    windspeed = current["windspeed"]
    winddirection = calculate_bearing(current["winddirection"])
    weathercode = current["weathercode"]
    date, time = current["time"].split("T")

    daily = j["daily"]
    day_weathercode = daily["weathercode"]
    apparent_temperature_max = daily["apparent_temperature_max"]
    apparent_temperature_min = daily["apparent_temperature_min"]
    sunrise = daily["sunrise"]
    sunrise = sunrise[1]
    sunrise = sunrise.split("T")[1]
    sunset = daily["sunset"]
    sunset = sunset[1]
    sunset = sunset.split("T")[1]


    precipitation_sum =    daily["precipitation_sum"]
    precipitation_probability_max =    daily["precipitation_probability_max"]
    winddirection_10m_dominant =     daily["winddirection_10m_dominant"]
    winddirection_10m_dominant = calculate_bearing(winddirection_10m_dominant[1])
    r.close()

def get_data_airquality():
    global pm10, pm2_5, alder_pollen, uv_index, birch_pollen, grass_pollen, mugwort_pollen, olive_pollen, ragweed_pollen

    print(f"Requesting URL: {URL2}")
    r2 = urequests.get(URL2)

    # open the json data
    j2 = r2.json()
    print("Airquality Data obtained!")
    print(j2)

    # parse relevant data from json
    airquality = j2["hourly"]
    print("Air quality:", airquality)

    # If a key doesn't exist, it'll default to a list with a single None item
    pm10 = airquality.get("pm10", [None])[1]
    pm2_5 = airquality.get("pm2_5", [None])[1]

    # Ensure uv_index list has no None values before applying max
    uv_values = [val for val in airquality.get("uv_index", []) if val is not None]
    uv_index = max(uv_values) if uv_values else 'NA'

    alder_pollen = airquality.get("alder_pollen", [None])[1]
    birch_pollen = airquality.get("birch_pollen", [None])[1]
    grass_pollen = airquality.get("grass_pollen", [None])[1]
    mugwort_pollen = airquality.get("mugwort_pollen", [None])[1]
    olive_pollen = airquality.get("olive_pollen", [None])[1]
    ragweed_pollen = airquality.get("ragweed_pollen", [None])[1]

    print(f"{uv_index} UVIndex ")

    r2.close()


def calculate_bearing(d):
    # calculates a compass direction from the wind direction in degrees
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ix = round(d / (360. / len(dirs)))
    return dirs[ix % len(dirs)]


def draw_page(text_color, background_color):
    
    # Define the icon file names based on the text color for simplicity
    # Assuming white text (15) uses dark icons and black text (0) uses light icons
    icon_prefix = "_dark" if text_color == 15 else ""
    icon_snow = f"/icons/icon-snow{icon_prefix}.jpg"
    icon_rain = f"/icons/icon-rain{icon_prefix}.jpg"
    icon_cloud = f"/icons/icon-cloud{icon_prefix}.jpg"
    icon_sun = f"/icons/icon-sun{icon_prefix}.jpg"
    icon_storm = f"/icons/icon-storm{icon_prefix}.jpg"
    
    # Clear the display with the background color
    display.set_pen(background_color)
    display.clear()
    
    # Use the text color for drawing text and other elements
    display.set_pen(text_color)
    display.rectangle(0, 0, WIDTH, 10)
    display.set_pen(background_color)
    display.text("Weather @ The Moving Castle", 10, 1, WIDTH, 0.6) # parameters are left padding, top padding, width of screen area, font size
    display.set_pen(text_color)

    display.set_font("bitmap8")

    if temperature is not None:
        # Choose an appropriate icon based on the weather code
        # Weather codes from https://open-meteo.com/en/docs
        # Weather icons from https://fontawesome.com/
        if weathercode in [71, 73, 75, 77, 85, 86]:  # codes for snow
            jpeg.open_file(icon_snow)
        elif weathercode in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:  # codes for rain
            jpeg.open_file(icon_rain)
        elif weathercode in [1, 2, 3, 45, 48]:  # codes for cloud
            jpeg.open_file(icon_cloud)
        elif weathercode in [0]:  # codes for sun
            jpeg.open_file(icon_sun)
        elif weathercode in [95, 96, 99]:  # codes for storm
            jpeg.open_file(icon_storm)
            
        try:
            jpeg.decode(10,30, jpegdec.JPEG_SCALE_FULL)
        except Exception as e:
            print("Error opening or decoding JPEG:", e)

        # show current temperature, with highs and lows
        display.set_pen(text_color)
        display.text(f"{temperature}°C  ", 20, 95, WIDTH - 50, 2)
        display.text(f"{apparent_temperature_min[1]}°C, {apparent_temperature_max[1]}°C", 20, 115, WIDTH - 50, 1)

        # show prob and amount of rain today
        jpeg.open_file(icon_rain)
        jpeg.decode(100,20, jpegdec.JPEG_SCALE_HALF)
        display.set_pen(text_color)
        display.text(f"{precipitation_probability_max[1]}% ", 135, 25, WIDTH - 105, 2)
        display.text(f"{precipitation_sum[1]} mm ", 135, 45, WIDTH - 105, 1)
       
        
        
#        [{apparent_temperature_min[1]}°C, {apparent_temperature_max[1]}°C]
        # show five day high temperatures
        display.set_pen(text_color)
#        display.text(f"Forecast: {apparent_temperature_max[2]}°C | {apparent_temperature_max[3]}°C | {apparent_temperature_max[4]}°C | {apparent_temperature_max[5]}°C | {apparent_temperature_max[6]}°C", 10, 30, WIDTH - 50, 1)
        # show sunrise, sunset
        display.text(f"Wind : {windspeed} km/h {winddirection} | Prevailing : {winddirection_10m_dominant}", 100, 60, WIDTH - 105, 1.5)
        display.text(f"Sunrise : {sunrise} | Sunset : {sunset}", 100, 70, WIDTH - 105, 1.5)

# Show tomorrow's weather
        print("Daily weathercodes")
        print(day_weathercode)
        if day_weathercode[2] in [71, 73, 75, 77, 85, 86]:  # codes for snow
            jpeg.open_file(icon_snow)
        elif day_weathercode[2] in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:  # codes for rain
            jpeg.open_file(icon_rain)
        elif day_weathercode[2] in [1, 2, 3, 45, 48]:  # codes for cloud
            jpeg.open_file(icon_cloud)
        elif day_weathercode[2] in [0]:  # codes for sun
            jpeg.open_file(icon_sun)
        elif day_weathercode[2] in [95, 96, 99]:  # codes for storm
            jpeg.open_file(icon_storm)
        display.set_pen(text_color)
        display.text("+1 Day", 160, 110, WIDTH - 105, 1.5)
        jpeg.decode(190,90, jpegdec.JPEG_SCALE_HALF)

# Show day after tomorrow's weather

        if day_weathercode[3] in [71, 73, 75, 77, 85, 86]:  # codes for snow
            jpeg.open_file(icon_snow)
        elif day_weathercode[3] in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:  # codes for rain
            jpeg.open_file(icon_rain)
        elif day_weathercode[3] in [1, 2, 3, 45, 48]:  # codes for cloud
            jpeg.open_file(icon_cloud)
        elif day_weathercode[3] in [0]:  # codes for sun
            jpeg.open_file(icon_sun)
        elif day_weathercode[3] in [95, 96, 99]:  # codes for storm
            jpeg.open_file(icon_storm)
        display.set_pen(text_color)
        display.text("+2 Day", 230, 110, WIDTH - 105, 1.5)
        jpeg.decode(260,90, jpegdec.JPEG_SCALE_HALF)

#        display.text(f"Wind Direction: {winddirection}", int(WIDTH / 3), 68, WIDTH - 105, 2)
        display.set_pen(text_color)
        display.text(f"Updated {time}", 100, 90, WIDTH - 105, 1)
#  display pollen counts & particulate
        display.text(f"PM10  : {pm10}", 170, 15, WIDTH - 105, 1.5)
        display.text(f"Alder : {alder_pollen}", 170, 25, WIDTH - 105, 1.5)
        display.text(f"Grass : {grass_pollen}", 170, 35, WIDTH - 105, 1.5)
        display.text(f"Ragweed : {ragweed_pollen}", 170, 45, WIDTH - 105, 1.5)
        display.text(f"PM2.5 : {pm2_5}", 230, 15, WIDTH - 105, 1.5)
        display.text(f"Birch : {birch_pollen}", 230, 25, WIDTH - 105, 1.5)
        display.text(f"Mugwort : {mugwort_pollen}", 230, 35, WIDTH - 105, 1.5)

# show date

        display.text(f"{date}", 1, 15, WIDTH - 105, 2)
# show UV index
        display.text(f"Max UV Index : {uv_index}", 100, 80, WIDTH - 105, 1)
    else:
        display.set_pen(text_color)
        display.rectangle(0, 60, WIDTH, 25)
        display.set_pen(background_color)
        display.text("Unable to display weather! Check your network settings in WIFI_CONFIG.py", 5, 65, WIDTH, 1)

    display.update()

# Connects to the wireless network. Ensure you have entered your details in WIFI_CONFIG.py :).
print("connecting")
display.connect()

#get_data()
#get_data_airquality()
#draw_page(15, 0)
#print("UV")
#print (uv_index)

# Call halt in a loop, on battery this switches off power.
# On USB, the app will exit when A+C is pressed because the launcher picks that up.
while True:
    
    #Define the sleep interval between refreshes
    sleep_time = 60
    
    # do one cycle with dark mode colours
    print("sleeping")
    badger2040.sleep_for(sleep_time)  # Or whatever duration you need
    print("waking & printing dark mode")
    get_data()
    get_data_airquality()       
    draw_page(15, 0)

    # do one cycle with light mode colours
    print("sleeping")
    badger2040.sleep_for(sleep_time)  # Or whatever duration you need
    print("waking & printing light mode")
    get_data()
    get_data_airquality()       
    draw_page(0, 15)    





