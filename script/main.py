from player import Player
from card import Card
from base import Base
import itertools
import random


# 十六个基础盒基地。每次游戏开始时从这里复制一份新的基地牌库。
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

base_deck = []
current_bases = []


def provide_base(num):
    """准备基地牌库，并翻开玩家人数加一张基地。"""
    global base_deck

    # 使用副本，避免破坏基础数据，也方便以后重新开始游戏。
    base_deck = bases.copy()
    random.shuffle(base_deck)
    current_bases.clear()

    for _ in range(num + 1):
        current_bases.append(base_deck.pop(0))

    print("当前场上的基地是：")
    for base in current_bases:
        print(base)


def add_base():
    """基地结算后补充一张新基地。"""
    if not base_deck:
        print("基地牌库已经用完，无法补充新基地")
        return

    new_base = base_deck.pop(0)
    current_bases.append(new_base)
    print(f"新的基地 {new_base} 已经添加到游戏中")


def show_info(player):
    """展示玩家的姓名、VP、手牌和弃牌堆。"""
    print(f"玩家姓名: {player.name}")
    print(f"胜利点: {player.vp}")
    print(f"手牌: {player.hand}")
    print(f"弃牌堆: {player.discard_pile}")


def start_turn(player):
    """开始玩家回合，并重置本回合的出牌状态。"""
    player.reset_turn()


def play_card(player: Player, card: Card, base: Base):
    """将一张随从牌打到指定基地，成功时返回 True。

    当前阶段只实现纯力量随从牌。行动牌暂时不会改变游戏状态。
    """
    if card.type != "minion":
        print("当前版本只支持打出随从牌")
        return False

    # 每回合默认只能打出一个随从，额外出牌能力以后再接入。
    if player.minion_played and player.minion_extra <= 0:
        print(f"{player.name} 已经打出过随从牌，不能再打出随从牌")
        return False

    if card not in player.hand:
        print(f"{player.name} 没有这张牌: {card}")
        return False

    # 随从打出后仍然留在基地，只有基地结算时才进入弃牌堆。
    player.hand.remove(card)
    card.owner = player
    base.minions.append(card)

    if player.minion_played:
        player.minion_extra -= 1
    else:
        player.minion_played = True

    print(f"{player.name} 将 {card} 打到了 {base.name}")
    return True


def choose_base():
    """显示当前基地，并读取玩家选择的基地。"""
    while True:
        for index, base in enumerate(current_bases, start=1):
            print(f"{index}. {base}")

        try:
            choice = int(input("请输入基地序号: ")) - 1
            if 0 <= choice < len(current_bases):
                return current_bases[choice]
        except ValueError:
            pass

        print("基地序号无效，请重新输入")


def get_point(base: Base, players: list[Player]):
    """结算基地并按力量排名分配 VP，然后清理基地上的随从。

    目前先采用简单的力量排序，平手规则将在基础流程跑通后补充。
    """
    scores = []
    for player in players:
        power = sum(card.power for card in base.minions if card.owner is player)
        scores.append((player, power))

    scores.sort(key=lambda item: item[1], reverse=True)
    print(f"基地 {base.name} 结算：")

    for index, (player, power) in enumerate(scores):
        if index >= len(base.VP):
            break

        print(f"{player.name}: {power} 力量")
        if power > 0:
            player.vp += base.VP[index]
            print(f"{player.name} 获得 {base.VP[index]} VP")

    # 计分后随从离开基地，进入原拥有者的弃牌堆。
    for card in base.minions:
        if card.owner is not None:
            card.owner.discard_pile.append(card)
    base.minions.clear()


def score_ready_bases(players):
    """结算所有达到爆破点的基地，并为每个基地补一张新基地。"""
    # 遍历副本，因为结算过程中会从 current_bases 删除基地。
    for base in current_bases[:]:
        if base.get_power() >= base.breakpoint:
            print(f"{base.name} 达到爆破点 {base.breakpoint}")
            get_point(base, players)
            current_bases.remove(base)
            add_base()


def play_turn(player, players):
    """执行一个玩家回合：出牌、基地结算和抽牌。"""
    start_turn(player)
    show_info(player)

    if not player.hand:
        print("当前没有手牌")
        player.draw_card(5)

    if player.hand:
        for index, card in enumerate(player.hand, start=1):
            print(f"{index}. {card}")

        while True:
            try:
                choice = int(input("请输入要打出的牌序号，输入 0 跳过: "))
                if choice == 0:
                    break
                if 1 <= choice <= len(player.hand):
                    card = player.hand[choice - 1]
                    play_card(player, card, choose_base())
                    break
            except ValueError:
                pass
            print("牌的序号无效，请重新输入")

    score_ready_bases(players)

    # 回合结束抽两张牌，牌库和弃牌堆都没有牌时会自然停止。
    player.draw_card(2)


def game_over(players):
    """判断是否有玩家达到 15 VP。"""
    for player in players:
        if player.vp >= 15:
            print(f"{player.name} 达到 {player.vp} VP，游戏结束")
            return True
    return False


def create_test_deck():
    """创建只包含力量属性的临时测试牌库。"""
    powers = [1, 2, 2, 3, 3, 3, 4, 4, 5, 5] * 2
    return [
        Card(f"测试随从{index}", "测试派系", "minion", power)
        for index, power in enumerate(powers, start=1)
    ]


def main():
    """启动一局文字版基础游戏。"""
    try:
        num = int(input("欢迎来到大杀四方,请输入玩家数量: "))
    except ValueError:
        print("玩家数量必须是数字")
        return

    if num < 2 or num > 4:
        print("人数不符合要求！")
        return

    players = []
    for _ in range(num):
        name = input("请输入玩家姓名: ")

        # 当前还没有正式派系，因此每名玩家先使用同一套测试牌。
        deck = create_test_deck()
        random.shuffle(deck)
        player = Player(name, [], [], deck, [])
        player.draw_card(5)
        players.append(player)

    # 随机决定第一位玩家，并保留之后的轮换顺序。
    game_players = random.sample(players, len(players))
    provide_base(num)

    # cycle 会无限轮换玩家，直到有人达到结束条件。
    for player in itertools.cycle(game_players):
        print(f"现在是 {player.name} 的回合")
        play_turn(player, players)
        if game_over(players):
            break


if __name__ == "__main__":
    main()
