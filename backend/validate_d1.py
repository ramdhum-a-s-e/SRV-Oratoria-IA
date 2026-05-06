# -*- coding: utf-8 -*-
"""
Validacion de Dimension 1 - Fluidez Mecanica y Prosodia
========================================================
Modos de uso:
  python validate_d1.py              -> genera audio de prueba con gTTS
  python validate_d1.py audio.wav    -> analiza un archivo existente
  python validate_d1.py --mic        -> graba con auto-stop por silencio (recomendado)
  python validate_d1.py --mic 120    -> igual, maximo 120 segundos
"""
import sys
import time
import json
import wave
from pathlib import Path

import os
os.environ.setdefault("WHISPER_DEVICE", "cpu")
os.environ.setdefault("WHISPER_MODEL_LIVE", "small")
os.environ.setdefault("WHISPER_MODEL_FINAL", "medium")

SAMPLERATE     = 16000
BLOCK_MS       = 100              # tamano del bloque de stream en ms (sin cortes)
BLOCK_FRAMES   = int(SAMPLERATE * BLOCK_MS / 1000)
SILENCE_STOP_S = 2.5              # segundos de silencio para parar automaticamente
CALIB_S        = 2.0              # segundos de calibracion al inicio


# ── Helpers de audio ──────────────────────────────────────────────────────────

def guardar_wav(audio_np, path: str):
    import numpy as np
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLERATE)
        wf.writeframes(audio_np.astype("int16").tobytes())


def generar_audio_gtts() -> str:
    texto = (
        "Buenos dias a todos. Hoy vamos a hablar sobre la importancia de la lectura. "
        "Leer nos permite aprender cosas nuevas y desarrollar nuestra imaginacion. "
        "Es importante leer todos los dias, aunque sea por pocos minutos. "
        "Los libros son nuestros mejores amigos y nos acompanan en todo momento. "
        "Por eso, debemos fomentar el habito de la lectura desde pequenos."
    )
    print("Generando audio de prueba con gTTS...")
    try:
        from gtts import gTTS
    except ImportError:
        print("ERROR: pip install gtts"); sys.exit(1)

    import av, numpy as np
    mp3_path, wav_path = "test_audio_d1.mp3", "test_audio_d1.wav"
    gTTS(text=texto, lang="es", tld="com.mx").save(mp3_path)

    frames = []
    with av.open(mp3_path) as container:
        resampler = av.AudioResampler(format="s16p", layout="mono", rate=SAMPLERATE)
        for frame in container.decode(audio=0):
            for out in resampler.resample(frame): frames.append(out.to_ndarray())
        for out in resampler.resample(None): frames.append(out.to_ndarray())

    guardar_wav(np.concatenate(frames, axis=1).flatten(), wav_path)
    print(f"Audio generado: {wav_path}\n")
    return wav_path


# ── Grabacion continua con VAD autocalibrando ─────────────────────────────────

def grabar_con_vad(max_seconds: int = 120) -> "np.ndarray | None":
    """
    Graba usando sd.InputStream (stream continuo, sin cortes).
    Paso 1: mide el ruido de fondo durante CALIB_S segundos.
    Paso 2: graba hasta detectar SILENCE_STOP_S de silencio o alcanzar max_seconds.
    """
    try:
        import sounddevice as sd
    except ImportError:
        print("ERROR: pip install sounddevice"); sys.exit(1)

    import numpy as np

    # ── Paso 1: Calibracion ───────────────────────────────────────────────────
    print(f"  Calibrando microfono ({CALIB_S}s — queda en silencio)...", end=" ", flush=True)
    calib_blocks = int(CALIB_S * 1000 / BLOCK_MS)
    calib_audio  = []

    with sd.InputStream(samplerate=SAMPLERATE, channels=1, dtype="int16",
                        blocksize=BLOCK_FRAMES) as stream:
        for _ in range(calib_blocks):
            data, _ = stream.read(BLOCK_FRAMES)
            calib_audio.append(data[:, 0].copy())

    ruido_rms = float(np.sqrt(np.mean(np.concatenate(calib_audio).astype(np.float64) ** 2)))
    umbral    = max(ruido_rms * 5, 80)   # 5x el ruido de fondo, minimo 80
    print(f"listo  (ruido fondo: {ruido_rms:.0f} RMS  ->  umbral voz: {umbral:.0f} RMS)")

    # ── Paso 2: Grabacion ─────────────────────────────────────────────────────
    print(f"\n  Para automaticamente tras {SILENCE_STOP_S}s de silencio (max {max_seconds}s)")
    print("  Habla ahora...\n")

    all_audio     = []
    silencio_acum = 0.0
    tiempo_total  = 0.0
    hay_voz       = False

    try:
        with sd.InputStream(samplerate=SAMPLERATE, channels=1, dtype="int16",
                            blocksize=BLOCK_FRAMES) as stream:
            while tiempo_total < max_seconds:
                data, _ = stream.read(BLOCK_FRAMES)
                buf = data[:, 0].copy()
                all_audio.append(buf)
                tiempo_total += BLOCK_MS / 1000

                rms = float(np.sqrt(np.mean(buf.astype(np.float64) ** 2)))

                # Barra de nivel simple
                nivel = min(int(rms / umbral * 20), 20)
                barra = ("#" * nivel).ljust(20)

                if rms >= umbral:
                    hay_voz       = True
                    silencio_acum = 0.0
                    print(f"  [{tiempo_total:5.1f}s] |{barra}| hablando       ", end="\r")
                else:
                    if hay_voz:
                        silencio_acum += BLOCK_MS / 1000
                        print(f"  [{tiempo_total:5.1f}s] |{barra}| silencio {silencio_acum:.1f}s  ", end="\r")
                        if silencio_acum >= SILENCE_STOP_S:
                            print(f"\n\n  -> Silencio de {silencio_acum:.1f}s. Fin de la grabacion.")
                            break
                    else:
                        print(f"  [{tiempo_total:5.1f}s] |{barra}| esperando voz  ", end="\r")

    except KeyboardInterrupt:
        print("\n\nGrabacion interrumpida.")

    if not hay_voz or len(all_audio) == 0:
        print("No se detecto voz. Verifica tu microfono o acercate mas.")
        return None

    return np.concatenate(all_audio)


