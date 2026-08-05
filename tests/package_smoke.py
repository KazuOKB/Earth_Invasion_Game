"""配布パッケージから標準設定を読み込めることを確認する。"""

from importlib.resources import files

from earth_invasion.configuration import load_application_config

normal_config = load_application_config("normal")
test_config = load_application_config("test")

assert normal_config.stage.invasion_target == 100
assert test_config.stage.invasion_target == 10
assert normal_config.gameplay.weapon.beam_speed_pixels_per_second == 600.0
assert normal_config.gameplay.invasion_rewards.meteor == 2
assert normal_config.gameplay.chaser.spawn_interval_seconds == 1.1
assert normal_config.gameplay.shooter.shot_interval_seconds == 1.2
assert normal_config.gameplay.boss.max_health == 12
assert normal_config.gameplay.audio.music_volume == 0.0
assert normal_config.gameplay.audio.sound_effect_volume == 0.0
assert test_config.stage.duration_seconds_for("meteor") == 2.0
assert files("earth_invasion.assets").joinpath("ufo003.png").read_bytes().startswith(b"\x89PNG")
assert files("earth_invasion.assets").joinpath("meteo2.png").read_bytes().startswith(b"\x89PNG")
assert files("earth_invasion.assets").joinpath("chaser.png").read_bytes().startswith(b"\x89PNG")
assert files("earth_invasion.assets").joinpath("shooter.png").read_bytes().startswith(b"\x89PNG")
assert files("earth_invasion.assets").joinpath("boss.png").read_bytes().startswith(b"\x89PNG")
assert files("earth_invasion.assets").joinpath("background.png").read_bytes().startswith(b"\x89PNG")
assert (
    files("earth_invasion.assets")
    .joinpath("music/bright_title.wav")
    .read_bytes()
    .startswith(b"RIFF")
)
assert (
    files("earth_invasion.assets")
    .joinpath("music/cheerful_invasion.wav")
    .read_bytes()
    .startswith(b"RIFF")
)
assert (
    files("earth_invasion.assets")
    .joinpath("music/defense_boss.wav")
    .read_bytes()
    .startswith(b"RIFF")
)

print("配布パッケージから標準設定、画像、BGMを読み込めました")
