from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Command:
    player_id: str


@dataclass(frozen=True)
class StartTurn(Command):
    pass


@dataclass(frozen=True)
class PlayCard(Command):
    card_id: str
    base_id: str | None = None
    target_ids: tuple[str, ...] = ()
    as_extra: bool = False


@dataclass(frozen=True)
class EndPlayPhase(Command):
    pass


@dataclass(frozen=True)
class ScoreBase(Command):
    base_id: str


@dataclass(frozen=True)
class ResolveChoice(Command):
    choice_id: str
    selected_ids: tuple[str, ...]


@dataclass(frozen=True)
class FinishTurn(Command):
    pass

