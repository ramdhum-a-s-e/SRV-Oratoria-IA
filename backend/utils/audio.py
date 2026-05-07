import wave
import av
import numpy as np

SAMPLERATE = 16000


def to_wav(input_path: str, output_path: str) -> None:
    """Convierte cualquier formato de audio a WAV 16kHz mono usando PyAV."""
    frames = []
    with av.open(input_path) as container:
        resampler = av.AudioResampler(format="s16p", layout="mono", rate=SAMPLERATE)
        for frame in container.decode(audio=0):
            for out in resampler.resample(frame):
                frames.append(out.to_ndarray())
        for out in resampler.resample(None):
            frames.append(out.to_ndarray())

    if not frames:
        raise ValueError(f"No se encontro audio en: {input_path}")

    audio = np.concatenate(frames, axis=1).flatten().astype("int16")

    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLERATE)
        wf.writeframes(audio.tobytes())
