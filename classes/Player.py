class Player():
    def __init__(self, playerId, balance, stage):
        self.playerId = playerId
        self.balance = balance

    def __str__(self):
        return f"Player ID: {self.playerId}, Balance: {self.balance}, Stage: {self.stage}"

