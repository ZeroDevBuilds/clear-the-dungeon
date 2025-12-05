from utils import SUIT, RANK, ALIGNMENT


class Cards:
    suit: SUIT | None
    rank: RANK
    value: int | None
    alignment: ALIGNMENT
    enabled: bool = False

    def to_str(self) -> str:
        suit_str = self.suit.value if self.suit else "J"
        rank_str = self.rank.value
        if self.enabled:
            return f":white_check_mark: [bold green]{rank_str}{suit_str}[/bold green]"
        else:
            return f"[black]{rank_str}[/black]{suit_str}"

    def to_log(self) -> str:
        suit_str = self.suit.value if self.suit else "J"
        rank_str = self.rank.value
        return f"{rank_str}{suit_str}"

    def __str__(self) -> str:
        return self.to_str()


def get_player_cards():
    cards: list[Cards] = []

    for suit in SUIT:
        for value in range(1, 10 + 1):
            card = Cards()
            card.suit = suit
            card.rank = RANK(str(value)) if value != 1 else RANK.ACE
            card.value = value
            card.alignment = ALIGNMENT.PLAYER
            cards.append(card)

    for joker in range(2):
        card = Cards()
        card.suit = None
        card.rank = RANK.JOKER
        card.value = 10
        card.alignment = ALIGNMENT.PLAYER
        cards.append(card)

    return cards


def get_royal_cards():
    cards: list[Cards] = []

    royal_values = {
        "JACK": 11,
        "QUEEN": 12,
        "KING": 13,
    }

    for suit in SUIT:
        for name, value in royal_values.items():
            card = Cards()
            card.suit = suit
            card.rank = RANK[name]
            card.value = value
            card.alignment = ALIGNMENT.ROYALS
            cards.append(card)

    return cards
