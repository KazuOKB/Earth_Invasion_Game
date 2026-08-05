"""上位スコアをローカルのJSONへ保存する。"""

from __future__ import annotations

import json
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

RANKING_LIMIT = 5


def default_ranking_path() -> Path:
    """通常起動でランキングを保存する場所を返す。"""

    return Path.home() / ".earth_invasion" / "ranking.json"


@dataclass(slots=True)
class ScoreRanking:
    """上位5件のスコアを読み書きする。"""

    path: Path
    scores: tuple[int, ...] = ()

    @classmethod
    def load(cls, path: Path | None = None) -> ScoreRanking:
        """保存済みランキングを読む。壊れている場合は空で始める。"""

        ranking_path = path if path is not None else default_ranking_path()
        try:
            value: object = json.loads(ranking_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return cls(path=ranking_path)

        if not isinstance(value, list):
            return cls(path=ranking_path)

        scores = [score for score in value if _is_valid_score(score)]
        return cls(path=ranking_path, scores=tuple(sorted(scores, reverse=True)[:RANKING_LIMIT]))

    def record(self, score: int) -> None:
        """0より大きいスコアを追加し、上位5件だけを上書き保存する。"""

        if isinstance(score, bool) or not isinstance(score, int) or score < 0:
            raise ValueError("scoreは0以上の整数にしてください")
        if score == 0:
            return

        updated_scores = tuple(sorted((*self.scores, score), reverse=True)[:RANKING_LIMIT])
        if updated_scores == self.scores:
            return

        self.scores = updated_scores
        self._save()

    def _save(self) -> None:
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path.write_text(
                json.dumps(self.scores, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary_path.replace(self.path)
        except OSError:
            with suppress(OSError):
                temporary_path.unlink(missing_ok=True)


def _is_valid_score(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value > 0
