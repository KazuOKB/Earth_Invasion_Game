"""配布パッケージから標準設定を読み込めることを確認する。"""

from earth_invasion.configuration import load_application_config

normal_config = load_application_config("normal")
test_config = load_application_config("test")

assert normal_config.stage.invasion_target == 100
assert test_config.stage.invasion_target == 10

print("配布パッケージから標準設定を読み込めました")
