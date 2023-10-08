from classes.Deck import Deck

class Game():
    def __init__(self, players):
        self.players = players
        self.stage = 1
        self.deck = Deck()
        self.deck.shuffle()

    def showDeck(self, showCards = True):
        print(f"Game with {len(self.deck.cards)} cards:")
        if showCards:
            self.deck.show()
    
    def __str__(self):
        return f"Game with {len(self.players)} players, on stage: {self.stage}"
