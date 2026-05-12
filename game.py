import random
import asyncio

class BingoGame:
    def __init__(self):
        self.players = {}
        self.called_numbers = []
        self.active = False
        self.winner = None
        self.total_cards = 200
        self.available_cards = list(range(1, 201))
        self.selection_time = 40
        self.selection_active = False
        self.current_selector = None
    
    def generate_card(self, card_id=None):
        card = {}
        letters = ['B', 'I', 'N', 'G', 'O']
        ranges = [range(1, 16), range(16, 31), range(31, 46), range(46, 61), range(61, 76)]
        for col_idx, (letter, num_range) in enumerate(zip(letters, ranges)):
            numbers = random.sample(list(num_range), 5)
            for row_idx in range(5):
                card[f"{letter}{row_idx+1}"] = numbers[row_idx]
        card["N3"] = "FREE"
        card["card_id"] = card_id if card_id else random.randint(1, 200)
        return card
    
    def create_game(self, chat_id):
        self.active = True
        self.players = {}
        self.called_numbers = []
        self.winner = None
        self.available_cards = list(range(1, 201))
        random.shuffle(self.available_cards)
        return True
    
    def add_player(self, user_id, username, num_cards=1):
        if user_id not in self.players and not self.winner:
            if len(self.available_cards) >= num_cards:
                cards = []
                for _ in range(num_cards):
                    if self.available_cards:
                        card_id = self.available_cards.pop(0)
                        card = self.generate_card(card_id)
                        cards.append(card)
                self.players[user_id] = {
                    'username': username,
                    'cards': cards,
                    'bingo_called': False,
                    'cards_bingo': []
                }
                return True, len(cards)
        return False, 0
    
    def get_remaining_cards(self):
        return len(self.available_cards)
    
    def call_number(self):
        if not self.active:
            return None
        available = [n for n in range(1, 76) if n not in self.called_numbers]
        if not available:
            return None
        number = random.choice(available)
        self.called_numbers.append(number)
        winner = self.check_all_cards_bingo()
        return number, winner
    
    def check_card_bingo(self, card):
        for row in range(1, 6):
            row_marked = 0
            for col in ['B', 'I', 'N', 'G', 'O']:
                key = f"{col}{row}"
                if key == "N3" or card[key] in self.called_numbers:
                    row_marked += 1
            if row_marked == 5:
                return True
        for col in ['B', 'I', 'N', 'G', 'O']:
            col_marked = 0
            for row in range(1, 6):
                key = f"{col}{row}"
                if key == "N3" or card[key] in self.called_numbers:
                    col_marked += 1
            if col_marked == 5:
                return True
        return False
    
    def check_all_cards_bingo(self):
        for user_id, player in self.players.items():
            if player['bingo_called']:
                continue
            for idx, card in enumerate(player['cards']):
                if idx in player['cards_bingo']:
                    continue
                if self.check_card_bingo(card):
                    player['cards_bingo'].append(idx)
                    player['bingo_called'] = True
                    self.winner = user_id
                    self.active = False
                    return user_id, len(player['cards_bingo'])
        return None, 0
