from player import Player
def main():
    num=int(input("欢迎来到大杀四方,请输入玩家数量: "))
    players = [input("请输入玩家名字: ") for _ in range(num)]
    factons = [input("请输入玩家派系: ") for _ in range(num*2)]

if __name__ == "__main__":
    main()