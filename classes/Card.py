class Card:
    def __init__(self, suit, val):
        self.suit = suit
        self.value = val   

    def show(self):
        if self.value == 1:
            print(f"A of {self.suit}")
        elif self.value == 11:
            print(f"J of {self.suit}")
        elif self.value == 12:
            print(f"Q of {self.suit}")
        elif self.value == 13:
            print(f"K of {self.suit}")
        else:
            print(f"{self.value} of {self.suit}")

    def __str__(self):
        if self.value == 1:
            return f"A of {self.suit}"
        elif self.value == 11:
            return f"J of {self.suit}"
        elif self.value == 12:
            return f"Q of {self.suit}"
        elif self.value == 13:
            return f"K of {self.suit}"
        else:
            return f"{self.value} of {self.suit}"
