import socket
import sys

HOST = 'localhost'
PORT = 8000

def get_mode():
    return "admin" if sys.argv[1:2] == ["admin"] else "client"

def handle_data(s, data, mode):
    decoded_data = data.decode().strip()
    print(f"{decoded_data}\n", end='')
    if decoded_data.startswith("(I)"):
        if decoded_data == "(I)-disconnect":
            print("Server has closed the connection.")
            s.close()
            return True
    elif decoded_data.startswith("(C)") and mode == "client":
        response = input("Client choice: ")
        s.send(response.encode())
    else:
        print(f"Unknown message: {decoded_data}", end="")
    return False

def main():
    mode = get_mode()
    print(f"{mode.capitalize()} mode")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.send(mode.encode())
            
            while True:
                try:
                    data = s.recv(1024)
                    if data and handle_data(s, data, mode):
                        break

                except KeyboardInterrupt:
                    print("\nClosing connection...")
                    s.send("(I)-disconnect".encode())
                    s.close()
                    break
                    
    except ConnectionRefusedError:
        print('The server is not running.')
    except ConnectionResetError:
        print('The server has closed the connection.')

if __name__ == "__main__":
    main()
