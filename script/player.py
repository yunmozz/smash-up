import random

from card import Card


class Player:
    """玩家对象，管理牌区、派系、VP和回合状态。"""

    def __init__(self, name: str, hand: list[Card], faction: list,
                 deck: list, discard_pile: list) -> None:
        """创建玩家，并初始化手牌、牌库、派系和弃牌堆。"""
        self.name = name
        self.hand = hand
        self.faction = faction
        self.deck = deck
        self.discard_pile = discard_pile
        self.vp = 0

        self.minion_played = False
        self.action_played = False
        self.minion_extra = 0
        self.action_extra = 0

    def draw_card(self, number=1):
        """从牌库抽牌，牌库为空时将弃牌堆洗回牌库。"""
        for _ in range(number):
            if not self.deck:
                if not self.discard_pile:
                    return
                random.shuffle(self.discard_pile)
                self.deck.extend(self.discard_pile)
                self.discard_pile.clear()

            self.hand.append(self.deck.pop(0))

    def reset_turn(self):
        """重置玩家本回合的出牌状态。"""
        self.minion_played = False
        self.action_played = False
        self.minion_extra = 0
        self.action_extra = 0
