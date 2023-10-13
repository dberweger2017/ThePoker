import random
from classes.Card import Card

class Deck:
    def __init__(self):
        self.cards = []
        self.build()

    def build(self):
        i = 0
        for s in ["Spades", "Clubs", "Diamonds", "Hearts"]:
            for v in range(2, 15):
                self.cards.append(Card(s, v, i))
                i += 1

    def show(self):
        for c in self.cards:
            c.show()

    def shuffle(self):
        for i in range(len(self.cards) - 1, 0, -1):
            r = random.randint(0, i)
            self.cards[i], self.cards[r] = self.cards[r], self.cards[i]

    def drawCard(self):
        return self.cards.pop()
    
    def __str__(self):
        return f"Cards: {self.cards}"
