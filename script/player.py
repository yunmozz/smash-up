from card import Card

class Player():
    def __init__(self,name:str,hand:list[Card],faction:list,deck:list,discard_pile:list) -> None:
        """玩家类，接收名字、手牌、派系、牌库和弃牌堆"""
        self.name = name
        self.hand = hand
        self.faction = faction
        self.deck = deck
        self.discard_pile = discard_pile

        self.minion_played = False
        self.action_played = False

        self.minion_extra=0
        self.action_extra=0