import urequests as requests
import ujson as json
import machine
import badger2040
import os

from badger2040 import WIDTH

display = badger2040.Badger2040()
display.set_update_speed(2)
display.connect()

##########################################################################################
# Define a function that clears the screen and prints a header row
##########################################################################################
def clear():
    display.set_pen(15)
    display.clear()
    display.set_pen(0)
    display.set_font("bitmap8")
    display.set_pen(0)
    display.rectangle(0, 0, WIDTH, 10)
    display.set_pen(15)
    display.text("Badger App provisioning", 10, 1, WIDTH, 0.6) # parameters are left padding, top padding, width of screen area, font size
    display.set_pen(0)

def download_file(url, destination_path):
    print(f"Downloading {url} to {destination_path}")
    response = requests.get(url)
    if response.status_code == 200:
        with open(destination_path, "wb") as f:
            f.write(response.content)
        print("Download complete")
    else:
        print("Failed to download:", url)

github_repo_url = "https://raw.githubusercontent.com/chrissyhroberts/badger2040w_code/main/"
provisioning_manifest_url = github_repo_url + "provisioning_manifest.json"

print(f"provisioning manifest URL is : {provisioning_manifest_url}")

# Retrieve provisioning manifest
manifest_response = requests.get(provisioning_manifest_url)

if manifest_response.status_code == 200:
    print("Provisioning manifest downloaded successfully.")
    clear()
    display.text("Provisioning manifest downloaded successfully.", 10, 35, WIDTH, 1)
    display.update()
    manifest_data = json.loads(manifest_response.content)
    folders_to_clean = manifest_data.get("folders_to_clean", [])
    files_to_keep = manifest_data["files"]

    # Clean up folders specified in the manifest
    for folder in folders_to_clean:
        print(f"Cleaning up folder: {folder}")
        folder_path = "./" + folder + "/"
        try:
            for filename in os.listdir(folder_path):
                entry_path = folder_path + filename
                # Check if it's a regular file (not a directory)
                try:
                    with open(entry_path, "rb"):
                        os.remove(entry_path)
                        print("Removed:", filename)
                except OSError:
                    pass
        except OSError:
            pass

    # Download and add files from manifest
    print("Downloading files from manifest...")
    clear()
    display.text(f"Downloading files in manifest...", 10, 15, WIDTH, 1)

num_files = len(files_to_keep)
for index, file_info in enumerate(files_to_keep, start=1):
    file_path = file_info["path"]
    file_folder = file_info.get("folder", "examples")
    print(f"File {file_path} ({index}/{num_files})")
    file_url = github_repo_url + file_path
    print(f"Downloading: {file_url}")
    destination_folder = "./" + file_folder
    try:
        os.mkdir(destination_folder)
    except OSError:
        pass
    destination_path = destination_folder + "/" + file_path.split("/")[-1]
    print(f"Saving to: {destination_path}")
    download_file(file_url, destination_path)
    print("Downloaded:", file_path)
    
    # Calculate the vertical position dynamically based on index
    text_vertical_position = 25 + (10 * ((index - 1) % 10))
    
    display.text(f"Downloaded: {file_path} ({index}/{num_files})", 10, text_vertical_position, WIDTH, 1)
    display.update()

    # Check if it's the 10th download, then clear display and show progress
    if index % 10 == 0:
        clear()
        display.text(f"Downloading files in manifest...", 10, 15, WIDTH, 1)
        display.update()

clear()
display.text(f"Provisioning complete", 10, 15, WIDTH, 1)
display.update()
