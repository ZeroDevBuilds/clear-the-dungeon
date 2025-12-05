from enum import Enum


class SUIT(Enum):
    HEARTS = "❤️"
    DIAMONDS = "🔷"
    CLUBS = "♣️"
    SPADES = "♠️"


class ALIGNMENT(Enum):
    PLAYER = "Good"
    ROYALS = "Evil"


class RANK(Enum):
    ACE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    JOKER = "🃏"
