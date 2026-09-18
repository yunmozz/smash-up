from __future__ import annotations

from dataclasses import dataclass
from random import Random

from smashup.domain.enums import Phase, Zone
from smashup.domain.exceptions import GameRuleError
from smashup.domain.models import (
    BaseDefinition,
    BaseInstance,
    CardDefinition,
    CardInstance,
    GameState,
    PlayerState,
    new_id,
)


@dataclass(frozen=True)
class PlayerSetup:
    name: str
    factions: tuple[str, ...]


class GameFactory:
    def __init__(self, random: Random | None = None):
        self.random = random or Random()

    def create(
        self,
        player_setups: list[PlayerSetup],
        card_definitions: list[CardDefinition],
        base_definitions: list[BaseDefinition],
    ) -> GameState:
        if not 2 <= len(player_setups) <= 4:
            raise GameRuleError("玩家人数必须为 2 到 4 人")
        card_catalog = {definition.id: definition for definition in card_definitions}
        by_faction: dict[str, list[CardDefinition]] = {}
        for definition in card_definitions:
            by_faction.setdefault(definition.faction, []).append(definition)

        players: list[PlayerState] = []
        cards: dict[str, CardInstance] = {}
        for setup in player_setups:
            player = PlayerState(new_id("player"), setup.name, setup.factions)
            for faction in setup.factions:
                if faction not in by_faction:
                    raise GameRuleError(f"找不到派系数据: {faction}")
                for definition in by_faction[faction]:
                    for _ in range(definition.quantity):
                        card = CardInstance(
                            new_id("card"),
                            definition.id,
                            player.id,
                            player.id,
                            Zone.DECK,
                            player.id,
                        )
                        cards[card.id] = card
                        player.deck.append(card.id)
            self.random.shuffle(player.deck)
            for card_id in tuple(player.deck[:5]):
                player.deck.remove(card_id)
                player.hand.append(card_id)
                cards[card_id].zone = Zone.HAND
            players.append(player)

        bases = [
            BaseInstance(new_id("base"), definition.id)
            for definition in base_definitions
        ]
        self.random.shuffle(bases)
        visible_count = len(players) + 1
        visible, deck = bases[:visible_count], bases[visible_count:]
        self.random.shuffle(players)
        return GameState(
            players=players,
            cards=cards,
            card_definitions=card_catalog,
            bases=visible,
            base_definitions={definition.id: definition for definition in base_definitions},
            base_deck=deck,
            phase=Phase.START_TURN,
        )
