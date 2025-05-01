import reciever_modular         # Bluetooth functions # type: ignore
import serial                   # type: ignore #serial library to handle comm with the Pico
import serial.tools.list_ports  # type: ignore #tool for listing available serial ports
import tkinter as tk            # GUI library
from tkinter import ttk, messagebox, scrolledtext  #more Tkinter widgets for better UI
import threading    #Allows concurrent execution to read serial data without freezing the GUI
import time         #used for adding delays during serial read
from matplotlib.figure import Figure # type: ignore
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # type: ignore
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk # type: ignore
import numpy as np # type: ignore

#Global variables
ser = None
adapter = None #selected adapter
peripherals = [] #found peripherals
peripheral = None #selected peripheral
service_characteristics = [] #available service/characteristic pairs from peripheral
service = None #selected service-characteristic pair
found_addresses = dict() #collection of our addresses stored as a dict
results = [] #collection of address/name strings to display
displayed = False #display check

#GUI Setup
#creates the main app window, sets the window title, and window size
root = tk.Tk()                      
root.title("Bluetooth Device Scanner")  
root.geometry("800x600")  

#UI Elements
#Creates frame to hold UI 
main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill=tk.BOTH, expand=True) #fill the window

label_title = ttk.Label(main_frame, text="Bluetooth Device Scanner", font=("Arial", 16))
label_title.pack(pady=5)  #padding

#Notification Area
notification_area = scrolledtext.ScrolledText(main_frame, width=70, height=15)  #text area for logs
notification_area.pack(pady=5)

#combobox frame
combobox_frame = ttk.Frame(main_frame)
combobox_frame.pack(pady=5)

#Peripheral combobox
peripheral_boxvar = tk.StringVar()
peripheral_box = ttk.Combobox(combobox_frame, textvariable=peripheral_boxvar, width=30, height=5)
peripheral_box['state'] = 'readonly'
peripheral_box.pack(side=tk.LEFT, padx=5, pady=5)

#service/characteristic combobox
service_boxvar = tk.StringVar()
service_box = ttk.Combobox(combobox_frame, textvariable=service_boxvar, width=30, height=5)
service_box['state'] = 'readonly'
service_box.pack(side=tk.LEFT, padx=5, pady=5)

#found addresses combobox
address_boxvar = tk.StringVar()
address_box = ttk.Combobox(combobox_frame, textvariable=address_boxvar, width=30, height=5)
address_box['state'] = 'readonly'
address_box.pack(side=tk.LEFT, padx=5, pady=5)

graph_frame = ttk.Frame(main_frame)

fig = Figure(figsize=(10, 10), dpi=100)
ax = fig.add_subplot()
ax.set_ylabel("RSSI")
canvas = FigureCanvasTkAgg(fig, master=graph_frame)  # A tk.DrawingArea.
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# -------------- SERIAL STUFF ------------------
# Initialize Serial Connection
def detect_pico():
    ports = serial.tools.list_ports.comports()  #get list of available serial ports
    for port in ports:
        if "Pico" in port.description or "USB Serial Device" in port.description:
            return port.device  #return the port name if a Pico is detected
    return None                 #return None if no Pico is found

def initialize_serial():
    global ser
    pico_port = detect_pico()  #try detect the Pico
    if pico_port:
        try:
            ser = serial.Serial(pico_port, 115200, timeout=1)  #open port 115200
            messagebox.showinfo("Success", f"Pico detected on {pico_port} and initialized!")
            notification_area.insert(tk.END, f"Pico detected on {pico_port}\n")
            start_reading_serial()  #read data from the Pico
        except serial.SerialException as e:
            messagebox.showerror("Error", f"Could not open serial port: {e}")
    else:
        messagebox.showwarning("Warning", "No Pico device detected. Please connect your Pico.")

#close Serial Connection
def close_serial():
    global ser
    if ser and ser.is_open:
        ser.close()
        notification_area.insert(tk.END, "Serial connection closed.\n")

#Send Test Connection to Pico
def test_connection():
    global ser
    if ser and ser.is_open:
        try:
            ser.write(b'test_connection\n')
            notification_area.insert(tk.END, "Sent test connection command to Pico.\n")
        except Exception as e:
            notification_area.insert(tk.END, f"Error sending test connection: {e}\n")
    else:
        messagebox.showwarning("Warning", "Serial connection not initialized.")

#send Status Command to Pico
def check_status():
    global ser
    if ser and ser.is_open:
        try:
            ser.write(b'status\n')
            notification_area.insert(tk.END, "Sent status command to Pico.\n")
        except Exception as e:
            notification_area.insert(tk.END, f"Error sending status command: {e}\n")
    else:
        messagebox.showwarning("Warning", "Serial connection not initialized.")

#start Scanning Command
def start_scan():
    global ser
    if ser and ser.is_open:
        try:
            ser.write(b'start_scan\n')
            notification_area.insert(tk.END, "Sent start scan command to Pico.\n")
        except Exception as e:
            notification_area.insert(tk.END, f"Error sending start scan command: {e}\n")
    else:
        messagebox.showwarning("Warning", "Serial connection not initialized.")

#read from Serial and display data
def read_from_serial():
    global ser
    while ser and ser.is_open:
        try:
            line = ser.readline().decode("utf-8").strip()  #reads line
            if line:
                notification_area.insert(tk.END, f"{line}\n")  # prints the line
                notification_area.see(tk.END)  #auto scrolls to show latest message
        except Exception as e:
            notification_area.insert(tk.END, f"Error reading from serial: {e}\n")
        time.sleep(0.1)  #delay between reads

