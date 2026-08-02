"""ステージ区間の進行を確認する。"""

import pytest

from earth_invasion.gameplay.stage import GamePhase, StageProgress, StageSchedule


def test_stage_starts_with_meteor_phase() -> None:
    stage = _create_test_stage()

    assert stage.phase is GamePhase.METEOR
    assert stage.remaining_seconds == 2.0


def test_stage_advances_when_phase_time_finishes() -> None:
    stage = _create_test_stage()

    stage.update(elapsed_seconds=2.0, invasion_gauge_is_full=False)

    assert stage.phase is GamePhase.CHASER
    assert stage.remaining_seconds == 2.0


def test_extra_time_carries_over_to_next_phase() -> None:
    stage = _create_test_stage()

    stage.update(elapsed_seconds=3.5, invasion_gauge_is_full=False)

    assert stage.phase is GamePhase.CHASER
    assert stage.remaining_seconds == pytest.approx(0.5)


def test_stage_waits_in_shooter_phase_when_gauge_is_not_full() -> None:
    stage = _create_test_stage()

    stage.update(elapsed_seconds=6.0, invasion_gauge_is_full=False)

    assert stage.phase is GamePhase.SHOOTER
    assert stage.remaining_seconds == 0.0


def test_full_gauge_does_not_skip_timed_phases() -> None:
    stage = _create_test_stage()

    stage.update(elapsed_seconds=5.0, invasion_gauge_is_full=True)

    assert stage.phase is GamePhase.SHOOTER
    assert stage.remaining_seconds == pytest.approx(1.0)


def test_stage_advances_to_boss_after_time_and_gauge_conditions() -> None:
    stage = _create_test_stage()
    stage.update(elapsed_seconds=6.0, invasion_gauge_is_full=False)

    stage.update(elapsed_seconds=0.1, invasion_gauge_is_full=True)

    assert stage.phase is GamePhase.BOSS
    assert stage.remaining_seconds is None


def test_boss_phase_has_no_time_limit() -> None:
    stage = _create_test_stage()
    stage.update(elapsed_seconds=6.0, invasion_gauge_is_full=True)

    stage.update(elapsed_seconds=100.0, invasion_gauge_is_full=True)

    assert stage.phase is GamePhase.BOSS


def test_non_positive_phase_duration_is_rejected() -> None:
    with pytest.raises(ValueError, match="meteor_duration_seconds"):
        StageSchedule(
            meteor_duration_seconds=0.0,
            chaser_duration_seconds=2.0,
            shooter_duration_seconds=2.0,
        )


def test_non_positive_elapsed_time_is_rejected() -> None:
    stage = _create_test_stage()

    with pytest.raises(ValueError, match="elapsed_seconds"):
        stage.update(elapsed_seconds=0.0, invasion_gauge_is_full=False)


def _create_test_stage() -> StageProgress:
    return StageProgress(
        schedule=StageSchedule(
            meteor_duration_seconds=2.0,
            chaser_duration_seconds=2.0,
            shooter_duration_seconds=2.0,
        )
    )
