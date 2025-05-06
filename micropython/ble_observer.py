import sys

# ruff: noqa: E402
sys.path.append("")

from micropython import const

import asyncio
import aioble
import bluetooth

import random
import struct

# org.bluetooth.service.GATT
_ENV_SENSE_UUID = bluetooth.UUID("a9d6ede1-f904-4419-b4ea-02d9d5af1577")
# org.bluetooth.characteristic.64-string
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


# Helper to encode the temperature characteristic encoding (sint16, hundredths of a degree).



# This would be periodically polling a hardware sensor.
async def sensor_task():
    while True:
        async with aioble.scan(duration_ms=1000) as scanner:
            async for result in scanner:
                temp_characteristic.write((str(result.name()) + "," + str(result.device) + "," + str(result.rssi)).encode('utf-8'), send_update = True)
                await asyncio.sleep_ms(10)
            await asyncio.sleep_ms(500)

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
