import time
import machine
import utime
import ntptime
import struct
import badger2040
import badger_os
import ujson as json
import network
from pcf85063a import PCF85063A
import urequests
from machine import RTC


############################################################################################################
# Initialize the Badger2040
badger = badger2040.Badger2040()
badger.connect()
badger.set_font("bitmap16")
badger.set_update_speed(2)

# Set display parameters
WIDTH = badger2040.WIDTH
HEIGHT = badger2040.HEIGHT

# Function to read the calendar URL from a file
def read_calendar_url_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            url = file.read().strip()  # Read the URL and strip any extra whitespace
            return url
    except OSError as e:
        print(f"Error reading file {file_path}: {e}")
        return None

# Path to the file containing the calendar URL
calendar_url_file = 'data/calendar_url.txt'

# Read the calendar URL from the file
ics_url = read_calendar_url_from_file(calendar_url_file)

# Check if the URL was successfully read from the file
if ics_url:
    print(f"Calendar URL loaded: {ics_url}")
else:
    print("Failed to load calendar URL. Please check the file.")


# Set timezone offset
timezone_offset = 1

# Map common timezones to their respective offsets
timezone_offsets = {
    "Eastern Standard Time": "-0500",  # EST (UTC-5)
    "Eastern Daylight Time": "-0400",  # EDT (UTC-4)
    "British Summer Time": "+0100",    # BST (UTC+1)
    "Greenwich Mean Time": "+0000",    # GMT (UTC)
    # Add more timezones as needed
}

# Set variable for inversion of colours, aimed at stopping screen burn
invert_colors = False
pen_color = 15
pen_color_2 = 0
############################################################################################################
# Synchronize with NTP to set the current time
def sync_ntp_time():
    try:
        # Synchronize with the NTP server to get the current time
        print("Synchronizing with NTP server...")
        ntptime.settime()
        print("NTP synchronization successful!")
    except Exception as e:
        print(f"Failed to synchronize with NTP server: {e}")

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
    rtc_pcf85063a.datetime((now[0], now[1], now[2], now[3], now[4], now[5], now[6]))

# Get current time in Unix timestamp format
def get_pcf_time():
    current_time_pcf = machine.RTC().datetime()
    year, month, day, weekday, hour, minute, second, yearday = current_time_pcf

    # Convert the extracted components to integers
    year = int(year)
    month = int(month)
    day = int(day)
    hour = int(hour) + timezone_offset
    minute = int(minute)
    second = int(second)

    # Calculate the Unix timestamp using time.mktime
    current_time_pcf = time.mktime((year, month, day, hour, minute, second, weekday, yearday))
    return current_time_pcf

# Define SHA1 constants and utility functions
HASH_CONSTANTS = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0]

############################################################################################################
# Main setup: Sync NTP, set time on RTCs
sync_ntp_time()
set_pico_time()
set_pcf85063a_time()

now = utime.localtime()
i2c = machine.I2C(0, scl=machine.Pin(5), sda=machine.Pin(4))
rtc_pcf85063a = PCF85063A(i2c)
rtc_pcf85063a.datetime(now)

print("PCF time set")
############################################################################################################


############################################################################################################
# Define functions for TOTP
############################################################################################################
def left_rotate(n, b):
    return ((n << b) | (n >> (32 - b))) & 0xFFFFFFFF

def expand_chunk(chunk):
    w = list(struct.unpack(">16L", chunk)) + [0] * 64
    for i in range(16, 80):
        w[i] = left_rotate((w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16]), 1)
    return w

