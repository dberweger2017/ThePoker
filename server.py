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

current_turn = None
current_phase = ""
game = None

def notify_admin(message, command=False):
    with clients_lock:
        for client_data in clients.values():
            if client_data['type'] == 'admin':
                msg = f"(C)-{message}\n" if command else f"(I)-{message}\n"
                client_data['connection'].send(msg.encode())

def notify_players(message):
    with clients_lock:
        for client_data in clients.values():
            if client_data['type'] == 'client':
                client_data['connection'].send(f"(I)-{message}\n".encode())

def notify_player(client_id, message):
    with clients_lock:
        clients[client_id]['connection'].send(f"(I)-{message}\n".encode())

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

def proceed_to_next_turn():
    print("Passing to new turn")
    global current_turn
    global game
    player_ids = game.getOrder()
    current_index = player_ids.index(current_turn)

    # Check if all players have made their bet
    if current_index + 1 == len(player_ids):
        # Next phase logic
        print("Phase ended")
        pass
    else:
        current_turn = player_ids[current_index + 1]
        notify_player(current_turn, "(C)-How much do you want to bet?")


def handle_player(conn, client_id):
    global current_phase, current_turn, game

    notify_admin(f"Player {client_id} has connected.")
    players[client_id] = Player(client_id, global_var.player_init_balance)
    
    conn.send("(C)-Are you ready? (y/n)\n".encode())
    
    while True:
        decision = receive_data(conn)
        if decision == "y":
            conn.send("(I)-You are ready\n".encode())
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
    
    while current_phase == "bet":
        print("Running bet phase")
        global current_turn
        if client_id == current_turn:
            conn.send("(C)-How much do you want to bet?\n".encode())
            bet = receive_data(conn)
            notify_players(f"Player {client_id} has bet {bet}")
            proceed_to_next_turn()

def check_all_players_ready():
    all_ready = all(player.isReady for player in players.values())
    
    if all_ready:
        notify_admin("All players are ready.")
        notify_admin("Start the game? (y/n)", command=True)

def runGame():
    global current_turn
    global game
    startGame()
    players = game.getOrder()
    current_turn = players[0]
    notify_players(f"Current turn: {current_turn}")
    print(f"Current turn: {current_turn}")
    current_phase = "bet"
    notify_players(f"Game in {current_phase} mode")
    print(f"Game in {current_phase} mode")

def startGame():
    global game
    game = Game(list(players.values()))
    winner, cards = game.start()

    for round in cards:
        for player_id, card in round:
            notify_player(player_id, f"Your card is {card}")
            time.sleep(2)

        for player_id, card in round:
            notify_players(f"{player_id} got card {card}")
            time.sleep(1)

    time.sleep(3)
    notify_players(f"Winner is {winner}!!")
    notify_player(winner, "You won the game!!")
    time.sleep(1)
    notify_players(f"The order of the game is {' -> '.join([str(item) for item in game.getOrder()])}")
    game.reset()

def process_admin_command(command):
    if command == "start game":
        print("Game is starting...")
        notify_players("Game is starting...")
        runGame()
        reset_players()
    elif command.startswith("say"):
        for client in clients.values():
            client['connection'].send(f"(I)-{command[4:]}\n".encode())

def reset_players():
    global players
    players = {}

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
