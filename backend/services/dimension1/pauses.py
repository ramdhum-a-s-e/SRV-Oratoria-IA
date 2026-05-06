from services.dimension1.fluency import WordToken

PAUSE_THRESHOLD_S = 0.5   # pausa mínima detectable
LONG_PAUSE_S = 2.0        # pausa larga (indica bloqueo o nerviosismo)


def detect_pauses(words: list[WordToken]) -> dict:
    if len(words) < 2:
        return {"total_pauses": 0, "long_pauses": 0, "avg_pause_s": 0.0, "pauses": []}

    pauses = []
    for i in range(1, len(words)):
        gap = words[i].start - words[i - 1].end
        if gap >= PAUSE_THRESHOLD_S:
            pauses.append({
                "duration_s": round(gap, 3),
                "after_word": words[i - 1].word,
                "before_word": words[i].word,
                "is_long": gap >= LONG_PAUSE_S,
            })

    avg = sum(p["duration_s"] for p in pauses) / len(pauses) if pauses else 0.0

    return {
        "total_pauses": len(pauses),
        "long_pauses": sum(1 for p in pauses if p["is_long"]),
        "avg_pause_s": round(avg, 3),
        "pauses": pauses,
    }