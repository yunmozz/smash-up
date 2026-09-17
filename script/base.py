class Base:
    """基地对象，保存爆破条件、VP奖励和基地上的随从。"""

    def __init__(self, name, breakpoint, VP):
        """创建基地，接收名称、爆破点和前三名的胜利点数。"""
        self.name = name
        self.breakpoint = breakpoint
        self.VP = VP
        self.power = 0
        self.minions = []

    def get_power(self):
        """根据基地上的随从重新计算基地当前力量。"""
        return sum(minion.power for minion in self.minions)

    def __str__(self):
        """返回基地的当前状态。"""
        return (
            f"{self.name} "
            f"(爆破点:{self.breakpoint}, "
            f"VP:{self.VP}, "
            f"当前力量:{self.get_power()})"
        )

    def __repr__(self):
        """返回基地的调试显示文字。"""
        return self.__str__()
