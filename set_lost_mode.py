#!/usr/bin/env python3

"""
set_lost_mode.py

Enable or disable lost mode for a list of mobile devices by reading in a CSV of
serial numbers.

Enable required columns:
    - serial_number
    - message
    - phone_number

Optional column:
    - play_sound

Disable required columns:
    - serial_number

Serial number, message, and phone number values must be filled out. Footnote
isn't included at this point because I didn't find it all that useful.

By default a sound will play when lost mode is enabled. Set play_sound to false
to not play a sound. It's best not to include a play_sound column at all if not
concerned with some iPads not playing sounds.

python3 ./set_lost_mode.py --csv /path/to/my/ipads.csv --mode enable
python3 ./set_lost_mode.py --csv /path/to/my/ipads.csv --mode disable
"""

import argparse
import csv
import os
import sys
from getpass import getpass
from xml.etree import ElementTree

import requests

# Jamf globals - change this to your Jamf Pro URL
# Formatted as 'https://myorg.jamfcloud.com' with no trailing slash
# If on prem and still using extended port 'https://jamf.myorg.com:8443'
JAMF_URL = "https://myorg.jamfcloud.com"


def get_credentials():
    """Prompt for username and password to be used in API."""
    username = input("API Username: ")
    password = getpass()
    return username, password


def enable_lost_mode(
    api_user, api_pass, device_serial, message, phone_number, sound=True
):
    """
    Send enable lost mode command by serial number.

    Message and phone number are required. Play sound can be disabled by passing
    in a value other than True, but will play by default.
    """
    # Build lost mode command XML
    command = ElementTree.Element("mobile_device_command")
    gen = ElementTree.SubElement(command, "general")
    ElementTree.SubElement(gen, "command").text = "EnableLostMode"
    ElementTree.SubElement(gen, "lost_mode_message").text = message
    ElementTree.SubElement(gen, "lost_mode_phone").text = phone_number
    ElementTree.SubElement(gen, "always_enforce_lost_mode").text = "true"
    if sound is True:
        ElementTree.SubElement(gen, "lost_mode_with_sound").text = "true"
    mobile_devices = ElementTree.SubElement(command, "mobile_devices")
    mobile_device = ElementTree.SubElement(mobile_devices, "mobile_device")
    ElementTree.SubElement(mobile_device, "serial_number").text = device_serial
    xml_raw = ElementTree.ElementTree(command)
    xml_data = ElementTree.tostring(xml_raw.getroot()).decode("utf-8")

    # API POST run mobile device command
    api_resource = JAMF_URL + "/JSSResource/mobiledevicecommands/command"
    post_command = requests.post(api_resource, auth=(api_user, api_pass), data=xml_data)

    try:
        post_command.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print("Error: " + str(e))
        print(xml_data)
        pass

    return post_command.status_code


def disable_lost_mode(api_user, api_pass, device_serial):
    """Send disable lost mode command by serial number."""
    # Build lost mode command XML
    command = ElementTree.Element("mobile_device_command")
    gen = ElementTree.SubElement(command, "general")
    ElementTree.SubElement(gen, "command").text = "DisableLostMode"
    mobile_devices = ElementTree.SubElement(command, "mobile_devices")
    mobile_device = ElementTree.SubElement(mobile_devices, "mobile_device")
    ElementTree.SubElement(mobile_device, "serial_number").text = device_serial
    xml_raw = ElementTree.ElementTree(command)
    xml_data = ElementTree.tostring(xml_raw.getroot()).decode("utf-8")

    # API POST run mobile device command
    api_resource = JAMF_URL + "/JSSResource/mobiledevicecommands/command"
    post_command = requests.post(api_resource, auth=(api_user, api_pass), data=xml_data)

    try:
        post_command.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print("Error: " + str(e))
        print(xml_data)
        pass

    return post_command.status_code


def main():
    """Do the main thing here."""
    # Argument to file path. Required.
    parser = argparse.ArgumentParser(
        description="Script to enable or disable lost mode for a list of mobile devices."
    )
    parser.add_argument(
        "--csv", "-c", metavar="/path/to/file.csv", help="Path to input CSV",
    )
    parser.add_argument(
        "--mode", "-m", metavar="enable/disable", help="Enable or disable lost mode",
    )
    arg = parser.parse_args()
    csv_file = arg.csv
    mode = arg.mode

    # Check to see if an enable/disable mode was set
    if mode is None:
        print(
            "Requires a mode be specified. Either enable or disable. Specify with --mode or -m."
        )
        sys.exit(1)
    elif mode == "disable" or mode == "enable":
        pass
    else:
        print(
            "Mode needs to be either 'enable' or 'disable'. Specify with --mode or -m."
        )
        sys.exit(1)

    # Get CSV path
    if csv_file is None:
        print("Requires a CSV path. Specify with --csv or -c.")
        sys.exit(1)
    elif os.path.isfile(csv_file):
        pass
    else:
        print("CSV doesn't exist. Check path and try again.")
        sys.exit(1)

    # Prompt for username and password
    creds = get_credentials()

    # Check to see if any devices in the list
    device_list = []
    with open(csv_file, newline="") as csv_data:
        reader = csv.reader(csv_data)
        for _ in reader:
            device_list = list(reader)
    if len(device_list) == 0:
        print("No iPads listed in CSV. No commands to send.")
        sys.exit(1)

    # Loop through CSV and send commands
    with open(csv_file, newline="") as csv_data:
        reader = csv.DictReader(csv_data)
        for row in reader:
            serial_number = row["serial_number"]
            message = row["message"]
            phone = row["phone_number"]
            try:
                sound = row["play_sound"]
            except KeyError:
                sound = None
                pass

            # Send lost mode commands
            if mode == "enable":
                try:
                    if sound is False or sound == "false" or sound == "FALSE":
                        enable_lost_mode(
                            creds[0],
                            creds[1],
                            serial_number,
                            message,
                            phone,
                            sound=False,
                        )
                    else:
                        enable_lost_mode(
                            creds[0], creds[1], serial_number, message, phone
                        )
                except Exception:
                    print(f"Error {serial_number} failed to send lost mode command")
                    pass

            if mode == "disable":
                try:
                    disable_lost_mode(creds[0], creds[1], serial_number)
                except Exception:
                    print(f"Error {serial_number} failed to send lost mode command")
                    pass


if __name__ == "__main__":
    main()
