import utime
import time
from machine import Pin, I2C
import ahtx0
import badger2040
from badger2040 import WIDTH, HEIGHT
import os
# Display Setup
display = badger2040.Badger2040()
display.set_update_speed(2)
display.set_thickness(4)


# Define a function that clears the screen and prints a header row
def clear():
    display.set_pen(15)
    display.clear()
    display.set_pen(0)
    display.set_font("bitmap8")
    display.set_pen(0)
    display.rectangle(0, 0, WIDTH, 10)
    display.rectangle(0, HEIGHT-10, WIDTH, HEIGHT-10)
    display.set_pen(15)
    display.text("Badger App provisioning", 10, 1, WIDTH, 0.6)
    display.set_pen(0)

def get_iso_timestamp():
    now = utime.localtime()
    iso_timestamp = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(
        now[0], now[1], now[2], now[3], now[4], now[5]
    )
    return iso_timestamp



# Define the chart area
chart_width = 200
chart_height = 80  # Fixed chart height of 80 pixels
chart_origin_x = int(0.5 * (WIDTH - chart_width))
chart_origin_y = int(0.5 * (HEIGHT - chart_height))


# Check if the directory exists, and create it if it doesn't
try:
    os.mkdir("data")
except OSError as e:
    if e.args[0] == 17:  # EEXIST - Directory already exists
        pass
    else:
        raise  # Raise the exception for other errors

    
    
# Define the path to the CSV file
csv_file_path = "data/logged_data.csv"




temperature_values = []
humidity_values = []

y_scale = 40  # Initial y-axis scale (0 to 80)
measurement_count = 0

try:
    while True:
        
        # Initialize I2C
        i2c = I2C(id=0, scl=Pin(5), sda=Pin(4))

        # Create the sensor object using I2C
        sensor = ahtx0.AHT20(i2c)
        # Read temperature from the sensor
       # Read temperature from the sensor
        temperature = sensor.temperature
        humidity = sensor.relative_humidity

        # Get the current timestamp in ISO format
        timestamp = get_iso_timestamp()

        # Append the measurement to the CSV file
        with open(csv_file_path, "a") as csv_file:
            csv_file.write("{}, {:.2f}, {:.2f}\n".format(timestamp, temperature, humidity))

        # Store the temperature and humidity value
        temperature_values.append(temperature)
        humidity_values.append(humidity)

        measurement_count += 1

        # Check button UP state
        if display.pressed(badger2040.BUTTON_UP):
            if y_scale == 80:
                y_scale = 60
            elif y_scale == 60:
                y_scale = 50
            elif y_scale == 50:
                y_scale = 40
            else:
                y_scale = 80
            print("Changed y_scale to:", y_scale)
            utime.sleep_ms(200)  # Debounce

        # Clear the display
        clear()

        # Draw the axes
        display.set_pen(0)
        display.line(chart_origin_x, chart_origin_y + chart_height, chart_origin_x + chart_width, chart_origin_y + chart_height,2)  # X-axis
        display.line(chart_origin_x, chart_origin_y, chart_origin_x, chart_origin_y + chart_height,2)  # Y-axis

        # Draw tickmarks and reference values on the y-axis
        for i in range(0, y_scale + 1, 10):
            tick_y = chart_origin_y + chart_height - int(i * chart_height / y_scale)
            display.set_pen(0)
            display.line(chart_origin_x - 3, tick_y, chart_origin_x + 3, tick_y)
            display.text("{}".format(i), chart_origin_x - 25, tick_y - 4, WIDTH, 0.5)
                
        # Draw axis labels
        display.text("Time", chart_origin_x + chart_width - 25, chart_origin_y + chart_height + 10, WIDTH, 0.5)
        #display.text("Temp", chart_origin_x - 20, chart_origin_y - 5, WIDTH, 0.5)

        # Draw the temperature data as lines
        for i in range(1, len(temperature_values)):
            x1 = chart_origin_x + int((i - 1) * chart_width / (len(temperature_values) - 1))
            x2 = chart_origin_x + int(i * chart_width / (len(temperature_values) - 1))
       # Draw the humidity data as lines
        for i in range(1, len(humidity_values)):
            x1 = chart_origin_x + int((i - 1) * chart_width / (len(humidity_values) - 1))
            x2 = chart_origin_x + int(i * chart_width / (len(humidity_values) - 1))
    
            y1_hum = chart_origin_y + chart_height - int((humidity_values[i - 1] * (chart_height / y_scale)))
            y2_hum = chart_origin_y + chart_height - int((humidity_values[i] * (chart_height / y_scale)))
    
            display.set_pen(7)  # Using blue for humidity
            display.line(x1, y1_hum, x2, y2_hum, 2)
     
            # Calculate the y-coordinate for the trace line
            y1 = chart_origin_y + chart_height - int((temperature_values[i - 1] * (chart_height / y_scale)))
            y2 = chart_origin_y + chart_height - int((temperature_values[i] * (chart_height / y_scale)))
            
            display.set_pen(0)
            display.line(x1, y1, x2, y2,2)

        # Calculate and display the average temperature
        if temperature_values:
            average_temp = sum(temperature_values) / len(temperature_values)
            average_humidity = sum(humidity_values) / len(humidity_values)

            display.set_pen(15)  # Pen color 0 is black
            display.text("Avg: {:.2f}°C".format(average_temp), 150, HEIGHT-9, WIDTH, 0.6)
            display.text("Current: {:.2f}°C".format(temperature), 150, 1, WIDTH, 0.6)  # Print current temperature
            display.text("| Avg: {:.2f}%RH".format(average_humidity), 240, HEIGHT-9, WIDTH, 0.6)
            display.text("Current: {:.2f}%RH".format(humidity), 240, 1, WIDTH, 0.6)
            print(f"Average temperature: {average_temp} | Current temperature: {temperature}")

        display.update()

        # Reset temperature_values list after 200 measurements
        if measurement_count == 200:
            temperature_values = []
            measurement_count = 0

        # Sleep for a while before the next observation
        utime.sleep(10)  # Adjust the sleep duration as needed

except KeyboardInterrupt:
    pass

