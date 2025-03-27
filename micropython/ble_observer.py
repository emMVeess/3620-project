# Global dictionaries for printing
device_map = {}
device_info = {}
device_id = 1

import sys

# ruff: noqa: E402
sys.path.append("")

from micropython import const

import asyncio
import aioble
import bluetooth
import random
import struct

#
#   VARIABLE NAMES ARE UNCHANGED FROM AN EXAMPLE
#   DO NOT EXPECT THEM TO BE WHAT THEY SAY THEY ARE
#

# org.bluetooth.service.GATT
_ENV_SENSE_UUID = bluetooth.UUID("a9d6ede1-f904-4419-b4ea-02d9d5af1577")
# org.bluetooth.characteristic.s64
_ENV_SENSE_TEMP_UUID = bluetooth.UUID("497d8d32-1e96-42b9-8041-d3ee7acc24e0")
# org.bluetooth.characteristic.gap.appearance.xml
_ADV_APPEARANCE_GENERIC_THERMOMETER = const(128)

# How frequently to send advertising beacons.
_ADV_INTERVAL_MS = 250_000


# Register GATT server.
temp_service = aioble.Service(_ENV_SENSE_UUID)
temp_characteristic = aioble.Characteristic(
    temp_service, _ENV_SENSE_TEMP_UUID, read=True, notify=True
)
aioble.register_services(temp_service)

'''
Prints devicelabel#, MAC Address, latest RSSI, and times seen
'''
def print_device_list():
    print("\n" + "-" * 50)

    #Sort by Device #
    sorted_items = sorted(
        device_map.items(),
        key=lambda item: int(item[1].split(" ")[1])
    )

    for mac_full, label in sorted_items:
        # Extract just the MAC ad from "Device(ADDR_RANDOM, xx:xx:xx:xx:xx:xx)"
        mac_clean = mac_full.split(", ")[1][:-1] if ", " in mac_full else mac_full

        rssi = device_info[mac_full]['rssi']
        count = device_info[mac_full]['seen']
        print(f"{label} | MAC: {mac_clean} | RSSI: {rssi} | Seen: {count}x")

    print("-" * 50 + "\n")

# This would be periodically polling a hardware sensor.
'''
sensor_task now tracks all devices by MAC address, assings each device a #,
keeps counter of how many times a device is seen, Updates RSSI per detection
calls def print_device_list to print
'''
async def sensor_task():
    global device_map, device_info, device_id

    while True:
        async with aioble.scan(duration_ms=500) as scanner:
            async for result in scanner:
                mac = str(result.device)

                if mac not in device_map:
                    device_map[mac] = f"Device {device_id}"
                    device_info[mac] = {
                        'rssi': result.rssi,
                        'seen': 1
                    }
                    device_id += 1
                else:
                    device_info[mac]['seen'] += 1
                    device_info[mac]['rssi'] = result.rssi

                print_device_list()
                
    #Old version of def sensor_task-to be deleted
    '''
    while True:
        async with aioble.scan(duration_ms=500) as scanner:
            async for result in scanner:
                #temp_characteristic.write((str(result.name()) + "," + str(result.device) + "," + str(result.rssi)).encode('utf-8'), send_update = True)
                print((str(result.name()) + "," + str(result.device) + "," + str(result.rssi)).encode('utf-8'))
    '''

# Serially wait for connections. Don't advertise while a central is
# connected.
async def peripheral_task():
    while True:
        async with await aioble.advertise(
            _ADV_INTERVAL_MS,
            name="mpy-temp",
            services=[_ENV_SENSE_UUID],
            appearance=_ADV_APPEARANCE_GENERIC_THERMOMETER,
        ) as connection:
            print("Connection from", connection.device)
            await connection.disconnected(timeout_ms=None)


# Run both tasks.
async def main():
    t1 = asyncio.create_task(sensor_task())
    t2 = asyncio.create_task(peripheral_task())
    await asyncio.gather(t1, t2)


asyncio.run(main())
