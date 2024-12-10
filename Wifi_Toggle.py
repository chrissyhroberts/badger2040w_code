import badger2040
import network_manager
import WIFI_CONFIG
import utime
from machine import Pin
import urequests

# Initialize the Badger2040
badger = badger2040.Badger2040()
network_manager_instance = network_manager.NetworkManager(country="GB")

def toggle_wifi(state):
    wlan = network_manager_instance._sta_if
    if state == "on":
        # Activate Wi-Fi
        wlan.active(True)
        wlan.connect(WIFI_CONFIG.SSID, WIFI_CONFIG.PSK)
        utime.sleep(5)  # Wait for connection
        if wlan.isconnected():
            print(f"Wi-Fi connected with IP address: {wlan.ifconfig()[0]}")
        else:
            print("Wi-Fi connection failed.")
    elif state == "off":
        # Deactivate Wi-Fi
        network_manager_instance._sta_if.disconnect()
        print("Wi-Fi disconnected from the network.")
        print(f"Wi-Fi  with IP address: {wlan.ifconfig()[0]}")

    else:
        print("Invalid state. Use 'on' or 'off'.")


# Example usage
toggle_wifi("on")


# Fetch a chunk of data after connecting
if network_manager_instance._sta_if.isconnected():
    URL = "http://httpbin.org/bytes/1024"  # Fetch 1KB of data
    try:
        response = urequests.get(URL)
        if response.status_code == 200:
            data_chunk = response.content
            print(f"Received data chunk: {data_chunk[:100]}...")  # Print first 100 bytes as a preview
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
        response.close()
    except Exception as e:
        print(f"An error occurred: {e}")
else:
    print("Wi-Fi not connected. Unable to fetch data.")

# Turn off Wi-Fi after use
toggle_wifi("off")


