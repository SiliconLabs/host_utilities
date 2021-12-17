# OTA from PC w/ BLE

## Summary ##
This python script allows your computer to perform an OTA upgrade on an EFR device that uses the User Application to handle the OTA as outlined in [AN1086](https://www.silabs.com/documents/public/application-notes/an1086-gecko-bootloader-bluetooth.pdf) section 4. The python script uses the [Bluetooth Low Energy platform Agnostic Klient (BLEAK)](https://bleak.readthedocs.io/en/latest/index.html) python library to access the computer's Bluetooth hardware.

Due to the limitations with BLEAK on MAC, a firmware upgrade using the Apploader is not operational so the script is tailored to User Application based OTA upgrades.

## Software versions ##
Gecko SDK 3.0 or newer
- Bluetooth SDK 3.0 or newer
Python 3.6 or newer

## Hardware Required ##
Any BLE compatible Silicon Labs device. The following parts are what we recommend:
- EFR32xG21 or EFR32xG22 (x= M, B) SoCs
- xGM210 or xGM220 (x= M, B) Modules
*Series 1 devices are also acceptable*

Any computer that is capable of BLE can be used. The BLEAK API is meant to be OS independent.

## Setup ##
### Computer with BLE
1. Install the latest version of [Python](https://www.python.org/downloads/)
2. Install the required python library dependencies. This script uses [BLEAK](https://bleak.readthedocs.io/en/latest/index.html) to interface with the computer's Bluetooth hardware. To ensure all required dependencies are installed run the following:
    ```
    $ pip install -r requirements.txt
    ```

### EFR Device
Modify the application to handle the OTA instead of using the Apploader which is used by default. This example code has instructions and documentation on setting up a project to handle an OTA through the User Application:
- [OTA handled by the User Application](https://github.com/SiliconLabs/bluetooth_applications/tree/2d1e2b5e0893950fe54f13d7d52f4949c0a116ab/ota_firmware_update_in_user_application)

Once you have a BLE project whose application handles the OTA firmware upgrade, we need to create the GBL images that will be uploaded to the EFR device.
1. Open the top level directory of the Simplicity Studio BLE project in the terminal (command prompt)
2. Run the create_bl_files.* script. You may need to modify permissions using the chmod command.
    - create_bl_files.sh for Linux or Mac
    - create_bl_files.bat for Windows
3. Copy the `output_gbl/full.gbl` file into the same directory as the ota_application_based.py script or save the absolute path to the file.

## How It Works ##
### Computer with BLE
To print the help text, run the following command:
```
$ python3 ota_application_based.py -h
```

To perform an OTA, use the following command:
```
$ python3 ota_application_based.py -d <device name> -f <file to ota>
```
An example use case after following the [Setup](#Setup) instruction:
```
$ python3 ota_application_based.py -d "Empty Example" -f full.gbl
```

When the python script performs the OTA, the computer is following the procedure listed in [AN1086](https://www.silabs.com/documents/public/application-notes/an1086-gecko-bootloader-bluetooth.pdf).

### EFR Device
[AN1086](https://www.silabs.com/documents/public/application-notes/an1086-gecko-bootloader-bluetooth.pdf) section 4 and the example code linked above have more detailed information on the EFR device-side works.

## Special Notes ##
This script was only tested with EFR devices using the User Application to handle the OTA firmware upgrades. Due to the limitations with BLEAK on MAC, a firmware upgrade using the Apploader is not operational so the script is tailored to User Application based OTA upgrades to keep the script compatible with all Operating Systems.

BLEAK was used to keep the script OS independent. Native APIs such as BlueZ or Windows C# Bluetooth API can be used for finer control with the target OS.
