

import csv
import glob
import os
import select
import serial
import sys
import time

PORT = '/dev/ttyACM1'
SERIAL_PORT = '/dev/ttyACM1'
BAUD_RATE = 115200
TIMEOUT = 1.0
LSB_PER_G = 16384.0

def detect_serial_port():
    """Return the first available serial device, preferring ACM over USB."""
    ports = []
    for pattern in ('/dev/ttyACM*', '/dev/ttyUSB*'):
        ports.extend(sorted(glob.glob(pattern)))

    if not ports:
        return SERIAL_PORT

    # Prefer ACM devices if present, otherwise use USB.
    for port in ports:
        if 'ttyACM' in port:
            return port

    return ports[0]


def get_serial_port():
    """Return the active serial port and keep a sensible fallback."""
    port = detect_serial_port()
    if port and os.path.exists(port):
        return port
    return SERIAL_PORT

def send_command(cmd_byte):
    port = get_serial_port()
    try:
        with serial.Serial(port, BAUD_RATE, timeout=1) as ser:
            # Short delay to ensure connection is clean
            time.sleep(0.1)

            # Send command as a single byte
            ser.write(bytes([cmd_byte]))
            print(f"Sent command: {hex(cmd_byte)} to {port}")
    except serial.SerialException as e:
        print(f"Error connecting to serial port {port}: {e}")



def send_commands(cmd_bytes):
    """
    Sends a sequence of bytes over the serial port.
    :param cmd_bytes: A list, tuple, or bytes object (e.g., [0x01, 0x02, 0x03])
    """
    port = get_serial_port()
    try:
        with serial.Serial(port, BAUD_RATE, timeout=1) as ser:
            # Short delay to ensure connection is clean
            time.sleep(0.1)

            # Convert list/tuple to bytes and send
            payload = bytes(cmd_bytes)
            ser.write(payload)

            # Print hex representation of sent bytes
            hex_string = " ".join(f"{b:02X}" for b in payload)
            print(f"Sent commands: {hex_string} to {port}")

    except serial.SerialException as e:
        print(f"Error connecting to serial port {port}: {e}")

def uart_number():
    user_input = input("Enter one digit to send (blank to cancel): ").strip()
    if len(user_input) != 1 or not user_input.isascii() or not user_input.isdigit():
        if user_input:
            print("Enter exactly one ASCII digit")
        return

    number_value = ord(user_input) - ord('0')
    send_command(number_value)

def uart_byte():
    user_input = input("Enter one letter or number to send (blank to cancel): ").strip()
    if len(user_input) != 1 or not user_input.isalnum() or not user_input.isascii():
        if user_input:
            print("Enter exactly one ASCII letter or number")
        return

    byte_value = ord(user_input)
    send_command(byte_value)


def parse_imu_line(raw_line):
    """Convert a raw serial line to x/y/z acceleration values in g."""
    try:
        line = raw_line.decode("utf-8", errors="ignore").strip()
        if not line:
            return None

        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5:
            return None

        log_nbr, raw_x, raw_y, raw_z, target = map(int, parts[:5])
        return {
            "log_nbr": log_nbr,
            "x": raw_x / LSB_PER_G,
            "y": raw_y / LSB_PER_G,
            "z": raw_z / LSB_PER_G,
            "target": target,
        }
    except (ValueError, UnicodeDecodeError):
        return None

        
def read_data():
    port = get_serial_port()

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=TIMEOUT)
    except Exception as exc:
        print(f"Could not open {port}: {exc}")
        return 1

    print(f"Reading IMU data from {port} at {BAUD_RATE} baud")
    print("Press Ctrl+C to stop\n")
    try:
        while True:
            raw_line = ser.readline()
            if not raw_line:
                continue

            values = parse_imu_line(raw_line)
            if values is None:
                continue

            print(
                f"X={values['x']:.4f} g  "
                f"Y={values['y']:.4f} g  "
                f"Z={values['z']:.4f} g"
            )
            print(f"log_nbr: {values['log_nbr']}")

    except KeyboardInterrupt:
        print("\nStopping IMU reader.")
    finally:
        ser.close()


def trace_data(csv_filename):
    """Read IMU samples until Enter is pressed and save them beside this script."""
    port = get_serial_port()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_dir_logs = script_dir + '/logs'
    csv_path = os.path.join(script_dir_logs, csv_filename)
    samples = []

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=TIMEOUT)
    except Exception as exc:
        print(f"Could not open {port}: {exc}")
        return []

    print(f"Tracing IMU samples to {csv_path} on {port}. Press Enter to stop.")

    try:
        with open(csv_path, "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["sample", "log_nbr", "x_g", "y_g", "z_g", "target"])

            while True:
                if select.select([sys.stdin], [], [], 0)[0]:
                    sys.stdin.readline()
                    break

                raw_line = ser.readline()
                if not raw_line:
                    continue

                values = parse_imu_line(raw_line)
                if values is None:
                    continue

                samples.append(values)
                writer.writerow([
                    len(samples),
                    f"{values['log_nbr']}",
                    f"{values['x']:.6f}",
                    f"{values['y']:.6f}",
                    f"{values['z']:.6f}",
                    f"{values['target']}",
                ])

                print(
                    f"[{len(samples)}] "
                    f"X={values['x']:.4f} g  "
                    f"Y={values['y']:.4f} g  "
                    f"Z={values['z']:.4f} g"
                )
    finally:
        ser.close()

    print(f"Saved {len(samples)} samples to {csv_path}")
    return samples

