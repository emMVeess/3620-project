import simplepyble
import time

adapter = ""
peripheral = ""
services = ""
characteristic = ""
service = ""

def get_available_adapters():
    adapters = simplepyble.Adapter.get_adapters()
    if len(adapters) == 0:
        return False
    return adapters #returns a list of adapter objects


def set_adapter(selected_adapter):  # requires an adapter object
    global adapter
    adapter = selected_adapter
    print(f"Selected adapter: {selected_adapter.identifier()} [{selected_adapter.address()}]")
    

def scan_for_devices():
    adapter.scan_for(5000)
    peripherals = adapter.scan_get_results()
    return peripherals #returns a list of peripheral objects

def select_connection(selected_peripheral): #requires a peripheral object
    global peripheral
    peripheral = selected_peripheral
    peripheral.connect()

def get_services(): 
    services = peripheral.services()
    service_characteristic_pair = []
    for service in services:
        for characteristic in service.characteristics():
            service_characteristic_pair.append((service.uuid(), characteristic.uuid()))
    return service_characteristic_pair #returns a list of tuples containing service-uuid, characteristic-uuid

def set_service(selected_service_characteristic_pair): #requires a tuple containing service-uuid, characteristic-uuid in that order
    global service
    global characteristic
    service, characteristic = selected_service_characteristic_pair


def subscribe_to_notifications(timesleep): #reuqires an int to tell the system to sleep for x seconds
    global service
    global characteristic
    peripheral.notify(service, characteristic, lambda data: print(f"Notification: {data.decode("utf-8")}"))
     # subscribes to notifications, running the callback function (lambda) every time the system sees it update
    time.sleep(timesleep)

    peripheral.disconnect()