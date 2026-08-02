"""ゲームルール用設定の検証を確認する。"""

import pytest

from earth_invasion.gameplay.settings import ChaserSettings, MeteorSettings


def test_non_positive_chaser_tracking_speed_is_rejected() -> None:
    with pytest.raises(ValueError, match="chaser.tracking_speed"):
        ChaserSettings(
            width=35,
            height=29,
            spawn_interval_seconds=0.8,
            horizontal_speed=240.0,
            tracking_speed=0.0,
        )


def test_meteor_minimum_speed_cannot_exceed_maximum() -> None:
    with pytest.raises(ValueError, match="minimum_speed"):
        MeteorSettings(
            width=130,
            height=130,
            spawn_interval_seconds=1.2,
            minimum_speed=301.0,
            maximum_speed=300.0,
        )
