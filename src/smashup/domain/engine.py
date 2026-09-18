from __future__ import annotations

from collections import deque
from random import Random

from smashup.domain.commands import (
    Command,
    EndPlayPhase,
    FinishTurn,
    PlayCard,
    ResolveChoice,
    ScoreBase,
    StartTurn,
)
from smashup.domain.effects import DrawCardsEffect, Effect, GainVPEffect, MoveCardEffect
from smashup.domain.enums import CardType, Duration, MoveReason, Phase, Zone
from smashup.domain.events import GameEvent, phase_changed
from smashup.domain.exceptions import GameRuleError
from smashup.domain.models import ChoiceRequest, GameState, new_id
from smashup.domain.ports import AbilityResolver


class GameEngine:
    """命令入口和规则协调器。

    引擎是无状态服务：一局游戏的数据全部位于 GameState，因此同一个引擎可以
    服务多局游戏，也便于单元测试和以后接入 Web API。
    """

    def __init__(self, abilities: AbilityResolver, random: Random | None = None):
        self.abilities = abilities
        self.random = random or Random()

    def execute(self, state: GameState, command: Command) -> list[GameEvent]:
        if state.pending_choice is not None and not isinstance(command, ResolveChoice):
            raise GameRuleError("必须先完成当前选择")
        handlers = {
            StartTurn: self._start_turn,
            PlayCard: self._play_card,
            EndPlayPhase: self._end_play_phase,
            ScoreBase: self._score_base,
            ResolveChoice: self._resolve_choice,
            FinishTurn: self._finish_turn,
        }
        try:
            handler = handlers[type(command)]
        except KeyError as error:
            raise TypeError(f"未知命令: {type(command).__name__}") from error
        return handler(state, command)

    def current_power(self, state: GameState, card_id: str) -> int:
        definition = state.card_definition(card_id)
        if definition.card_type is not CardType.MINION:
            return 0
        power = definition.printed_power or 0
        power += self.abilities.power_bonus(state, card_id)
        for modifier in state.modifiers:
            if modifier.target_card_id == card_id:
                power += modifier.amount
            elif (
                modifier.controller_id is not None
                and modifier.controller_id == state.cards[card_id].controller_id
            ):
                power += modifier.amount
        return max(0, power)

    def player_power_at_base(
        self, state: GameState, player_id: str, base_id: str
    ) -> int:
        base = state.base(base_id)
        return sum(
            self.current_power(state, card_id)
            for card_id in base.minion_ids
            if state.cards[card_id].controller_id == player_id
        )

    def total_power_at_base(self, state: GameState, base_id: str) -> int:
        return sum(
            self.current_power(state, card_id)
            for card_id in state.base(base_id).minion_ids
        )

    def ready_base_ids(self, state: GameState) -> tuple[str, ...]:
        return tuple(
            base.id
            for base in state.bases
            if self.total_power_at_base(state, base.id)
            >= state.base_definitions[base.definition_id].breakpoint
        )

    def _require_active_player(self, state: GameState, player_id: str) -> None:
        if state.active_player.id != player_id:
            raise GameRuleError("现在不是该玩家的回合")

    def _change_phase(self, state: GameState, phase: Phase) -> list[GameEvent]:
        old = state.phase
        state.phase = phase
        return [phase_changed(old, phase, state.active_player.id)]

    def _publish(
        self, state: GameState, initial_events: list[GameEvent]
    ) -> list[GameEvent]:
        """按队列处理事件，避免能力连锁通过递归调用而失控。"""
        queue = deque(initial_events)
        published: list[GameEvent] = []
        resolutions = 0
        while queue:
            event = queue.popleft()
            published.append(event)
            effects = self.abilities.effects_for_event(state, event)
            for effect in effects:
                queue.extend(self._apply_effect(state, effect))
                resolutions += 1
                if resolutions > 1_000:
                    raise RuntimeError("能力连锁超过安全上限，可能存在无限循环")
        return published

    def _apply_effect(self, state: GameState, effect: Effect) -> list[GameEvent]:
        return effect.apply(state, self.random)

    def _start_turn(self, state: GameState, command: StartTurn) -> list[GameEvent]:
        self._require_active_player(state, command.player_id)
        if state.phase is not Phase.START_TURN:
            raise GameRuleError("当前阶段不能开始回合")
        state.turn.number += 1
        state.turn.reset()
        state.modifiers = [
            modifier
            for modifier in state.modifiers
            if modifier.duration is not Duration.START_OF_OWNERS_TURN
            or state.cards[modifier.source_id].owner_id != command.player_id
        ]
        events = [GameEvent("turn_started", command.player_id)]
        events.extend(self._change_phase(state, Phase.PLAY_CARDS))
        return self._publish(state, events)

    def _consume_play(self, state: GameState, card_type: CardType, extra: bool) -> None:
        if card_type is CardType.MINION:
            if extra:
                if state.turn.extra_minion_plays <= 0:
                    raise GameRuleError("没有可用的额外随从出牌次数")
                state.turn.extra_minion_plays -= 1
            else:
                if state.turn.normal_minions_played >= 1:
                    raise GameRuleError("本回合已经使用普通随从出牌次数")
                state.turn.normal_minions_played += 1
        else:
            if extra:
                if state.turn.extra_action_plays <= 0:
                    raise GameRuleError("没有可用的额外行动出牌次数")
                state.turn.extra_action_plays -= 1
            else:
                if state.turn.normal_actions_played >= 1:
                    raise GameRuleError("本回合已经使用普通行动出牌次数")
                state.turn.normal_actions_played += 1

    def _play_card(self, state: GameState, command: PlayCard) -> list[GameEvent]:
        self._require_active_player(state, command.player_id)
        if state.phase is not Phase.PLAY_CARDS:
            raise GameRuleError("只能在出牌阶段打牌")
        if command.card_id not in state.active_player.hand:
            raise GameRuleError("该牌不在玩家手牌中")

        definition = state.card_definition(command.card_id)
        if definition.card_type is CardType.MINION and command.base_id is None:
            raise GameRuleError("打出随从必须选择基地")
        if command.base_id is not None:
            state.base(command.base_id)
        if definition.attach_to == "minion":
            if len(command.target_ids) != 1:
                raise GameRuleError("附着行动必须选择一个随从")
            target_id = command.target_ids[0]
            if target_id not in state.cards:
                raise GameRuleError("附着目标不存在")
            target = state.cards[target_id]
            if (
                state.card_definition(target_id).card_type is not CardType.MINION
                or target.zone is not Zone.BASE
                or target.zone_owner_id != command.base_id
            ):
                raise GameRuleError("附着目标必须是所选基地上的随从")

        self.abilities.validate_play(
            state,
            command.card_id,
            command.player_id,
            command.base_id,
            command.target_ids,
        )
        self._consume_play(state, definition.card_type, command.as_extra)

        attach_target = command.target_ids[0] if definition.attach_to == "minion" else None
        if definition.card_type is CardType.MINION or definition.attach_to:
            if command.base_id is None:
                raise GameRuleError("场上牌必须指定基地")
            move = MoveCardEffect(
                command.card_id,
                Zone.BASE,
                command.base_id,
                MoveReason.PLAY,
                command.player_id,
                attach_target,
            )
        else:
            move = MoveCardEffect(
                command.card_id,
                Zone.DISCARD,
                command.player_id,
                MoveReason.PLAY,
                command.player_id,
            )
        events = self._apply_effect(state, move)
        events.append(
            GameEvent(
                "card_played",
                command.player_id,
                command.card_id,
                {
                    "base_id": command.base_id,
                    "target_ids": command.target_ids,
                    "as_extra": command.as_extra,
                },
            )
        )
        return self._publish(state, events)

    def _end_play_phase(
        self, state: GameState, command: EndPlayPhase
    ) -> list[GameEvent]:
        self._require_active_player(state, command.player_id)
        if state.phase is not Phase.PLAY_CARDS:
            raise GameRuleError("当前不在出牌阶段")
        return self._publish(state, self._change_phase(state, Phase.SCORE_BASES))

    def _score_base(self, state: GameState, command: ScoreBase) -> list[GameEvent]:
        self._require_active_player(state, command.player_id)
        if state.phase is not Phase.SCORE_BASES:
            raise GameRuleError("当前不在基地计分阶段")
        if command.base_id not in self.ready_base_ids(state):
            raise GameRuleError("该基地尚未达到临界值")

        base = state.base(command.base_id)
        definition = state.base_definitions[base.definition_id]
        events: list[GameEvent] = []

        events.extend(self._change_phase(state, Phase.BEFORE_SCORE))
        events.extend(
            self._publish(
                state,
                [GameEvent("base_will_score", command.player_id, base.id)],
            )
        )
        events.extend(self._change_phase(state, Phase.WHEN_SCORE))

        participants = [
            player
            for player in state.players
            if any(
                state.cards[card_id].controller_id == player.id
                for card_id in base.minion_ids
            )
        ]
        powers = sorted(
            ((player, self.player_power_at_base(state, player.id, base.id)) for player in participants),
            key=lambda item: item[1],
            reverse=True,
        )
        previous_power: int | None = None
        rank = 0
        for position, (player, power) in enumerate(powers, start=1):
            if power != previous_power:
                rank = position
                previous_power = power
            award = definition.vp[rank - 1] if rank <= len(definition.vp) else 0
            if award:
                events.extend(
                    self._publish(
                        state, self._apply_effect(state, GainVPEffect(player.id, award, base.id))
                    )
                )

        events.extend(
            self._publish(
                state,
                [
                    GameEvent(
                        "base_scoring",
                        command.player_id,
                        base.id,
                        {"powers": {player.id: power for player, power in powers}},
                    )
                ],
            )
        )
        events.extend(self._change_phase(state, Phase.AFTER_SCORE))
        events.extend(
            self._publish(
                state,
                [GameEvent("base_scored", command.player_id, base.id)],
            )
        )

        for card_id in tuple(base.minion_ids + base.action_ids):
            owner_id = state.cards[card_id].owner_id
            events.extend(
                self._publish(
                    state,
                    self._apply_effect(
                        state,
                        MoveCardEffect(
                            card_id,
                            Zone.DISCARD,
                            owner_id,
                            MoveReason.SCORE_CLEANUP,
                        ),
                    ),
                )
            )
        state.bases.remove(base)
        state.base_discard.append(base)
        if state.base_deck:
            state.bases.append(state.base_deck.pop(0))
        events.append(GameEvent("base_replaced", command.player_id, base.id))
        events.extend(self._change_phase(state, Phase.SCORE_BASES))
        return events

    def _finish_turn(self, state: GameState, command: FinishTurn) -> list[GameEvent]:
        self._require_active_player(state, command.player_id)
        if state.phase is not Phase.SCORE_BASES:
            raise GameRuleError("只能在基地计分阶段结束后收尾")
        if self.ready_base_ids(state):
            raise GameRuleError("仍有达到临界值的基地必须结算")
        events = self._change_phase(state, Phase.DRAW_CARDS)
        events.extend(
            self._publish(
                state,
                self._apply_effect(state, DrawCardsEffect(command.player_id, 2)),
            )
        )
        excess = len(state.active_player.hand) - 10
        if excess > 0:
            state.pending_choice = ChoiceRequest(
                id=new_id("choice"),
                player_id=command.player_id,
                prompt=f"请选择 {excess} 张牌弃掉，将手牌降至 10 张",
                option_ids=tuple(state.active_player.hand),
                minimum=excess,
                maximum=excess,
                continuation={"type": "discard_to_hand_limit"},
            )
            events.append(
                GameEvent(
                    "choice_requested",
                    command.player_id,
                    payload={"choice_id": state.pending_choice.id},
                )
            )
            return events
        events.extend(self._complete_turn(state))
        return events

    def _resolve_choice(
        self, state: GameState, command: ResolveChoice
    ) -> list[GameEvent]:
        choice = state.pending_choice
        if choice is None or choice.id != command.choice_id:
            raise GameRuleError("选择请求不存在或已经失效")
        if choice.player_id != command.player_id:
            raise GameRuleError("该选择不属于此玩家")
        selected = tuple(dict.fromkeys(command.selected_ids))
        if not choice.minimum <= len(selected) <= choice.maximum:
            raise GameRuleError("选择数量不符合要求")
        if any(item not in choice.option_ids for item in selected):
            raise GameRuleError("选择中包含非法目标")

        events: list[GameEvent] = []
        if choice.continuation.get("type") == "discard_to_hand_limit":
            for card_id in selected:
                events.extend(
                    self._publish(
                        state,
                        self._apply_effect(
                            state,
                            MoveCardEffect(
                                card_id,
                                Zone.DISCARD,
                                command.player_id,
                                MoveReason.DISCARD,
                                command.player_id,
                            ),
                        ),
                    )
                )
            state.pending_choice = None
            events.extend(self._complete_turn(state))
            return events
        raise GameRuleError("未知的选择后续操作")

    def _complete_turn(self, state: GameState) -> list[GameEvent]:
        events = self._change_phase(state, Phase.END_TURN)
        state.modifiers = [
            modifier
            for modifier in state.modifiers
            if modifier.duration is not Duration.END_OF_TURN
        ]
        events.extend(
            self._publish(
                state,
                [GameEvent("turn_ended", state.active_player.id)],
            )
        )
        leaders = sorted(state.players, key=lambda player: player.vp, reverse=True)
        if leaders and leaders[0].vp >= 15:
            highest = leaders[0].vp
            winners = tuple(player.id for player in leaders if player.vp == highest)
            if len(winners) == 1:
                state.winner_ids = winners
                events.extend(self._change_phase(state, Phase.GAME_OVER))
                events.append(GameEvent("game_over", winners[0]))
                return events
        state.active_player_index = (state.active_player_index + 1) % len(state.players)
        events.extend(self._change_phase(state, Phase.START_TURN))
        return events
