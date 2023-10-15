from classes.Deck import Deck

class Game():
    def __init__(self, players):
        self.players = players
        self.stage = 0
        self.deck = Deck()
        self.deck.shuffle()
        self.pot = 0
        self.round = 1
        self.table = []

        self.blindBet = 10
        self.minTableBet = 0

        self.smallBlind = None
        self.bigBlind = None

    def getPlayerIndex(self, playerId):
        # returns the index of the player with the given playerId
        return [player.playerId for player in self.players].index(playerId)

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

    def getOrder(self):
        return [player.playerId for player in self.players]

    def determineButton(self):
        def drawCardsForPlayers(player_ids):
            return [[player_id, self.deck.drawCard()] for player_id in player_ids]
        
        def getHighestCards(cards):
            cards.sort(key=lambda x: x[1].value)
            highest_value = cards[-1][1].value
            return [card for card in cards if card[1].value == highest_value]
        
        # Initialize with all players
        player_ids = [player.playerId for player in self.players]
        
        # Store all drawn cards for each round
        all_drawn_cards = []
        
        while True: 
            # Draw cards for the current player IDs
            cards = drawCardsForPlayers(player_ids)
            all_drawn_cards.append(cards)
            
            # Get the highest cards
            highest_cards = getHighestCards(cards)
            
            # If only one highest card, return the winner and all drawn cards
            if len(highest_cards) == 1:
                return highest_cards[0][0], all_drawn_cards
            
            # Otherwise, continue with only the players who had the highest cards
            player_ids = [card[0] for card in highest_cards]

    def changeButton(self, button):
        #Rotates the players so that the button is last
        button_index = [player.playerId for player in self.players].index(button)
        self.players = self.players[button_index+1:] + self.players[:button_index+1]
        
        self.players[0].type = "smallblind"
        self.players[1].type = "bigblind"

        self.smallBlind = self.players[0].playerId
        self.bigBlind = self.players[1].playerId

    def start(self):
        if self.stage != 0:
            print("Game already started, can't start again")
            return
        self.stage = 1
        winner, tries = self.determineButton()
        self.changeButton(winner)
        return winner, tries

    def reset(self):
        self.stage = 1
        self.deck = Deck()
        self.deck.shuffle()
    
    def __str__(self):
        return f"Game with {len(self.players)} players, on stage: {self.getStage()}"
