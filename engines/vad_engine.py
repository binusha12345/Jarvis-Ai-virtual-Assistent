import numpy as np
import sounddevice as sd
import speech_recognition as sr
from core.config import SAMPLE_RATE, CHUNK_SIZE, ENERGY_THRESHOLD, SILENCE_CHUNKS_LIMIT

recognizer = sr.Recognizer()

def listen_smart_vad():
    recorded_chunks = []
    has_started = False
    silence = 0
    max_duration = 120

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', blocksize=CHUNK_SIZE) as stream:
        for _ in range(max_duration):
            chunk, _ = stream.read(CHUNK_SIZE)
            arr = chunk.flatten()
            rms = np.sqrt(np.mean(np.square(arr, dtype=np.float32))) if len(arr) > 0 else 0

            if rms > ENERGY_THRESHOLD:
                has_started = True
                silence = 0
                recorded_chunks.append(chunk)
            elif has_started:
                recorded_chunks.append(chunk)
                silence += 1
                if silence >= SILENCE_CHUNKS_LIMIT:
                    break
            else:
                recorded_chunks.append(chunk)
                if len(recorded_chunks) > 4:
                    recorded_chunks.pop(0)

    if not has_started or len(recorded_chunks) < 5:
        return b""
    full_audio = np.concatenate(recorded_chunks, axis=0)
    return full_audio.tobytes()