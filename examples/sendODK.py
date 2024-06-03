import urequests
import binascii
import network
import os
import uos
import time
import badger2040

# Initialize the Badger eINK display
display = badger2040.Badger2040()
display.led(128)
display.set_update_speed(2)

# Constants
WIDTH = 250  # Width of the Badger2040 display
HEIGHT = 122  # Height of the Badger2040 display

# Your existing functions (connect_to_wifi, base64_encode, submit_submission, log_submission, walk, load_submitted_files, submit_xml_files_in_folder) go here...

def connect_to_wifi(ssid, password):
    # set up the screen with a black background and black pen
    display.set_pen(0)  # Change this to 0 if a white background is used
    display.clear()
    display.set_pen(15)

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        display.text('Already connected to Wi-Fi', 10, 20)
        display.update()
        return

    wlan.connect(ssid, password)

    while not wlan.isconnected():
        display.text('Connecting to Wi-Fi...', 10, 20)
        display.update()

    display.text('Connected to Wi-Fi', 10, 40)
    display.text('Network config:' + str(wlan.ifconfig()), 10, 60)
    display.update()

def base64_encode(string):
    # Encoding the string to bytes
    encoded_bytes = string.encode('utf-8')

    # Encoding bytes to base64
    encoded_base64_bytes = binascii.b2a_base64(encoded_bytes)

    # Decoding base64 bytes to string
    encoded_base64_string = encoded_base64_bytes.decode('utf-8').strip()

    return encoded_base64_string

def submit_submission(file_path, url, username, password):
    with open(file_path, 'r') as file:
        xml_data = file.read()

    encoded_credentials = base64_encode(username + ':' + password)

    headers = {
        'Content-Type': 'application/xml',
        'Authorization': 'Basic ' + encoded_credentials
    }

    response = urequests.post(url, headers=headers, data=xml_data)

    if response.status_code in (200, 201):
    	display.set_pen(0)  # Change this to 0 if a white background is used
    	display.clear()
    	display.set_pen(15)    	
        display.text('Submission successful', 10, 60)
        display.update()
        log_submission(file_path, success=True, response_text=response.text)
    else:
    	display.set_pen(0)  # Change this to 0 if a white background is used
    	display.clear()
    	display.set_pen(15)    	
        display.text('Submission failed: ' + str(response.status_code), 10, 40)
        display.text('Response: ' + response.text, 10, 60)
        display.update()
        log_submission(file_path, success=False, response_text=response.text)

def log_submission(file_path, success, response_text):
    with open('log.txt', 'a') as log_file:
        status = 'Success' if success else 'Failure'
        log_entry = f"File: {file_path}, Status: {status}, Response: {response_text}\n"
        log_file.write(log_entry)


def walk(directory):
    file_paths = []
    for entry in uos.listdir(directory):
        entry_path = directory + '/' + entry
        if uos.stat(entry_path)[0] & 0x4000:
            file_paths.extend(walk(entry_path))
        else:
            file_paths.append(entry_path)
    return file_paths


def load_submitted_files():
    submitted_files = set()
    if 'log.txt' in uos.listdir():
        print("Log file exists")
        with open('log.txt', 'r') as log_file:
            for line in log_file:
                file_path, status, _ = line.strip().split(', ')
                if status == 'Status: Success':  # Correct the status check
                    # Extract the filename from the full file path
                    filename = file_path.split('/')[-1]
                    print("Adding filename to submitted files:", filename)
                    submitted_files.add(filename)
                else:
                    print("Skipping file:", file_path, "with status:", status)
    else:
        print("Log file does not exist")
    print("Submitted files:", submitted_files)
    return submitted_files

def count_unique_uuids(log_file_path):
    unique_uuids = set()
    if log_file_path in uos.listdir():
        with open(log_file_path, 'r') as log_file:
            for line in log_file:
                file_path, _, response = line.strip().split(', ')
                uuid = response.split('/')[-1]
                unique_uuids.add(uuid)
    return len(unique_uuids)

def submit_xml_files_in_folder(folder_path, url, username, password):
    # Load the set of submitted files from the log
    submitted_files = load_submitted_files()

    # Add a counter for successful submissions
    successful_submissions = 0

    file_paths = walk(folder_path)
    for file_path in file_paths:
        if file_path.endswith('.xml'):
            # Extract the filename from the full file path
            filename = file_path.split('/')[-1]
            if filename not in submitted_files:
                print('Submitting file:', file_path)

                # Instead of printing, use the Badger eINK display to show the submission status.
                display.set_pen(0)  # Change this to 0 if a white background is used
                display.clear()
                display.set_pen(15)
                display.text('Submitting file:', 10, 40)
                display.text(file_path, 10, 60)
                display.update()

                submit_submission(file_path, url, username, password)
                print('---')

                # Update the log and counter only after a successful submission
                if filename not in submitted_files:
                    log_submission(file_path, success=True, response_text='')
                    successful_submissions += 1

                submitted_files.add(filename)  # Update the set with the filename

    # Get the total number of unique UUID numbers in the log file
    unique_uuid_count = count_unique_uuids('log.txt')

    # Display the total number of successful submissions
    display.set_pen(0)  # Change this to 0 if a white background is used
    display.clear()
    display.set_pen(15)

    display.text('Submissions Sent Now:', 10, 20)
    display.text(str(successful_submissions), 10, 40)
    display.text('Total Submissions :', 10, 60)
    display.text(str(unique_uuid_count), 10, 80)
    display.update()

    print("Submitted files:", submitted_files)


##########################
# MAIN
##########################

print("Connecting to Wi-Fi...")
connect_to_wifi('YOURNETWORKSSID', 'YOURNETWORKPASSWORD")

folder_path = 'instances'  # Update with the actual folder path
url = 'https://YOURCENTRALURL/v1/projects/YOURPROJECTID/forms/YOURFORMNAME/submissions'
username = 'YOURCENTRALUSERNAME"
password = 'YOURCENTRALPASSWORD'

submit_xml_files_in_folder(folder_path, url, username, password)
