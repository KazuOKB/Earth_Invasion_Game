"""配布パッケージから標準設定を読み込めることを確認する。"""

from importlib.resources import files

from earth_invasion.configuration import load_application_config

normal_config = load_application_config("normal")
test_config = load_application_config("test")

assert normal_config.stage.invasion_target == 100
assert test_config.stage.invasion_target == 10
assert files("earth_invasion.assets").joinpath("ufo003.png").read_bytes().startswith(b"\x89PNG")

print("配布パッケージから標準設定とUFO画像を読み込めました")
