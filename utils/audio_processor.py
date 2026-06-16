import os
import yt_dlp
from pydub import AudioSegment
from pathlib import Path

# Safely creates the download folder relative to where the code runs on any OS
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

def download_youtube_audio(url: str) -> str:
    """Downloads YouTube audio and converts it safely to a cross-platform WAV path."""
    # Use standard yt-dlp template string, let pathlib format the output directory string
    output_template = str(DOWNLOAD_DIR / "%(title)s.%(ext)s")
    
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        raw_filename = ydl.prepare_filename(info)
        # Force resolve to cross-platform standard wav file extension path
        filename = Path(raw_filename).with_suffix(".wav")
        
    return str(filename.absolute())

def convert_to_wav(input_path: str) -> str:
    """Convert any local audio/video file format to an optimized WAV file in the download directory."""
    file_path = Path(input_path).absolute()
    # FIXED: Forces the converted file into your local 'downloads' cache directory instead of the source folder
    output_path = DOWNLOAD_DIR / f"{file_path.stem}_converted.wav"
    
    audio = AudioSegment.from_file(str(file_path))
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(str(output_path), format="wav")
    return str(output_path.absolute())

def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    """Chunks long audio files dynamically inside the local downloads cache folder."""
    file_path = Path(wav_path).absolute()
    audio = AudioSegment.from_wav(str(file_path))
    chunk_ms = chunk_minutes * 60 * 1000 

    chunks = []
    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start : start + chunk_ms]
        # FIXED: Forces chunks to stay isolated in your local 'downloads' folder
        chunk_path = DOWNLOAD_DIR / f"{file_path.stem}_chunk_{i}.wav"
        chunk.export(str(chunk_path), format="wav")
        chunks.append(str(chunk_path.absolute()))
    
    return chunks


def process_input(source: str) -> list:
    """Main input processor routing both URL and Local tracks cleanly."""
    # Clean up outer quotes added by terminal file drag-and-drops
    source = source.strip("'\" ")
    
    if source.startswith(("http://", "https://")):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks


print(process_input("/home/ehsan-al-muhaimin/Videos/Tanvir_Ishtiaq23141010.mp4"))