# /// script
# dependencies = ["pygame-ce"]
# ///

"""pygbagが読み込むブラウザ版のエントリーポイント。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SOURCE_ROOT))

from earth_invasion.configuration import load_application_config  # noqa: E402
from earth_invasion.pygame_app.app import PygameApplication  # noqa: E402


async def main() -> None:
    """通常用の設定でブラウザ版を起動する。"""

    config = load_application_config(profile="normal")
    await PygameApplication(config).run_async()


if __name__ == "__main__":
    asyncio.run(main())
