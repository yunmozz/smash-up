from __future__ import annotations

from pathlib import Path
from random import Random

from smashup.abilities.common import create_default_registry
from smashup.application.game_factory import GameFactory, PlayerSetup
from smashup.application.game_service import GameService
from smashup.domain.commands import EndPlayPhase, FinishTurn, PlayCard, ScoreBase, StartTurn
from smashup.domain.engine import GameEngine
from smashup.domain.enums import CardType, Phase
from smashup.domain.exceptions import GameRuleError
from smashup.infrastructure.json_loader import load_bases, load_faction


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _name(service: GameService, card_id: str) -> str:
    return service.state.card_definition(card_id).name


def _show_table(service: GameService) -> None:
    state = service.state
    print("\n当前基地：")
    for index, base in enumerate(state.bases, 1):
        definition = state.base_definitions[base.definition_id]
        total = service.engine.total_power_at_base(state, base.id)
        cards = ", ".join(_name(service, card_id) for card_id in base.minion_ids)
        print(f"  {index}. {definition.name} {total}/{definition.breakpoint} [{cards}]")


def _choose_index(prompt: str, count: int, allow_skip: bool = False) -> int | None:
    while True:
        raw = input(prompt).strip()
        if allow_skip and raw == "0":
            return None
        try:
            value = int(raw) - 1
            if 0 <= value < count:
                return value
        except ValueError:
            pass
        print("输入的序号无效。")


def _play_one_card(service: GameService) -> bool:
    state = service.state
    player = state.active_player
    print(f"\n{player.name} 手牌：")
    for index, card_id in enumerate(player.hand, 1):
        definition = state.card_definition(card_id)
        power = "" if definition.printed_power is None else f" 力量 {definition.printed_power}"
        print(f"  {index}. {definition.name} ({definition.card_type.value}){power}")
    selected = _choose_index("选择要打的牌（0 跳过）: ", len(player.hand), True)
    if selected is None:
        return False
    card_id = player.hand[selected]
    definition = state.card_definition(card_id)
    base_id = None
    target_ids: tuple[str, ...] = ()
    if definition.card_type is CardType.MINION or definition.attach_to:
        _show_table(service)
        base_index = _choose_index("选择基地: ", len(state.bases))
        assert base_index is not None
        base_id = state.bases[base_index].id

    if any(spec.handler == "return_minion_on_play" for spec in definition.abilities):
        candidates = [candidate for base in state.bases for candidate in base.minion_ids]
        if candidates:
            print("可选的返回目标（该能力允许不选择）：")
            for index, candidate in enumerate(candidates, 1):
                print(f"  {index}. {_name(service, candidate)}")
            choice = _choose_index("选择目标（0 不发动）: ", len(candidates), True)
            if choice is not None:
                target_ids = (candidates[choice],)
    elif definition.attach_to == "minion" and base_id is not None:
        candidates = list(state.base(base_id).minion_ids)
        if not candidates:
            print("该基地没有随从，无法附着。")
            return False
        for index, candidate in enumerate(candidates, 1):
            print(f"  {index}. {_name(service, candidate)}")
        choice = _choose_index("选择附着目标: ", len(candidates))
        assert choice is not None
        target_ids = (candidates[choice],)

    service.execute(PlayCard(player.id, card_id, base_id, target_ids))
    return True


def main() -> None:
    root = _project_root()
    cards = load_faction(root / "faction" / "Aliens.json")
    cards += load_faction(root / "faction" / "Dinosaurs.json")
    bases = load_bases(root / "data" / "bases.json")
    print("Smash Up 规则引擎演示（当前数据包：Aliens + Dinosaurs）")
    names = [
        input("玩家 1 名称: ").strip() or "玩家 1",
        input("玩家 2 名称: ").strip() or "玩家 2",
    ]
    state = GameFactory(Random()).create(
        [PlayerSetup(name, ("Aliens", "Dinosaurs")) for name in names],
        cards,
        bases,
    )
    service = GameService(state, GameEngine(create_default_registry()))

    while state.phase is not Phase.GAME_OVER:
        player = state.active_player
        print(f"\n=== 第 {state.turn.number + 1} 回合：{player.name}（{player.vp} VP） ===")
        service.execute(StartTurn(player.id))
        _show_table(service)
        while True:
            try:
                if not _play_one_card(service):
                    break
            except GameRuleError as error:
                print(f"不能这样做：{error}")
        service.execute(EndPlayPhase(player.id))
        while service.engine.ready_base_ids(state):
            ready = service.engine.ready_base_ids(state)
            print("达到临界值的基地：")
            for index, base_id in enumerate(ready, 1):
                print(f"  {index}. {state.base_definition(base_id).name}")
            selected = _choose_index("选择先结算的基地: ", len(ready))
            assert selected is not None
            service.execute(ScoreBase(player.id, ready[selected]))
        service.execute(FinishTurn(player.id))
        if state.pending_choice is not None:
            from smashup.domain.commands import ResolveChoice

            choice = state.pending_choice
            service.execute(
                ResolveChoice(player.id, choice.id, choice.option_ids[-choice.maximum :])
            )

    winners = ", ".join(state.player(player_id).name for player_id in state.winner_ids)
    print(f"游戏结束，胜者：{winners}")


if __name__ == "__main__":
    main()

