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
#clear()
#display.text(f"provisioning manifest URL is : {provisioning_manifest_url}",10,15,WIDTH,1)

# Retrieve provisioning manifest
#print("Downloading provisioning manifest...")
#display.text(f"Downloading provisioning manifest...",10,25,WIDTH,1)
#display.update()

manifest_response = requests.get(provisioning_manifest_url)

if manifest_response.status_code == 200:
    print("Provisioning manifest downloaded successfully.")    
    clear()
    display.text("Provisioning manifest downloaded successfully.",10,35,WIDTH,1)
    display.update()
    manifest_data = json.loads(manifest_response.content)
    files_to_keep = manifest_data["files"]


    # Download and add files from manifest
    print("Downloading files from manifest...")
    clear()
    display.text(f"Downloading files in manifest...", 10, 15, WIDTH, 1)

    num_files = len(files_to_keep)
    for index, file_to_add in enumerate(files_to_keep, start=1):
        print(f"File {file_to_add} ({index}/{num_files})")
        file_url = github_repo_url + file_to_add
        print(f"Downloading: {file_url}")
        destination_path = "./" + file_to_add  # Modify this path as needed
        print(f"Saving to: {destination_path}")
        download_file(file_url, destination_path)
        print("Downloaded:", file_to_add)
        display.text(f"Downloaded: {file_to_add} ({index}/{num_files})", 10, 25+(10*index), WIDTH, 1)
        display.update()


    # Clean up files not in manifest
    print("Cleaning up files not in manifest...")
    clear()
    display.text(f"Cleaning up files not in manifest...", 10, 15, WIDTH, 1)
    display.update()

    files_to_ignore = ["apps.py", "icon-apps.jpg"]
    existing_files = os.listdir("./examples")
    num_files_to_delete = len([file for file in existing_files if file not in [f.split("/")[-1] for f in files_to_keep] and file not in files_to_ignore])

    for index, file in enumerate(existing_files, start=1):
        file_name = file.split("/")[-1]
        if file_name not in [f.split("/")[-1] for f in files_to_keep] and file_name not in files_to_ignore:
            print(f"File to remove: ./examples/{file_name}")
            file_path = "./examples/" + file_name
            os.remove(file_path)
            print("Removed:", file_name)
            display.text(f"Removed: {file_name} ({index}/{num_files_to_delete})", 10, 25+(10*index), WIDTH, 1)
            display.update()

print("Provisioning complete.")

clear()
display.text(f"Provisioning complete.", 10, 15, WIDTH, 1)
display.update()

            
