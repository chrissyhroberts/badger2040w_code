import ujson as json
import utime
import hashlib
import hmac
import ntptime
import struct
import badger2040
import badger_os

badger = badger2040.Badger2040()

badger.set_pen(15)
badger.clear()
badger.set_pen(1)

badger.connect()
badger.set_font("bitmap16")

badger.set_update_speed(2)

# Set display parameters
WIDTH = badger2040.WIDTH
HEIGHT = badger2040.HEIGHT

if badger.isconnected():
    # Synchronize with the NTP server to get the current time
    ntptime.settime()

# Function to generate a TOTP for a given secret key
def generate_totp(secret_key, time_step=30):
    current_time = utime.time()
    time_step_counter = current_time // time_step

    # Pack the counter as an 8-byte big-endian value
    packed_counter = struct.pack(">Q", time_step_counter)

    # Encode the secret_key as bytes
    secret_key_bytes = secret_key.encode('utf-8')

    # Calculate the HMAC-SHA1 hash of the packed counter using the secret key
    hmac_digest = hmac.new(secret_key_bytes, packed_counter, hashlib.sha1).digest()

    # Get the 4-byte dynamic truncation offset (last nibble of the hash)
    offset = hmac_digest[-1] & 0x0F

    # Extract a 4-byte integer from the hash starting at the offset
    truncated_hash = hmac_digest[offset:offset + 4]

    # Convert the truncated hash to an integer
    otp_value = struct.unpack(">I", truncated_hash)[0] & 0x7FFFFFFF

    # Generate a 6-digit OTP by taking the modulo of the value
    otp_value = otp_value % 1000000

    return "{:06}".format(otp_value)

# Load keys from the JSON file
with open('data/totp_keys.json', 'r') as json_file:
    keys = json.load(json_file)

# Display the current OTP codes once at startup
key_info = []
x = 10  # Initial x position
y = 20  # Initial y position

for key in keys:
    name = key["name"]
    secret_key = key["key"]
    otp_value = generate_totp(secret_key)
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
badger.set_pen(15)

for info in key_info:
    badger.text(info, x, y, WIDTH, 0.6)
    y += 10
    
    # Check if y has reached HEIGHT - 15
    if y >= HEIGHT - 15:
        y = 20  # Reset y to its original value
        x += 100  # Add 80 to x

badger.update()

# Main loop
while True:
    current_time = utime.localtime()
    seconds = current_time[5]  # Get seconds from the current_time tuple

    # Calculate the time remaining until the next zero or 30 seconds
    wait_time = 30 - (seconds % 30) if seconds % 30 != 0 else 0

    if wait_time == 0:
        # Create a list to accumulate key information
        key_info = []

        for key in keys:
            name = key["name"]
            secret_key = key["key"]
            otp_value = generate_totp(secret_key)

            print(f"{name} - Current OTP:", otp_value)
            
            # Append key information to the list
            key_info.append(f"{otp_value} : {name}")

        # Display all key information on the Badger screen
        badger.set_pen(15)
        badger.clear()
        # Draw the page header
        badger.set_font("bitmap8")
        badger.set_pen(15)
        badger.rectangle(0, 0, WIDTH, 10)
        badger.set_pen(0)
        badger.rectangle(0, 10, WIDTH, HEIGHT)
        badger.text("Badger TOTP Authenticator", 10, 1, WIDTH, 0.6)
        badger.set_pen(15)

        y = 20
        x = 10

        for info in key_info:
            badger.text(info, x, y, WIDTH, 0.6)
            y += 10
    
            # Check if y has reached HEIGHT - 15
            if y >= HEIGHT - 15:
                y = 20  # Reset y to its original value
                x += 100  # Add 80 to x

        badger.update()

    utime.sleep(1)  # Sleep for 1 second to avoid repeated printing
