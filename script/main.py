from player import Player
from card import Card
from base import Base
import random
import itertools

# 十六个基地列表
bases = [
    Base("The Homeworld", 23, [4, 2, 1]),
    Base("The Mothership", 20, [4, 2, 1]),
    Base("Jungle Oasis", 12, [2, 0, 0]),
    Base("Tar Pits", 16, [4, 3, 2]),
    Base("Ninja Dojo", 18, [2, 3, 2]),
    Base("Temple of Goju", 18, [2, 3, 2]),
    Base("The Grey Opal", 17, [3, 1, 1]),
    Base("Tortuga", 21, [4, 3, 2]),
    Base("Factory 436-1337", 25, [2, 2, 1]),
    Base("The Central Brain", 19, [4, 2, 1]),
    Base("Cave of Shinies", 23, [4, 2, 1]),
    Base("Mushroom Kingdom", 20, [5, 3, 2]),
    Base("School of Wizardry", 20, [3, 2, 1]),
    Base("The Great Library", 22, [4, 2, 1]),
    Base("Evans City Cemetery", 20, [5, 3, 2]),
    Base("Rhodes Plaza Mall", 24, [0, 0, 0]),
]

current_bases = []

factions=["忍者","海盗","僵尸","机器人","恐龙","外星人","吸血鬼","魔法师"]  # 当前游戏中的基地列表

def provide_base(num):
    """分发基地"""
    random.shuffle(bases)
    for _ in range(num+1):
        current_bases.append(bases.pop(0))
    print("当前场上的基地是：")
    for base in current_bases:
        print(base)

def add_base(num):
    """当基地被爆破后，添加新的基地"""
    if len(current_bases) < num+1:
        for _ in range(num+1-len(current_bases)):
            current_bases.append(bases.pop(0))
    else:
        print("当前基地数量已达上限，无法添加新的基地")
    print(f"新的基地 {current_bases[-1]} 已经添加到游戏中")
    print("当前场上的基地是：")
    for base in current_bases:
        print(base)

def show_info(player):
    """展示玩家信息"""
    print(f"玩家姓名: {player.name}")
    print(f"手牌: {player.hand}")
    print(f"弃牌堆: {player.discard_pile}")

def start_turn():
    """开始回合阶段，某些特殊效果触发"""
    pass

def play_card(player:Player, card:Card):
    """玩家打出一张牌"""
    #检验玩家是否已经打出过随从牌或行动牌
    if card.minion_played:
        print(f"{player.name} 已经打出过随从牌，不能再打出随从牌")
        return
    if card.action_played:
        print(f"{player.name} 已经打出过行动牌，不能再打出行动牌")
        return

    #打出牌之后修改玩家的打牌状态
    if card.type == "minion":
        player.minion_played = True
    elif card.type == "action":
        player.action_played = True

    #打出牌后修改数组状态
    if card in player.hand:
        player.hand.remove(card)
        player.discard_pile.append(card)
        print(f"{player.name} 打出了 {card}")
    else:
        print(f"{player.name} 没有这张牌: {card}")

    #触发卡牌效果
    
def get_point(base:Base, player:Player):
    """计算玩家在基地上的分数"""
    pass

def play_turn(player):
    """玩家进行回合"""
    show_info(player)
    start_turn()
    play_card(player, player.hand[int(input("请输入要打出的牌的序号: ")) - 1])
    get_point(base,player)

def game_over():
    """判断游戏是否结束"""
    pass

def main():
    num=int(input("欢迎来到大杀四方,请输入玩家数量: "))
    players = []
    for _ in range(num):
        if num < 2 or num > 4:
        #检查玩家数量是否合法
            print("人数不符合要求！")
            return
        facton1, facton2 = map(input("请输入该玩家派系对应序号(空格分割): ").split())
        players.append(Player(input("请输入玩家姓名: "), [], [factions[int(facton1)-1], factions[int(facton2)-1]], [], []))
    Game_players = random.sample(players, len(players))
    #打乱数组，作为回合顺序

    #分发基地
    provide_base(num)

    for player in itertools.cycle(Game_players):
    #循环回合，直到游戏结束。itertools.cycle()会无限循环迭代器
        print(f"现在是 {player.name} 的回合")

        # 每名玩家进行回合
        play_turn(player)

        # 满足结束条件时退出循环
        if game_over():
            break

if __name__ == "__main__":
    main()