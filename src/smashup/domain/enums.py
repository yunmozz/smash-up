from __future__ import annotations

from enum import Enum, auto


class CardType(str, Enum):
    MINION = "minion"
    ACTION = "action"


class Zone(str, Enum):
    DECK = "deck"
    HAND = "hand"
    DISCARD = "discard"
    BASE = "base"
    BASE_DECK = "base_deck"
    BASE_DISCARD = "base_discard"


class MoveReason(str, Enum):
    PLAY = "play"
    MOVE = "move"
    DESTROY = "destroy"
    DISCARD = "discard"
    RETURN = "return"
    PLACE = "place"
    DRAW = "draw"
    SCORE_CLEANUP = "score_cleanup"


class Phase(Enum):
    SETUP = auto()
    START_TURN = auto()
    PLAY_CARDS = auto()
    SCORE_BASES = auto()
    BEFORE_SCORE = auto()
    WHEN_SCORE = auto()
    AFTER_SCORE = auto()
    DRAW_CARDS = auto()
    END_TURN = auto()
    GAME_OVER = auto()


class Duration(str, Enum):
    PERMANENT = "permanent"
    END_OF_TURN = "end_of_turn"
    START_OF_OWNERS_TURN = "start_of_owners_turn"


class TargetKind(str, Enum):
    MINION = "minion"
    BASE = "base"
    PLAYER = "player"
    CARD_IN_HAND = "card_in_hand"

