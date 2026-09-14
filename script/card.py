class Card:
    """卡牌的父类，包括名字、派系、力量和能力"""
    def __init__(self, name, faction):
        self.name = name
        self.faction = faction
        self.type = None
        #每个派系的能力不一样，可以一个派系做成一个子类，继承这个父类

class Aliens(Card):
    """外星人派系的卡牌"""
    def __init__(self, name):
        super().__init__(name, "Aliens")
    #外星人的能力主要是返回手牌和让别人弃牌。后续的方法可以围着这个写

    def reflect(target_minion, player, base):
        """选中一个基地，返回其上一个随从到其拥有者手牌"""
        pass

    def gainVP(player):
        """Invader的能力是获得1VP"""
        pass

    def move(target_minion, origin_base, target_base):
        """选中一个随从，移动到另一个基地"""
        pass

    def Play_bottom(player, target_minion):
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

class Dinosaurs(Card):
    """恐龙派系的卡牌"""
    def __init__(self, name):
        super().__init__(name, "Dinosaurs")
    # 恐龙拥有纯粹的数值，拥有大量增加力量的手段

    def King_Rex():
        """无能力，七点力量"""
        pass

    def Laseratops(player, target_minion):
        """消灭一个印刷力量小于二的仆从"""
        pass

    def Armor_Stego():
        """在其他玩家回合获得两力量"""
        pass

    def War_Raptor():
        """每有一只War Raptor在此基地,同名牌(包括自身)获得一力量"""
        pass

    def Augmentation(player, target_minion):
        """一个随从获得4点力量知道回合结束"""
        pass

    def Howl(player, target_minion):
        """自身场上所有的随从获得1点力量直到回合结束"""
        pass

    def Natural_Selection(selected_minion, player, target_minion):
        """选中一个基地上己方随从，消灭其力量小于等于其力量的随从"""
        pass

    def Rampage(selected_minion):
        """选择己方一个随从，将该基地的临界值降低这个随从的力量数值"""
        pass

    def Survival_of_the_Fittest(player, base, target_minion):
        """对每个存在高力量随从的基地,消灭力量最小的随从，相同时自己选择"""
        pass

    def Tooth_and_Claw_and_Guns(selected_minion):
        """打出在随从上,使其不受其他玩家卡牌影响"""
        pass

    def Upgrade(selected_minion):
        """在随从上打出,使其力量+2"""
        pass

    def Wildlife_Preserve(base):
        """在基地上打出,使你在这个基地上的随从不受其他玩家卡牌影响"""
        pass
    
