# Smash Up 重构架构学习文档

本文解释这次重构解决了什么问题、每个目录和类承担什么职责、使用了哪些设计方法，以及以后如何增加派系和新机制。

## 1. 重构目标

原始版本适合验证最基础的流程，但 `script/main.py` 同时保存状态、读取键盘、打印内容、执行规则和结算基地。继续添加卡牌时，最容易出现下面的结构：

```python
if card.name == "Invader":
    ...
elif card.name == "War Raptor":
    ...
elif card.name == "Shinobi":
    ...
```

这种代码有三个问题：

1. 每增加一个派系都要修改核心流程，旧派系容易被改坏。
2. 规则和 `input()` 绑定后，无法直接复用于网页、网络对战或自动测试。
3. 卡牌会互相影响，单纯按顺序调用方法无法表达触发、替代和持续能力。

因此本次重构的目标是：

- 核心规则不知道界面是 CLI 还是 React；
- 每局游戏拥有独立状态，不使用模块全局变量；
- 普通能力由通用规则积木组合；
- 新机制通过注册能力处理器扩展；
- 所有重要操作都可测试、可记录；
- 未实现的卡牌能力不会被伪装成已经实现。

### 重构过程复盘

这次不是把旧类原样搬到更多文件，而是按依赖关系逐步拆开：

1. **先识别变化点**：派系能力、基地能力和 UI 最常变化；回合规则与区域规则是相对稳定的核心。
2. **收拢状态**：把原来的 `bases`、`base_deck`、`current_bases` 和玩家回合标记收进 `GameState`。
3. **分离静态与动态数据**：把原来的单一 `Card` 拆成 `CardDefinition` 和 `CardInstance`。
4. **切断 UI 依赖**：把 `input()`、`print()` 移到 `interfaces/cli.py`，领域层改为接收 Command。
5. **统一状态修改**：把抽牌、返回、弃牌、清场等操作归一到 Effect 和区域移动。
6. **显式化流程**：用 Phase 代替隐藏在函数调用顺序里的回合阶段。
7. **建立扩展机制**：用 Event Queue 和 Ability Registry 让新能力接入，而不是修改主循环。
8. **数据外置**：派系和基地静态内容由 JSON 加载，Python 只负责行为。
9. **迁移可运行入口**：保留 `script/main.py`，但让它仅转发到新的 CLI，旧启动命令仍然有效。
10. **用测试锁定行为**：先验证通用规则和代表性能力，再继续增加机制。

这种顺序的重点是每一步都只解决一种耦合。若一开始先写几十个卡牌子类，虽然文件看起来变多，核心规则仍然会彼此缠绕。

原结构与新结构的主要对应关系如下：

| 原结构 | 新位置 | 变化原因 |
|---|---|---|
| `script/card.py` | `domain/models.py` + `abilities/` | 数据身份和卡牌行为不再绑在继承树上 |
| `script/base.py` | `BaseDefinition` + `BaseInstance` | 支持基地能力、牌库和唯一实例 |
| `script/player.py` | `PlayerState` + Effect | 玩家保存状态，规则操作由引擎负责 |
| `script/main.py` 的规则函数 | `domain/engine.py` | 规则从输入输出中独立出来 |
| `script/main.py` 的交互 | `interfaces/cli.py` | CLI 成为可替换适配器 |
| Python 中硬编码基地 | `data/bases.json` | 静态内容数据化 |

## 2. 总体分层

```text
interfaces（CLI / 未来的 HTTP API）
                  │ 提交 Command，读取结果
                  ▼
application（创建牌局、用例门面）
                  │ 调用
                  ▼
domain（状态、规则引擎、事件、效果、规约）
                  ▲
                  │ 实现数据加载等外部细节
infrastructure（JSON、未来的数据库/存档）

abilities（通过领域层扩展卡牌和基地规则）
```

