from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Protocol

from smashup.domain.enums import CardType, Duration, MoveReason, Zone
from smashup.domain.events import GameEvent, card_moved
from smashup.domain.exceptions import GameRuleError
from smashup.domain.models import GameState, PowerModifier, new_id


class Effect(Protocol):
    """可组合的原子规则操作。"""

    def apply(self, state: GameState, random: Random) -> list[GameEvent]: ...


def _remove_from_current_zone(state: GameState, card_id: str) -> None:
    card = state.cards[card_id]
    if card.zone_owner_id is None:
        return
    if card.zone in (Zone.DECK, Zone.HAND, Zone.DISCARD):
        player = state.player(card.zone_owner_id)
        collection = {
            Zone.DECK: player.deck,
            Zone.HAND: player.hand,
            Zone.DISCARD: player.discard,
        }[card.zone]
        if card_id in collection:
            collection.remove(card_id)
    elif card.zone is Zone.BASE:
        try:
            base = state.base(card.zone_owner_id)
        except StopIteration:
            return
        for collection in (base.minion_ids, base.action_ids):
            if card_id in collection:
                collection.remove(card_id)


@dataclass(frozen=True)
class MoveCardEffect:
    card_id: str
    destination: Zone
    destination_id: str | None
    reason: MoveReason
    actor_id: str | None = None
    attach_to_id: str | None = None

    def apply(self, state: GameState, random: Random) -> list[GameEvent]:
        card = state.cards[self.card_id]
        old_zone = card.zone
        _remove_from_current_zone(state, self.card_id)

        if self.destination in (Zone.DECK, Zone.HAND, Zone.DISCARD):
            player_id = self.destination_id or card.owner_id
            player = state.player(player_id)
            collection = {
                Zone.DECK: player.deck,
                Zone.HAND: player.hand,
                Zone.DISCARD: player.discard,
            }[self.destination]
            collection.append(self.card_id)
            card.zone_owner_id = player_id
            card.controller_id = card.owner_id
            card.attached_to_id = None
        elif self.destination is Zone.BASE:
            if self.destination_id is None:
                raise GameRuleError("移动到基地时必须提供基地 ID")
            base = state.base(self.destination_id)
            definition = state.card_definition(self.card_id)
            target = (
                base.minion_ids
                if definition.card_type is CardType.MINION
                else base.action_ids
            )
            target.append(self.card_id)
            card.zone_owner_id = self.destination_id
            card.attached_to_id = self.attach_to_id
        else:
            raise GameRuleError(f"暂不支持移动到区域 {self.destination.value}")

        card.zone = self.destination
        return [
            card_moved(
                self.card_id,
                self.actor_id,
                old_zone,
                self.destination,
                self.reason,
                self.destination_id,
            )
        ]


@dataclass(frozen=True)
class GainVPEffect:
    player_id: str
    amount: int
    source_id: str | None = None

    def apply(self, state: GameState, random: Random) -> list[GameEvent]:
        state.player(self.player_id).vp += self.amount
        return [
            GameEvent(
                "vp_gained",
                self.player_id,
                self.source_id,
                {"amount": self.amount},
            )
        ]


@dataclass(frozen=True)
class GrantExtraPlayEffect:
    player_id: str
    card_type: CardType
    amount: int = 1

    def apply(self, state: GameState, random: Random) -> list[GameEvent]:
        if self.card_type is CardType.MINION:
            state.turn.extra_minion_plays += self.amount
        else:
            state.turn.extra_action_plays += self.amount
        return [
            GameEvent(
                "extra_play_granted",
                self.player_id,
                payload={"card_type": self.card_type.value, "amount": self.amount},
            )
        ]


@dataclass(frozen=True)
class DrawCardsEffect:
    player_id: str
    amount: int

    def apply(self, state: GameState, random: Random) -> list[GameEvent]:
        player = state.player(self.player_id)
        events: list[GameEvent] = []
        for _ in range(self.amount):
            if not player.deck:
                if not player.discard:
                    break
                random.shuffle(player.discard)
                for card_id in player.discard:
                    card = state.cards[card_id]
                    card.zone = Zone.DECK
                    card.zone_owner_id = player.id
                player.deck.extend(player.discard)
                player.discard.clear()
                events.append(GameEvent("discard_shuffled", player.id))
            card_id = player.deck[0]
            events.extend(
                MoveCardEffect(
                    card_id,
                    Zone.HAND,
                    player.id,
                    MoveReason.DRAW,
                    player.id,
                ).apply(state, random)
            )
        return events


@dataclass(frozen=True)
class AddPowerModifierEffect:
    amount: int
    source_id: str
    target_card_id: str | None = None
    controller_id: str | None = None
    duration: Duration = Duration.END_OF_TURN

    def apply(self, state: GameState, random: Random) -> list[GameEvent]:
        modifier = PowerModifier(
            id=new_id("modifier"),
            amount=self.amount,
            source_id=self.source_id,
            target_card_id=self.target_card_id,
            controller_id=self.controller_id,
            duration=self.duration,
        )
        state.modifiers.append(modifier)
        return [
            GameEvent(
                "power_modifier_added",
                source_id=self.source_id,
                payload={"modifier_id": modifier.id, "amount": self.amount},
            )
        ]


@dataclass(frozen=True)
class SequenceEffect:
    effects: tuple[Effect, ...]

    def apply(self, state: GameState, random: Random) -> list[GameEvent]:
        events: list[GameEvent] = []
        for effect in self.effects:
            events.extend(effect.apply(state, random))
        return events