def sha1(message):
    h = HASH_CONSTANTS
    padded_message = message + b"\x80" + \
        (b"\x00" * (63 - (len(message) + 8) % 64)) + \
        struct.pack(">Q", 8 * len(message))
    chunks = [padded_message[i:i+64] for i in range(0, len(padded_message), 64)]

    for chunk in chunks:
        expanded_chunk = expand_chunk(chunk)
        a, b, c, d, e = h
        for i in range(0, 80):
            if 0 <= i < 20:
                f = (b & c) | ((~b) & d)
                k = 0x5A827999
            elif 20 <= i < 40:
                f = b ^ c ^ d
                k = 0x6ED9EBA1
            elif 40 <= i < 60:
                f = (b & c) | (b & d) | (c & d)
                k = 0x8F1BBCDC
            else:  # 60 <= i < 80
                f = b ^ c ^ d
                k = 0xCA62C1D6
            a, b, c, d, e = (
                (left_rotate(a, 5) + f + e + k + expanded_chunk[i]) & 0xFFFFFFFF,
                a,
                left_rotate(b, 30),
                c,
                d,
            )
        h = (
            (h[0] + a) & 0xFFFFFFFF,
            (h[1] + b) & 0xFFFFFFFF,
            (h[2] + c) & 0xFFFFFFFF,
            (h[3] + d) & 0xFFFFFFFF,
            (h[4] + e) & 0xFFFFFFFF,
        )

    return struct.pack(">5I", *h)

def hmac_sha1(key, message):
    key_block = key + (b'\0' * (64 - len(key)))
    key_inner = bytes((x ^ 0x36) for x in key_block)
    key_outer = bytes((x ^ 0x5C) for x in key_block)

    inner_message = key_inner + message
    outer_message = key_outer + sha1(inner_message)

    return sha1(outer_message)

def base32_decode(message):
    padded_message = message + '=' * (8 - len(message) % 8)
    chunks = [padded_message[i:i+8] for i in range(0, len(padded_message), 8)]

    decoded = []

    for chunk in chunks:
        bits = 0
        bitbuff = 0

        for c in chunk:
            if 'A' <= c <= 'Z':
                n = ord(c) - ord('A')
            elif '2' <= c <= '7':
                n = ord(c) - ord('2') + 26
            elif c == '=':
                continue
            else:
                raise ValueError("Not Base32")

            bits += 5
            bitbuff <<= 5
            bitbuff |= n

            if bits >= 8:
                bits -= 8
                byte = bitbuff >> bits
                bitbuff &= ~(0xFF << bits)
                decoded.append(byte)

    return bytes(decoded)