这里采用的是轻量 Clean Architecture，而不是为了分层而分层。依赖方向的关键是：领域层不导入 CLI，也不读取 JSON 文件。这样替换界面或存储方式不会改动游戏规则。

## 3. 目录职责

### `src/smashup/domain`

整个项目最核心的目录，只放游戏概念与规则。

| 文件 | 作用 |
|---|---|
| `models.py` | 定义卡牌模板、单张卡牌实例、玩家、基地、回合和完整 `GameState` |
| `enums.py` | 统一卡牌类型、区域、移动原因、阶段和效果期限 |
| `commands.py` | 表达玩家或界面“想做什么” |
| `events.py` | 表达系统中“已经发生了什么” |
| `effects.py` | 实际修改状态的原子操作 |
| `engine.py` | 校验并执行命令，推进阶段、处理事件和基地计分 |
| `specifications.py` | 用可组合条件表达合法目标 |
| `ports.py` | 定义领域层所需的能力解析接口，保持依赖方向 |
| `exceptions.py` | 区分玩家规则错误和数据文件错误 |

### `src/smashup/abilities`

`registry.py` 定义能力处理器协议和注册表。`common.py` 放可跨派系复用的能力，例如“打出时获得 VP”“打出时返回随从”和持续力量奖励。

以后可以建立 `aliens.py`、`dinosaurs.py` 等文件存放不能用通用参数表达的能力。派系能力可以依赖领域概念，但不应读取键盘或直接操作前端。

### `src/smashup/application`

- `GameFactory` 根据玩家选择、卡牌定义和基地定义创建一局完整游戏。
- `GameService` 是应用门面。CLI 或未来的 Web 路由不需要知道引擎内部如何分发命令。

### `src/smashup/infrastructure`

`json_loader.py` 把外部 JSON 转换成领域定义对象，并进行基本的数据校验。未来的存档、数据库仓库、固定随机数源也应放在这一层。

### `src/smashup/interfaces`

`cli.py` 是当前文字界面。它只负责展示状态、获取人的选择、组装 Command 和展示规则错误。它不负责计算力量和分数。以后增加 FastAPI 或 React 后端时，可以保留领域层并替换这一层。

### `faction` 与 `data`

- `faction/*.json`：派系卡牌定义；
- `data/bases.json`：基地定义；
- `ability_zh`：给人看的卡面文本；
- `abilities`：给程序执行的结构化能力声明。

展示文字和执行规则必须分开。程序不应尝试解析自然语言卡面。

### `tests`

这里保存规则的可执行示例。目前覆盖数据数量、出牌限制、事件能力、组合效果、持续力量、附着行动和平手计分。

## 4. Definition 与 Instance 为什么必须分开

`CardDefinition` 是不可变模板：

```python
CardDefinition(
    id="dinosaurs.war-raptor",
    name="War Raptor",
    printed_power=2,
    quantity=4,
)
```

一副牌中的四张 War Raptor 共享这个定义。

`CardInstance` 表示牌局中的某一张实体：

```python
CardInstance(
    id="card-a81f...",
    definition_id="dinosaurs.war-raptor",
    owner_id="player-1",
    controller_id="player-1",
    zone=Zone.BASE,
)
```

实例拥有唯一 ID，才能可靠处理四张同名牌中的某一张、附着目标、临时控制权、当前区域和每回合一次的能力。

这是享元思想的一种应用：共享静态定义，每个实体只保存运行时状态。基地也同样分成 `BaseDefinition` 和 `BaseInstance`。

## 5. GameState：聚合根

`GameState` 是一局游戏的唯一状态入口，包含玩家牌区、全部卡牌实例、基地、当前玩家和阶段、回合计数、临时修正、待处理选择和胜者。

它采用领域驱动设计中的 Aggregate Root 思想：规则修改都通过引擎进入，不再由不同模块各自保存一份全局状态。这也让未来服务器可以维护多局游戏：

```python
games: dict[str, GameState]
```

## 6. Command、Event 与 Effect 的区别

