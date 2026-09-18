"""兼容旧启动方式：在项目根目录执行 ``python script/main.py``。"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from smashup.interfaces.cli import main


if __name__ == "__main__":
    main()
