import urequests as requests
import ujson as json
import machine
import badger2040
import os

display = badger2040.Badger2040()
display.set_update_speed(2)
display.connect()

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
print("Downloading provisioning manifest...")
manifest_response = requests.get(provisioning_manifest_url)

if manifest_response.status_code == 200:
    print("Provisioning manifest downloaded successfully.")
    manifest_data = json.loads(manifest_response.content)
    files_to_keep = manifest_data["files"]


    # Download and add files from manifest
    print("Downloading files from manifest...")
    for file_to_add in files_to_keep:
        print(f"File {file_to_add}")
        file_url = github_repo_url + file_to_add
        print(f"Downloading: {file_url}")
        destination_path = "./" + file_to_add  # Modify this path as needed
        print(f"Saving to: {destination_path}")
        download_file(file_url, destination_path)
        print("Downloaded:", file_to_add)

    # Clean up files not in manifest
    print("Cleaning up files not in manifest...")
    files_to_ignore = ["apps.py", "icon-apps.py"]
    existing_files = os.listdir("./examples")
    for file in existing_files:
        file_name = file.split("/")[-1]
        if file_name not in [f.split("/")[-1] for f in files_to_keep] and file_name not in files_to_ignore:
            print(f"File to remove: ./examples/{file_name}")
            file_path = "./examples/" + file_name
            os.remove(file_path)
            print("Removed:", file_name)

print("Provisioning complete.")