### Command：请求执行

```python
PlayCard(player_id, card_id, base_id, target_ids)
```

它表达“玩家想把这张牌打到这里”。命令可能失败，例如不是该玩家回合、牌不在手中或已经用完普通随从次数。

### Event：已经发生的事实

```python
GameEvent("card_played", actor_id, card_id, payload)
```

事件已经发生，不能被判定为“非法”。其他能力可以监听它。事件以后也可以用于动画、战报、回放和网络同步。

### Effect：状态改变的积木

```python
GainVPEffect(player_id, 1)
MoveCardEffect(card_id, Zone.HAND, owner_id, MoveReason.RETURN)
GrantExtraPlayEffect(player_id, CardType.MINION)
```

能力不应该到处写 `player.hand.append(...)`，而应产生 Effect。Effect 统一维护区域一致性并继续产生事件。

完整流程是：

```text
PlayCard Command
    → 引擎校验
    → MoveCardEffect
    → card_moved Event
    → card_played Event
    → 能力注册表找到处理器
    → 处理器产生新 Effect
    → 新 Event 继续进入队列
```

## 7. 为什么使用事件队列

卡牌能力会形成连锁。直接在函数里递归调用能力，会让顺序不清楚、战报难记录，也难以发现无限连锁。

`GameEngine._publish()` 使用先进先出的事件队列处理连锁，并设置安全上限。当前版本已经建立队列和监听器扫描，但完整的多玩家 Special 轮流 Pass 窗口仍是后续工作。

## 8. 回合状态机

回合阶段通过 `Phase` 显式表示：

```text
START_TURN
    → PLAY_CARDS
    → SCORE_BASES
        → BEFORE_SCORE
        → WHEN_SCORE
        → AFTER_SCORE
        → SCORE_BASES（继续检查）
    → DRAW_CARDS
    → END_TURN
    → 下一玩家 START_TURN
```

每条命令都会检查当前阶段。例如 `PlayCard` 只允许在 `PLAY_CARDS`，`ScoreBase` 只允许在 `SCORE_BASES`。

这属于有限状态机方法。当前使用 Enum 和阶段处理方法，没有为每个阶段创建一个类；对现阶段规模来说更直观。未来阶段规则非常复杂时，再拆成独立 State 类。

## 9. 区域移动和 MoveReason

规则区分 `PLAY / MOVE / DESTROY / DISCARD / RETURN / PLACE / DRAW`。这些动作可能最终都把牌从一个列表移到另一个列表，但规则意义不同。

`MoveCardEffect` 同时记录目标区域和 `MoveReason`，因此未来可以让 Nukebot 只监听真正的 `DESTROY`，让基地清场使用 `SCORE_CLEANUP` 而不误触发“被消灭后”，并确保 MOVE 不触发“打出时”。

不要绕过 Effect 直接修改 `hand`、`discard` 或 `base.minion_ids`，否则事件系统无法知道发生了什么。

## 10. 动态力量与 Modifier

`printed_power` 永远保存卡面印刷值。当前力量由 `GameEngine.current_power()` 查询：

```text
印刷力量 + 场上能力提供的持续加成 + 临时 PowerModifier = 当前力量（最低为 0）
```

例如两张 War Raptor 在同一基地时，每张当前力量都是：

```text
印刷 2 + 两张 War Raptor × 1 = 4
```

这种做法避免反复修改原始力量，也避免牌离场后忘记撤销加成。临时 Modifier 使用 `Duration` 描述何时失效。

后续可以用同一方法增加基地临界值、能力取消、卡牌标签和“不受影响”规则。

## 11. Strategy / Specification

目标规则经常是若干条件的组合：

```text
是随从 AND 位于场上 AND 位于这个基地 AND 力量不高于 3
```

`specifications.py` 把这些条件实现为可组合对象，而不是让每张牌重复遍历和判断。当前已有 `AllOf`、`IsMinion`、`IsInPlay`、`AtBase`、`ControlledBy` 等基础规约。

