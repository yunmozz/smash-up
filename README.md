# Smash Up 学习项目

这是一个使用 Python 编写的《大杀四方（Smash Up）》规则引擎。项目当前重点不是图形界面，而是建立一个能够持续增加派系和特殊机制的基础架构。

## 当前状态

已经完成：

- 领域状态与 CLI 分离；
- 卡牌定义与卡牌实例分离；
- 命令入口、事件队列和可组合 Effect；
- 显式回合阶段和基地计分流程；
- 普通出牌与额外出牌次数；
- 动态力量计算和附着行动基础；
- JSON 派系/基地加载与能力注册表；
- 选择请求模型；
- 两个派系数据加载；
- 若干示例能力和自动化测试。

尚未完成：

- 基础盒全部卡牌和基地能力；
- 完整的 Special 轮流响应窗口；
- 销毁替代、保护、能力取消等高级规则；
- 初始手牌无随从时的重抽流程；
- 正式的玩家派系选择界面；
- 网络后端和前端。

当前的 Aliens 和 Dinosaurs JSON 都能组成完整的 20 张派系牌，但只有架构文档中列出的示例能力接入了可执行处理器。其他卡牌的中文能力文本仍然只是资料，留待后续逐张实现。

## 运行环境

- Python 3.11 或更高版本
- 当前只使用 Python 标准库

在项目根目录运行文字演示：

```powershell
python script\main.py
```

运行测试：

```powershell
python -m unittest discover -s tests -v
```

## 从哪里开始阅读

1. 阅读 [ARCHITECTURE.md](ARCHITECTURE.md)，理解重构动机和各层职责。
2. 阅读 `src/smashup/domain/models.py`，了解游戏状态。
3. 阅读 `src/smashup/domain/commands.py` 和 `events.py`，区分意图与事实。
4. 阅读 `src/smashup/domain/engine.py`，跟踪一条命令如何执行。
5. 阅读 `src/smashup/abilities/common.py` 和派系 JSON，理解能力注册机制。
6. 阅读 `tests/test_engine.py`，从可运行示例理解规则。

规则资料保留在 [rules.md](rules.md)，完整卡牌资料保留在 [cards.md](cards.md)。
