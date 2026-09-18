from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from smashup.domain.enums import CardType, Zone
from smashup.domain.models import GameState


class CardSpecification(Protocol):
    """策略/规约接口：封装“什么牌可以成为目标”。"""

    def is_satisfied_by(self, state: GameState, card_id: str) -> bool: ...


@dataclass(frozen=True)
class AllOf:
    specifications: tuple[CardSpecification, ...]

    def is_satisfied_by(self, state: GameState, card_id: str) -> bool:
        return all(spec.is_satisfied_by(state, card_id) for spec in self.specifications)


@dataclass(frozen=True)
class IsMinion:
    def is_satisfied_by(self, state: GameState, card_id: str) -> bool:
        return state.card_definition(card_id).card_type is CardType.MINION


@dataclass(frozen=True)
class IsInPlay:
    def is_satisfied_by(self, state: GameState, card_id: str) -> bool:
        return state.cards[card_id].zone is Zone.BASE


@dataclass(frozen=True)
class AtBase:
    base_id: str

    def is_satisfied_by(self, state: GameState, card_id: str) -> bool:
        card = state.cards[card_id]
        return card.zone is Zone.BASE and card.zone_owner_id == self.base_id


@dataclass(frozen=True)
class ControlledBy:
    player_id: str

    def is_satisfied_by(self, state: GameState, card_id: str) -> bool:
        return state.cards[card_id].controller_id == self.player_id


@dataclass(frozen=True)
class NotControlledBy:
    player_id: str

    def is_satisfied_by(self, state: GameState, card_id: str) -> bool:
        return state.cards[card_id].controller_id != self.player_id


@dataclass(frozen=True)
class PrintedPowerAtMost:
    maximum: int

    def is_satisfied_by(self, state: GameState, card_id: str) -> bool:
        power = state.card_definition(card_id).printed_power
        return power is not None and power <= self.maximum


def matching_cards(state: GameState, specification: CardSpecification) -> tuple[str, ...]:
    return tuple(
        card_id
        for card_id in state.cards
        if specification.is_satisfied_by(state, card_id)
    )

