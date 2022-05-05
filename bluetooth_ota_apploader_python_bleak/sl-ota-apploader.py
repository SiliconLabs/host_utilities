#!/usr/bin/env python3
"""
sl-ota-apploader: Implements bluetooth OTA flashing for SiLabs EFR32 devices, using the AppLoader.

This is "Standalone Bootloader Operation" mode, in UG489.  Silabs provides demo code
for "Application Bootloader Operation" mode at
https://github.com/SiliconLabs/host_utilities/blob/feature/bluetooth_ota_python_bleak/bluetooth_ota_python_bleak

Requirements:
Your Bluez configuration _must_ have Cache=yes (or no) to work.  It _will not_ work with the default Cache=always.
See https://github.com/hbldh/bleak/discussions/816

Your application must provide the minimum service hooks as described in Ch 3.6,
"Triggering Reboot into DFU Mode from the User Application" of AN1086.
(In other words, provide the OTA service, the control characteristic, and handle the reboot)

Tested on: Linux, with Bluez 5.64

See also:
    UG489 - Gecko bootloader user guide (gsdk 4+)
    AN1086 - Gecko bootloader Bluetooth
"""
import argparse
import asyncio
import logging
import struct
import time
import uuid

import bleak
import bleak.backends.device
import bleak.backends.scanner
import bleak.backends.service
import bleak.uuids


class SL_OTA_UUIDS:
    SVC = uuid.UUID("1d14d6ee-fd63-4fa1-bfa4-8f47b42119f0")
    CCONTROL = uuid.UUID("F7BF3564-FB6D-4E53-88A4-5E37E0326063")
    CDATA =    uuid.UUID("984227F3-34FC-4045-A5D0-2C581F81A153")
    CAPPLOADER_VERSION = uuid.UUID("4F4A2368-8CCA-451E-BFFF-CF0E2EE23E9F")
    COTA_VERSION = uuid.UUID("4CC07BCF-0868-4B32-9DAD-BA4CC41E5316")
    CGECKO_BL_VERSION = uuid.UUID("25F05C0A-E917-46E9-B2A5-AA2BE1245AFE")
    CAPP_VERSION = uuid.UUID("0D77CC11-4AC1-49F2-BFA9-CD96AC7A92F8")


class SL_OTA_COMMANDS:
    START = bytearray([0])
    FINISH = bytearray([3])
    DISCONNECT = bytearray([4])  # This will also reboot, which is fine...


#logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s %(message)s', level=logging.DEBUG)
#logging.getLogger("bleak").setLevel(logging.INFO)


class SL_OTA_Helper():
    """
    Simple helper to parse the OTA version information, only used for printing in this app
    """
    def __init__(self, client: bleak.BleakClient):
        self.c = client
        self._loaded = False

    async def load_ota_info(self):
        al_ver = await self.c.read_gatt_char(SL_OTA_UUIDS.CAPPLOADER_VERSION)
        self.al_maj, self.al_minor, self.al_patch, self.al_build = struct.unpack("<HHHH", al_ver)
        ota_ver = await self.c.read_gatt_char(SL_OTA_UUIDS.COTA_VERSION)
        self.ota_ver = ota_ver[0]
        gecko_ver = await self.c.read_gatt_char(SL_OTA_UUIDS.CGECKO_BL_VERSION)
        self.gk_maj, self.gk_minor, self.cust_version = struct.unpack("<BBH", gecko_ver)

        self._loaded = True

    def __repr__(self):
        if self._loaded:
            return f"AppLoader {self.al_maj}.{self.al_minor}.{self.al_patch}-{self.al_build}, "\
                    f"OTA: {self.ota_ver}, Gecko {self.gk_maj}.{self.gk_minor}, customer: {self.cust_version:#06x}"
        return f"Unprobed {self.c}"


def get_args():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--device", help="Device to connect to",
                        #required=True,
                        default="D0:CF:5E:D9:12:3D")
    parser.add_argument("--reliable", help="Use acknowledged writes, slower, but more reliable", default=False, action="store_true")
    parser.add_argument("-f", "--file", help="OTA upgrade file", type=argparse.FileType('rb'), required=True)
    options = parser.parse_args()
    return options


