class Base():
    def __init__(self,name,breakpoint,VP:list[int]) -> None:
        """基地的父类，接收名字、爆破点、胜利点数(一共3个，所以是列表)和该基地的随从列表"""
        self.name = name
        self.breakpoint = breakpoint
        self.VP = VP
        self.attach_cards = []