这是 Specification Pattern，同时每项条件也是一种可替换的策略。以后 UI 可以用同一个规约取得合法目标并进行高亮。

## 12. 能力注册表与数据驱动

派系 JSON 中的能力示例：

```json
{
  "name": "Invader",
  "type": "minion",
  "power": 3,
  "ability_zh": "获得 1 VP。",
  "abilities": [
    {"handler": "gain_vp_on_play", "params": {"amount": 1}}
  ]
}
```

启动时注册处理器：

```python
registry.register("gain_vp_on_play", GainVPOnPlay())
```

这里组合了 Registry、Factory、Strategy 和 Plugin Architecture 的思想：JSON 决定使用哪些能力，Registry 将稳定字符串映射到实现，Handler 是可替换策略，新派系无需修改 `GameEngine`。

不要试图把所有复杂规则都写成 JSON，否则会逐渐创造一门缺少调试工具的自制语言。简单能力使用通用 handler 和参数，多步骤能力组合通用 Effect，真正独特的机制编写清晰命名的 Python handler。

## 13. 当前接入的示例能力

| Handler | 示例卡牌 | 状态 |
|---|---|---|
| `gain_vp_on_play` | Invader | 已执行 |
| `return_minion_on_play` | Supreme Overlord、Collector、Beam Up、Abduction | 已执行基础版本 |
| `grant_extra_play_on_play` | Abduction | 已执行 |
| `power_during_other_turns` | Armor Stego | 已执行 |
| `power_per_same_name_here` | War Raptor | 已执行 |
| `attached_power_bonus` | Upgrade | 已执行 |

其他卡牌仍保留 `ability_zh`，但尚未声明可执行 handler。尤其是 Special、销毁替代、免疫、能力取消、搜索牌库和复杂选择，应该在相应基础机制完成后实现。

## 14. ChoiceRequest 为什么存在

领域层不能调用 `input()`，因为网页请求不能停在服务器里等待玩家输入。

需要选择时，状态保存一个 `ChoiceRequest`。界面读取它、展示选项，再提交 `ResolveChoice`。当前已把回合末超过 10 张手牌的弃牌做成这个流程。普通打牌目标暂时直接包含在 `PlayCard.target_ids` 中。

以后复杂能力可以统一扩展为：能力发出 ChoiceRequest，ResolveChoice 继续尚未完成的 Effect 序列。

## 15. 基地计分实现

计分逻辑已经处理：

- 只有达到临界值的基地可以计分；
- 多个基地满足时由当前玩家逐个提交 `ScoreBase`；
- 明确经过 BEFORE、WHEN、AFTER 三个阶段；
- 只有在基地上控制随从的玩家参与排名；
- 平手共享同一名次，并跳过后续名次；
- 清场使用 `SCORE_CLEANUP` 而不是 `DESTROY`；
- 旧基地进入基地弃牌堆并补充新基地；
- 结算后重新检查其他基地。

例如力量 `10、10、5` 的名次是 `1、1、3`。基地能力已经可以从 JSON 加载，注册表也会把场上基地作为事件来源扫描；具体 16 个基地 handler 尚未填写。

## 16. 如何增加一个新派系

### 第一步：建立数据文件

复制现有 JSON 结构，保证每种卡牌有数量、名称、类型、力量和展示文本，数量总计符合派系规则。ID 省略时会由加载器根据派系和名称生成。

### 第二步：盘点能力积木

先检查 `common.py` 是否已有可复用 handler。例如“获得 VP”“额外出随从”无需创建新类。

### 第三步：实现新机制

假设新增“打出时抽两张”：

```python
class DrawOnPlay(BaseAbilityHandler):
    def on_event(self, state, source_id, spec, event):
        if event.name != "card_played" or event.source_id != source_id:
            return []
        return [DrawCardsEffect(event.actor_id, spec.params["amount"])]
```

