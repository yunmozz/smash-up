class Card:
    """卡牌的父类，包括名字、派系、力量和能力"""
    def __init__(self, name, faction):
        self.name = name
        self.faction = faction
        #每个派系的能力不一样，可以一个派系做成一个子类，继承这个父类

class Aliens(Card):
    """外星人派系的卡牌"""
    def __init__(self, name):
        super().__init__(name, "Aliens")
    #外星人的能力主要是返回手牌和让别人弃牌。后续的方法可以围着这个写

    def reflect(card, player, base):
        """选中一个基地，返回其上一个随从到其拥有者手牌"""
        pass

    def gainVP(player):
        """Invader的能力是获得1VP"""
        pass

    def move(card, origin_base, target_base):
        """选中一个随从，移动到另一个基地"""
        pass

    def Play_bottom(player, card):
        """选中一个随从，放到基地的底部"""
        pass

    def cancel(base):
        """选中一个基地，取消其能力"""
        pass

    def look(player):
        """选中一个玩家，查看其手牌"""
        pass

    def change(base):
        """选中一个基地，从基地牌库找一张基地替换它"""
        pass