class Card:
    def __init__(self, suit, val):
        self.suit = suit
        self.value = val

    def show(self):
        if self.value == 1:
            print(f"Ace of {self.suit}")
        elif self.value == 11:
            print(f"Jack of {self.suit}")
        elif self.value == 12:
            print(f"Queen of {self.suit}")
        elif self.value == 13:
            print(f"King of {self.suit}")
        else:
            print(f"{self.value} of {self.suit}")
