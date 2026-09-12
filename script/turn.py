from player import Player

class Turn():
    def __init__(self,player:Player) -> None:
        """回合类，接收玩家对象"""
        self.player = player

        self.minion_played = False
        self.action_played = False

        self.minion_extra=0
        self.action_extra=0