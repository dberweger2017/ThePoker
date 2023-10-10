class Player():
    def __init__(self, playerId, balance):
        self.playerId = playerId
        self.balance = balance
        self.hand = []
        self.isReady = False
        self.bet = 0

    def receive(self, card):
        self.hand.append(card)

    def __str__(self):
        return f"Player ID: {self.playerId}, Balance: {self.balance}, Stage: {self.stage}"

