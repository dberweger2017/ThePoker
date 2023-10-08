import socket
import sys

HOST = 'localhost'
PORT = 8000

try:
    type = sys.argv[1]
    if type == "admin":
        print("Admin mode")
        mode = 1
    else:
        print("Client mode")
        mode = 2
except IndexError:
    print("Client mode")
    mode = 2

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        if mode == 1:
            s.send("admin".encode())
        else:
            s.send("client".encode())
        while True:
            try:
                data = s.recv(1024)
                if data:
                    decoded_data = data.decode().strip()
                    if decoded_data.startswith("(I)"):
                        # Handle (I) data
                        if decoded_data == "(I)-disconnect":
                            print("Server has closed the connection.")
                            s.close()
                            break
                        else:
                            print(data.decode(), end='')

                    elif decoded_data.startswith("(C)"):
                        # Handle (C) data
                        print(data.decode(), end='')
                        response = input("Client choice: ")
                        s.send(response.encode())
                    else:
                        print("Unknown message: ", data.decode(), end="")

            except KeyboardInterrupt:
                print("\nClosing connection...")
                s.send("(I)-disconnect".encode())
                s.close()
                break
                    
except ConnectionRefusedError:
    print('The server is not running.')
    exit()
