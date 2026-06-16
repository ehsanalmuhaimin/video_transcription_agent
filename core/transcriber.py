from faster_whisper import WhisperModel
import os 

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

_model = None

def load_model():
    global _model

    if _model is None:
        print(f"Loading model")
        # CPU and float32 optimization prevents warnings and speeds up transcription
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="float32")
    return _model 


def transcribe_chunk(chunk_path: str, translate: bool = False) -> str:
    model = load_model()
    task = "translate" if translate else "transcribe"
    
    # model.transcribe returns a tuple: (segments, info)
    segments, info = model.transcribe(chunk_path, task=task, beam_size=5)
    
    # Safely extract text from the generator segments
    chunk_text = "".join([segment.text for segment in segments])
    return chunk_text

def transcribe_all(chunks: list, translate: bool = False) -> str:
    full_transcription = ""
    for i, chunk in enumerate(chunks):
        print(f"Transcribing chunk {i+1}")
        text = transcribe_chunk(chunk, translate=translate)
        full_transcription += text + " "
    print("Transcription completed")    
    return full_transcription