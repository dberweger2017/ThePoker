import socket
import threading
from classes.Game import Game
from classes.Player import Player
import misc.global_var as global_var
import queue
from threading import Lock
import time

HOST = 'localhost'
PORT = 8000
clients = {}
players = {}
command_queue = queue.Queue()
clients_lock = Lock()

def notify_admin(message):
    global clients, clients_lock
    with clients_lock:
        for c_id, client_data in clients.items():
            if client_data['type'] == 'admin':
                client_data['connection'].send(f"(I)-{message}\n".encode())

def handle_socket_errors(func):
    def wrapper(*args, **kwargs):
        client_id, *other_args = args
        try:
            return func(client_id, *other_args, **kwargs)
        except socket.error as e:
            print(f"Client {client_id} encountered a socket error: {e}")
            players.pop(client_id)
    return wrapper

# Define a function to handle incoming client connections
@handle_socket_errors
def handle_client(conn, addr, client_id):
    global n_players, ready_players, command_queue, clients, players

    print(f'New client connected with ID {client_id}: {addr}')

    conn.settimeout(1)

    # Send the client their ID
    conn.send(f'(I)-Your ID is {client_id}\n'.encode())

    client_type = None
    while client_type not in ["admin", "client"]:
        try:
            client_type = conn.recv(1024).decode().strip()
        except socket.timeout:
            pass
    with clients_lock:
        clients[client_id] = {'connection': conn, 'type': client_type}

    if client_type == "admin":
        print(f"Admin connected with ID {client_id}")
        while True:
            try:
                command = conn.recv(1024).decode().strip()
            except socket.timeout:
                time.sleep(0.1)
                continue
            if command == "start game":
                command_queue.put("start game")
            elif command.startswith("say"):
                for client in clients:
                    clients[client]['connection'].send(f"(I)-{command[4:]}\n".encode())

    elif client_type == "client":
        notify_admin(f"Player {client_id} has connected.")
        players[client_id] = Player(client_id, global_var.player_init_balance)
        
        # Ask the client if they are ready
        decision = None
        conn.send("(C)-Are you ready? (y/n)\n".encode())
        while decision != "y":
            try:
                decision = conn.recv(1024).decode().strip()
            except socket.timeout:
                time.sleep(0.1)
                continue
                
            if decision == None:
                continue
            elif decision == "y":
                conn.send("(I)-You are ready\n".encode())
                notify_admin(f"Player {client_id} is ready.")
                players[client_id].isReady = True
                for key, player in players.items():
                    notify_admin(f"{key} -> {player.isReady}")

            elif decision == "n":
                conn.send("(I)-You are not ready\n".encode())
                notify_admin(f"Player {client_id} has disconnected.")
                players.pop(client_id)
                conn.close()
                return
            else:
                conn.send("(I)-Unknown decision\n".encode())
                conn.send("(C)-Are you ready? (y/n)\n".encode())
                decision = None

        while True:
            try:
                command = command_queue.get_nowait()
                if command == "start game":
                    conn.send("Game is starting\n".encode())
                    # Initialize player, start game, etc.
                    break
            except queue.Empty:
                conn.send("".encode())
            time.sleep(0.1)
    else:
        print(f"Unknown type connected with ID {client_id}")
        conn.send("(I)-Unknown type\n".encode())
        conn.close()

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
    exit()
except Exception as e:
    print("Server shutting down...")
    print(e)
    server_socket.close()
    exit()
