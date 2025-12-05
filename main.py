import random
from rich.table import Table
from rich.console import Console
from rich.align import Align
from rich.style import Style
from rich.text import Text
from cards import Cards, get_player_cards, get_royal_cards
from utils import RANK
import logging
from datetime import datetime

logger = logging.getLogger("GameOn")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    f"game_{datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')}.log"
)
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


class GameOn:
    TBL_STYLE = Style(bgcolor="grey23")
    ROW_STYLE = Style(bgcolor="yellow4")
    ATTACK_STYLE = Style(bgcolor="gold1", color="black")

    player_deck: list[Cards]
    royal_deck: list[Cards]
    player_hand: list[Cards]
    dungeon_room: list[Cards | None]
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
            f"{idx + 1}": {"m": x, "attacks": []}
            for idx, x in enumerate(self.dungeon_room)
        }

        self._display_game_state()
        self._game_loop()

    def _game_loop(self):
        while True:
            hand_index, monster_index = self._get_player_action()
            logger.debug(
                f"Player selection, attack card: {self.player_hand[hand_index].to_log()} on monster card: {self.dungeon_room[monster_index].to_log() if self.dungeon_room[monster_index] else 'None'}"
            )

            self._turn_end(hand_index, monster_index)
            self._display_game_state()

    def _get_player_action(self) -> tuple[int, int]:
        # player hand then monster a card to play by its number (1, 2, 3) or 'q' to quit:
        while True:
            input_prompt = "Your turn : "
            user_input = input(input_prompt).strip()

            if user_input == "h":
                self.console.print("""
                Help:   
                Enter the number of the card in your hand followed by the 
                    number of the monster in the dungeon room you want to attack. 
                    For example, '1 2' to use your first card on the second monster. 
                Enter 'd' to discard your hand and draw a new one. 
                Enter 'q' to quit the game.
                """)
                continue

            if user_input.lower() == "q":
                self.console.print("Quitting the game. Goodbye!")
                exit(0)

            # discard player hand and get new hand
            if user_input.lower() == "d":
                self.player_hand = self._get_new_hand()
                self._display_game_state()
                continue

            actions = user_input.split(" ")
            if len(actions) != 2:
                self.console.print(
                    "Invalid input format. Please enter in the format 'hand# monster#'."
                )
                continue
            else:
                hand_input, monster_input = actions
                if hand_input in ["1", "2", "3"] and monster_input in [
                    "1",
                    "2",
                    "3",
                    "4",
                ]:
                    hand_index = int(hand_input) - 1
                    monster_index = int(monster_input) - 1
                    if hand_index < len(self.player_hand) and monster_index < len(
                        self.dungeon_room
                    ):
                        return hand_index, monster_index
                    else:
                        self.console.print(
                            "Invalid card or monster number. Please choose valid numbers."
                        )
                else:
                    self.console.print(
                        "Invalid input. Please enter numbers corresponding to your hand and the dungeon room."
                    )

    def _turn_end(self, hand_index: int, monster_index: int):
        if self.dungeon_room[monster_index] is None:
            self.console.print(
                f"Monster {monster_index + 1} is already defeated. Choose another monster."
            )
            return

        if self._state_valid_attack(hand_index, monster_index) == 1:
            return

        if self._state_monster_activation(hand_index, monster_index) == 1:
            return

        # check player hand is empty
        if not self.player_hand:
            self.player_hand = self._get_new_hand()

        # check dungeon room is empty
        if all(card is None for card in self.dungeon_room):
            self.console.print("All monsters defeated! You win!")
            exit(0)

        # check player deck is empty
        if not self.player_deck:
            self.console.print("Player deck is empty! Game over!")
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
            attacks = self.game_state.get(f"{idx + 1}", {}).get("attacks", [])
            if attacks:
                attack_str = "  ".join([attack.to_str() for attack in attacks])
                attack_row.append(attack_str)
            else:
                attack_row.append("-")
        return attack_row

    def _pop_player_card(self, monster_idx, hand_idx: int):
        state_key = str(monster_idx + 1)
        if self.player_hand:
            player_card = self.player_hand.pop(hand_idx)
            m = self.game_state[state_key]["m"]

            self.game_state[state_key]["attacks"].append(player_card)

            logger.debug(
                f"Popped attack card {player_card.to_log()} on monster card {m.to_log() if m else 'None'}"
            )
            logger.debug(
                f"Current attacks on Monster {m.to_log()}: {[card.to_log() for card in self.game_state[state_key]['attacks']]}"
            )

    def _state_valid_attack(self, hand_idx, monster_idx):
        state_key = str(monster_idx + 1)
        curr_game_state = self.game_state[state_key]
        curr_monster = curr_game_state["m"]
        curr_attacks = curr_game_state["attacks"]

        # first attack can be any card
        if len(curr_attacks) == 0:
            logger.debug(
                "First attack played on monster {} at no {}",
                curr_monster.to_log(),
                state_key,
            )
            self._pop_player_card(monster_idx, hand_idx)
            return 0

        # second attack must sum to at least monster value or be a joker
        if len(curr_attacks) == 1:
            # check if card can be played
            player_card = self.player_hand[hand_idx]
            sum_ = curr_attacks[0].value + player_card.value
            if sum_ >= curr_monster.value:
                logger.debug(
                    "Second attack played on monster {} at no {}",
                    curr_monster.to_log(),
                    state_key,
                )
                self._pop_player_card(monster_idx, hand_idx)
                self._state_monster_defeatable(monster_idx)
                return 0
            else:
                self.console.print(
                    f"Attack value insufficient for Monster {monster_idx + 1}. Attack failed."
                )
                return 1

    def _state_monster_activation(self, hand_idx: int, monster_idx: int):
        state_key = str(monster_idx + 1)
        curr_game_state = self.game_state[state_key]
        curr_monster = curr_game_state["m"]
        curr_attacks = curr_game_state["attacks"]

        # attacks must be 2 card only, new card should be activation card
        if len(curr_attacks) == 2:
            # check if activation condition met
            sum_ = sum(attack_card.value for attack_card in curr_attacks)
            if sum_ >= curr_monster.value:
                new_attack = self.player_hand[hand_idx]

                # match suit or joker for third played card
                if (
                    new_attack.suit == curr_monster.suit
                    or new_attack.rank == RANK.JOKER
                ):
                    logger.debug(
                        "Activation card played on monster {} at no {}",
                        curr_monster.to_log(),
                        state_key,
                    )
                    self.console.print(
                        f"Activation card played on Monster {monster_idx + 1}!"
                    )
                    self.console.print(f"Monster {monster_idx + 1} defeated!")
                    self._pop_player_card(monster_idx, hand_idx)

                    # draw new royal card to dungeon room
                    m = None
                    if self.royal_deck:
                        m = self.royal_deck.pop()

                    logger.debug(
                        f"Drew new monster card: {m.to_log() if m else 'X'} into dungeon room slot {monster_idx + 1}."
                    )
                    self.dungeon_room[monster_idx] = m
                    self.game_state[state_key] = {"m": m, "attacks": []}
                    return 0
                else:
                    self.console.print(
                        f"Activation card suit does not match Monster {monster_idx + 1}. Activation failed."
                    )
                    return 1
        return 0

    def _state_monster_defeatable(self, monster_idx):
        state_key = str(monster_idx + 1)
        game_state = self.game_state[state_key]

        if (
            sum(attack_card.value for attack_card in game_state["attacks"])
            >= game_state["m"].value
        ):
            self.game_state[state_key]["m"].enabled = True
            logger.debug(
                f"Monster card {self.dungeon_room[monster_idx].to_log()} is now defeatable."
            )
            # for x in self.game_state[f"{state_idx + 1}"]["attacks"]:
            #     x.enabled = True

    def _shuffle(self, deck: list[Cards]) -> list[Cards]:
        random.shuffle(deck)
        return deck

    def _create_player_deck(self) -> list[Cards]:
        deck: list[Cards] = get_player_cards()
        return self._shuffle(deck)

    def _create_royal_deck(self) -> list[Cards]:
        royal_deck: list[Cards] = get_royal_cards()
        return self._shuffle(royal_deck)

    def _get_new_room(self) -> list[Cards | None]:
        room: list[Cards | None] = []
        for _ in range(4):
            if self.royal_deck:
                room.append(self.royal_deck.pop())
            else:
                return []
        return room

    def _get_new_hand(self) -> list[Cards]:
        hand: list[Cards] = []
        for _ in range(3):
            if self.player_deck:
                hand.append(self.player_deck.pop())
            else:
                break
        return hand


if __name__ == "__main__":
    game = GameOn()
