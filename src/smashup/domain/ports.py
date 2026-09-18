from __future__ import annotations

from typing import Protocol

from smashup.domain.effects import Effect
from smashup.domain.events import GameEvent
from smashup.domain.models import GameState


class AbilityResolver(Protocol):
    """领域层需要的能力解析端口，由外部的 AbilityRegistry 实现。"""

    def validate_play(
        self,
        state: GameState,
        source_id: str,
        actor_id: str,
        base_id: str | None,
        target_ids: tuple[str, ...],
    ) -> None: ...

    def effects_for_event(
        self, state: GameState, event: GameEvent
    ) -> list[Effect]: ...

    def power_bonus(self, state: GameState, target_id: str) -> int: ...

