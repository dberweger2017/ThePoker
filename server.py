import socket
import threading
from classes.Game import Game
from classes.Player import Player
import misc.global_var as global_var
import queue
from threading import Lock

HOST = 'localhost'
PORT = 8000
clients = {}
players = []
command_queue = queue.Queue()
clients_lock = Lock()

def notify_admin(message):
    global clients, clients_lock
    with clients_lock:
        for c_id, client_data in clients.items():
            if client_data['type'] == 'admin':
                client_data['connection'].send(f"(I)-{message}\n".encode())

# Define a function to handle incoming client connections
def handle_client(conn, addr, client_id):
    global n_players, ready_players, command_queue, clients, players

    conn.settimeout(1)

    try:

        print(f'New client connected with ID {client_id}: {addr}')

        # Send the client their ID
        conn.send(f'(I)-Your ID is {client_id}\n'.encode())

        # Receive the type of client (admin or client)
        client_type = conn.recv(1024).decode().strip()
        with clients_lock:
            clients[client_id] = {'connection': conn, 'type': client_type}

        if client_type == "admin":
            print(f"Admin connected with ID {client_id}")
            while True:
                command = conn.recv(1024).decode().strip()
                if command == "start game":
                    command_queue.put("start game")
                elif command.startswith("say"):
                    for client in clients:
                        clients[client]['connection'].send(f"(I)-{command[4:]}\n".encode())

        elif client_type == "client":
            print(f"Regular client connected with ID {client_id}")
            notify_admin(f"Player {client_id} has connected.")
            players.append(Player(client_id, global_var.player_init_balance))
            
            # Ask the client if they are ready
            decision = None
            while decision != "y":
                conn.send("(C)-Are you ready? (y/n)\n".encode())
                decision = conn.recv(1024).decode().strip()
                if decision == "y":
                    players[client_id-1].isReady = True
                    conn.send("(I)-You are ready\n".encode())
                    notify_admin(f"Player {client_id} is ready.")
                elif decision == "n":
                    conn.send("(I)-You are not ready\n".encode())
                    conn.close()
                else:
                    conn.send("(I)-Unknown decision\n".encode())

            while True:
                try:
                    command = command_queue.get_nowait()
                    if command == "start game":
                        conn.send("Game is starting\n".encode())
                        # Initialize player, start game, etc.
                        break
                except queue.Empty:
                    pass
        else:
            print(f"Unknown type connected with ID {client_id}")
            conn.send("(I)-Unknown type\n".encode())
            conn.close()
    except:
        print(f"Client with ID {client_id} has disconnected.")
        notify_admin(f"Player {client_id} has disconnected.")
        with clients_lock:
            del clients[client_id]

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))

server_socket.listen()

print(f'Server listening on {HOST}:{PORT}')

client_id_counter = 0

try:
    while True:
        conn, addr = server_socket.accept()
        client_id_counter += 1
        threading.Thread(target=handle_client, args=(conn, addr, client_id_counter)).start()
except KeyboardInterrupt:
    print("Server shutting down...")
    server_socket.close()
