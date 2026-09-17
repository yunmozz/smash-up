class Card:
    """卡牌父类，保存名称、派系、类型、力量和拥有者。"""

    def __init__(self, name, faction, card_type, power=0):
        """创建一张卡牌。"""
        self.name = name
        self.faction = faction
        self.type = card_type
        self.power = power
        self.owner = None

    def __str__(self):
        """返回适合展示的卡牌信息。"""
        return f"{self.name}(力量:{self.power})"

    def __repr__(self):
        """返回卡牌的调试显示文字。"""
        return self.__str__()


class Aliens(Card):
    """外星人派系的卡牌占位类。"""

    def __init__(self, name):
        """创建一张暂未实现具体能力的外星人随从牌。"""
        super().__init__(name, "Aliens", "minion")


class Dinosaurs(Card):
    """恐龙派系的卡牌占位类。"""

    def __init__(self, name):
        """创建一张暂未实现具体能力的恐龙随从牌。"""
        super().__init__(name, "Dinosaurs", "minion")
