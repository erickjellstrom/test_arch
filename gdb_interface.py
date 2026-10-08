import socket

HOST = "127.0.0.1"
PORT = 50001  # cortex-debug's explicit override port for OpenOCD TCL

# The base address straight from your map file snippet
STRUCT_BASE_ADDRESS = 0x20000060  

# Mapping fields with explicit byte sizes (1, 2, or 4 bytes)
# Note: Ensure your struct offsets in RAM match your C struct padding/alignment!
FIELDS = {
    "1": {"name": "digital_switch_1",  "address": hex(STRUCT_BASE_ADDRESS + 0), "size": 1}, # 0x20000060
    "2": {"name": "digital_switch_2",  "address": hex(STRUCT_BASE_ADDRESS + 1), "size": 1}, # 0x20000061
    "3": {"name": "analog_slider_val", "address": hex(STRUCT_BASE_ADDRESS + 2), "size": 2}, # 0x20000062 (Uses 2 bytes)
    "4": {"name": "state_machine_cmd", "address": hex(STRUCT_BASE_ADDRESS + 4), "size": 1}, # 0x20000064
}

def write_ram(address_hex, value, size):
    """Injects a variable-sized value into STM32 RAM via OpenOCD TCL port."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        
        # Select the correct OpenOCD command based on size
        if size == 1:
            cmd_type = "mwb"  # memory write byte (8-bit)
        elif size == 2:
            cmd_type = "mwh"  # memory write half-word (16-bit)
        elif size == 4:
            cmd_type = "mww"  # memory write word (32-bit)
        else:
            print(f"Error: Unsupported size {size} bytes.")
            return

        # Format and send the command
        cmd = f"{cmd_type} {address_hex} {value}"
        s.sendall(f"{cmd}\x1a".encode('utf-8'))
        
        # Read and discard response to flush the buffer
        s.recv(1024)
        s.close()
        
        print(f"-> Injected {value} ({size}-byte) into {address_hex}")
    except ConnectionRefusedError:
        print(f"Error: Connection refused on port {PORT}. Is the VS Code Debugger running?")

def gdb():
    while True:
        print("\nAvailable Struct Fields:")
        for key, field in FIELDS.items():
            print(f" [{key}] {field['name']} ({field['address']}) [{field['size']} byte(s)]")
        print(" [Q] Quit")
        
        choice = input("\nSelect a field to modify: ").strip().lower()
        if choice == 'q':
            break
            
        if choice in FIELDS:
            field_meta = FIELDS[choice]
            size = field_meta["size"]
            
            # Calculate maximum allowed value dynamically based on size
            # 1 byte -> 255, 2 bytes -> 65535, 4 bytes -> 4294967295
            max_val = (1 << (size * 8)) - 1 
            
            try:
                val_in = input(f"Enter new value for {field_meta['name']} (0-{max_val}): ")
                val = int(val_in)
                
                # Dynamic bounds safety check protecting your uint lengths
                if 0 <= val <= max_val:
                    write_ram(field_meta["address"], val, size)
                else:
                    print(f"Value out of bounds for a uint{size*8} (must be 0-{max_val}).")
            except ValueError:
                print("Invalid input. Please enter an integer.")
        else:
            print("Invalid choice. Try again.")

