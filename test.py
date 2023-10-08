from classes.Game import Game
from classes.Player import Player

players = []

for i in range(1, 7):
    players.append(Player(i, 1000))

game = Game(players)

game.showDeck(False)

winner, tries = game.start()
print(f"Winner: {winner}")

print([player.playerId for player in game.players])
