from classes.Deck import Deck

class Game():
    def __init__(self, players):
        self.players = players
        self.stage = 1
        self.deck = Deck()
        self.deck.shuffle()
    
    def __str__(self):
        return f"Players: {self.players}, Stage: {self.stage}, Deck: {self.deck}"