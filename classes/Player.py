class Player():
    def __init__(self, playerId, balance):
        self.playerId = playerId
        self.balance = balance
        self.hand = []
        self.isReady = False
        self.bet = 0
        self.type = "player" # player, smallblind, bigblind or button
        self.name = None
        self.called = False
        self.folded = False
        self.allIn = False

    def receive(self, card):
        self.hand.append(card)

    def __str__(self):
        return self.name