#start a separate thread to read from serial
def start_reading_serial():
    read_thread = threading.Thread(target=read_from_serial, daemon=True)  #Create a background thread for reading
    read_thread.start()

# --------------------- BLUETOOTH STUFF ---------------------
#Initialize available Bluetooth adapters
def initialize_adapter():
    adapter_thread = threading.Thread(target=get_adapters(), daemon=True)
    adapter_thread.start() #select all adapters

def get_adapters():
    global adapter
    adapters = reciever_modular.get_available_adapters() #get all Bluetooth adapters, formatted in list
    if len(adapters) == 0:
        messagebox.showwarning("Warning", "No Bluetooth adapter available.")
    else:
        adapter = adapters[0] #defaulting to adapter 0, often the only adapter available
        notification_area.insert(tk.END, f"Initialized adapter {adapter.identifier()} (Address: {adapter.address()})\n")
        notification_area.insert(tk.END, "Scanning for available devices...\n")
        scan_thread = threading.Thread(target=scan_devices, daemon=True) #start scanning for available devices to connect to
        scan_thread.start()

def scan_devices():
    global adapter
    global peripherals
    peripherals = reciever_modular.scan_for_devices(adapter) #scan for available devices for 5 seconds
    notification_area.insert(tk.END, "finished scanning.\n")
    result = list(map(lambda a: f"{a.identifier()} [{a.address()}]", peripherals)) 
    peripheral_box['values'] = result #put human-readable names into first combobox
    peripheral_box.current(0)

def set_peripheral():
    global peripheral
    global peripherals
    selected = peripheral_box.current() #get index of peripheral box, use parallel list to actually select
    peripheral = peripherals[selected]
    notification_area.insert(tk.END, "Connecting to selected peripheral...\n")
    peripheral_thread = threading.Thread(target=connect_peripheral, daemon=True) 
    peripheral_thread.start() #actually connect to peripheral

def connect_peripheral():
    global peripheral
    global service_characteristics
    peripheral.connect()
    result = []
    notification_area.insert(tk.END, "Peripheral connected! getting services...\n")
    services = peripheral.services()
    for s in services:
        for c in s.characteristics():
            service_characteristics.append((s.uuid(), c.uuid())) #putting services into a tuple
    for (s, c) in service_characteristics:
        result.append(f"{s} {c}") #putthing the tuples into a human-readable list, using parallel list to actually control
    service_box['values'] = result
    service_box.current(0)

def set_characteristic():
    global peripheral
    global service_characteristics
    global service
    result = service_box.current()
    service = service_characteristics[result]
    notification_area.insert(tk.END, f"Service-Characteristic pair set.\n")

def start_observing():
    observer_thread = threading.Thread(target=observer, daemon=True)
    observer_thread.start()

def observer():
    global peripheral
    global service
    s, c = service
    peripheral.notify(s, c, lambda data: deconstruct_data(data))
    
def deconstruct_data(data):
    global found_addresses
    global results
    test = data.decode('utf-8').split(',')
    name = test[0]
    address = test[2][1:18]
    rssi = test[3]
    
    notification_area.insert(tk.END, f"GOT: Name: {name}, Address: {address}, RSSI: {rssi}\n")
    notification_area.see(tk.END)
    
    if address in found_addresses.keys():
        found_addresses[address]["rssi"].append(int(rssi))
    else:
        this_address = {"name": name, "rssi": [int(rssi)]}
        results.append(f"{address} ({this_address['name']})")
        found_addresses.update({address: this_address})

    if displayed:
        ax.cla()
        result = address_box.get()
        result = result[0:17]
        ax.plot(found_addresses[result]['rssi'], color='green')
        canvas.draw()
    
    address_box['values'] = results
    
def stop_observing():
    disconnect_thread = threading.Thread(target=disconnect, daemon=True)
    disconnect_thread.start()

def disconnect():
    global peripheral
    try:
        peripheral.disconnect()
    except RuntimeError:
        print("Runtime error")
    notification_area.insert(tk.END, f"Disconnected from peripheral.\n")

def close_app():
    root.destroy()

def graph_selected():
    result = address_box.get()
    if result == "":
        messagebox.showwarning("Warning", "No address found.")
        return
    result = result[0:17]
    graph_thread = threading.Thread(target=make_graph(result), daemon=True)
    graph_thread.start()

    
def make_graph(result):
    global displayed
    ax.plot(found_addresses[result]['rssi'], color='green')
    canvas.draw()
    displayed = True


#buttons for GUI
button_frame = ttk.Frame(main_frame)
button_frame.pack(pady=5)

init_button = ttk.Button(button_frame, text="Initialize Bluetooth Adapter", command=initialize_adapter)
init_button.pack(side=tk.LEFT, padx=5)
scan_button = ttk.Button(button_frame, text="Set Peripheral", command=set_peripheral)
scan_button.pack(side=tk.LEFT, padx=5)
test_button = ttk.Button(button_frame, text="Set Characteristic", command=set_characteristic)
test_button.pack(side=tk.LEFT, padx=5)
status_button = ttk.Button(button_frame, text="Start Observing", command=start_observing)
status_button.pack(side=tk.LEFT, padx=5)
close_button = ttk.Button(button_frame, text="Disconnect from Observer", command=stop_observing)
close_button.pack(side=tk.LEFT, padx=5)
graph_button = ttk.Button(button_frame, text="Graph Selected", command=graph_selected)
graph_button.pack(side=tk.LEFT, padx=5)

graph_frame.pack(pady=5)
# close the serial connection
root.protocol("WM_DELETE_WINDOW", close_app)
root.mainloop()  # Run GUI 