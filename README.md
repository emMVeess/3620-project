An app to pull data from a bluetooth observer running on a Raspberry Pico 2 W.
Tested on Python 3.11.10 with no issues.

THIS PROGRAM REQUIRES YOU TO HAVE A WORKING BLUETOOTH ADAPTER.

run 'pip install -r requirements.txt' to get requirements to run the app.
Then, just run 'python3 bluetoothConnectionApp.py' to run the app.

On the side of the Raspberry Pico, put /micropython/main.py onto your Pico and then restart it.  The Pico should then start advertising itself as "mpy-temp" to anything that can pick up a Bluetooth signal.
