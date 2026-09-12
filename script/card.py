class Card:
    """卡牌的父类，包括名字、派系、力量和能力"""
    def __init__(self, name, faction, power, ability):
        self.name = name
        self.faction = faction
        self.power = power
        self.ability = ability
        #这里是存能力的文本，到时候可以做一个字典。具体能力怎么触发用其它方法实现。
        #每个派系的能力不一样，可以一个派系做成一个子类，继承这个父类

class Aliens(Card):
    """外星人派系的卡牌"""
    def __init__(self, name, power, ability):
        super().__init__(name, "Aliens", power, ability)
    #外星人的能力主要是返回手牌和让别人弃牌。后续的方法可以围着这个写