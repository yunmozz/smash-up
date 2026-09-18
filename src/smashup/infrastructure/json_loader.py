from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from smashup.domain.enums import CardType
from smashup.domain.exceptions import DataValidationError
from smashup.domain.models import AbilitySpec, BaseDefinition, CardDefinition


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _abilities(raw: list[dict[str, Any]] | None) -> tuple[AbilitySpec, ...]:
    return tuple(
        AbilitySpec(item["handler"], item.get("params", {}))
        for item in (raw or [])
    )


def load_faction(path: str | Path) -> list[CardDefinition]:
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    faction = data.get("faction")
    if not faction or not isinstance(data.get("cards"), list):
        raise DataValidationError(f"派系文件格式错误: {source}")
    definitions: list[CardDefinition] = []
    seen: set[str] = set()
    for raw in data["cards"]:
        card_id = raw.get("id", f"{_slug(faction)}.{_slug(raw['name'])}")
        if card_id in seen:
            raise DataValidationError(f"卡牌 ID 重复: {card_id}")
        seen.add(card_id)
        quantity = int(raw["quantity"])
        if quantity < 1:
            raise DataValidationError(f"{card_id} 的 quantity 必须大于 0")
        definitions.append(
            CardDefinition(
                id=card_id,
                name=raw["name"],
                faction=faction,
                card_type=CardType(raw["type"]),
                printed_power=raw.get("power"),
                text_zh=raw.get("ability_zh", ""),
                quantity=quantity,
                abilities=_abilities(raw.get("abilities")),
                attach_to=raw.get("attach_to"),
            )
        )
    return definitions


def load_bases(path: str | Path) -> list[BaseDefinition]:
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    definitions = []
    for raw in data["bases"]:
        definitions.append(
            BaseDefinition(
                id=raw["id"],
                name=raw["name"],
                breakpoint=int(raw["breakpoint"]),
                vp=tuple(raw["vp"]),
                text_zh=raw.get("ability_zh", ""),
                abilities=_abilities(raw.get("abilities")),
            )
        )
    return definitions

