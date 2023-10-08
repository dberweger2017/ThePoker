from classes.Game import Game

players = []

for i in range(1, 7):
    players.append(f"Player {i}", 1000)

game = Game(players)

print(game)