def totp(time, key, step_secs=30, digits=6):
    hmac = hmac_sha1(base32_decode(key), struct.pack(">Q", time // step_secs))
    offset = hmac[-1] & 0xF
    code = ((hmac[offset] & 0x7F) << 24 |
            (hmac[offset + 1] & 0xFF) << 16 |
            (hmac[offset + 2] & 0xFF) << 8 |
            (hmac[offset + 3] & 0xFF))
    code = str(code % 10 ** digits)
    
    return (
        "0" * (digits - len(code)) + code,
        step_secs - time % step_secs
    )

# Load keys from the JSON file
with open('data/totp_keys.json', 'r') as json_file:
    keys = json.load(json_file)

def get_pcf_time():
    current_time = time.time()
    current_time_pcf = machine.RTC().datetime()
    print("current time system:", current_time)
    print("current time pcf:", current_time_pcf)

    # Extract the components from the tuple
    year, month, day, weekday, hour, minute, second, yearday = current_time_pcf

    # Convert the extracted components to integers
    year = int(year)
    month = int(month)
    day = int(day)
    hour = int(hour)
    minute = int(minute)
    second = int(second)

    # Calculate the Unix timestamp using time.mktime
    current_time_pcf = time.mktime((year, month, day, hour, minute, second, weekday, yearday))
    
    return current_time_pcf

print(f"current time standard : {time.time()}")
print(f"current time pfc : {get_pcf_time()}")
print(f"time.time {time.time()}")

def display_otp():
    key_info = []
    x = 230  # Initial x position
    y = 20  # Initial y position

    for key in keys:
        name = key["name"]
        secret_key = key["key"]
        otp_value, sec_remain = totp(get_pcf_time(), secret_key, 30, 6)
        key_info.append(f"{otp_value}")

    badger.set_pen(pen_color)
    badger.clear()
    # Draw the page header
    badger.set_font("bitmap8")
    badger.set_pen(pen_color)
    badger.rectangle(0, 0, WIDTH, 10)
    badger.set_pen(pen_color_2)
    badger.rectangle(0, 10, WIDTH, HEIGHT)
    badger.text(f"Time to refresh : {sec_remain} S", 180, 1, WIDTH, 0.6)

    badger.set_pen(pen_color)

    for info in key_info:
        badger.text(info, x, y, WIDTH, 2)
        y += 30

        if y >= HEIGHT - 15:
            y = 20  # Reset y to its original value
            x += 100  # Add 80 to x


def show_current_time():
    # Show current date and time
    spot_time = machine.RTC().datetime()
    year = spot_time[0]
    month = spot_time[1]
    day = spot_time[2]
    hour = spot_time[4] + timezone_offset
    minute = spot_time[5]

    month = ('00' + str(month))[-2:]
    day = ('00' + str(day))[-2:]
    hour = ('00' + str(hour))[-2:]
    minute = ('00' + str(minute))[-2:]
    badger.text(f"{year}-{month}-{day}", 10, 20, WIDTH, 2)
    badger.text(f"{hour}:{minute}", 10, 40, WIDTH, 3)

############################################################################################################

############################################################################################################
############################################################################################################
# Define functions for Calendar

# Function to fetch and process the .ics data
def fetch_and_process_ics():
    buffer = ""  # Buffer to accumulate data
    in_event = False  # Flag to track if we're inside a VEVENT section
    event_data = []  # List to store the current event's data

    try:
        response = urequests.get(ics_url)
        if response.status_code == 200:
            print(f"Successfully connected: {response.status_code}")
            print(f"Headers: {response.headers}")

            while True:
                chunk = response.raw.read(2048)  # Read in 2048-byte chunks
                if not chunk:
                    break

                try:
                    decoded_chunk = chunk.decode('utf-8')  # Decode without 'errors' argument
                except Exception as e:
                    print(f"Error decoding chunk: {e}")
                    break  # Exit on error

                buffer += decoded_chunk
                lines = buffer.splitlines(keepends=True)
                buffer = ""  # Clear the buffer

                for line in lines:
                    if line.startswith("BEGIN:VEVENT"):
                        in_event = True
                        event_data = []  # Start collecting event data
                    if in_event:
                        event_data.append(line)
                    if line.startswith("END:VEVENT"):
                        in_event = False
                        yield event_data  # Yield the complete event
                        event_data = []  # Reset for the next event

                if lines[-1][-1] != '\n':  # If the last line was incomplete, keep it in the buffer
                    buffer = lines[-1]
        else:
            print(f"Failed to fetch calendar data. Status code: {response.status_code}")
            yield None
    except Exception as e:
        print(f"Request failed: {e}")
        yield None
    finally:
        try:
            response.close()
        except Exception as e:
            print(f"Error closing response: {e}")

# Parse events for today's date and handle the TZID (time zone information)
def parse_ics_for_today(ics_generator):
    events = []
    now = list(time.localtime())
    today = "{:04d}{:02d}{:02d}".format(now[0], now[1], now[2])
    print("Local date (today):", today)

    for event_data in ics_generator:
        if event_data is None:
            continue

        event = {}
        tzoffsetfrom = None
        tzid = None

        print("\nProcessing new event...")

        for line in event_data:
            line = line.strip()
            if line.startswith("SUMMARY:"):
                event["name"] = line[len("SUMMARY:"):].strip()
            elif line.startswith("DTSTART;TZID="):
                tzid = line.split("=")[1].split(":")[0].strip()
                dtstart = line.split(":")[-1].strip()
                event["start"] = dtstart
                print(f"Event start time (before adjustment): {event['start']}")
                print(f"Detected time zone: {tzid}")
            elif line.startswith("DTEND;TZID="):
                tzid = line.split("=")[1].split(":")[0].strip()
                dtend = line.split(":")[-1].strip()
                event["end"] = dtend
                print(f"Event end time (before adjustment): {event['end']}")
            elif line.startswith("TZOFFSETFROM:"):
                tzoffsetfrom = line[len("TZOFFSETFROM:"):].strip()
                print(f"Captured TZOFFSETFROM value: {tzoffsetfrom}")

        if tzoffsetfrom is None and tzid is not None:
            tzoffsetfrom = timezone_offsets.get(tzid, "+0000")
            print(f"Inferred TZOFFSETFROM from TZID ({tzid}): {tzoffsetfrom}")

        def parse_datetime(dt_str):
            year = int(dt_str[0:4])
            month = int(dt_str[4:6])
            day = int(dt_str[6:8])
            hour = int(dt_str[9:11])
            minute = int(dt_str[11:13])
            second = int(dt_str[13:15])
            return time.mktime((year, month, day, hour, minute, second, 0, 0, -1))

        def format_datetime(timestamp):
            tm = time.localtime(timestamp)
            return "{:04d}{:02d}{:02d}T{:02d}{:02d}{:02d}".format(
                tm[0], tm[1], tm[2], tm[3], tm[4], tm[5])

        def apply_offset(event_time, tz_offset):
            sign = 1 if tz_offset[0] == '+' else -1
            offset_hours = int(tz_offset[1:3]) * sign
            offset_minutes = int(tz_offset[3:5]) * sign
            total_offset_seconds = (offset_hours * 3600) + (offset_minutes * 60)

            print(f"\nApplying timezone adjustment for {tz_offset}:")
            event_timestamp = parse_datetime(event_time)
            adjusted_timestamp = event_timestamp - total_offset_seconds
            print(f"   Adjusted to UTC: {time.localtime(adjusted_timestamp)}")

            return format_datetime(adjusted_timestamp)

        if "start" in event:
            event["start"] = apply_offset(event["start"], tzoffsetfrom)
            print(f"Adjusted event start time: {event['start']}")

        if "end" in event:
            event["end"] = apply_offset(event["end"], tzoffsetfrom)
            print(f"Adjusted event end time: {event['end']}")

        if event.get("start", "")[:8] == today:
            events.append(event)
            print(f"Event '{event['name']}' is happening today. Added to the list.")

    return events
# Function to get current and next events
def get_current_and_next_events(events):
    current_time = get_current_time_ics_format()  # Get current time in ICS format

    current_event = None
    next_event = None

    for event in events:
        # If the event is ongoing, set it as the current event
        if event["start"] <= current_time <= event["end"]:
            current_event = event
        # Find the next upcoming event
        elif event["start"] > current_time:
            if not next_event or event["start"] < next_event["start"]:
                next_event = event

    return current_event, next_event


# Manually format the current time as YYYYMMDDTHHMMSS for comparison with .ics events
def get_current_time_ics_format():
    now = list(time.localtime())  # Get current time in list form to modify
    now[3] = (now[3] + timezone_offset) % 24  # Apply timezone offset and wrap around if necessary
    
    # Return formatted time as YYYYMMDDTHHMMSS
    return "{:04d}{:02d}{:02d}T{:02d}{:02d}{:02d}".format(now[0], now[1], now[2], now[3], now[4], now[5])


# Display current and next events without labels for "Start:"
def display_current_and_next_events(current_event, next_event):
    y = 80
    badger.set_font("bitmap8")
    badger.rectangle(0, 0, WIDTH, 10)
    badger.set_pen(pen_color_2)
    badger.text("Badger Dashboard", 10, 1, WIDTH, 0.6)

    badger.set_pen(pen_color)

    if current_event:
        badger.text(f"{current_event['start'][9:13]}-{current_event['end'][9:13]}", 10, y, WIDTH, 2)
        badger.text(f"{current_event['name']}", 100, y, WIDTH, 2)
    else:
        badger.text("No current meeting", 10, y, WIDTH, 2)

    if next_event:
        badger.text(f"{next_event['start'][9:13]}-{next_event['end'][9:13]}", 10, y + 25, WIDTH, 2)
        badger.text(f"{next_event['name']}", 100, y + 25, WIDTH, 2)
    else:
        badger.text("No More meetings", 10, y + 25, WIDTH, 2)


# Declare global variables to store current and next events
global_current_event = None
global_next_event = None

# Refresh calendar data
def refresh_calendar():
    global global_current_event, global_next_event  # Access the global variables

    ics_generator = fetch_and_process_ics()  # Fetch the calendar data
    events = parse_ics_for_today(ics_generator)  # Parse today's events

    if events:
        print(f"Events found: {len(events)}")
        print(events)
        global_current_event, global_next_event = get_current_and_next_events(events)  # Store events globally
        display_current_and_next_events(global_current_event, global_next_event)  # Update display

    else:
        print("No events found for today.")
        global_current_event = None
        global_next_event = None

# Calculate the time left until the next 15-minute mark after manual refresh
def calculate_time_until_next_refresh():
    current_minutes = time.localtime()[4]  # Get the current minute
    if current_minutes % 15 == 0:
        return 0  # It's exactly on a 15-minute mark
    else:
        return 15 - (current_minutes % 15)  # Time left until the next 15-minute interval

############################################################################################################
# SET INITIAL STATE
############################################################################################################
# Get the current time
# Initialize the variable to track time since last refresh
current_time = time.localtime()
current_minutes = current_time[4]

if current_minutes % 15 == 0:
    time_since_last_refresh = 0
else:
    time_since_last_refresh = 15 - (current_minutes % 15)  # Time left until the next 15-minute mark

badger.clear()
display_otp()
show_current_time()
refresh_calendar()
badger.update()

############################################################################################################


while True:
    # Get the current time
    current_time = time.localtime()
    current_minutes = current_time[4]  # Minutes part of the current time
    current_seconds = current_time[5]  # Seconds part of the current time

    # Refresh the clock every time the seconds equal 0
    if current_seconds == 0:
        display_otp()  # Display OTP
        show_current_time()  # Call the function to update the clock display
        display_current_and_next_events(global_current_event, global_next_event)  # Display cached events
        badger.update()

    # Increment time since last refresh
    time_since_last_refresh += 1  # Assume the loop runs every minute (utime.sleep(60) below)

    # If it's time for the 15-minute interval refresh (both conditions must be met)
    if time_since_last_refresh >= 15 and current_minutes in [0, 15, 30, 45]:
        display_otp()  # Display OTP
        show_current_time()  # Call the function to update the clock display
        refresh_calendar()  # Refresh calendar and update events
        time_since_last_refresh = 0  # Reset the timer after refresh

    # Check for Button A press
    if badger.pressed(badger2040.BUTTON_A):
        utime.sleep_ms(50)  # Debounce delay
        if badger.pressed(badger2040.BUTTON_A):  # Ensure it's still pressed
            display_otp()  # Display OTP
            show_current_time()  # Display the updated current time
            display_current_and_next_events(global_current_event, global_next_event)  # Display cached events
            badger.update()

            invert_colors = not invert_colors  # Toggle colors
            pen_color = 0 if invert_colors else 15
            pen_color_2 = 15 if invert_colors else 0  # Set colors

            # Debounce wait for release
            while badger.pressed(badger2040.BUTTON_A):
                utime.sleep_ms(10)

    if badger.pressed(badger2040.BUTTON_B):
        utime.sleep_ms(50)  # Debounce delay
        if badger.pressed(badger2040.BUTTON_B):  # Ensure it's still pressed
            display_otp()  # Display OTP
            show_current_time()  # Display the updated current time
            refresh_calendar()  # Refresh calendar and update events
            badger.update()

            # Fully reset time_since_last_refresh to 0 since a manual refresh was triggered
            time_since_last_refresh = 0  # Manual refresh means no time has passed since the last refresh

            print("Manual refresh triggered, time since last refresh reset.")

            invert_colors = not invert_colors  # Toggle colors
            pen_color = 0 if invert_colors else 15
            pen_color_2 = 15 if invert_colors else 0  # Set colors

            # Debounce wait for release
            while badger.pressed(badger2040.BUTTON_B):
                utime.sleep_ms(10)

    if badger.pressed(badger2040.BUTTON_C):
        print("Entering sleep mode.")
        badger.set_pen(0)
        badger.clear()
        badger.set_pen(15)
        badger.text("Sleeping...", 10, 10, WIDTH, 1.0)
        badger.update()
        
        # Sleep loop until Button C is pressed again
        while True:
            utime.sleep(1)  # Sleep for 1 second
            if badger.pressed(badger2040.BUTTON_C):  # Check if Button C is pressed again
                print("Waking up from sleep mode.")
                badger.set_pen(0)
                badger.clear()
                badger.set_pen(15)
                badger.text("Waking up...press b to refresh", 10, 10, WIDTH, 1.0)
                badger.update()
                utime.sleep(1)  # Small delay for visual feedback
                break  # Exit sleep loop and resume normal operation


    # Sleep to reduce polling frequency and save power (1 second sleep to catch the seconds turning 0)
    utime.sleep(1)

