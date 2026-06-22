from dataclasses import dataclass
from faster_whisper import WhisperModel


@dataclass
class WordToken:
    word: str
    start: float
    end: float


def transcribe(audio_path: str, model: WhisperModel) -> tuple[list[WordToken], str]:
    segments, _ = model.transcribe(audio_path, language="es", word_timestamps=True)
    words = []
    for segment in segments:
        if segment.words:
            for w in segment.words:
                words.append(WordToken(word=w.word.strip(), start=float(w.start), end=float(w.end)))
    transcript = " ".join(w.word for w in words)
    return words, transcript


LONG_PAUSE_S = 1.5  # pausa > 1.5s = bloqueo, no cuenta como tiempo de habla


def calculate_ppm(words: list[WordToken]) -> dict:
    if not words:
        return {"ppm": 0.0, "word_count": 0, "speech_duration_s": 0.0}

    # Suma duración de cada palabra + gaps cortos (excluye bloqueos)
    speech_duration = sum(w.end - w.start for w in words)
    for i in range(1, len(words)):
        gap = words[i].start - words[i - 1].end
        if gap < LONG_PAUSE_S:
            speech_duration += gap

    ppm = len(words) / (speech_duration / 60) if speech_duration > 0 else 0.0

    return {
        "ppm": round(ppm, 1),
        "word_count": len(words),
        "speech_duration_s": round(speech_duration, 2),
    }
