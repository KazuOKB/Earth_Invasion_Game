"""Earth Invasion Gameのコマンドライン起動処理。"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from earth_invasion.configuration import (
    STAGE_PROFILES,
    ApplicationConfig,
    ConfigError,
    load_application_config,
)


def main(arguments: Sequence[str] | None = None) -> int:
    """設定を読み込み、新しいゲームの起動準備を行う。"""

    parser = _create_parser()
    options = parser.parse_args(arguments)

    try:
        config = load_application_config(
            profile=options.stage_profile,
            data_directory=options.data_directory,
        )
    except ConfigError as error:
        print(f"設定エラー: {error}", file=sys.stderr)
        return 2

    if options.check_config:
        _print_summary(config)
        return 0

    from earth_invasion.pygame_app.app import PygameApplication

    return PygameApplication(config).run()


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Earth Invasion Game")
    parser.add_argument(
        "--stage-profile",
        choices=STAGE_PROFILES,
        default="normal",
        help="使用するステージ時間設定",
    )
    parser.add_argument(
        "--data-directory",
        type=Path,
        default=None,
        help="設定ファイルがあるディレクトリ",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="画面を開かず、読み込んだ設定を表示する",
    )
    return parser


def _print_summary(config: ApplicationConfig) -> None:
    resolution = config.gameplay.logical_resolution
    print("Earth Invasion Game")
    print(f"設定: {config.stage.profile}")
    print(f"内部画面: {resolution.width}x{resolution.height}")
    print(f"侵略ゲージ目標: {config.stage.invasion_target}")
