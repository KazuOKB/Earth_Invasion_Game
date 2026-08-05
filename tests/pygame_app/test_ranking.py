"""ローカルランキングの保存を確認する。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from earth_invasion.pygame_app.ranking import ScoreRanking


def test_missing_ranking_starts_empty(tmp_path: Path) -> None:
    ranking = ScoreRanking.load(tmp_path / "ranking.json")

    assert ranking.scores == ()


def test_only_top_five_scores_are_saved_in_descending_order(tmp_path: Path) -> None:
    path = tmp_path / "ranking.json"
    ranking = ScoreRanking.load(path)

    for score in (300, 100, 600, 200, 500, 400):
        ranking.record(score)

    assert ranking.scores == (600, 500, 400, 300, 200)
    assert json.loads(path.read_text(encoding="utf-8")) == [600, 500, 400, 300, 200]
    assert ScoreRanking.load(path).scores == ranking.scores


def test_score_below_fifth_place_does_not_overwrite_file(tmp_path: Path) -> None:
    path = tmp_path / "ranking.json"
    path.write_text("[500, 400, 300, 200, 100]", encoding="utf-8")
    ranking = ScoreRanking.load(path)
    saved_text = path.read_text(encoding="utf-8")

    ranking.record(50)

    assert ranking.scores == (500, 400, 300, 200, 100)
    assert path.read_text(encoding="utf-8") == saved_text


def test_zero_score_is_not_saved(tmp_path: Path) -> None:
    path = tmp_path / "ranking.json"
    ranking = ScoreRanking.load(path)

    ranking.record(0)

    assert ranking.scores == ()
    assert not path.exists()


def test_invalid_saved_values_are_ignored(tmp_path: Path) -> None:
    path = tmp_path / "ranking.json"
    path.write_text('[100, true, "300", -1, 200]', encoding="utf-8")

    assert ScoreRanking.load(path).scores == (200, 100)


def test_broken_json_starts_empty(tmp_path: Path) -> None:
    path = tmp_path / "ranking.json"
    path.write_text("not json", encoding="utf-8")

    assert ScoreRanking.load(path).scores == ()


@pytest.mark.parametrize("score", [-1, 1.5, True])
def test_invalid_score_is_rejected(tmp_path: Path, score: object) -> None:
    ranking = ScoreRanking.load(tmp_path / "ranking.json")

    with pytest.raises(ValueError, match="score"):
        ranking.record(cast(int, score))
