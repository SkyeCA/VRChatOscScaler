import tkinter as tk
from tkinter import messagebox
import threading
import time
from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server

# VRChat default OSC ports
VRCHAT_OSC_IN_PORT = 9000   # Port VRChat listens on
VRCHAT_OSC_OUT_PORT = 9001  # Port VRChat sends to
IP = "127.0.0.1"
TIMEOUT_SECONDS = 5.0       # How long without data before we assume VRC is disconnected

class VRChatEyeHeightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VRChat OSC Scaler")
        self.root.geometry("380x200") # Slightly smaller window since we removed a label
        self.root.resizable(False, False)

        # Default to True unless explicitly denied
        self.scaling_allowed = True
        self.current_height = 1.0
        self.last_osc_time = 0.0
        self.is_connected = False

        # Set up the OSC Client (Sends to VRChat)
        self.client = udp_client.SimpleUDPClient(IP, VRCHAT_OSC_IN_PORT)

        self.setup_ui()
        self.start_osc_server()
        
        # Start the connection monitor loop
        self.root.after(1000, self.check_connection_loop)

    def setup_ui(self):
        # Connection Status
        self.conn_var = tk.StringVar(value="Status: DISCONNECTED")
        self.conn_label = tk.Label(self.root, textvariable=self.conn_var, fg="red", font=("Arial", 10, "bold"))
        self.conn_label.pack(pady=(15, 5))

        # Scaling Status
        self.allowed_var = tk.StringVar(value="Scaling Status: ALLOWED")
        self.allowed_label = tk.Label(self.root, textvariable=self.allowed_var, fg="green", font=("Arial", 9))
        self.allowed_label.pack(pady=5)

        # Input Frame
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Eye Height (0.01 - 10000):").pack(side=tk.LEFT)

        self.height_var = tk.DoubleVar(value=self.current_height)
        self.entry = tk.Entry(input_frame, textvariable=self.height_var, width=12)
        self.entry.pack(side=tk.LEFT, padx=5)

        self.send_btn = tk.Button(self.root, text="Update Height", command=self.send_height, bg="#e0e0e0")
        self.send_btn.pack(pady=5)

        # Disable inputs initially until we get a connection heartbeat
        self.entry.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)

    def check_connection_loop(self):
        # Check if we've received any OSC data recently
        time_since_last_msg = time.time() - self.last_osc_time

        if time_since_last_msg > TIMEOUT_SECONDS:
            if self.is_connected:
                self.is_connected = False
                self.conn_var.set("Status: DISCONNECTED")
                self.conn_label.config(fg="red")
                self.entry.config(state=tk.DISABLED)
                self.send_btn.config(state=tk.DISABLED)
        else:
            if not self.is_connected:
                self.is_connected = True
                self.conn_var.set("Status: CONNECTED")
                self.conn_label.config(fg="green")
                # Enable inputs immediately upon connection if scaling is allowed
                if self.scaling_allowed:
                    self.entry.config(state=tk.NORMAL)
                    self.send_btn.config(state=tk.NORMAL)

        # Check again in 1 second
        self.root.after(1000, self.check_connection_loop)

    def send_height(self):
        if not self.scaling_allowed:
            messagebox.showerror("Disabled", "Scaling is currently disabled by the VRChat avatar.")
            return

        try:
            val = float(self.height_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid numeric value.")
            return

        if val < 0.01:
            val = 0.01
            self.height_var.set(val)
        elif val > 10000.0:
            val = 10000.0
            self.height_var.set(val)

        if val < 0.1 or val > 100.0:
            proceed = messagebox.askyesno(
                "Extreme Value Warning", 
                f"Value {val} is outside the typical range (0.1 - 100).\n\nAre you sure you want to send this?"
            )
            if not proceed:
                return

        self.client.send_message("/avatar/eyeheight", val)

    def osc_heartbeat(self, address, *args):
        # Any incoming message updates our last seen timer
        self.last_osc_time = time.time()

    def handle_eyeheight(self, address, *args):
        self.last_osc_time = time.time()
        if args:
            val = args[0]
            self.current_height = val
            # Update the entry box automatically when VRChat changes the height
            self.root.after(0, self.height_var.set, val)

    def handle_scaling_allowed(self, address, *args):
        self.last_osc_time = time.time()
        if args:
            self.scaling_allowed = bool(args[0])
            if self.scaling_allowed:
                self.root.after(0, self.allowed_var.set, "Scaling Status: ALLOWED")
                self.root.after(0, lambda: self.allowed_label.config(fg="green"))
                if self.is_connected:
                    self.root.after(0, lambda: self.send_btn.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.entry.config(state=tk.NORMAL))
            else:
                self.root.after(0, self.allowed_var.set, "Scaling Status: DISABLED")
                self.root.after(0, lambda: self.allowed_label.config(fg="red"))
                self.root.after(0, lambda: self.send_btn.config(state=tk.DISABLED))
                self.root.after(0, lambda: self.entry.config(state=tk.DISABLED))

    def start_osc_server(self):
        disp = dispatcher.Dispatcher()
        
        # Catch-all to act as our connection heartbeat
        disp.set_default_handler(self.osc_heartbeat) 
        
        # Specific handlers
        disp.map("/avatar/eyeheight", self.handle_eyeheight)
        disp.map("/avatar/eyeheightscalingallowed", self.handle_scaling_allowed)

        server = osc_server.ThreadingOSCUDPServer((IP, VRCHAT_OSC_OUT_PORT), disp)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = VRChatEyeHeightApp(root)
    root.mainloop()