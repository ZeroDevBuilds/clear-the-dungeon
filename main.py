import random
from rich.table import Table
from rich.console import Console
from rich.align import Align
from rich.style import Style
from rich.text import Text
from cards import Card, get_player_cards, get_royal_cards
from utils import RANK
import logging
from datetime import datetime

logger = logging.getLogger("GameOn")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    f"logs/game_{datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')}.log"
)
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


class GameOn:
    TBL_STYLE = Style(bgcolor="grey23")
    ROW_STYLE = Style(bgcolor="yellow4")
    ATTACK_STYLE = Style(bgcolor="gold1", color="black")

    ENEMY = "enemy"
    ATTACKS = "attacks"

    player_deck: list[Card]
    royal_deck: list[Card]
    player_hand: list[Card]
    dungeon_room: list[Card | None]
    game_state: dict

    def __init__(self):
        self.player_deck = []
        self.royal_deck = []
        self.player_hand = []
        self.dungeon_room = []
        self.console = Console(color_system="truecolor")
        self._setup_game()

    def _setup_game(self):
        self.player_deck = self._create_player_deck()
        self.royal_deck = self._create_royal_deck()

        self.dungeon_room = self._get_new_room()
        self.player_hand = self._get_new_hand()
        self.game_state = {
            f"{idx + 1}": {"m": x, GameOn.ATTACKS: []}
            for idx, x in enumerate(self.dungeon_room)
        }

        self._display_game_state()
        self._game_loop()

    def _game_loop(self):
        while True:
            hand_idx, enemy_idx = self._get_player_action()
            royal_card = self.dungeon_room[enemy_idx]
            logger.debug(
                "Player selection, attack card: %s on royal card: %s",
                self.player_hand[hand_idx].to_log(),
                royal_card.to_log() if royal_card else 'None'
            )

            self._turn_end(hand_idx, enemy_idx)
            self._display_game_state()

    def _get_player_action(self) -> tuple[int, int]:

        while True:
            input_prompt = "Your turn : "
            user_input = input(input_prompt).strip()

            if self._input_is_help(user_input):
                continue

            if self._input_is_quit(user_input):
                exit(0)

            if self._input_is_discard(user_input):
                continue

            actions = user_input.split(" ")
            if self._input_is_invalid(actions):
                continue

            # valid input
            hand_input, enemy_input = actions
            hand_index = int(hand_input) - 1
            enemy_index = int(enemy_input) - 1
            return hand_index, enemy_index


    def _input_is_help(self, user_input: str) -> bool:
        if user_input == "h":
            self.console.print("""
            Help:   
            Enter the number of the card in your hand followed by the 
                number of the royal in the dungeon room you want to attack. 
                For example, '1 2' to use your first card on the second royal card. 
            Enter 'd' to discard your hand and draw a new one. 
            Enter 'q' to quit the game.
            """)
            return True
        return False
    
    def _input_is_quit(self, user_input: str) -> bool:
        if user_input.lower() == "q":
            self.console.print("Quitting the game. Goodbye!")
            return True
        return False

    def _input_is_discard(self, user_input: str) -> bool:
        if user_input.lower() == "d":
            # discard player hand and get new hand
            self._replenish_player_hand(discard_hand=True)

            self._display_game_state()
            return True
        return False
    
    def _input_is_invalid(self, inputs: list[str]) -> bool:
        if len(inputs) != 2:
            self.console.print(
                "Invalid input format. Please enter in the format 'hand# royal#'."
            )
            return True
        
        hand_input, enemy_input = inputs
        if hand_input not in ["1", "2", "3"] or enemy_input not in ["1", "2", "3", "4",]:
            self.console.print(
                    "Invalid input. Please enter numbers corresponding to your hand and the dungeon room."
                )
            return True
        
        hand_index = int(hand_input) - 1
        enemy_index = int(enemy_input) - 1
        if hand_index >= len(self.player_hand) or enemy_index >= len(self.dungeon_room):
            self.console.print(
                    "Invalid player or royal number. Please choose valid numbers."
                )
            return True
        return False

    def _turn_end(self, hand_index: int, enemy_index: int):
        if self.dungeon_room[enemy_index] is None:
            self.console.print(
                f"Royal {enemy_index + 1} is already defeated. Choose another royal."
            )
            return
        
        state_key = str(enemy_index + 1)
        curr_game_state = self.game_state[state_key]
        attack_stage = len(curr_game_state[GameOn.ATTACKS])

        match attack_stage:
            case 0:
                self._do_first_attack(hand_index, enemy_index)
            case 1:
                self._do_second_attack(hand_index, enemy_index)
            case 2:
                self._do_third_attack(hand_index, enemy_index)

        # check player hand is empty
        self._replenish_player_hand(discard_hand=False)

        # check dungeon room is empty
        self._game_over_player_wins()

        # check player deck is empty
        self._game_over_player_loses()
    
    def _replenish_player_hand(self, discard_hand: bool = False):
        if len(self.player_hand) == 0 or self.player_hand is None or discard_hand:
            self.player_hand = self._get_new_hand()

            if len(self.player_hand) > 0:
                logger.debug("Player hand replenished. New hand: %s",
                                [card.to_log() for card in self.player_hand])
            else:
                self._game_over_player_loses()

    def _game_over_player_loses(self):
        if not self.player_deck:
            self.console.print("Player deck is empty! Game over!")
            exit(0)

    def _game_over_player_wins(self):
        if all(card is None for card in self.dungeon_room):
            self.console.print("All royals defeated! You win!")
            exit(0)

    def _display_game_state(self):
        print("\033[2J\033[H", end="")
        self.console.print("\n" + " :video_game: " * (self.console.width // 2) + "\n")

        self._display_deck_status()

        self._display_dungeon_room()

        self._display_player_hand()

    def _display_dungeon_room(self):
        if self.dungeon_room:
            table = Table(
                title="Dungeon Room",
                min_width=60,
                style=GameOn.TBL_STYLE,
                expand=True,
                padding=(1, 0),
                row_styles=[GameOn.ROW_STYLE],
            )

            # create one column per room slot
            for i in range(len(self.dungeon_room)):
                table.add_column(f"{i + 1}", justify="center")

            # build the row showing each card or an empty cell
            row = [
                card.to_str() if card is not None else "X" for card in self.dungeon_room
            ]
            table.add_row(*row)

            # build the attack row if there are any attacks
            attack_row = self._display_attack_rows()
            if any(attack != "-" for attack in attack_row):
                table.add_row(*attack_row, style=GameOn.ATTACK_STYLE)

            table = Align.center(table, vertical="middle")
            self.console.print(table)

    def _display_player_hand(self):
        if self.player_hand:
            table = Table(
                title="Player Hand",
                min_width=50,
                padding=(1, 0),
                style=GameOn.TBL_STYLE,
            )

            for i in range(len(self.player_hand)):
                table.add_column(f"{i + 1}", justify="center")

            hand_row = [card.to_str() for card in self.player_hand]
            table.add_row(*hand_row, style=GameOn.ROW_STYLE)

            table = Align.center(table, vertical="middle")
            self.console.print(table)

    def _display_deck_status(self):
        table = Table(style=GameOn.TBL_STYLE)

        table.add_column("Player Deck", justify="center")
        table.add_column("Royal Deck", justify="center")

        table.add_row(
            Text(str(len(self.player_deck)), style="black"),
            Text(str(len(self.royal_deck)), style="black"),
            style=GameOn.ROW_STYLE,
        )

        table = Align.center(table, vertical="middle")
        self.console.print(table)

    def _display_attack_rows(self) -> list:
        attack_row = []
        for idx in range(len(self.dungeon_room)):
            attacks = self.game_state.get(f"{idx + 1}", {}).get(GameOn.ATTACKS, [])
            if attacks:
                attack_str = "  ".join([attack.to_str() for attack in attacks])
                attack_row.append(attack_str)
            else:
                attack_row.append("-")
        return attack_row

    def _pop_player_card(self, enemy_idx: int, hand_idx: int):
        state_key = str(enemy_idx + 1)
        if self.player_hand:
            player_card = self.player_hand.pop(hand_idx)
            m = self.game_state[state_key]["m"]

            self.game_state[state_key][GameOn.ATTACKS].append(player_card)

            logger.debug(
                "Popped attack card %s on royal card %s",
                player_card.to_log(),
                m.to_log() if m else 'None'
            )
            logger.debug(
                "Current attacks on royal %s: %s",
                m.to_log(),
                [card.to_log() for card in self.game_state[state_key][GameOn.ATTACKS]]
            )

    def _do_first_attack(self, hand_idx: int, enemy_idx: int):
        state_key = str(enemy_idx + 1)
        curr_game_state = self.game_state[state_key]
        curr_enemy: Card = curr_game_state["m"]
        curr_attacks = curr_game_state[GameOn.ATTACKS]

        # first attack can be any card
        if len(curr_attacks) == 0:
            logger.debug(
                "First attack played on royal %s at no %s",
                curr_enemy.to_log(),
                state_key,
            )
            self._pop_player_card(enemy_idx, hand_idx)
    
    def _do_second_attack(self, hand_idx: int, enemy_idx: int):
        state_key = str(enemy_idx + 1)
        curr_game_state = self.game_state[state_key]
        curr_enemy: Card = curr_game_state["m"]
        curr_attacks = curr_game_state[GameOn.ATTACKS]

        # second attack must sum to at least royal value or be a joker
        if len(curr_attacks) == 1:
            # check if card can be played
            player_card = self.player_hand[hand_idx]
            sum_ = curr_attacks[0].value + player_card.value
            if sum_ >= curr_enemy.value:
                logger.debug(
                    "Second attack played on royal %s at no %s",
                    curr_enemy.to_log(),
                    state_key,
                )
                self._pop_player_card(enemy_idx, hand_idx)
                self._state_enemy_defeatable(enemy_idx)
            else:
                self.console.print(
                    f"Attack value insufficient for royal {enemy_idx + 1}. Attack failed."
                )

    def _do_third_attack(self, hand_idx: int, enemy_idx: int):
        state_key = str(enemy_idx + 1)
        curr_game_state = self.game_state[state_key]
        curr_enemy = curr_game_state["m"]

        new_attack = self.player_hand[hand_idx]

        # match suit or joker for third played card
        if new_attack.suit != curr_enemy.suit or new_attack.rank != RANK.JOKER:
            self.console.print(
                f"Activation card suit does not match enemy's suit {enemy_idx + 1}. Activation failed."
            )
            return

        logger.debug(
            "Activation card played on royal %s at no %s",
            curr_enemy.to_log(),
            state_key,
        )
        self.console.print(
            f"Activation card played on royal {enemy_idx + 1}!"
        )
        self.console.print(f"Royal {enemy_idx + 1} defeated!")

        self._pop_player_card(enemy_idx, hand_idx)
        self._draw_new_royal(state_key, enemy_idx)
        

    def _draw_new_royal(self, state_key, enemy_idx):
        m = None
        if self.royal_deck:
            m = self.royal_deck.pop()

        logger.debug(
            "Drew new royal card: %s into dungeon room slot %s.",
            m.to_log() if m else 'X',
            state_key
        )

        # reset game state with new enemy
        self.dungeon_room[enemy_idx] = m
        self.game_state[state_key] = {"m": m, GameOn.ATTACKS: []}
        
    def _state_enemy_defeatable(self, enemy_idx: int):
        state_key = str(enemy_idx + 1)
        game_state = self.game_state[state_key]

        if (
            sum(attack_card.value for attack_card in game_state[GameOn.ATTACKS])
            >= game_state["m"].value
        ):
            self.game_state[state_key]["m"].enabled = True
            royal_card = self.dungeon_room[enemy_idx]
            logger.debug(
                "Royal card %s is now defeatable.",
                royal_card.to_log() if royal_card else 'X'
            )
            # for x in self.game_state[f"{state_idx + 1}"][GameOn.ATTACKS]:
            #     x.enabled = True

    def _shuffle(self, deck: list[Card]) -> list[Card]:
        random.shuffle(deck)
        return deck

    def _create_player_deck(self) -> list[Card]:
        deck: list[Card] = get_player_cards()
        return self._shuffle(deck)

    def _create_royal_deck(self) -> list[Card]:
        royal_deck: list[Card] = get_royal_cards()
        return self._shuffle(royal_deck)

    def _get_new_room(self) -> list[Card | None]:
        room: list[Card | None] = []
        for _ in range(4):
            if self.royal_deck:
                room.append(self.royal_deck.pop())
            else:
                return []
        return room

    def _get_new_hand(self) -> list[Card]:
        hand: list[Card] = []
        for _ in range(3):
            if self.player_deck:
                hand.append(self.player_deck.pop())
            else:
                break
        return hand


if __name__ == "__main__":
    game = GameOn()
