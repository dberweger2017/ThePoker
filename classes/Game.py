from classes.Deck import Deck
import random
from collections import Counter
from operator import itemgetter
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

    def changeButton(self, button, button_index = None):
        #Rotates the players so that the button is last
        if button_index == None:
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
    
    def reset(self, winner = None):
        self.stage = 1
        self.deck = Deck()
        self.deck.shuffle()
        self.pot = 0
        self.round = 1
        self.minTableBet = 0
        self.table = []
        for player in self.players:
            player.hand = []
            player.bet = 0
            player.called = False
            player.folded = False
        if winner != None:
            winner = self.players[winner]
            self.changeButton(None, self.getPlayerIndex(winner.playerId))

    # Function to evaluate the hand strength and high card
    def evaluate_hand(self, hand, table):
        cards = hand + table
        cards.sort(key=lambda x: x.value, reverse=True)
        values = [card.value for card in cards]
        suits = [card.suit for card in cards]
        
        # Check for Royal Flush
        if set(values[:5]) == set([10, 11, 12, 13, 14]) and len(set(suits[:5])) == 1:
            return 9, 14
        
        # Check for Straight Flush
        for i in range(0, len(cards) - 4):
            if all(cards[i+j].value == cards[i].value - j for j in range(5)) and len(set(suits[i:i+5])) == 1:
                return 8, cards[i].value
        
        # Check for Four of a Kind
        count = Counter(values)
        if 4 in count.values():
            return 7, [k for k, v in count.items() if v == 4][0]
        
        # Check for Full House
        if 3 in count.values() and 2 in count.values():
            return 6, [k for k, v in count.items() if v == 3][0]
        
        # Check for Flush
        count = Counter(suits)
        if 5 in count.values():
            return 5, max(values)
        
        # Check for Straight
        for i in range(0, len(cards) - 4):
            if all(cards[i+j].value == cards[i].value - j for j in range(5)):
                return 4, cards[i].value
        
        # Check for Three of a Kind
        count = Counter(values)
        if 3 in count.values():
            return 3, [k for k, v in count.items() if v == 3][0]
        
        # Check for Two Pairs
        if list(count.values()).count(2) == 2:
            two_pairs = [k for k, v in sorted(count.items(), key=lambda x: x[0], reverse=True) if v == 2]
            return 2, max(two_pairs)
        
        # Check for Pair
        if 2 in count.values():
            return 1, [k for k, v in count.items() if v == 2][0]
        
        # High Card
        return 0, max(values)

    def determine_winner(self, players, table):
        player_scores = []
        for player in players:
            if not player.folded:
                score, high_card = self.evaluate_hand(player.hand, table)
                player_scores.append((score, high_card, player))
        
        player_scores.sort(key=itemgetter(0, 1), reverse=True)
        
        # Finding potential winners (same score and high card)
        top_score, top_high_card = player_scores[0][:2]
        potential_winners = [player[2] for player in player_scores if player[0] == top_score and player[1] == top_high_card]
        
        # If multiple potential winners, pick a random one
        if len(potential_winners) > 1:
            winner = random.choice(potential_winners)
        else:
            winner = potential_winners[0]
            
        return winner

    def determineWinner(self):
        players_to_determine = [player for player in self.players if not player.folded]
        
        if len(players_to_determine) == 1:
            print("Returning the only player left")
            winner = players_to_determine[0]
            return self.getPlayerIndex(winner.playerId), winner
        else:
            print("Determining winner based on hand strength")
            winner = self.determine_winner(players_to_determine, self.table)
            return self.getPlayerIndex(winner.playerId), winner
    
    def __str__(self):
        return f"Game with {len(self.players)} players, on stage: {self.getStage()}"
