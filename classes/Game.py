from classes.Deck import Deck

class Game():
    def __init__(self, players):
        self.players = players
        self.stage = 1
        self.deck = Deck()
        self.deck.shuffle()

    def getStage(self):
        if self.stage == 1:
            return "Pre-Flop"
        elif self.stage == 2:
            return "Flop"
        elif self.stage == 3:
            return "Turn"
        elif self.stage == 4:
            return "River"
        else:
            return "Unknown"

    def showDeck(self, showCards = True):
        print(f"Game with {len(self.deck.cards)} cards:")
        if showCards:
            self.deck.show()
    
    def __str__(self):
        return f"Game with {len(self.players)} players, on stage: {self.getStage()}"
