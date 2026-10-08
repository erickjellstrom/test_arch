import uart_interface as ui
import gdb_interface as gi

def uart_string():
    user_input = input("Enter file name string")
    return user_input

if __name__ == "__main__":
    
    while True:
        
        print("\nTest Menu:\n")
        print("Please select:\n") 
        choice = input("\n1. uart read\n" \
        "2. gdb start\n" \
        "4. uart trace\n" \
        "5. send one letter or number\n" \
        "6. send one number (0-9)\n" \
        "q. quit ").strip().lower()

        if choice == '1':
            ui.read_data()
        
        if choice == '2':
            gi.gdb()

        if choice == '4':
            s = uart_string()
            ui.trace_data('my_trace_'+ s)

        if choice == '5':
            ui.uart_byte()

        if choice == '6':
            ui.uart_number()

        if choice == 'q':
            break

    
