import socket
import threading

# Define the host and port to listen on
HOST = 'localhost'
PORT = 8000

# Define a function to handle incoming client connections
def handle_client(conn, addr, client_id):
    print(f'New client connected with ID {client_id}: {addr}')

    # Send the client their ID
    conn.send(f'Your ID is {client_id}'.encode())

    # Keep listening for incoming messages from the client
    while True:
        data = conn.recv(1024)
        if not data:
            break
        print(f'Received message from client {client_id}: {data.decode()}')

    # Close the connection when the client disconnects
    print(f'Client {client_id} disconnected: {addr}')
    conn.close()

# Create a socket object and bind it to the host and port
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))

# Listen for incoming connections
server_socket.listen()

print(f'Server listening on {HOST}:{PORT}')

# Initialize the client ID counter
client_id_counter = 0

# Keep listening for incoming connections and spawn a new thread to handle each one
while True:
    conn, addr = server_socket.accept()
    client_id_counter += 1
    threading.Thread(target=handle_client, args=(conn, addr, client_id_counter)).start()
