from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from smashup.domain.enums import CardType, Duration, Phase, Zone


def new_id(prefix: str) -> str:
    """生成适合日志阅读、同时在一局游戏内唯一的实例 ID。"""
    return f"{prefix}-{uuid4().hex[:12]}"


@dataclass(frozen=True)
class AbilitySpec:
    """JSON 中的一项能力声明；handler 指向能力注册表中的实现。"""

    handler: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CardDefinition:
    """卡牌模板。同名的多张实体共享一个不可变定义。"""

    id: str
    name: str
    faction: str
    card_type: CardType
    printed_power: int | None
    text_zh: str
    quantity: int = 1
    abilities: tuple[AbilitySpec, ...] = ()
    attach_to: str | None = None


@dataclass(frozen=True)
class BaseDefinition:
    id: str
    name: str
    breakpoint: int
    vp: tuple[int, int, int]
    text_zh: str = ""
    abilities: tuple[AbilitySpec, ...] = ()


@dataclass
class CardInstance:
    """牌局中的单张实体。临时状态放在实例上，而不是定义上。"""

    id: str
    definition_id: str
    owner_id: str
    controller_id: str
    zone: Zone
    zone_owner_id: str | None = None
    attached_to_id: str | None = None
    exhausted_abilities: set[str] = field(default_factory=set)


@dataclass
class BaseInstance:
    id: str
    definition_id: str
    minion_ids: list[str] = field(default_factory=list)
    action_ids: list[str] = field(default_factory=list)


@dataclass
class PlayerState:
    id: str
    name: str
    factions: tuple[str, ...]
    deck: list[str] = field(default_factory=list)
    hand: list[str] = field(default_factory=list)
    discard: list[str] = field(default_factory=list)
    vp: int = 0


@dataclass
class TurnState:
    number: int = 0
    normal_minions_played: int = 0
    normal_actions_played: int = 0
    extra_minion_plays: int = 0
    extra_action_plays: int = 0

    def reset(self) -> None:
        self.normal_minions_played = 0
        self.normal_actions_played = 0
        self.extra_minion_plays = 0
        self.extra_action_plays = 0


@dataclass
class PowerModifier:
    id: str
    amount: int
    source_id: str
    target_card_id: str | None = None
    controller_id: str | None = None
    duration: Duration = Duration.PERMANENT


@dataclass
class ChoiceRequest:
    id: str
    player_id: str
    prompt: str
    option_ids: tuple[str, ...]
    minimum: int = 1
    maximum: int = 1
    continuation: dict[str, Any] = field(default_factory=dict)


@dataclass
class GameState:
    """一局游戏的唯一可变状态（Aggregate Root）。"""

    players: list[PlayerState]
    cards: dict[str, CardInstance]
    card_definitions: dict[str, CardDefinition]
    bases: list[BaseInstance]
    base_definitions: dict[str, BaseDefinition]
    base_deck: list[BaseInstance] = field(default_factory=list)
    base_discard: list[BaseInstance] = field(default_factory=list)
    active_player_index: int = 0
    phase: Phase = Phase.SETUP
    turn: TurnState = field(default_factory=TurnState)
    modifiers: list[PowerModifier] = field(default_factory=list)
    pending_choice: ChoiceRequest | None = None
    winner_ids: tuple[str, ...] = ()

    @property
    def active_player(self) -> PlayerState:
        return self.players[self.active_player_index]

    def player(self, player_id: str) -> PlayerState:
        return next(player for player in self.players if player.id == player_id)

    def base(self, base_id: str) -> BaseInstance:
        return next(base for base in self.bases if base.id == base_id)

    def card_definition(self, card_id: str) -> CardDefinition:
        return self.card_definitions[self.cards[card_id].definition_id]

    def base_definition(self, base_id: str) -> BaseDefinition:
        return self.base_definitions[self.base(base_id).definition_id]

