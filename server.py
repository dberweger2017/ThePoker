import socket
import threading
import queue
import time
from threading import Lock
from classes.Game import Game
from classes.Player import Player
import misc.global_var as global_var
import sys

HOST = '0.0.0.0'
PORT = 8000

fast_game = False
delay = 0.1

clients = {}
players = {}
clients_lock = Lock()

current_turn = None
current_phase = "starting"
game = None
blind = 10

def next_phase(reset = False):
    global current_phase
    if reset:
        current_phase = "bet"
        return
    phases = ["starting", "waiting", "gamesetup", "bet", "determinwinner"]
    next_phase = phases[phases.index(current_phase) + 1]
    print(f"Changing phase {current_phase} -> {next_phase}")
    current_phase = next_phase

def notify_admin(message, command=False):
    with clients_lock:
        for client_data in clients.values():
            if client_data['type'] == 'admin':
                msg = f"(C)-{message}\n" if command else f"(I)-{message}\n"
                client_data['connection'].send(msg.encode())

def notify_players(message, text=True):
    with clients_lock:
        for client_data in clients.values():
            if client_data['type'] == 'client':
                if text:
                    client_data['connection'].send(f"(I)-{message}\n".encode())
                else:
                    client_data['connection'].send(f"(D)-{message}\n".encode())

def notify_player(client_id, message):
    with clients_lock:
        clients[client_id]['connection'].send(message.encode())

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
        print(f"Unknown client type {client_type}")
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
    global current_turn, game, players

    player_ids = game.getOrder()
    current_index = player_ids.index(current_turn)

    next_index = current_index + 1

    print(player_ids)
    print(current_index)
    print(next_index)

    # Check if all players have made their bet
    if next_index == len(player_ids):
        game.round += 1
        current_turn = player_ids[0]
        if players[current_turn].folded:
            proceed_to_next_turn()
    else:
        current_turn = player_ids[next_index]
        if players[current_turn].folded:
            proceed_to_next_turn()

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
                    notify_admin(f"Player {client_id} is ready.")
                    players[client_id].isReady = True
                    conn.send("(D)-name\n".encode())
                    players[client_id].name = receive_data(conn)
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
                notify_player(client_id, f"(I)-Your balance is {players[client_id].balance}$\n")
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
                        notify_player(client_id, f"(C)-How much do you want to bet? (minbet: {game.minTableBet}$, -1 to leave)")
                        bet_str = receive_data(conn)
                        try:
                            bet = int(bet_str)
                        except ValueError:
                            notify_player(client_id, f"(I)-Invalid bet {bet_str}\n")
                            continue

                        if bet == 0:
                            bet = game.minTableBet

                        if bet == game.minTableBet:
                            if not (client_id == game.bigBlind and game.round == 1):
                                print(f"---Setting this player as called: {client_id}")
                                players[client_id].called = True

                        # Cases
                        if bet < game.minTableBet and bet != -1 and bet != players[client_id].balance:
                            notify_player(client_id, f"(I)-You must bet at least {game.minTableBet}$\n")
                        
                        elif bet - players[client_id].bet > players[client_id].balance and bet != players[client_id].balance:
                            notify_player(client_id, f"(I)You don't have enough money (money: {players[client_id].balance})\n")
                        
                        elif bet <= players[client_id].balance:
                            # This is including the case where bet == -1
                            legal_bet = True
                    
                    
                if legal_bet:
                    if bet != -1:
                        if bet > game.minTableBet:
                            # Player raises, reset the called flag
                            for player in game.players:
                                print("Resetting calls")
                                player.called = False
                            if not (client_id == game.bigBlind and game.round == 1):
                                print(f"---Setting this player as called: {client_id}")
                                players[client_id].called = True

                            game.minTableBet = bet

                        # Update player balance
                        delta = bet - players[client_id].bet
                        players[client_id].balance -= delta
                        players[client_id].bet = bet
                        game.pot += delta

                        if delta != 0:
                            print(f"Player {client_id} bet {bet}$")
                            notify_admin(f"Player {client_id} bet {bet}$")
                            notify_players(f"Player {client_id} bet {bet}$")
                        else:
                            print(f"Player {client_id} called")
                            notify_admin(f"Player {client_id} called")
                            notify_players(f"Player {client_id} called")

                        # Update player data
                        notify_players(f"{str(players[client_id])}={players[client_id].balance}",text=False)
                        notify_players(f"pot>{game.pot}",text=False)

                        notify_players(f"Balance of {client_id} is {players[client_id].balance}$\n")
                        notify_players(f"Pot is {game.pot}$\n")

                    else:
                        # Player folds
                        print(f"Player {client_id} folded")
                        notify_admin(f"Player {client_id} folded")
                        notify_players(f"Player {client_id} folded")
                        players[client_id].folded = True

                    #if everyone except one player has folded, that player wins
                    if len(game.players) - 1 == sum([player.folded for player in game.players]):
                        next_phase()
                        continue
                    else:
                        # Update the admin on the current state of the game
                        notify_admin(f"Current pot: {game.pot}$")
                        notify_admin(f"Current table bet: {game.minTableBet}$")
                        notify_admin(f"Current turn: {current_turn}")
                        notify_admin(f"Current table: {game.table}")
                        for player in game.players:
                            if player.folded:
                                notify_admin(f"Player {str(player)} {player.playerId} is folded")
                            else:
                                notify_admin(f"Player {str(player)} {player.playerId} is in the game")
                        proceed_to_next_turn()
            else:
                time.sleep(1)

