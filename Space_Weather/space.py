# This example grabs current weather details from Open Meteo and displays them on Badger 2040 W.
# Find out more about the Open Meteo API at https://open-meteo.com

import badger2040
from badger2040 import WIDTH
import urequests
import jpegdec
import machine

rtc = machine.RTC()

# Set display parameters
WIDTH = badger2040.WIDTH
HEIGHT = badger2040.HEIGHT

# Set your latitude/longitude here (find yours by right clicking in Google Maps!)
LAT = 63.38609085276884
LNG = -1.4239983439328177
TIMEZONE = "auto"  # determines time zone from lat/long

URL = "http://api.open-meteo.com/v1/forecast?latitude=" + str(LAT) + "&longitude=" + str(LNG) + "&current_weather=true&daily=weathercode,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,precipitation_sum,precipitation_probability_max,winddirection_10m_dominant&timezone=" + TIMEZONE

# Declare cleaned_lines as a global variable to store the extracted data
cleaned_lines = []

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


def get_solar_weather():

    global cleaned_lines  # Use the global cleaned_lines variable to store the extracted data

    global source, updated, solarflux, aindex, kindex, kindexnt, xray, sunspots, heliumline, protonflux, electonflux, aurora, normalization, latdegree, solarwind, magneticfield, geomagfield, signalnoise,fof2,muffactor, muf

    solar_url = "https://www.hamqsl.com/solarxml.php"

    # Display Setup
    display = badger2040.Badger2040()

    display.led(128)
    display.set_update_speed(2)

    jpeg = jpegdec.JPEG(display.display)

    # Make a GET request to the URL using urequests
    response = urequests.get(solar_url)

    # Check if the request was successful
    if response.status_code == 200:
        # Get the content as a string
        xml_content = response.content.decode('utf-8')

        # Manually extract data
        source = extract_element(xml_content, "source")
        updated = extract_element(xml_content, "updated")
        solarflux = extract_element(xml_content, "solarflux")
        aindex = extract_element(xml_content, "aindex")
        kindex = extract_element(xml_content, "kindex")
        kindexnt = extract_element(xml_content, "kindexnt")
        xray = extract_element(xml_content, "xray")
        sunspots = extract_element(xml_content, "sunspots")
        heliumline = extract_element(xml_content, "heliumline")
        protonflux = extract_element(xml_content, "protonflux")
        electonflux = extract_element(xml_content, "electonflux")
        aurora = extract_element(xml_content, "aurora")
        normalization = extract_element(xml_content, "normalization")
        latdegree = extract_element(xml_content, "latdegree")
        solarwind = extract_element(xml_content, "solarwind")
        magneticfield = extract_element(xml_content, "magneticfield")
        geomagfield = extract_element(xml_content, "geomagfield")
        signalnoise = extract_element(xml_content, "signalnoise")
        fof2 = extract_element(xml_content, "fof2")
        muffactor = extract_element(xml_content, "muffactor")
        muf = extract_element(xml_content, "muf")
        
        print("source:", source)
        print("updated:", updated)
        print("solarflux:", solarflux)
        print("aindex:", aindex)
        print("kindex:", kindex)
        print("kindexnt:", kindexnt)
        print("xray:", xray)
        print("sunspots:", sunspots)
        print("heliumline:", heliumline)
        print("protonflux:", protonflux)
        print("electonflux:", electonflux)
        print("aurora:", aurora)
        print("normalization:", normalization)
        print("latdegree:", latdegree)
        print("solarwind:", solarwind)
        print("magneticfield:", magneticfield)
        print("geomagfield:", geomagfield)
        print("signalnoise:", signalnoise)
        print("fof2:", fof2)
        print("muffactor:", muffactor)
        print("muf:", muf)
        
        
        # Extract the contents of the calculatedconditions node
        start_index = xml_content.find("<calculatedconditions>")
        end_index = xml_content.find("</calculatedconditions>") + len("</calculatedconditions>")
        calculated_conditions = xml_content[start_index:end_index]

        # Process the calculated_conditions data
        lines = calculated_conditions.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip().startswith("<band name="):
                line = line.replace('<band name="', '').replace('" time="', ' ').replace('">', ' : ').replace('</band>', '')
                cleaned_lines.append(line)


        for line in cleaned_lines:
            print(line)
        

    else:
        print("Error:", response.status_code)

# define function to extract elements of xml data
def extract_element(content, element_name):
    start_tag = f"<{element_name}>"
    end_tag = f"</{element_name}>"
    start_index = content.find(start_tag)
    end_index = content.find(end_tag)
    if start_index != -1 and end_index != -1:
        element_value = content[start_index + len(start_tag):end_index]
        return element_value
    return None

def calculate_bearing(d):
    # calculates a compass direction from the wind direction in degrees
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ix = round(d / (360. / len(dirs)))
    return dirs[ix % len(dirs)]


