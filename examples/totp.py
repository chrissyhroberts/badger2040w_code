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



badger = badger2040.Badger2040()
badger.connect()
badger.set_font("bitmap16")
badger.set_update_speed(2)

# Set display parameters
WIDTH = badger2040.WIDTH
HEIGHT = badger2040.HEIGHT

if badger.isconnected():
    # Synchronize with the NTP server to get the current time
    print("Connected to Wi-Fi, setting time on RTC")
    ntptime.settime()
    print ("Disconnecting")
    wlan = network.WLAN()
    wlan.disconnect()
    print("Disconnected from Wi-Fi")    
else:
    print("No Wi-Fi")    
    
#set timezone offset
timezone_offset = 1

# Define SHA1 constants and utility functions
HASH_CONSTANTS = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0]

# Set the time on the external PCF85063A RTC
print("setting pcf time")

now = utime.localtime()
i2c = machine.I2C(0, scl=machine.Pin(5), sda=machine.Pin(4))
rtc_pcf85063a = PCF85063A(i2c)
rtc_pcf85063a.datetime(now)
    
# Set the time on the external PCF85063A RTC
print("pcf time set")


#####################################################
# Define functions
#####################################################

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
            elif 60 <= i < 80:
                f = b ^ c ^ d
                k = 0xCA62C1D6
            a, b, c, d, e = (
                left_rotate(a, 5) + f + e + k + expanded_chunk[i] & 0xFFFFFFFF,
                a,
                left_rotate(b, 30),
                c,
                d,
            )
        h = (
            h[0] + a & 0xFFFFFFFF,
            h[1] + b & 0xFFFFFFFF,
            h[2] + c & 0xFFFFFFFF,
            h[3] + d & 0xFFFFFFFF,
            h[4] + e & 0xFFFFFFFF,
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
    
    # Add debugging prints
#    print(f"HMAC: {hmac.hex()}")
#    print(f"Offset: {offset}")
#    print(f"Code: {code}")
    
    return (
        "0" * (digits - len(code)) + code,
        step_secs - time % step_secs
    )

#####################################################
# Load keys from the JSON file
#####################################################

with open('data/totp_keys.json', 'r') as json_file:
    keys = json.load(json_file)

# Display the current OTP codes once at startup
key_info = []
x = 10  # Initial x position
y = 20  # Initial y position

#####################################################
# Get and check current times
#####################################################

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



for key in keys:
    name = key["name"]
    secret_key = key["key"]
    otp_value, sec_remain = totp(get_pcf_time(), secret_key,  30, 6)
    
    key_info.append(f"{otp_value} : {name}")

badger.set_pen(15)
badger.clear()
# Draw the page header
badger.set_font("bitmap8")
badger.set_pen(15)
badger.rectangle(0, 0, WIDTH, 10)
badger.set_pen(0)
badger.rectangle(0, 10, WIDTH, HEIGHT)
badger.text("Badger TOTP Authenticator", 10, 1, WIDTH, 0.6)
badger.text(f"Time to refresh : {sec_remain} S", 180, 1, WIDTH, 0.6)

badger.set_pen(15)

for info in key_info:
    badger.text(info, x, y, WIDTH, 0.6)
    y += 10
    
    # Check if y has reached HEIGHT - 15
    if y >= HEIGHT - 15:
        y = 20  # Reset y to its original value
        x += 100  # Add 80 to x

#show current date and time
spot_time = machine.RTC().datetime()
hour = spot_time[4]
hour = hour + timezone_offset
badger.text(f"{spot_time[0]}-{spot_time[1]}-{spot_time[2]}", 200, 70, WIDTH, 2)
badger.text(f"{hour}:{spot_time[5]}", 200, 90, WIDTH, 3)
badger.update()

while True:
    badger.keepalive()
    
    # Calculate the current OTP value and remaining time until next refresh
    null, cadence = otp_value, remaining = totp(get_pcf_time(), "LMESUJEY7PTJSNYO5LKSME5HWQO6XZ5L", 30, 6)

    if cadence == 30:
        # If the cadence timer is zero or negative, it's time to refresh
        key_info = []
        x = 10  # Initial x position
        y = 20  # Initial y position

        for key in keys:
            name = key["name"]
            secret_key = key["key"]
            otp_value, remaining = totp(get_pcf_time(), secret_key, 30, 6)
            key_info.append(f"{otp_value} : {name}")
            sec_remain = max(sec_remain, remaining)

        badger.set_pen(15)
        badger.clear()
        # Draw the page header
        badger.set_font("bitmap8")
        badger.set_pen(15)
        badger.rectangle(0, 0, WIDTH, 10)
        badger.set_pen(0)
        badger.rectangle(0, 10, WIDTH, HEIGHT)
        badger.text("Badger TOTP Authenticator", 10, 1, WIDTH, 0.6)
        badger.text(f"Time to refresh : {sec_remain} S", 180, 1, WIDTH, 0.6)
        print(f"Time to refresh : {sec_remain} S")
        badger.set_pen(15)

        for info in key_info:
            badger.text(info, x, y, WIDTH, 0.6)
            y += 10

            # Check if y has reached HEIGHT - 15
            if y >= HEIGHT - 15:
                y = 20  # Reset y to its original value
                x += 100  # Add 80 to x
        #show current date and time
        #show current date and time
        spot_time = machine.RTC().datetime()
        hour = spot_time[4]
        hour = hour + timezone_offset
        badger.text(f"{spot_time[0]}-{spot_time[1]}-{spot_time[2]}", 200, 70, WIDTH, 2)
        badger.text(f"{hour}:{spot_time[5]}", 200, 90, WIDTH, 3)
        badger.update()
        utime.sleep_ms(25000)
        null, cadence = otp_value, remaining = totp(get_pcf_time(), "LMESUJEY7PTJSNYO5LKSME5HWQO6XZ5L", 30, 6)
    # Put the microcontroller into deep sleep during cadence countdown
    # Sleep for 30 seconds (cadence duration)
    if cadence > 0:
        cadence -= 1
  # Sleep in milliseconds