def handle_game():
    global current_phase, game, players, current_turn
    print("i. Server ready to start game")
    next_phase()
    pastReady = False
    while True:
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
            notify_players("Determining the button: ")
            game = Game(list(players.values()))
            button, cards = game.start()
            rounds = len(cards)
            for i, round in enumerate(cards):
                for player_id, card in round: 
                    notify_player(player_id, f"(I)-Your card is {card}\n")
                    notify_player(player_id, f"(D)-hand:{card.id}")
                time.sleep(delay*5)
                for player_id, card in round:
                    notify_players(f"{player_id} got card {card}\n")
                    notify_players(f"table:{card.id}", text=False)
                    time.sleep(delay)
                if rounds > 1:
                    if i + 1 < rounds:
                        notify_players(f"There is a tie!")
                        time.sleep(delay*3)
                        notify_players("hand:-1", text=False)
                        notify_players("table:-1", text=False)

            time.sleep(delay*3)

            notify_players(f"The button is {button}!!")

            notify_players("Starting game in 3s...")
            time.sleep(delay*3)
            
            notify_players(f"The order of the game is {' -> '.join([str(item) for item in game.getOrder()])}")

            game.reset()

            notify_players("hand:-1", text=False)
            notify_players("table:-1", text=False)
            next_phase()
            
        if current_phase == "bet":
            for player in game.players:
                player.hand.append(game.deck.drawCard())
                player.hand.append(game.deck.drawCard())
                notify_player(player.playerId, f"(I)-Your hand is {' '.join([str(card) for card in player.hand])}")
                notify_players(f"{str(player)}={player.balance}",text=False)
                for card in player.hand:
                    notify_player(player.playerId, f"(D)-hand:{card.id}\n")
            
            current_turn = game.getOrder()[0]
            print(game.smallBlind, game.bigBlind)
        
        while current_phase == "bet":
            # check if the amount of players that have called plus the amount of players that have folded is equal to the amount of players
            amount_called = 0
            amount_folded = 0
            for player in game.players:
                if player.folded:
                    amount_folded += 1
                elif player.called: # if the player has folded, they can't call
                    amount_called += 1
                
            if amount_called + amount_folded == len(game.players) or amount_folded == len(game.players) - 1:
                notify_admin("All players have called")
                notify_players("All players have called")
                print("All players have called")
                
                # reset the called flag for all players
                for player in game.players:
                    player.called = False

                if len(game.table) == 0:
                    print("Showing first three cards")
                    game.table.append(game.deck.drawCard())
                    game.table.append(game.deck.drawCard())
                    game.table.append(game.deck.drawCard())
                    notify_players(f"table:{game.table[-1].id}", text=False)
                    notify_players(f"table:{game.table[-2].id}", text=False)
                    notify_players(f"table:{game.table[-3].id}", text=False)
                elif len(game.table) == 3:
                    print("Showing fourth card")
                    game.table.append(game.deck.drawCard())
                    notify_players(f"table:{game.table[-1].id}", text=False)
                elif len(game.table) == 4:
                    print("Showing fifth card")
                    game.table.append(game.deck.drawCard())
                    notify_players(f"table:{game.table[-1].id}", text=False)
                elif len(game.table) == 5:
                    notify_players("All cards have been drawn")
                    next_phase()
                    continue
            else:
                #print(f"Amount called: {amount_called}, amount folded: {amount_folded}, total players: {len(game.players)}")
                time.sleep(0.1)

        if current_phase == "determinwinner":
            print("Determining winner")
            notify_players("Determining winner")
            inx, winner = game.determineWinner()
            print(f"The winner is {winner}")
            notify_players(f"The winner is {winner}")
            notify_admin(f"The winner is {winner}")

            # Im not sure if it retuns a copy of the player or a reference to the player
            game.players[inx].balance += game.pot

            notify_players(f"{str(game.players[inx])}={game.players[inx].balance}",text=False)

            game.pot = 0
            game.reset(inx)
            notify_players("hand:-1", text=False)
            notify_players("table:-1", text=False)
            time.sleep(delay*3)
            next_phase(reset = True)

if __name__ == "__main__":
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
    except OSError as e:
        print("Server is probably running.")
        print(e)
        # close all connections
        for client in clients.values():
            client['connection'].close()
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