class GameRuleError(ValueError):
    """命令违反游戏规则时抛出，可安全展示给界面用户。"""


class DataValidationError(ValueError):
    """派系或基地数据不完整、格式错误。"""

