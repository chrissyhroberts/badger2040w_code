import utime
from machine import Pin, I2C
import machine
import ahtx0
import badger2040
from badger2040 import WIDTH, HEIGHT
import os
from pcf85063a import PCF85063A

# ==== CONFIGURATION ====
csv_file_path = "data/logged_data.csv"
LOG_INTERVAL = 1800  # seconds between measurements
y_scale = 100

# ==== INIT HARDWARE ====
display = badger2040.Badger2040()
display.set_thickness(4)
i2c = machine.I2C(0, scl=machine.Pin(5), sda=machine.Pin(4))
rtc = PCF85063A(i2c)
sensor = ahtx0.AHT20(i2c)

# ==== FILESYSTEM ====
try:
    os.mkdir("data")
except OSError as e:
    if e.args[0] != 17:
        raise

# ==== FUNCTIONS ====

def clear():
    display.set_pen(15)
    display.clear()
    display.set_font("bitmap8")

    # Top and bottom bars
    display.set_pen(0)
    display.rectangle(0, 0, WIDTH, 10)
    display.rectangle(0, HEIGHT - 10, WIDTH, 10)

    # White title on top bar
    display.set_pen(15)
    display.text("Temp/Humidity Logger", 10, 1, WIDTH, 0.6)

def get_iso_timestamp():
    now = rtc.datetime()
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(*now[:6])

def read_last_n_entries_from_csv(n=50):
    ts, temps, hums = [], [], []
    try:
        with open(csv_file_path, "r") as f:
            lines = f.readlines()[-n:]
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) == 3:
                    try:
                        tstamp, temp, hum = parts
                        ts.append(tstamp)
                        temps.append(float(temp))
                        hums.append(float(hum))
                    except ValueError:
                        continue
    except OSError as e:
        if e.args[0] != 2:
            raise
    return ts, temps, hums

# ==== CHART AREA ====
chart_width = 200
chart_height = 80
chart_origin_x = int(0.5 * (WIDTH - chart_width))
chart_origin_y = int(0.5 * (HEIGHT - chart_height))
legend_origin_x = chart_origin_x + chart_width + 20
legend_origin_y = chart_origin_y

# ==== MAIN LOOP ====
try:
    while True:
        # === Read sensor ===
        temperature = sensor.temperature
        humidity = sensor.relative_humidity
        timestamp = get_iso_timestamp()

        # === Log to file ===
        with open(csv_file_path, "a") as f:
            f.write(f"{timestamp}, {temperature:.2f}, {humidity:.2f}\n")

        # === Read data ===
        _, temperature_values, humidity_values = read_last_n_entries_from_csv()
        num_points = len(temperature_values)

        # === Handle y_scale button ===
        if display.pressed(badger2040.BUTTON_UP):
            y_scale = {100: 80, 80: 60, 60: 50, 50: 40}.get(y_scale, 100)
            print("Changed y_scale to:", y_scale)
            utime.sleep_ms(200)

        # === Full clear and redraw ===
        display.set_update_speed(badger2040.UPDATE_NORMAL)
        display.set_pen(15)
        display.clear()
        clear()

        # === Axes ===
        display.set_pen(0)
        display.line(chart_origin_x, chart_origin_y + chart_height,
                     chart_origin_x + chart_width, chart_origin_y + chart_height)
        display.line(chart_origin_x, chart_origin_y,
                     chart_origin_x, chart_origin_y + chart_height)

        # === Y-ticks ===
        for i in range(0, y_scale + 1, 10):
            tick_y = chart_origin_y + chart_height - int(i * chart_height / y_scale)
            display.line(chart_origin_x - 3, tick_y, chart_origin_x + 3, tick_y)
            display.text(f"{i}", chart_origin_x - 25, tick_y - 4, WIDTH, 0.5)

        # === Legend ===
        display.set_pen(0)
        display.rectangle(legend_origin_x - 5, legend_origin_y, 15, 8)
        display.text("Temp", legend_origin_x + 12, legend_origin_y, WIDTH, 0.5)

        display.set_pen(4)
        display.rectangle(legend_origin_x - 5, legend_origin_y + 25, 15, 8)
        display.text("RH %", legend_origin_x + 12, legend_origin_y + 25, WIDTH, 0.5)

        # === Plot bars ===
        if num_points > 0:
            bar_unit = chart_width / num_points
            for i in range(num_points):
                x_base = chart_origin_x + int(i * bar_unit)
                temp_val = min(temperature_values[i], y_scale)
                hum_val = min(humidity_values[i], y_scale)

                temp_height = int(temp_val * chart_height / y_scale)
                hum_height = int(hum_val * chart_height / y_scale)

                # Temp bar (left half)
                display.set_pen(0)
                display.rectangle(x_base, chart_origin_y + chart_height - temp_height,
                                  int(bar_unit // 2), temp_height)

                # RH bar (right half)
                display.set_pen(4)
                display.rectangle(x_base + int(bar_unit // 2),
                                  chart_origin_y + chart_height - hum_height,
                                  int(bar_unit // 2), hum_height)

        # === Summary stats ===
        if temperature_values:
            avg_temp = sum(temperature_values) / len(temperature_values)
            avg_hum = sum(humidity_values) / len(humidity_values)

            # White text over black bars
            display.set_pen(15)
            display.text(f"Now: {temperature:.1f}°C | {humidity:.1f}%RH", 170, 1, WIDTH, 0.6)
            display.text(f"Avg: {avg_temp:.1f}°C | {avg_hum:.1f}%RH", 150, HEIGHT - 9, WIDTH, 0.6)
            display.text(timestamp, 10, HEIGHT - 9, WIDTH, 0.6)

        # === Show display ===
        display.update()

        # === Wait for next measurement ===
        utime.sleep(LOG_INTERVAL)

except KeyboardInterrupt:
    pass



