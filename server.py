import socket
import threading
import queue
import time
from threading import Lock
from classes.Game import Game
from classes.Player import Player
import misc.global_var as global_var
import sys

HOST = 'localhost'
PORT = 8000

clients = {}
players = {}
clients_lock = Lock()

current_turn = None
current_phase = "starting"
game = None
blind = 10

def next_phase():
    global current_phase
    phases = ["starting", "waiting", "gamesetup", "bet"]
    next_phase = phases[phases.index(current_phase) + 1]
    print(f"Changing phase {current_phase} -> {next_phase}")
    current_phase = next_phase

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

def notify_player(client_id, message, command=False):
    with clients_lock:
        msg = f"(C)-{message}\n" if command else f"(I)-{message}\n"
        clients[client_id]['connection'].send(msg.encode())

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

def process_admin_command(command):
    if command == "start game":
        next_phase()
    elif command.startswith("say"):
        for client in clients.values():
            client['connection'].send(f"(I)-{command[4:]}\n".encode())

def handle_admin(conn):
    print(f"Admin connected")
    while True:
        command = receive_data(conn)
        process_admin_command(command)

def receive_data(conn, timeout=1):
    while True:
        try:
            return conn.recv(1024).decode().strip()
        except socket.timeout:
            time.sleep(timeout)
            continue

def proceed_to_next_turn():
    print("Passing to new turn")
    global current_turn, game
    player_ids = game.getOrder()
    current_index = player_ids.index(current_turn)

    # Check if all players have made their bet
    if current_index + 1 == len(player_ids):
        game.round += 1
        current_turn = player_ids[0]
    else:
        current_turn = player_ids[current_index + 1]

def handle_player(conn, client_id):
    global current_phase, current_turn, game

    while True:
        if current_phase == "waiting":
            notify_admin(f"Player {client_id} has connected.")
            players[client_id] = Player(client_id, global_var.player_init_balance)
            conn.send("(C)-Are you ready to start the game? (y/n)\n".encode())
        
        while current_phase == "waiting":
            if players[client_id].isReady == False:
                decision = receive_data(conn)
                if decision == "y":
                    conn.send("(I)-You are ready\n".encode())
                    players[client_id].isReady = True
                    continue

                elif decision == "n":
                    conn.send("(I)-You are not ready\n".encode())
                    notify_admin(f"Player {client_id} has disconnected.")
                    players.pop(client_id, None)
                    conn.close()
                    continue

                else:
                    conn.send("(I)-Unknown decision\n".encode())
                    conn.send("(C)-Are you ready? (y/n)\n".encode())
            else:
                time.sleep(1)
        
        while current_phase == "bet":
            global current_turn, game
            if client_id == current_turn:
                print(f"Player {client_id} is betting, this player is {game.players[game.getPlayerIndex(client_id)].type}")
                notify_players(f"Waiting for player {client_id} to bet...")
                notify_player(client_id, f"Your balance is {players[client_id].balance}$\n")
                legal_bet = True
                if client_id == game.smallBlind and game.round == 1:
                    bet = game.blindBet
                    print(f"Player {client_id} is small blind, autobetting {bet}")
                elif client_id == game.bigBlind and game.round == 1:
                    bet = game.blindBet * 2
                    print(f"Player {client_id} is small blind, autobetting {bet}")
                else:
                    legal_bet = False
                    while not legal_bet:
                        notify_player(client_id, f"How much do you want to bet? (minbet: {game.minTableBet}$, -1 to leave)", command=True)
                        bet_str = receive_data(conn)
                        try:
                            bet = int(bet_str)
                        except ValueError:
                            notify_player(client_id, f"Invalid bet {bet_str}\n")
                            continue
                        
                        if bet < game.minTableBet:
                            notify_player(client_id, f"You must bet at least {game.minTableBet}$\n")
                        elif bet > players[client_id].balance:
                            notify_player(client_id, f"You don't have enough money (money: {players[client_id].balance})\n")
                        elif bet <= players[client_id].balance:
                            # This is including the case where bet == -1
                            legal_bet = True
                    
                if legal_bet:
                    if bet != -1:
                        print(f"Player {client_id} bet {bet}$")
                        notify_admin(f"Player {client_id} bet {bet}$")
                        notify_players(f"Player {client_id} bet {bet}$")

                        # Update player balance
                        players[client_id].balance -= bet
                        game.pot += bet
                        game.minTableBet = bet

                        notify_players(f"Balance of {client_id} is {players[client_id].balance}$\n")
                        notify_players(f"Pot is {game.pot}$\n")

                    notify_players("n")
                    proceed_to_next_turn()
            else:
                time.sleep(1)

def handle_game():
    global current_phase, game, players, current_turn
    print("i. Server ready to start game")
    next_phase()
    pastReady = False
    while current_phase == "waiting":
        if len(players) != 0:
            all_ready = all(player.isReady for player in players.values())
            if all_ready and not pastReady:
                notify_admin("All players are ready.")
                notify_admin("Start the game? (y/n)", command=True)
            else:
                time.sleep(1)
            pastReady = all_ready

    if current_phase == "gamesetup":
        notify_players("clear")
        notify_players("Determining the button: ")
        game = Game(list(players.values()))
        button, cards = game.start()
        rounds = len(cards)
        for i, round in enumerate(cards):
            for player_id, card in round:
                notify_player(player_id, f"Your card is {card}")
            time.sleep(2)
            for player_id, card in round:
                notify_players(f"{player_id} got card {card}")
                time.sleep(1)
            if rounds > 1:
                if i + 1 < rounds:
                    notify_players(f"There is a tie!")
                    time.sleep(1)

        time.sleep(3)

        notify_players(f"The button is {button}!!")

        notify_players("Starting game in 3s...")
        time.sleep(1)
        notify_players("Starting game in 2s...")
        time.sleep(1)
        notify_players("Starting game in 1s...")
        time.sleep(1)
        notify_players("clear")
        
        notify_players(f"The order of the game is {' -> '.join([str(item) for item in game.getOrder()])}")
        notify_players("n")

        game.reset()
        next_phase()
        
    if current_phase == "bet":
        for player in game.players:
            player.hand.append(game.deck.drawCard())
            player.hand.append(game.deck.drawCard())
            notify_player(player.playerId, f"Your hand is {' '.join([str(card) for card in player.hand])}")
        current_turn = game.getOrder()[0]
        print(game.smallBlind, game.bigBlind)
        pass

if __name__ == "__main__":
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
    except OSError as e:
        print("Server is probably running.")
        print(e)
        print("Exiting...")
        sys.exit(0)

    print(f'Server listening on {HOST}:{PORT}')

    client_id_counter = 0

    try:
        threading.Thread(target=handle_game).start()
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