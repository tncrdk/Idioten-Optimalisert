import deck
import abstract_agent


class Game:
    def __init__(self, log_turn: bool, custom_deck=None) -> None:
        if bool(custom_deck):
            self.deck = custom_deck
        else:
            self.deck = deck.Deck()
        self.pile = deck.Deck(generate_deck=False)

        self.turns = 0
        self.max_rounds = 10_000
        self.burnt_cards = []
        self.log_turn = log_turn

    """ 
    SETUP
    """

    def add_players(
        self,
        player1: abstract_agent.AbstractAgent,
        player2: abstract_agent.AbstractAgent,
    ):
        self.players = (player1, player2)

    def deal_cards(self):
        for player in self.players:
            for _ in range(3):
                player.add_card_to_hand(self.deck.pop_top_card())
                player.visible_table_cards.append(self.deck.pop_top_card())
                player.hidden_table_cards.append(self.deck.pop_top_card())
        self.pile.add_card(self.deck.pop_top_card())

    """ 
    RUN GAME
    """

    def run_game(self):
        game_finished = False
        player, opponent = self.players[0], self.players[1]

        while not game_finished:
            self.turns += 1
            if player.finished:
                winner = player
                game_finished = True
                break

            self.take_turn(player, opponent)
            player, opponent = opponent, player
            game_finished = self.turns > self.max_rounds

        tot_rounds = self.turns / 2
        return winner, tot_rounds  # kan legge til flere stats kanskje

    """ 
    PLAY TURN
    """

    def take_turn(
        self,
        player: abstract_agent.AbstractAgent,
        oppnonent: abstract_agent.AbstractAgent,
    ):
        playable_cards = self.get_playable_cards(player, self.pile, False)
        can_play = bool(playable_cards)
        state = {
            "player_hand": player.hand,
            "playable_cards": playable_cards,
            "player_visible_table_cards": player.visible_table_cards,
            "opponents_cards": player.opponents_cards,
            "pile": self.pile,
            "burnt_cards": self.burnt_cards,
        }

        if not can_play:
            self.can_not_play_actions(playable_cards, player, oppnonent, self.pile)

        else:
            player.process_state(state)
            player_input = player.return_output()
            self.make_play(player_input, self.pile, self.deck, self.burnt_cards)
            self.restore_player_hand(player, self.deck)
            if (
                not (self.deck or player.hand or player.visible_table_cards)
                and player.hidden_table_cards
            ):
                player.take_hidden_table_cards()
            player.check_if_finished()

    def simulate_play(
        self,
        player: abstract_agent.AbstractAgent,
        index: int,
        card: deck.Card,
        root_state: dict,
        cards_played: list,
    ) -> tuple:
        """Simulates a play and returns ([possible_state], [state_to_investigate])"""

        pile = root_state["pile"]
        deck = root_state["deck"]
        burnt_cards = root_state["burnt_cards"]
        cards_played.append((index, card))

        deck.add_card(player.play_card_by_index(index))
        self.apply_side_effects(card, pile, deck, burnt_cards)

        playable_cards = self.get_playable_cards(player, pile, True)
        root_state["playable_cards"] = playable_cards

        if card.value == 10 or card.value == 2 and bool(player.hand):
            return ([], [root_state])
        elif not bool(playable_cards):
            return ([root_state], [])
        return ([root_state], [root_state])

    """ 
    ACTIONS
    """

    def make_play(
        self,
        player: abstract_agent.AbstractAgent,
        player_input: list,
        pile: deck.Deck,
        deck: deck.Deck,
        burnt_cards: list,
    ) -> None:
        for play in player_input:
            pile.add_card(player.play_card_by_index(play))
            self.apply_side_effects(player, play, pile, deck, burnt_cards)
            # add to oppnents_cards

    def can_not_play_actions(
        self,
        player: abstract_agent.AbstractAgent,
        opponent: abstract_agent.AbstractAgent,
        pile: deck.Deck,
    ) -> None:
        player.hand += pile.cards
        opponent.opponents_cards += pile.cards
        pile.clear()

    def restore_player_hand(
        self, player: abstract_agent.AbstractAgent, deck: deck.Deck
    ) -> None:
        while len(player.hand) < 3 and deck:
            player.add_card_to_hand(deck.pop_top_card())

    def apply_side_effects(
        self,
        player: abstract_agent.AbstractAgent,
        card_played: deck.Card,
        pile: deck.Deck,
        deck: deck.Deck,
        burnt_cards: list,
    ) -> None:
        """Sjekk om det skal skje noe spesielt på grunn kortet som ble spilt. Hvis ja, gjennomfør disse effektene"""

        if card_played.value == 10 or self.check_4_in_a_row():
            burnt_cards += pile
            pile.clear()

        if not (deck or player.hand) and player.visible_table_cards:
            player.take_visible_table_cards()

    def log_turn(self) -> None:
        pass

    """ 
    GET-FUNCTIONS
    """

    def get_playable_cards(
        self, player: abstract_agent.AbstractAgent, pile: deck.Deck, is_building: bool
    ) -> list:
        if not bool(pile):
            playable_cards = list(enumerate(player.hand))
            return playable_cards

        playable_cards = []

        if is_building:
            for index, card in enumerate(player.hand):
                if self.check_if_buildable_card(card, pile.get_top_card()):
                    playable_cards.append((index, card))
            return playable_cards

        else:
            for index, card in enumerate(player.hand):
                if self.check_if_playable_card(card):
                    playable_cards.append((index, card))
            return playable_cards

    """
    CHECKS
    """

    def check_if_playable_card(self, card, top_pile_card) -> bool:
        if not bool(top_pile_card):
            return True
        elif card.value == 2 or card.value == 10:
            return True
        elif card.value >= top_pile_card.value:
            return True
        return False

    def check_if_buildable_card(self, card, top_pile_card) -> bool:
        if card.value == 10:
            return False
        if top_pile_card.value == card.value:
            return True
        if top_pile_card.value + 1 == card.value:
            return True
        return False

    def check_4_in_a_row(self, pile) -> bool:
        CARDS_TO_CHECK = 4
        if len(pile) < CARDS_TO_CHECK:
            return False
        for card in pile[-CARDS_TO_CHECK + 1 :]:
            if card.value != pile[-CARDS_TO_CHECK].value:
                return False
        return True


if __name__ == "__main__":
    pass