注册并在 JSON 中引用：

```python
registry.register("draw_on_play", DrawOnPlay())
```

```json
"abilities": [
  {"handler": "draw_on_play", "params": {"amount": 2}}
]
```

### 第四步：写场景测试

至少验证能力在正确事件触发、不在错误事件触发、无合法目标、多张同类牌，以及与基地和计分窗口的组合。

如果新增一张牌必须在 `GameEngine` 中增加卡名判断，说明扩展点可能不够，应优先增加通用 Event、Effect、Modifier 或 Specification。

## 17. 测试方法

项目使用标准库 `unittest`，无需额外安装依赖：

```powershell
python -m unittest discover -s tests -v
```

测试采用 Arrange–Act–Assert：创建固定随机种子的牌局，执行 Command 或 Effect，然后检查状态和事件。固定随机种子能确保洗牌测试可重复。

规则测试比只测试类构造更有价值，测试名应像规则句子，例如：

```python
test_tied_players_share_first_place_and_skip_second
test_abduction_composes_return_and_extra_play_effects
```

## 18. 本次重构用到的技术和方法

| 方法 | 在项目中的用途 |
|---|---|
| Clean Architecture | 隔离界面、应用、领域和基础设施 |
| Domain Model | 用代码表达玩家、卡牌、基地、区域和回合 |
| Aggregate Root | 使用 GameState 维护一局游戏的一致状态 |
| Command Pattern | 把玩家意图建模为可校验命令 |
| Event-Driven Architecture | 让触发能力监听已经发生的事实 |
| Effect Objects | 把状态修改拆成可组合、可记录的规则积木 |
| State Machine | 限制不同回合阶段允许的操作 |
| Strategy Pattern | 把能力和目标判断作为可替换实现 |
| Specification Pattern | 组合目标合法性条件 |
| Registry Pattern | 用字符串 ID 查找能力处理器 |
| Factory Pattern | 集中创建牌局和唯一实例 |
| Data-Driven Design | 用 JSON 描述静态卡牌和能力参数 |
| Dependency Injection | 向引擎注入能力注册表和随机数源 |
| Facade Pattern | GameService 向界面提供单一入口 |
| Immutable Definitions | 用 frozen dataclass 保护静态模板 |
| Deterministic Testing | 注入固定种子的 Random 重现牌局 |

## 19. 下一步推荐顺序

不要立即把八个派系全部写完。推荐依次补足：

1. 完整 Choice continuation，让多步骤能力可以暂停和恢复；
2. Destroy 之前的替代/阻止窗口；
3. Special 的轮流行动和连续 Pass；
4. 统一的当前力量、印刷力量和目标查询上下文；
5. 附着牌随宿主离场；
6. 保护、免疫和“是否受影响”判定；
7. 基地能力与能力取消；
8. 搜索、展示、重排牌库等操作；
9. 按 Aliens、Dinosaurs、Wizards、Robots 的顺序完成派系；
10. 再接 Web API 和前端。

Aliens 能覆盖返回、额外出牌、换基地和计分后能力；Dinosaurs 能覆盖力量、临时效果、附着和消灭，很适合先验证引擎边界。

## 20. 已知边界

当前版本是“可运行的基础框架”，不是完整基础盒实现：

- Special 窗口已有阶段和事件，但没有多人轮流 Pass 控制器；
- Return 基础版通过 PlayCard 直接提交目标，尚未统一改为异步 ChoiceRequest；
- Collector 的力量上限验证目前基于印刷力量，后续应接入统一 CurrentPower 查询上下文；
- 初始五张全无随从时的公开、弃置和重抽尚未实现；
- 尚未实现附着行动随宿主离场；
- 游戏状态尚未做 JSON 序列化和事件持久化；
- CLI 是架构演示，不代表最终用户体验。

保留并明确这些边界是刻意的：先让基础职责清楚、测试可运行，再逐个机制推进，更容易观察每次重构解决了什么问题。
