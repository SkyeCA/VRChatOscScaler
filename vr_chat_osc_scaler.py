import tkinter as tk
from tkinter import messagebox
import threading
import time
import webbrowser
from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server

# VRChat default OSC ports
VRCHAT_OSC_IN_PORT = 9000
VRCHAT_OSC_OUT_PORT = 9001
IP = "127.0.0.1"
TIMEOUT_SECONDS = 5.0

class VRChatEyeHeightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VRChat OSC Scaler")
        self.root.geometry("380x280")
        self.root.resizable(False, False)

        self.scaling_allowed = True
        self.current_height = 1.0
        self.last_osc_time = 0.0
        self.is_connected = False
        
        # Threading control for transitions
        self.transition_thread = None
        self.cancel_transition = False

        self.client = udp_client.SimpleUDPClient(IP, VRCHAT_OSC_IN_PORT)

        self.setup_ui()
        self.start_osc_server()
        self.root.after(1000, self.check_connection_loop)

    def setup_ui(self):
        # Status labels
        self.conn_var = tk.StringVar(value="Status: DISCONNECTED")
        self.conn_label = tk.Label(self.root, textvariable=self.conn_var, fg="red", font=("Arial", 10, "bold"))
        self.conn_label.pack(pady=(10, 0))

        # Start as UNKNOWN since we aren't connected yet
        self.allowed_var = tk.StringVar(value="Scaling Status: UNKNOWN")
        self.allowed_label = tk.Label(self.root, textvariable=self.allowed_var, fg="gray", font=("Arial", 9))
        self.allowed_label.pack(pady=5)

        # Current Height Display (Start as UNKNOWN and gray)
        self.current_display_var = tk.StringVar(value="Current In-Game Height: UNKNOWN")
        self.current_display_label = tk.Label(self.root, textvariable=self.current_display_var, font=("Arial", 10, "italic"))
        
        # Save the default system text color before we turn it gray, safely supporting dark mode themes
        self.default_text_color = self.current_display_label.cget("fg")
        self.current_display_label.config(fg="gray")
        self.current_display_label.pack(pady=(5, 10))

        # Input Frame
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=5)

        # Target Height Input
        tk.Label(input_frame, text="Target Height:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.target_var = tk.DoubleVar(value=1.0)
        self.target_entry = tk.Entry(input_frame, textvariable=self.target_var, width=10)
        self.target_entry.grid(row=0, column=1, pady=2)

        # Duration Input
        tk.Label(input_frame, text="Duration (seconds):").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.duration_var = tk.DoubleVar(value=3.0)
        self.duration_entry = tk.Entry(input_frame, textvariable=self.duration_var, width=10)
        self.duration_entry.grid(row=1, column=1, pady=2)

        # Auto-select text on click
        self.target_entry.bind("<FocusIn>", self.select_all_text)
        self.duration_entry.bind("<FocusIn>", self.select_all_text)

        # Buttons Frame
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=(10, 5))

        self.instant_btn = tk.Button(btn_frame, text="Set Instantly", command=lambda: self.trigger_update(instant=True), bg="#e0e0e0")
        self.instant_btn.grid(row=0, column=0, padx=5)

        self.transition_btn = tk.Button(btn_frame, text="Smooth Transition", command=lambda: self.trigger_update(instant=False), bg="#cce5ff")
        self.transition_btn.grid(row=0, column=1, padx=5)

        # GitHub Link
        link_label = tk.Label(self.root, text="GitHub: SkyeCA/VRChatOscScaler", fg="blue", cursor="hand2", font=("Arial", 9, "underline"))
        link_label.pack(pady=5)
        link_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/SkyeCA/VRChatOscScaler"))

        # Initially disable inputs
        self.set_ui_state(tk.DISABLED)

    def select_all_text(self, event):
        self.root.after(50, lambda: event.widget.select_range(0, tk.END))
        self.root.after(50, lambda: event.widget.icursor(tk.END))

    def set_ui_state(self, state):
        self.target_entry.config(state=state)
        self.duration_entry.config(state=state)
        self.instant_btn.config(state=state)
        self.transition_btn.config(state=state)

    def check_connection_loop(self):
        time_since_last_msg = time.time() - self.last_osc_time
        if time_since_last_msg > TIMEOUT_SECONDS:
            if self.is_connected:
                self.is_connected = False
                self.conn_var.set("Status: DISCONNECTED")
                self.conn_label.config(fg="red")
                self.set_ui_state(tk.DISABLED)
                
                # Switch to UNKNOWN states when disconnected
                self.allowed_var.set("Scaling Status: UNKNOWN")
                self.allowed_label.config(fg="gray")
                self.current_display_var.set("Current In-Game Height: UNKNOWN")
                self.current_display_label.config(fg="gray")
        else:
            if not self.is_connected:
                self.is_connected = True
                self.conn_var.set("Status: CONNECTED")
                self.conn_label.config(fg="green")
                
                # Restore the height display to the last known variable and default color
                self.current_display_var.set(f"Current In-Game Height: {self.current_height}")
                self.current_display_label.config(fg=self.default_text_color)
                
                # Restore the correct scaling display based on internal state
                if self.scaling_allowed:
                    self.allowed_var.set("Scaling Status: ALLOWED")
                    self.allowed_label.config(fg="green")
                    self.set_ui_state(tk.NORMAL)
                else:
                    self.allowed_var.set("Scaling Status: DISABLED")
                    self.allowed_label.config(fg="red")
                    self.set_ui_state(tk.DISABLED)

        self.root.after(1000, self.check_connection_loop)

    def trigger_update(self, instant=False):
        if not self.scaling_allowed:
            messagebox.showerror("Disabled", "Scaling is disabled by the VRChat avatar.")
            return

        try:
            target_val = float(self.target_var.get())
            duration = float(self.duration_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values.")
            return

        self.cancel_transition = True
        
        target_val = max(0.01, min(target_val, 10000.0))
        self.target_var.set(target_val)

        if target_val < 0.1 or target_val > 100.0:
            if not messagebox.askyesno("Warning", f"Value {target_val} is extreme. Continue?"):
                return

        if instant or duration <= 0:
            self.client.send_message("/avatar/eyeheight", target_val)
        else:
            self.cancel_transition = False
            self.transition_thread = threading.Thread(
                target=self._transition_loop, 
                args=(self.current_height, target_val, duration),
                daemon=True
            )
            self.transition_thread.start()

    def _transition_loop(self, start_val, target_val, duration):
        hz = 30.0 
        interval = 1.0 / hz
        steps = int(duration * hz)
        
        for i in range(1, steps + 1):
            if self.cancel_transition:
                return 
                
            current = start_val + (target_val - start_val) * (i / steps)
            self.client.send_message("/avatar/eyeheight", current)
            time.sleep(interval)
            
        if not self.cancel_transition:
            self.client.send_message("/avatar/eyeheight", target_val)

    def osc_heartbeat(self, address, *args):
        self.last_osc_time = time.time()

    def handle_eyeheight(self, address, *args):
        self.last_osc_time = time.time()
        if args:
            self.current_height = round(args[0], 2)
            # Only update the string if we are currently connected, so we don't accidentally overwrite the "UNKNOWN" state during a timeout blip
            if self.is_connected:
                self.root.after(0, self.current_display_var.set, f"Current In-Game Height: {self.current_height}")

    def handle_scaling_allowed(self, address, *args):
        self.last_osc_time = time.time()
        if args:
            self.scaling_allowed = bool(args[0])
            if self.scaling_allowed:
                self.root.after(0, self.allowed_var.set, "Scaling Status: ALLOWED")
                self.root.after(0, lambda: self.allowed_label.config(fg="green"))
                if self.is_connected:
                    self.root.after(0, lambda: self.set_ui_state(tk.NORMAL))
            else:
                self.root.after(0, self.allowed_var.set, "Scaling Status: DISABLED")
                self.root.after(0, lambda: self.allowed_label.config(fg="red"))
                self.root.after(0, lambda: self.set_ui_state(tk.DISABLED))

    def start_osc_server(self):
        disp = dispatcher.Dispatcher()
        disp.set_default_handler(self.osc_heartbeat) 
        disp.map("/avatar/eyeheight", self.handle_eyeheight)
        disp.map("/avatar/eyeheightscalingallowed", self.handle_scaling_allowed)

        server = osc_server.ThreadingOSCUDPServer((IP, VRCHAT_OSC_OUT_PORT), disp)
        threading.Thread(target=server.serve_forever, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = VRChatEyeHeightApp(root)
    root.mainloop()