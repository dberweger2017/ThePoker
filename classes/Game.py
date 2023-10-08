from classes.Deck import Deck

class Game():
    def __init__(self, players, stage):
        self.players = players
        self.stage = stage
        self.deck = Deck()
        self.deck.shuffle()