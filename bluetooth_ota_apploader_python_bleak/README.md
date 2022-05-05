# OTA (Apploader) from PC w/ BLE

## Summary ##
This python script allows your computer to perform an OTA upgrade on an EFR device that uses the
Apploader to handle the OTA as outlined in [AN1086](https://www.silabs.com/documents/public/application-notes/an1086-gecko-bootloader-bluetooth.pdf) Chapter 3. The python script uses the [Bluetooth Low Energy platform Agnostic Klient (BLEAK)](https://bleak.readthedocs.io/en/latest/index.html) python library to access the computer's Bluetooth hardware.


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
Include the OTA service component into your app like normal, by adding the "OTA DFU" component if
not already included.  The "Bluetooth - SoC Empty" example/template project includes this by default.

Once you have a BLE project whose application handles the OTA firmware upgrade, we need to create the GBL images that will be uploaded to the EFR device.
1. Open the top level directory of the Simplicity Studio BLE project in the terminal (command prompt)
2. Run the create_bl_files.* script. You may need to modify permissions using the chmod command.
    - create_bl_files.sh for Linux or Mac
    - create_bl_files.bat for Windows
3. Copy the `output_gbl/full.gbl` file into the same directory as the sl-ota-apploader.py script or save the absolute path to the file.

## How It Works ##
### Computer with BLE
To print the help text, run the following command:
```
$ python3 sl-ota-apploader.py -h
```

To perform an OTA, use the following command:
```
$ python3 sl-ota-apploader.py -d <device name or address> -f <file to ota>
```
An example use case after following the [Setup](#Setup) instruction:
```
$ python3 sl-ota-apploader.py -d "Empty Example" -f application.gbl
```

When the python script performs the OTA, the computer is following the procedure listed in [AN1086](https://www.silabs.com/documents/public/application-notes/an1086-gecko-bootloader-bluetooth.pdf).

### EFR Device
[AN1086](https://www.silabs.com/documents/public/application-notes/an1086-gecko-bootloader-bluetooth.pdf) section 3 have more detailed information on the EFR device-side works.

## Special Notes ##
BLEAK was used to keep the script OS independent. Native APIs such as BlueZ or Windows C# Bluetooth API can be used for finer control with the target OS.
Still, at this point in time, the script has only been tested on Linux, with BlueZ 5.64.
Additionally, you _must_ edit your /etc/bluetooth/main.conf and set ```Cache=yes``` at least.  If you need to
do OTA updates of _paired_ devices, you must set ```Cache=no```
See https://github.com/hbldh/bleak/discussions/816 for more information

