from __future__ import annotations

from smashup.abilities.registry import AbilityRegistry, BaseAbilityHandler
from smashup.domain.effects import (
    GainVPEffect,
    GrantExtraPlayEffect,
    MoveCardEffect,
)
from smashup.domain.enums import CardType, MoveReason, Zone
from smashup.domain.exceptions import GameRuleError
from smashup.domain.specifications import AllOf, AtBase, IsInPlay, IsMinion


class GainVPOnPlay(BaseAbilityHandler):
    def on_event(self, state, source_id, spec, event):
        if event.name != "card_played" or event.source_id != source_id:
            return []
        return [GainVPEffect(event.actor_id, int(spec.params["amount"]), source_id)]


class GrantExtraPlayOnPlay(BaseAbilityHandler):
    def on_event(self, state, source_id, spec, event):
        if event.name != "card_played" or event.source_id != source_id:
            return []
        card_type = CardType(spec.params["card_type"])
        return [GrantExtraPlayEffect(event.actor_id, card_type)]


class ReturnMinionOnPlay(BaseAbilityHandler):
    def validate_play(self, state, source_id, actor_id, base_id, target_ids, spec):
        if len(target_ids) > 1:
            raise GameRuleError("该能力最多选择一个随从")
        if not target_ids:
            return
        target_id = target_ids[0]
        target = state.cards.get(target_id)
        if target is None:
            raise GameRuleError("目标随从不存在")
        checks = [IsMinion(), IsInPlay()]
        if spec.params.get("same_base"):
            if base_id is None:
                raise GameRuleError("该能力要求来源牌位于基地")
            checks.append(AtBase(base_id))
        if not AllOf(tuple(checks)).is_satisfied_by(state, target_id):
            raise GameRuleError("目标不符合返回手牌能力的条件")
        maximum = spec.params.get("maximum_power")
        if maximum is not None:
            printed = state.card_definition(target_id).printed_power or 0
            if printed > int(maximum):
                raise GameRuleError(f"目标的印刷力量不能高于 {maximum}")

    def on_event(self, state, source_id, spec, event):
        if event.name != "card_played" or event.source_id != source_id:
            return []
        target_ids = tuple(event.payload.get("target_ids", ()))
        if not target_ids:
            return []
        target = state.cards[target_ids[0]]
        return [
            MoveCardEffect(
                target.id,
                Zone.HAND,
                target.owner_id,
                MoveReason.RETURN,
                event.actor_id,
            )
        ]


class PowerDuringOtherTurns(BaseAbilityHandler):
    def power_bonus(self, state, source_id, target_id, spec):
        source = state.cards[source_id]
        if source_id != target_id:
            return 0
        return (
            int(spec.params["amount"])
            if state.active_player.id != source.controller_id
            else 0
        )


class PowerPerSameNameHere(BaseAbilityHandler):
    def power_bonus(self, state, source_id, target_id, spec):
        source = state.cards[source_id]
        if source_id != target_id or source.zone_owner_id is None:
            return 0
        source_definition = state.card_definition(source_id)
        base = state.base(source.zone_owner_id)
        count = sum(
            state.card_definition(card_id).id == source_definition.id
            for card_id in base.minion_ids
        )
        return count * int(spec.params.get("amount", 1))


class AttachedPowerBonus(BaseAbilityHandler):
    def power_bonus(self, state, source_id, target_id, spec):
        source = state.cards[source_id]
        return (
            int(spec.params["amount"])
            if source.attached_to_id == target_id
            else 0
        )


def create_default_registry() -> AbilityRegistry:
    registry = AbilityRegistry()
    registry.register("gain_vp_on_play", GainVPOnPlay())
    registry.register("grant_extra_play_on_play", GrantExtraPlayOnPlay())
    registry.register("return_minion_on_play", ReturnMinionOnPlay())
    registry.register("power_during_other_turns", PowerDuringOtherTurns())
    registry.register("power_per_same_name_here", PowerPerSameNameHere())
    registry.register("attached_power_bonus", AttachedPowerBonus())
    return registry

