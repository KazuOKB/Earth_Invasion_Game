"""キーボード入力からプレイヤー操作への変換を確認する。"""

from earth_invasion.pygame_app.input import create_player_command


def test_up_key_creates_upward_command() -> None:
    command = create_player_command(up_pressed=True, down_pressed=False)

    assert command.vertical_direction == -1


def test_down_key_creates_downward_command() -> None:
    command = create_player_command(up_pressed=False, down_pressed=True)

    assert command.vertical_direction == 1


def test_both_keys_cancel_each_other() -> None:
    command = create_player_command(up_pressed=True, down_pressed=True)

    assert command.vertical_direction == 0
