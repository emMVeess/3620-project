import serial                   #serial library to handle comm with the Pico
import serial.tools.list_ports  #tool for listing available serial ports
import tkinter as tk            # GUI library
from tkinter import ttk, messagebox, scrolledtext  #more Tkinter widgets for better UI
import threading    #Allows concurrent execution to read serial data without freezing the GUI
import time         #used for adding delays during serial read

#Global variables
ser = None  #Serial connection object

#GUI Setup
#creates the main app window, sets the window title, and window size
root = tk.Tk()                      
root.title("Bluetooth Device Scanner")  
root.geometry("600x400")  

#UI Elements
#Creates frame to hold UI 
main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill=tk.BOTH, expand=True) #fill the window

label_title = ttk.Label(main_frame, text="Bluetooth Device Scanner", font=("Arial", 16))
label_title.pack(pady=5)  #padding

#Notification Area
notification_area = scrolledtext.ScrolledText(main_frame, width=70, height=15)  #text area for logs
notification_area.pack(pady=5)

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

#buttons for GUI
button_frame = ttk.Frame(main_frame)
button_frame.pack(pady=5)

init_button = ttk.Button(button_frame, text="Initialize Serial", command=initialize_serial)
init_button.pack(side=tk.LEFT, padx=5)
scan_button = ttk.Button(button_frame, text="Start Scanning", command=start_scan)
scan_button.pack(side=tk.LEFT, padx=5)
test_button = ttk.Button(button_frame, text="Test Connection", command=test_connection)
test_button.pack(side=tk.LEFT, padx=5)
status_button = ttk.Button(button_frame, text="Status", command=check_status)
status_button.pack(side=tk.LEFT, padx=5)
close_button = ttk.Button(button_frame, text="Close Serial", command=close_serial)
close_button.pack(side=tk.LEFT, padx=5)

# close the serial connection
root.protocol("WM_DELETE_WINDOW", close_serial)
root.mainloop()  # Run GUI 