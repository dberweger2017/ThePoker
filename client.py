import socket
import sys

HOST = 'localhost'
PORT = 8000

def get_mode():
    return "admin" if sys.argv[1:2] == ["admin"] else "client"

def handle_data(s, data, mode):
    decoded_data = data.decode().strip().split("\n")
    for line in decoded_data:
        print(line)
        if line.startswith("(I)"):
            if line == "(I)-disconnect":
                print("Server has closed the connection.")
                s.close()
                return True
        elif line.startswith("(C)"):
            if line == "(C)-Start the game? (y/n)":
                response = input("Client choice: ")
                if response == "y":
                    s.send("start game".encode())
                else:
                    print("Game cancelled.")
            else:
                response = input("Client choice: ")
                s.send(response.encode())
        else:
            print(f"Unknown message: {line}", end="")
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
