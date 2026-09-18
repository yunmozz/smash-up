from __future__ import annotations

import sys
import unittest
from pathlib import Path
from random import Random

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from smashup.abilities.common import create_default_registry
from smashup.application.game_factory import GameFactory, PlayerSetup
from smashup.domain.commands import (
    EndPlayPhase,
    FinishTurn,
    PlayCard,
    ResolveChoice,
    ScoreBase,
    StartTurn,
)
from smashup.domain.effects import MoveCardEffect
from smashup.domain.engine import GameEngine
from smashup.domain.enums import MoveReason, Phase, Zone
from smashup.domain.exceptions import GameRuleError
from smashup.infrastructure.json_loader import load_bases, load_faction


class EngineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.definitions = load_faction(ROOT / "faction" / "Aliens.json")
        self.definitions += load_faction(ROOT / "faction" / "Dinosaurs.json")
        self.base_definitions = load_bases(ROOT / "data" / "bases.json")
        self.state = GameFactory(Random(7)).create(
            [
                PlayerSetup("Alice", ("Aliens", "Dinosaurs")),
                PlayerSetup("Bob", ("Aliens", "Dinosaurs")),
            ],
            self.definitions,
            self.base_definitions,
        )
        self.engine = GameEngine(create_default_registry(), Random(7))

    def card(self, player_id: str, definition_id: str, occurrence: int = 0) -> str:
        matches = [
            card.id
            for card in self.state.cards.values()
            if card.owner_id == player_id and card.definition_id == definition_id
        ]
        return matches[occurrence]

    def move(self, card_id: str, zone: Zone, destination_id: str) -> None:
        MoveCardEffect(
            card_id, zone, destination_id, MoveReason.PLACE
        ).apply(self.state, Random(1))

    def test_faction_data_builds_twenty_card_decks(self) -> None:
        totals: dict[str, int] = {}
        for definition in self.definitions:
            totals[definition.faction] = totals.get(definition.faction, 0) + definition.quantity
        self.assertEqual({"Aliens": 20, "Dinosaurs": 20}, totals)
        self.assertTrue(all(len(player.deck) + len(player.hand) == 40 for player in self.state.players))
        self.assertTrue(all(len(player.hand) == 5 for player in self.state.players))

    def test_normal_minion_play_is_limited_to_one(self) -> None:
        player = self.state.active_player
        first = self.card(player.id, "dinosaurs.king-rex")
        second = self.card(player.id, "dinosaurs.laseratops")
        self.move(first, Zone.HAND, player.id)
        self.move(second, Zone.HAND, player.id)
        base_id = self.state.bases[0].id
        self.engine.execute(self.state, StartTurn(player.id))
        self.engine.execute(self.state, PlayCard(player.id, first, base_id))
        with self.assertRaises(GameRuleError):
            self.engine.execute(self.state, PlayCard(player.id, second, base_id))

    def test_invader_ability_is_dispatched_from_json_handler(self) -> None:
        player = self.state.active_player
        invader = self.card(player.id, "aliens.invader")
        self.move(invader, Zone.HAND, player.id)
        self.engine.execute(self.state, StartTurn(player.id))
        events = self.engine.execute(
            self.state, PlayCard(player.id, invader, self.state.bases[0].id)
        )
        self.assertEqual(1, player.vp)
        self.assertIn("vp_gained", [event.name for event in events])

    def test_abduction_composes_return_and_extra_play_effects(self) -> None:
        player = self.state.active_player
        opponent = self.state.players[1]
        target = self.card(opponent.id, "dinosaurs.king-rex")
        action = self.card(player.id, "aliens.abduction")
        base_id = self.state.bases[0].id
        self.move(target, Zone.BASE, base_id)
        self.move(action, Zone.HAND, player.id)
        self.engine.execute(self.state, StartTurn(player.id))
        self.engine.execute(
            self.state, PlayCard(player.id, action, target_ids=(target,))
        )
        self.assertIn(target, opponent.hand)
        self.assertIn(action, player.discard)
        self.assertEqual(1, self.state.turn.extra_minion_plays)

    def test_two_war_raptors_each_receive_bonus_for_both(self) -> None:
        player = self.state.active_player
        first = self.card(player.id, "dinosaurs.war-raptor", 0)
        second = self.card(player.id, "dinosaurs.war-raptor", 1)
        base_id = self.state.bases[0].id
        self.move(first, Zone.BASE, base_id)
        self.move(second, Zone.BASE, base_id)
        self.assertEqual(4, self.engine.current_power(self.state, first))
        self.assertEqual(4, self.engine.current_power(self.state, second))

    def test_attached_upgrade_changes_derived_power(self) -> None:
        player = self.state.active_player
        target = self.card(player.id, "dinosaurs.king-rex")
        upgrade = self.card(player.id, "dinosaurs.upgrade")
        base_id = self.state.bases[0].id
        self.move(target, Zone.BASE, base_id)
        self.move(upgrade, Zone.HAND, player.id)
        self.engine.execute(self.state, StartTurn(player.id))
        self.engine.execute(
            self.state, PlayCard(player.id, upgrade, base_id, (target,))
        )
        self.assertEqual(9, self.engine.current_power(self.state, target))
        self.assertIn(upgrade, self.state.base(base_id).action_ids)

    def test_tied_players_share_first_place_and_skip_second(self) -> None:
        first, second = self.state.players
        base = self.state.bases[0]
        base.definition_id = "dinosaurs.jungle-oasis"
        first_rex = self.card(first.id, "dinosaurs.king-rex")
        second_rex = self.card(second.id, "dinosaurs.king-rex")
        self.move(first_rex, Zone.BASE, base.id)
        self.move(second_rex, Zone.BASE, base.id)
        self.state.phase = Phase.SCORE_BASES
        self.engine.execute(self.state, ScoreBase(first.id, base.id))
        self.assertEqual(2, first.vp)
        self.assertEqual(2, second.vp)
        self.assertIn(first_rex, first.discard)
        self.assertIn(second_rex, second.discard)

    def test_finishing_turn_draws_two_and_advances_active_player(self) -> None:
        player = self.state.active_player
        next_player = next(item for item in self.state.players if item.id != player.id)
        starting_hand = len(player.hand)
        self.engine.execute(self.state, StartTurn(player.id))
        self.engine.execute(self.state, EndPlayPhase(player.id))
        self.engine.execute(self.state, FinishTurn(player.id))
        self.assertEqual(starting_hand + 2, len(player.hand))
        self.assertEqual(next_player.id, self.state.active_player.id)
        self.assertIs(Phase.START_TURN, self.state.phase)

    def test_hand_limit_creates_resumable_choice(self) -> None:
        player = self.state.active_player
        while len(player.hand) < 10:
            self.move(player.deck[0], Zone.HAND, player.id)
        self.engine.execute(self.state, StartTurn(player.id))
        self.engine.execute(self.state, EndPlayPhase(player.id))
        self.engine.execute(self.state, FinishTurn(player.id))
        choice = self.state.pending_choice
        self.assertIsNotNone(choice)
        assert choice is not None
        self.assertEqual(2, choice.minimum)
        self.engine.execute(
            self.state,
            ResolveChoice(player.id, choice.id, choice.option_ids[:2]),
        )
        self.assertEqual(10, len(player.hand))
        self.assertIsNone(self.state.pending_choice)


if __name__ == "__main__":
    unittest.main()
