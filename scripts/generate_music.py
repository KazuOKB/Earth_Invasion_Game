"""Earth Invasion Game用のオリジナルBGMを生成する。"""

from __future__ import annotations

import math
import sys
import wave
from array import array
from dataclasses import dataclass
from pathlib import Path

SAMPLE_RATE = 22_050
OUTPUT_DIRECTORY = Path(__file__).parents[1] / "src/earth_invasion/assets/music"
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


@dataclass(frozen=True, slots=True)
class Track:
    """1曲分のテンポと音符。"""

    filename: str
    beats_per_minute: int
    melody: tuple[str | None, ...]
    bass: tuple[str | None, ...]


def main() -> None:
    """3曲のWAVファイルを生成する。"""

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for track in _tracks():
        output_path = OUTPUT_DIRECTORY / track.filename
        _write_track(output_path, track)
        print(f"generated: {output_path}")


def _tracks() -> tuple[Track, ...]:
    title_melody = (
        "C5",
        "E5",
        "G5",
        "E5",
        "D5",
        "F5",
        "A5",
        "F5",
        "E5",
        "G5",
        "C6",
        "G5",
        "D5",
        "G5",
        "B5",
        "G5",
        "C5",
        "E5",
        "G5",
        "C6",
        "B5",
        "G5",
        "E5",
        "D5",
        "F5",
        "A5",
        "G5",
        "E5",
        "D5",
        "G4",
        "C5",
        None,
    )
    invasion_melody = (
        "E5",
        "G5",
        "C6",
        "G5",
        "E5",
        "G5",
        "D6",
        "C6",
        "F5",
        "A5",
        "C6",
        "A5",
        "G5",
        "E5",
        "D5",
        "G5",
        "E5",
        "G5",
        "A5",
        "C6",
        "B5",
        "G5",
        "E5",
        "D5",
        "F5",
        "A5",
        "D6",
        "C6",
        "G5",
        "E5",
        "C5",
        None,
    )
    boss_melody = (
        "A4",
        "C5",
        "E5",
        "A5",
        "G5",
        "E5",
        "D5",
        "E5",
        "A4",
        "C5",
        "F5",
        "A5",
        "G5",
        "F5",
        "E5",
        "D5",
        "C5",
        "E5",
        "G5",
        "C6",
        "B5",
        "G5",
        "E5",
        "G5",
        "D5",
        "F5",
        "A5",
        "D6",
        "C6",
        "A5",
        "E5",
        None,
    )

    return (
        Track(
            filename="bright_title.wav",
            beats_per_minute=128,
            melody=title_melody * 2,
            bass=_expand_bass(("C3", "F3", "C3", "G2", "C3", "A2", "F2", "G2")) * 2,
        ),
        Track(
            filename="cheerful_invasion.wav",
            beats_per_minute=150,
            melody=invasion_melody * 2,
            bass=_expand_bass(("C3", "A2", "F2", "G2", "C3", "A2", "D3", "G2")) * 2,
        ),
        Track(
            filename="defense_boss.wav",
            beats_per_minute=174,
            melody=boss_melody * 2,
            bass=_expand_bass(("A2", "A2", "F2", "G2", "C3", "G2", "D3", "E3")) * 2,
        ),
    )


def _expand_bass(notes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(note for note in notes for _ in range(4))


def _write_track(path: Path, track: Track) -> None:
    if len(track.melody) != len(track.bass):
        raise ValueError(f"melodyとbassの長さが異なります: {track.filename}")

    step_seconds = 60.0 / track.beats_per_minute / 2.0
    samples_per_step = round(SAMPLE_RATE * step_seconds)
    samples = array("h")

    for step_index, (melody_note, bass_note) in enumerate(
        zip(track.melody, track.bass, strict=True)
    ):
        for sample_in_step in range(samples_per_step):
            elapsed_seconds = sample_in_step / SAMPLE_RATE
            sample = _square_note(melody_note, elapsed_seconds, step_seconds)
            sample += _triangle_note(bass_note, elapsed_seconds, step_seconds)
            sample += _drum_sample(step_index, sample_in_step, elapsed_seconds)
            samples.append(round(32_767 * max(min(sample, 0.95), -0.95)))

    if sys.byteorder == "big":
        samples.byteswap()

    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(samples.tobytes())


def _square_note(note: str | None, elapsed: float, duration: float) -> float:
    if note is None:
        return 0.0

    frequency = _note_frequency(note)
    wave_value = 1.0 if math.sin(2.0 * math.pi * frequency * elapsed) >= 0 else -1.0
    return 0.11 * _note_envelope(elapsed, duration) * wave_value


def _triangle_note(note: str | None, elapsed: float, duration: float) -> float:
    if note is None:
        return 0.0

    frequency = _note_frequency(note)
    cycle = (frequency * elapsed) % 1.0
    wave_value = 4.0 * abs(cycle - 0.5) - 1.0
    return 0.12 * _note_envelope(elapsed, duration) * wave_value


def _note_envelope(elapsed: float, duration: float) -> float:
    attack = min(elapsed / 0.008, 1.0)
    release = min((duration - elapsed) / 0.035, 1.0)
    return max(min(attack, release), 0.0)


def _drum_sample(step_index: int, sample_index: int, elapsed: float) -> float:
    value = 0.0

    if step_index % 8 in (0, 4) and elapsed < 0.10:
        kick_frequency = 105.0 - 50.0 * elapsed / 0.10
        kick_decay = 1.0 - elapsed / 0.10
        value += 0.16 * kick_decay * math.sin(2.0 * math.pi * kick_frequency * elapsed)

    if step_index % 2 == 1 and elapsed < 0.035:
        noise = _noise_value(step_index, sample_index)
        value += 0.035 * (1.0 - elapsed / 0.035) * noise

    if step_index % 8 in (2, 6) and elapsed < 0.075:
        noise = _noise_value(step_index + 31, sample_index)
        value += 0.07 * (1.0 - elapsed / 0.075) * noise

    return value


def _noise_value(step_index: int, sample_index: int) -> float:
    value = (step_index * 7_919 + sample_index * 104_729) % 65_521
    return value / 32_760.5 - 1.0


def _note_frequency(note: str) -> float:
    name = note[:-1]
    octave = int(note[-1])
    note_index = NOTE_NAMES.index(name)
    midi_number = (octave + 1) * 12 + note_index
    return float(440.0 * 2.0 ** ((midi_number - 69) / 12.0))


if __name__ == "__main__":
    main()
