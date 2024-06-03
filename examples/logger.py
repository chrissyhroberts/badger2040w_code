import utime
import time
from machine import Pin, I2C
import machine
import ahtx0
import badger2040
from badger2040 import WIDTH, HEIGHT
import os
from pcf85063a import PCF85063A

# Display Setup
display = badger2040.Badger2040()
display.set_update_speed(2)
display.set_thickness(4)

# Create PCF85063A RTC instance
i2c = machine.I2C(0, scl=machine.Pin(5), sda=machine.Pin(4))
rtc_pcf85063a = PCF85063A(i2c)

def clear():
    display.set_pen(15)
    display.clear()
    display.set_pen(0)
    display.set_font("bitmap8")
    display.set_pen(0)
    display.rectangle(0, 0, WIDTH, 10)
    display.rectangle(0, HEIGHT-10, WIDTH, HEIGHT-10)
    display.set_pen(15)
    display.text("Temp/Humidity Logger", 10, 1, WIDTH, 0.6)
    display.set_pen(0)

def get_iso_timestamp():
    now = rtc_pcf85063a.datetime()
    iso_timestamp = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(
        now[0], now[1], now[2], now[3], now[4], now[5]
    )
    print(iso_timestamp)
    return iso_timestamp

def round_temperature_and_humidity(temperature, humidity):
    return round(temperature, 2), round(humidity, 2)

def read_last_n_entries_from_csv(n=50):
    timestamp_values = []
    temperature_values = []
    humidity_values = []

    try:
        with open(csv_file_path, "r") as csv_file:
            csv_file.seek(0, 2)
            lines = []
            while len(lines) < n:
                try:
                    csv_file.seek(-2900, 1)
                    chunk = csv_file.read(2900)
                    lines = chunk.splitlines() + lines
                    if csv_file.tell() == 0:
                        break
                except OSError:
                    break
            lines = lines[-n:]
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) == 3:
                    timestamp, temperature, humidity = parts
                    try:
                        timestamp_values.append(timestamp)
                        temperature_values.append(float(temperature))
                        humidity_values.append(float(humidity))
                    except ValueError:
                        continue
    except OSError as e:
        if e.args[0] != 2:
            raise
    return timestamp_values, temperature_values, humidity_values

chart_width = 200
chart_height = 80
chart_origin_x = int(0.5 * (WIDTH - chart_width))
chart_origin_y = int(0.5 * (HEIGHT - chart_height))
legend_origin_x = chart_origin_x + chart_width + 20
legend_origin_y = chart_origin_y

try:
    os.mkdir("data")
except OSError as e:
    if e.args[0] != 17:
        raise

csv_file_path = "data/logged_data.csv"

y_scale = 100
measurement_count = 0

i2c = machine.I2C(0, scl=machine.Pin(5), sda=machine.Pin(4))
rtc_pcf85063a = PCF85063A(i2c)
print(f"PCF_RTC: {rtc_pcf85063a.datetime()}")

try:
    while True:
        i2c = I2C(id=0, scl=Pin(5), sda=Pin(4))
        sensor = ahtx0.AHT20(i2c)
        temperature = sensor.temperature
        humidity = sensor.relative_humidity
        timestamp = get_iso_timestamp()

        with open(csv_file_path, "a") as csv_file:
            csv_file.write("{}, {:.2f}, {:.2f}\n".format(timestamp, temperature, humidity))

        _, temperature_values, humidity_values = read_last_n_entries_from_csv()

        print(f"Temperature Values: {temperature_values}")
        print(f"Humidity Values: {humidity_values}")

        measurement_count += 1

        if display.pressed(badger2040.BUTTON_UP):
            if y_scale == 100:
                y_scale = 80
            elif y_scale == 80:
                y_scale = 60
            elif y_scale == 60:
                y_scale = 50
            elif y_scale == 50:
                y_scale = 40
            else:
                y_scale = 80
            print("Changed y_scale to:", y_scale)
            utime.sleep_ms(200)

        clear()

        display.set_pen(0)
        display.line(chart_origin_x, chart_origin_y + chart_height, chart_origin_x + chart_width, chart_origin_y + chart_height, 2)
        display.line(chart_origin_x, chart_origin_y, chart_origin_x, chart_origin_y + chart_height, 2)

        for i in range(0, y_scale + 1, 10):
            tick_y = chart_origin_y + chart_height - int(i * chart_height / y_scale)
            display.set_pen(0)
            display.line(chart_origin_x - 3, tick_y, chart_origin_x + 3, tick_y)
            display.text("{}".format(i), chart_origin_x - 25, tick_y - 4, WIDTH, 0.5)

        display.set_pen(0)
        display.line(legend_origin_x-5, legend_origin_y, legend_origin_x + 15, legend_origin_y, 2)
        display.text("Temp", legend_origin_x - 5, legend_origin_y + 5, WIDTH, 0.5)

        display.set_pen(0)
        display.line(legend_origin_x-5, legend_origin_y + 25, legend_origin_x + 15, legend_origin_y + 25, 2)
        display.set_pen(0)
        display.text("RH %", legend_origin_x - 5, legend_origin_y + 30, WIDTH, 0.5)

        for i in range(1, len(temperature_values)):
            x1 = chart_origin_x + int((i - 1) * chart_width / (len(temperature_values) - 1))
            x2 = chart_origin_x + int(i * chart_width / (len(temperature_values) - 1))
            y1 = chart_origin_y + chart_height - int((temperature_values[i - 1] * (chart_height / y_scale)))
            y2 = chart_origin_y + chart_height - int((temperature_values[i] * (chart_height / y_scale)))
            display.set_pen(0)
            display.line(x1, y1, x2, y2, 2)

        for i in range(1, len(humidity_values)):
            x1 = chart_origin_x + int((i - 1) * chart_width / (len(humidity_values) - 1))
            x2 = chart_origin_x + int(i * chart_width / (len(humidity_values) - 1))
            y1_hum = chart_origin_y + chart_height - int((humidity_values[i - 1] * (chart_height / y_scale)))
            y2_hum = chart_origin_y + chart_height - int((humidity_values[i] * (chart_height / y_scale)))
            display.set_pen(7)
            display.line(x1, y1_hum, x2, y2_hum, 2)

        if temperature_values:
            average_temp = sum(temperature_values) / len(temperature_values)
            average_humidity = sum(humidity_values) / len(humidity_values)
            display.set_pen(15)
            display.text("Avg: {:.2f}°C".format(average_temp), 195, HEIGHT-9, WIDTH, 0.6)
            display.text("| {:.2f}%RH".format(average_humidity), 250, HEIGHT-9, WIDTH, 0.6)
            display.text("Current: {:.2f}°C".format(temperature), 175, 1, WIDTH, 0.6)
            display.text("| {:.2f}%RH".format(humidity), 250, 1, WIDTH, 0.6)
            print(f"Average temperature: {average_temp} | Current temperature: {temperature} | Humidity {humidity}")
            display.text(get_iso_timestamp(), 10, HEIGHT-9, WIDTH, 0.6)

        display.update()

        utime.sleep(2)

except KeyboardInterrupt:
    pass

