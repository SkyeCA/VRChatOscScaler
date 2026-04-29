Create a complete Python desktop application using tkinter and python-osc that controls a VRChat avatar's eye height via OSC. The application must run entirely on localhost (127.0.0.1) where VRChat listens on port 9000 and sends on port 9001.

Core Technical Requirements:
1. OSC Server & Client: Run an OSC UDP server on a daemon background thread to receive data without freezing the Tkinter UI. Use an OSC client to send data to VRChat. All UI updates triggered by incoming OSC messages must be safely queued to the main thread using root.after().
2. Connection Heartbeat: Create a catch-all default OSC handler that updates a last_osc_time variable whenever any message is received from VRChat. Run a loop every 1 second checking if a message has been received in the last 5.0 seconds. 
  - If connected: Display "Status: CONNECTED" in green. 
  - If disconnected: Display "Status: DISCONNECTED" in red, disable all inputs, and set the scaling and current height labels to "UNKNOWN" (gray text).
3. OSC Handlers:
  - /avatar/eyeheight: Update the internal current height variable (rounded to 2 decimal places) and update a read-only UI label showing the current height (only if the app is currently connected).
  - /avatar/eyeheightscalingallowed: Update a boolean flag. If True, set a UI label to "Scaling Status: ALLOWED" (green) and enable inputs. If False, set it to "DISABLED" (red) and disable inputs.
4. Input Constraints: The minimum allowable height is 0.01 and the maximum is 10,000. If the user attempts to send a value lower than 0.1 or higher than 100, trigger a Tkinter yes/no warning messagebox asking them to confirm the extreme value before sending.

Application Features & Actions:
1. Set Instantly: A button that reads a "Target Height" tk.Entry and immediately sends it to /avatar/eyeheight.
2. Smooth Transition: A button that reads the target height and a "Duration (seconds)" tk.Entry. It must start a background daemon thread that linearly interpolates from the current in-game height to the target height over the specified duration, sending 30 OSC updates per second (30Hz).
3. Override Safety: Include a cancel_transition flag. If the user clicks "Set Instantly" or starts a new transition while one is already running, the old background thread must terminate early so they don't fight each other.
4. Quality of Life: Bind a <FocusIn> event to the target and duration entry boxes so that clicking them automatically highlights all the text inside (use a 50ms delay to prevent the native click from clearing the selection).

UI Layout:
- Window size around 380x280, non-resizable.
- Top: Connection Status Label.
- Below that: Scaling Allowed Status Label.
- Below that: Read-only "Current In-Game Height" Label.
- Middle: A grid frame containing "Target Height" (default 1.0) and "Duration (seconds)" (default 3.0) input boxes.
- Below that: A frame side-by-side with the "Set Instantly" and "Smooth Transition" buttons.
- Bottom Center: A clickable hyperlink (blue, underlined, hand cursor) reading "GitHub: SkyeCA/VRChatOscScaler" that opens the URL https://github.com/SkyeCA/VRChatOscScaler in the default web browser using the webbrowser module. Stack this directly below the buttons with minimal padding to avoid dead space.