# ── Reporte ───────────────────────────────────────────────────────────────────

def imprimir_reporte(ppm_r, pauses_r, prosody_r, tiempos: dict, transcript: str):
    sep = "=" * 60
    print(f"\n{sep}")
    print("  REPORTE FINAL D1 - FLUIDEZ MECANICA Y PROSODIA")
    print(sep)

    print(f"\n[Transcripcion completa]\n  {transcript if transcript else '(sin texto detectado)'}")

    print(f"\n[Tiempos de analisis]")
    for k, v in tiempos.items():
        print(f"  {k:12}: {v:.2f}s")

    ppm  = ppm_r["ppm"]
    tag  = "[OK] Normal" if 80 <= ppm <= 120 else ("[^] Rapido" if ppm > 120 else "[v] Lento")
    print(f"\n[PPM - Velocidad de habla]")
    print(f"  Palabras    : {ppm_r['word_count']}")
    print(f"  Duracion    : {ppm_r['speech_duration_s']}s")
    print(f"  PPM         : {ppm}  {tag}  (objetivo 1er grado: 80-120)")

    print(f"\n[Pausas]")
    print(f"  >= 0.5s : {pauses_r['total_pauses']}")
    print(f"  >= 2.0s : {pauses_r['long_pauses']}  <- bloqueos")
    print(f"  Promedio: {pauses_r['avg_pause_s']}s")
    for p in pauses_r.get("pauses", [])[:6]:
        flag = " <- LARGA" if p["is_long"] else ""
        print(f"    '{p['after_word']}' -> '{p['before_word']}': {p['duration_s']}s{flag}")

    if prosody_r:
        p = prosody_r
        print(f"\n[Prosodia - Praat]")
        print(f"  F0 promedio : {p['f0_mean_hz']} Hz")
        print(f"  F0 std      : {p['f0_std_hz']} Hz  (mayor = mas expresivo)")
        j_ok = p["jitter_pct"] is not None and p["jitter_pct"] < 1.04
        s_ok = p["shimmer_db"] is not None and p["shimmer_db"] < 0.35
        h_ok = p["hnr_db"] is not None and p["hnr_db"] > 20
        print(f"  Jitter      : {p['jitter_pct']}%  {'[OK] Voz sana' if j_ok else '[!!] Elevado'}")
        print(f"  Shimmer     : {p['shimmer_db']} dB  {'[OK] Estable' if s_ok else '[!!] Elevado'}")
        print(f"  HNR         : {p['hnr_db']} dB  {'[OK] Clara' if h_ok else '[!!] Ruidosa'}")
        print(f"  Intensidad  : {p['intensity_mean_db']} dB")

    print(f"\n[JSON]\n{json.dumps({'ppm': ppm_r, 'pauses': {k:v for k,v in pauses_r.items() if k!='pauses'}, 'prosody': prosody_r, 'latency_s': tiempos}, indent=2, ensure_ascii=False)}")


# ── Modo archivo ──────────────────────────────────────────────────────────────

def modo_archivo(audio_path: str):
    from services.audio_processor import get_model_final
    from services.dimension1 import transcribe, calculate_ppm, detect_pauses, analyze_prosody

    print("Cargando modelo...")
    model = get_model_final()

    t0 = time.time()
    words, transcript = transcribe(audio_path, model)
    t_w = time.time() - t0

    t1 = time.time()
    prosody_r = analyze_prosody(audio_path)
    t_p = time.time() - t1

    imprimir_reporte(calculate_ppm(words), detect_pauses(words), prosody_r,
                     {"whisper": round(t_w,2), "praat": round(t_p,2), "total": round(t_w+t_p,2)},
                     transcript)


# ── Modo microfono ────────────────────────────────────────────────────────────

def modo_microfono(max_seconds: int = 120):
    import numpy as np
    from services.audio_processor import get_model_final
    from services.dimension1 import transcribe, calculate_ppm, detect_pauses, analyze_prosody

    print("Cargando modelos (solo la primera vez tarda)...")
    get_model_final()

    audio = grabar_con_vad(max_seconds)
    if audio is None:
        return

    final_path = "test_mic_d1_full.wav"
    guardar_wav(audio, final_path)
    duracion = len(audio) / SAMPLERATE
    print(f"\nAnalizando {duracion:.1f}s de audio con modelo medium + Praat...")

    t0 = time.time()
    words, transcript = transcribe(final_path, get_model_final())
    t_w = time.time() - t0

    t1 = time.time()
    prosody_r = analyze_prosody(final_path)
    t_p = time.time() - t1

    imprimir_reporte(calculate_ppm(words), detect_pauses(words), prosody_r,
                     {"whisper": round(t_w,2), "praat": round(t_p,2), "total": round(t_w+t_p,2)},
                     transcript)

    Path("_partial.wav").unlink(missing_ok=True)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if args and args[0] == "--mic":
        segundos = int(args[1]) if len(args) > 1 else 120
        modo_microfono(segundos)
    elif args and Path(args[0]).exists():
        print(f"Analizando: {args[0]}\n")
        modo_archivo(args[0])
    else:
        modo_archivo(generar_audio_gtts())

if __name__ == "__main__":
    main()