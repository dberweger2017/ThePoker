from classes.Game import Game
from classes.Player import Player

players = []

for i in range(1, 7):
    players.append(Player(f"Player {i}", 1000))

game = Game(players)

game.showDeck(False)

winner, tries = game.start()
print(f"Winner: {winner}")
for i, cards in enumerate(tries):
    print(f"Round {i + 1}: {[f'{player_id}, {str(card)}' for player_id, card in cards]}")
