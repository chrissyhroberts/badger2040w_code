# This code pulls solar weather data from xml files hosted at https://www.hamqsl.com/solarxml.php
# Please check the terms of service there before using this code

import requests
import xml.etree.ElementTree as ET

# Replace with the URL for solar data
solar_url = "https://www.hamqsl.com/solarxml.php"

# Make a GET request to the URL
response = requests.get(solar_url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the XML content
    xml_content = response.content
    root = ET.fromstring(xml_content)
    
    # Retrieve and print calculatedconditions
    calculated_conditions_element = root.find(".//calculatedconditions")
    if calculated_conditions_element is not None:
        for band_element in calculated_conditions_element.findall(".//band"):
            band_name = band_element.get("name")
            band_time = band_element.get("time")
            band_value = band_element.text.upper()
            print(f"{band_name} : {band_time} : {band_value}")
    
    # Retrieve and print calculatedvhfconditions
    calculated_vhf_conditions_element = root.find(".//calculatedvhfconditions")
    if calculated_vhf_conditions_element is not None:
        for phenomenon_element in calculated_vhf_conditions_element.findall(".//phenomenon"):
            phenomenon_name = phenomenon_element.get("name")
            phenomenon_location = phenomenon_element.get("location")
            phenomenon_value = phenomenon_element.text
            print(f"{phenomenon_name} : {phenomenon_location} : {phenomenon_value}")
    
    # Retrieve and print other specific elements
    elements_to_print = [
        "source",
        "updated",
        "solarflux",
        "aindex",
        "kindex",
        "kindexnt",
        "xray",
        "sunspots",
        "heliumline",
        "protonflux",
        "electonflux",
        "aurora",
        "normalization",
        "latdegree",
        "solarwind",
        "magneticfield",
        "geomagfield",
        "signalnoise",
        "fof2",
        "muffactor",
        "muf",
    ]
    for element_name in elements_to_print:
        element = root.find(f".//{element_name}")
        if element is not None:
            print(f"{element_name} : {element.text}")
else:
    print("Error:", response.status_code)
