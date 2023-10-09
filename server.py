import socket
import threading
import queue
import time
from threading import Lock
from classes.Game import Game
from classes.Player import Player
import misc.global_var as global_var

HOST = 'localhost'
PORT = 8000

clients = {}
players = {}
command_queue = queue.Queue()
clients_lock = Lock()

def notify_admin(message, command=False):
    with clients_lock:
        for client_data in clients.values():
            if client_data['type'] == 'admin':
                msg = f"(C)-{message}\n" if command else f"(I)-{message}\n"
                client_data['connection'].send(msg.encode())

def handle_socket_errors(func):
    def wrapper(client_id, *args, **kwargs):
        try:
            return func(client_id, *args, **kwargs)
        except socket.error as e:
            print(f"Client {client_id} encountered a socket error: {e}")
            players.pop(client_id, None)
    return wrapper

@handle_socket_errors
def handle_client(conn, addr, client_id):
    print(f'New client connected with ID {client_id}: {addr}')
    conn.settimeout(1)
    conn.send(f'(I)-Your ID is {client_id}\n'.encode())

    client_type = receive_data(conn)
    with clients_lock:
        clients[client_id] = {'connection': conn, 'type': client_type}

    if client_type == "admin":
        handle_admin(conn)
    elif client_type == "client":
        handle_player(conn, client_id)
    else:
        print(f"Unknown type connected with ID {client_id}")
        conn.send("(I)-Unknown type\n".encode())
        conn.close()

def receive_data(conn, timeout=1):
    while True:
        try:
            return conn.recv(1024).decode().strip()
        except socket.timeout:
            time.sleep(timeout)
            continue

def handle_admin(conn):
    print(f"Admin connected")
    while True:
        command = receive_data(conn)
        process_admin_command(command)

def handle_player(conn, client_id):
    notify_admin(f"Player {client_id} has connected.")
    players[client_id] = Player(client_id, global_var.player_init_balance)
    
    conn.send("(C)-Are you ready? (y/n)\n".encode())
    
    while True:
        decision = receive_data(conn)
        if decision == "y":
            conn.send("(I)-You are ready\n".encode())
            notify_admin(f"Player {client_id} is ready.")
            players[client_id].isReady = True
            check_all_players_ready()
            break
        elif decision == "n":
            conn.send("(I)-You are not ready\n".encode())
            notify_admin(f"Player {client_id} has disconnected.")
            players.pop(client_id, None)
            conn.close()
            return
        else:
            conn.send("(I)-Unknown decision\n".encode())
            conn.send("(C)-Are you ready? (y/n)\n".encode())

def check_all_players_ready():
    all_ready = all(player.isReady for player in players.values())
    
    if all_ready:
        notify_admin("All players are ready.")
        notify_admin("Start the game? (y/n)", command=True)

def process_admin_command(command):
    if command == "start game":
        command_queue.put("start game")
    elif command.startswith("say"):
        for client in clients.values():
            client['connection'].send(f"(I)-{command[4:]}\n".encode())

if __name__ == "__main__":
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
    except Exception as e:
        print("Server shutting down due to error:", e)
        server_socket.close()
