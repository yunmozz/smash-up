class Base():
    def __init__(self,name,breakpoint,VP:list[int]) -> None:
        """基地的父类，接收名字、爆破点、胜利点数(一共3个,所以是列表)和该基地的随从列表"""
        self.name = name
        self.breakpoint = breakpoint
        self.VP = VP        
        self.power = 0

    def __str__(self) -> str:
        return f"{self.name} (爆破点: {self.breakpoint}, 胜利点数: {self.VP}, 当前力量: {self.power})"

    def __repr__(self) -> str:
        return self.__str__()