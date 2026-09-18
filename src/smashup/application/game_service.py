from __future__ import annotations

from smashup.domain.commands import Command
from smashup.domain.engine import GameEngine
from smashup.domain.events import GameEvent
from smashup.domain.models import GameState


class GameService:
    """应用层门面；未来 Web 路由和 CLI 都只依赖这个接口。"""

    def __init__(self, state: GameState, engine: GameEngine):
        self.state = state
        self.engine = engine

    def execute(self, command: Command) -> list[GameEvent]:
        return self.engine.execute(self.state, command)

