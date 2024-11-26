import datetime
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, filtfilt
import serial
from matplotlib.animation import FuncAnimation

# Set up the serial port
serial_port = '/dev/cu.usbmodem1101'  # Replace with your serial port (e.g., '/dev/ttyUSB0' on Linux)
baud_rate = 115200      # Replace with your baud rate
ser = serial.Serial(serial_port, baud_rate)

# Initialize data buffers
ppg1_raw = []
times1_sec = []

# Parameters for the bandpass filter
lowcut = 0.3    # Lower cutoff frequency in Hz
highcut = 2.5   # Upper cutoff frequency in Hz
order = 4       # Filter order

# Initialize plotting
fig, ax1 = plt.subplots(figsize=(12, 6))

# Set up the plot
line1, = ax1.plot([], [], label='Filtered & Normalized')
line2, = ax1.plot([], [], label='Unfiltered & Normalized')
text_handle = ax1.text(0.02, 0.95, '', transform=ax1.transAxes, fontsize=14,
                       verticalalignment='top')  # Text for displaying heart rate

ax1.set_xlabel('Time (seconds)')
ax1.set_ylabel('Normalized PPG Signal')
ax1.set_title('Real-Time PPG Signal with Heart Rate')
ax1.legend()
ax1.set_xlim(0, 10)  # Show last 10 seconds
ax1.set_ylim(0, 1)

# Sampling frequency (will be updated dynamically)
Fs = None

# Initialize start_time
start_time = None

def update(frame):
    global Fs, start_time

    # Read a line from the serial port
    try:
        line = ser.readline().decode('utf-8').strip()
        if line:
            # Parse the PPG value
            ppg_value = float(line)
            current_time = datetime.datetime.now()
            if start_time is None:
                start_time = current_time
                elapsed_time = 0.0
            else:
                elapsed_time = (current_time - start_time).total_seconds()

            # Append data to buffers
            times1_sec.append(elapsed_time)
            ppg1_raw.append(ppg_value)

            # Ensure buffers don't get too large
            max_buffer_length = 500  # Adjust as needed
            if len(ppg1_raw) > max_buffer_length:
                times1_sec.pop(0)
                ppg1_raw.pop(0)

            # Update sampling frequency
            if len(times1_sec) > 1:
                Ts_values = np.diff(times1_sec[-10:])  # Time intervals between last 10 samples
                Ts = np.mean(Ts_values)  # Average sampling interval
                if Ts > 0:
                    Fs = 1 / Ts

            # Proceed only if Fs is known
            if Fs and len(ppg1_raw) > max(order * 3, 10):
                # Design the Butterworth bandpass filter
                b, a = butter(order, [lowcut, highcut], btype='band', fs=Fs)
                # Apply the filter
                ppg1_filtered_signal = filtfilt(b, a, ppg1_raw)

                # Normalize signals
                ppg1_filtered_normalized = (ppg1_filtered_signal - np.min(ppg1_filtered_signal)) / (np.max(ppg1_filtered_signal) - np.min(ppg1_filtered_signal))
                ppg1_unfiltered_normalized = (np.array(ppg1_raw) - np.min(ppg1_raw)) / (np.max(ppg1_raw) - np.min(ppg1_raw))

                # Update time axis
                time_axis = np.array(times1_sec) - times1_sec[0]

                # Update signal plots
                line1.set_data(time_axis, ppg1_filtered_normalized)
                line2.set_data(time_axis, ppg1_unfiltered_normalized)
                ax1.set_xlim(time_axis[-1] - 10, time_axis[-1])  # Show last 10 seconds

                # Compute the dominant frequency
                #N = len(ppg1_unfiltered_normalized)
                #if N > 1 and Ts > 0:
                    # Use Welch's method for better frequency estimation
                    #from scipy.signal import welch
                    #f, Pxx = welch(ppg1_unfiltered_normalized, fs=Fs, nperseg=min(256, N))
                    # Find the frequency with the maximum power
                    #idx = np.argmax(Pxx)
                    #dominant_freq = f[idx]
                    # Calculate heart rate in BPM
                    #heart_rate_bpm = dominant_freq * 120
                    # Update the text on the plot
                    #text_handle.set_text(f'Heart Rate: {heart_rate_bpm:.1f} BPM')

        return line1, line2, text_handle

    except Exception as e:
        print(f"Error: {e}")
        return line1, line2, text_handle

# Create the animation
ani = FuncAnimation(fig, update, interval=50, blit=True)

plt.tight_layout()
plt.show()
