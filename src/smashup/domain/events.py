from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from smashup.domain.enums import MoveReason, Phase, Zone


@dataclass(frozen=True)
class GameEvent:
    """已经发生的事实；payload 只携带 ID 和简单值，便于序列化。"""

    name: str
    actor_id: str | None = None
    source_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


def phase_changed(old: Phase, new: Phase, player_id: str) -> GameEvent:
    return GameEvent(
        "phase_changed", player_id, payload={"old": old.name, "new": new.name}
    )


def card_moved(
    card_id: str,
    actor_id: str | None,
    old_zone: Zone,
    new_zone: Zone,
    reason: MoveReason,
    destination_id: str | None,
) -> GameEvent:
    return GameEvent(
        "card_moved",
        actor_id,
        card_id,
        {
            "old_zone": old_zone.value,
            "new_zone": new_zone.value,
            "reason": reason.value,
            "destination_id": destination_id,
        },
    )