def draw_page():
    # Clear the display
    global cleaned_lines  # Use the global cleaned_lines variable to display the extracted data
    print(f"cleaned lines {cleaned_lines}")
    display.set_pen(15)
    display.clear()
    display.set_pen(0)

    # Draw box around display
    display.line(2,0,2,HEIGHT-1,2)
    display.line(WIDTH-1,0,WIDTH-1,HEIGHT-1,2)
    display.line(2,HEIGHT-1,WIDTH-1,HEIGHT-1,2)

    # Draw divider lines vertical
    display.line(105,10,105,HEIGHT,1)
    display.line(245,10,245,40,1)
    display.line(190,40,190,HEIGHT,1)

    # Draw divider lines horizontal
    display.line(190,40,WIDTH,40,1)
    
    # Draw the page header
    display.set_font("bitmap8")
    display.set_pen(0)
    display.rectangle(0, 0, WIDTH, 10)
    display.set_pen(15)
    display.text("Current Space Weather", 10, 1, WIDTH, 0.6) # parameters are left padding, top padding, width of screen area, font size
    display.set_pen(0)

    display.set_font("bitmap8")

    if temperature is not None:
        # Choose an appropriate icon based on the weather code
        # Weather codes from https://open-meteo.com/en/docs
        # Weather icons from https://fontawesome.com/
        if weathercode in [71, 73, 75, 77, 85, 86]:  # codes for snow
            jpeg.open_file("/icons/icon-snow.jpg")
        elif weathercode in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:  # codes for rain
            jpeg.open_file("/icons/icon-rain.jpg")
        elif weathercode in [1, 2, 3, 45, 48]:  # codes for cloud
            jpeg.open_file("/icons/icon-cloud.jpg")
        elif weathercode in [0]:  # codes for sun
            jpeg.open_file("/icons/icon-sun.jpg")
        elif weathercode in [95, 96, 99]:  # codes for storm
            jpeg.open_file("/icons/icon-storm.jpg")
        jpeg.decode(260,5, jpegdec.JPEG_SCALE_HALF)

        # show current temperature, with highs and lows
        display.set_pen(0)
        display.text(f"{temperature}°C  ", 110, 95, WIDTH - 50, 2)
        display.text(f"{apparent_temperature_min[1]}°C, {apparent_temperature_max[1]}°C", 110, 115, WIDTH - 50, 1)
   
        # Display each line with incremented horizontal position
        x_position = 190  # Initial x position
        y_position = 45  # y position for displaying cleaned lines
        for line in cleaned_lines:
            display.text(line, x_position, y_position, WIDTH, 0.6)
            y_position += 10  # Increment the y position for the next line

        

#  display solar weather data

        display.text(f"Solar Flux  : {solarflux}", 10, 15, WIDTH - 105, 1.5)
        display.text(f"A index : {aindex}", 110, 45, WIDTH - 105, 1.5)
        display.text(f"K index : {kindex}", 110, 35, WIDTH - 105, 1.5)
        display.text(f"X-ray : {xray}", 10, 55, WIDTH - 105, 1.5)
        display.text(f"Sunspots : {sunspots}", 10, 25, WIDTH - 105, 1.5)
        display.text(f"Helium Line : {heliumline}", 10, 65, WIDTH - 105, 1.5)
        display.text(f"Proton Flux : {protonflux}", 10, 75, WIDTH - 105, 1.5)
        display.text(f"Electron Flux : {electonflux}", 10, 85, WIDTH - 105, 1.5)
        display.text(f"Aurora : {aurora}", 10, 95, WIDTH - 105, 1.5)
        display.text(f"Normalisation : {normalization}", 10, 105, WIDTH - 105, 1.5)
        display.text(f"Lat Degree : {latdegree}", 10, 115, WIDTH - 105, 1.5)

        display.text(f"Magnetic Field : {magneticfield}", 110, 25, WIDTH - 105, 1.5)
        display.text(f"Solar Wind : {solarwind}", 10, 35, WIDTH - 105, 1.5)
        display.text(f"Geomagnetic Field : {geomagfield}", 110, 15, WIDTH - 105, 1.5)
        display.text(f"Signal Noise : {signalnoise}", 10, 45, WIDTH - 105, 1.5)
        display.text(f"FOF-2 : {fof2}", 110, 55, WIDTH - 105, 1.5)
        display.text(f"MUF Factor : {muffactor}", 110, 65, WIDTH - 105, 1.5)
        display.text(f"MUF : {muf}", 110, 75, WIDTH - 105, 1.5)

# show date and time

        display.set_pen(15)
#        display.text(f"{date}", 120,1 , WIDTH - 105, 1)
        display.text(f"{updated}", 120,1 , WIDTH - 105, 1)

    else:
        display.set_pen(0)
        display.rectangle(0, 60, WIDTH, 25)
        display.set_pen(15)
        display.text("Unable to display weather! Check your network settings in WIFI_CONFIG.py", 5, 65, WIDTH, 1)

    display.update()

# Connects to the wireless network. Ensure you have entered your details in WIFI_CONFIG.py :).
print("connecting")
display.connect()

get_data()
get_solar_weather()
draw_page()

# Call halt in a loop, on battery this switches off power.
# On USB, the app will exit when A+C is pressed because the launcher picks that up.
while True:
    badger2040.sleep_for(30)
    get_data()
    get_solar_weather()
    draw_page()


