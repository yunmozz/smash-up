from __future__ import annotations

from typing import Protocol

from smashup.domain.effects import Effect
from smashup.domain.events import GameEvent
from smashup.domain.models import AbilitySpec, GameState


class AbilityHandler(Protocol):
    def validate_play(
        self,
        state: GameState,
        source_id: str,
        actor_id: str,
        base_id: str | None,
        target_ids: tuple[str, ...],
        spec: AbilitySpec,
    ) -> None: ...

    def on_event(
        self,
        state: GameState,
        source_id: str,
        spec: AbilitySpec,
        event: GameEvent,
    ) -> list[Effect]: ...

    def power_bonus(
        self,
        state: GameState,
        source_id: str,
        target_id: str,
        spec: AbilitySpec,
    ) -> int: ...


class BaseAbilityHandler:
    """能力适配器。子类只覆盖自己需要的扩展点。"""

    def validate_play(self, state, source_id, actor_id, base_id, target_ids, spec):
        return None

    def on_event(self, state, source_id, spec, event):
        return []

    def power_bonus(self, state, source_id, target_id, spec):
        return 0


class AbilityRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, AbilityHandler] = {}

    def register(self, name: str, handler: AbilityHandler) -> None:
        if name in self._handlers:
            raise ValueError(f"能力处理器重复注册: {name}")
        self._handlers[name] = handler

    def get(self, name: str) -> AbilityHandler:
        try:
            return self._handlers[name]
        except KeyError as error:
            raise KeyError(f"没有注册能力处理器: {name}") from error

    def validate_play(self, state, source_id, actor_id, base_id, target_ids) -> None:
        definition = state.card_definition(source_id)
        for spec in definition.abilities:
            self.get(spec.handler).validate_play(
                state, source_id, actor_id, base_id, target_ids, spec
            )

    def effects_for_event(self, state: GameState, event: GameEvent) -> list[Effect]:
        sources: list[tuple[str, tuple[AbilitySpec, ...]]] = []
        seen: set[str] = set()
        if event.source_id in state.cards:
            sources.append(
                (event.source_id, state.card_definition(event.source_id).abilities)
            )
            seen.add(event.source_id)
        elif event.source_id is not None:
            for base in state.bases:
                if base.id == event.source_id:
                    sources.append(
                        (base.id, state.base_definitions[base.definition_id].abilities)
                    )
                    seen.add(base.id)
                    break
        for card_id, card in state.cards.items():
            if card.zone.value == "base" and card_id not in seen:
                sources.append((card_id, state.card_definition(card_id).abilities))
                seen.add(card_id)
        for base in state.bases:
            if base.id not in seen:
                sources.append(
                    (base.id, state.base_definitions[base.definition_id].abilities)
                )

        effects: list[Effect] = []
        for source_id, specs in sources:
            for spec in specs:
                effects.extend(
                    self.get(spec.handler).on_event(
                        state, source_id, spec, event
                    )
                )
        return effects

    def power_bonus(self, state: GameState, target_id: str) -> int:
        total = 0
        for source_id, card in state.cards.items():
            if card.zone.value != "base":
                continue
            for spec in state.card_definition(source_id).abilities:
                total += self.get(spec.handler).power_bonus(
                    state, source_id, target_id, spec
                )
        for base in state.bases:
            for spec in state.base_definitions[base.definition_id].abilities:
                total += self.get(spec.handler).power_bonus(
                    state, base.id, target_id, spec
                )
        return total