async def runthing(opts):
    def my_filter(dev: bleak.backends.device.BLEDevice, adv: bleak.backends.scanner.AdvertisementData):
        if dev.address == opts.device:
            logging.info("Matched by address!")
            return True
        if dev.name == opts.device:
            logging.info("Matched by name!")
            return True
        logging.debug("ignoring: %s (%s)", dev.address, dev.name)
        return False

    dev = await bleak.BleakScanner.find_device_by_filter(my_filter)
    if not dev:
        raise bleak.BleakError(f"Couldn't find a matching device for: {opts.device}")

    disconn_event = asyncio.Event()

    def handle_disconnect1(d: bleak.BleakClient):
        logging.debug("Lost connection with: %s (this is expected)", d)
        disconn_event.set()

    print(f"Device found: {dev}, attempting to connect...", end='', flush=True)
    async with bleak.BleakClient(dev, disconnected_callback=handle_disconnect1) as client1:
        print("...Connected!")
        svcs = await client1.get_services()
        # Find any matching services. We _expect_ one, and only one, but we get cached with different handle ids...
        sl_ota = [s for s in svcs if s.uuid == str(SL_OTA_UUIDS.SVC)]
        # for s in sl_ota:
        #     [print(f"SL OTA handle: {s.handle} char: {c.handle} uuid: {c.uuid} desc: {c.description} ") for c in s.characteristics]
        if len(sl_ota) < 1:
            raise bleak.BleakError(f"Device doesn't appear to have the OTA service?")

        # FIXME - handle already being in OTA mode?
        print(f"Requesting app reboot into OTA mode...", end='', flush=True)
        await client1.write_gatt_char(SL_OTA_UUIDS.CCONTROL, SL_OTA_COMMANDS.START, True)
        logging.debug(f"Waiting to be disconnected from App")
        await disconn_event.wait()
    print(f"...Rebooted!")

    async with bleak.BleakClient(dev) as client2:
        svcs = await client2.get_services()
        sl_ota = [s for s in svcs if s.uuid == str(SL_OTA_UUIDS.SVC)]
        # for s in sl_ota:
        #     [print(f"SL OTA handle: {s.handle} char: {c.handle} uuid: {c.uuid} desc: {c.description} ") for c in s.characteristics]
        if len(sl_ota) < 1:
            raise bleak.BleakError(f"Device doesn't appear to have the OTA service?")

        logging.debug("Fetching OTA version information")
        helper = SL_OTA_Helper(client2)
        await helper.load_ota_info()
        print(f"OTA version information: {helper}")

        print(f"Determining MTU available...", end='', flush=True)
        await client2._acquire_mtu()
        print(f"MTU = {client2.mtu_size}")

        # You _must_ reissue this command to the AppLoader as well!
        await client2.write_gatt_char(SL_OTA_UUIDS.CCONTROL, SL_OTA_COMMANDS.START, True)
        gbl_img = bytearray(opts.file.read())
        fsize = len(gbl_img)
        t_start = time.time()
        chunk_size = client2.mtu_size - 3    # 3 bytes for Write ATT operation
        chunks = (fsize // chunk_size) + 1
        print(f"Uploading {fsize} bytes in {chunks} chunks of {chunk_size}")
        for idx,chunk in enumerate((
                gbl_img[i : i + chunk_size] for i in range(0, fsize, chunk_size)
        )):
            logging.debug(f"Uploading chunk: {idx+1}/{chunks}")
            if opts.reliable:
                await client2.write_gatt_char(SL_OTA_UUIDS.CDATA, chunk, True)
            else:
                await client2.write_gatt_char(SL_OTA_UUIDS.CDATA, chunk, False)
                await asyncio.sleep(.002)  # lol, spray and pray!
            if idx > 0 and idx % 60 == 0:
                print("")
            print(".", end='', flush=True)
        print("")

        t_delta = time.time() - t_start
        print(f"Upload complete, wrote {fsize}B in {t_delta:.2f}sec ({fsize / t_delta:0.2f} Bps / {fsize*8/t_delta:0.2f} bps)")
        print(f"Returning to Application mode.")
        await client2.write_gatt_char(SL_OTA_UUIDS.CCONTROL, SL_OTA_COMMANDS.FINISH, True)


async def domain(opts):
    bleak.uuids.register_uuids({
        str(SL_OTA_UUIDS.SVC): "SiLabs OTA service",
        str(SL_OTA_UUIDS.CCONTROL): "SL OTA Control",
        str(SL_OTA_UUIDS.CDATA): "SL OTA Data",
        str(SL_OTA_UUIDS.CAPPLOADER_VERSION): "SL OTA AppLoader Version",
        str(SL_OTA_UUIDS.CGECKO_BL_VERSION): "SL OTA Gecko BL Version",
        str(SL_OTA_UUIDS.COTA_VERSION): "SL OTA Version",
        str(SL_OTA_UUIDS.CAPP_VERSION): "SL OTA App version",
    })
    await runthing(opts)


if __name__ == "__main__":
    a = get_args()
    asyncio.run(domain(a))
