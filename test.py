import os
from pathlib import Path
from dotenv import load_dotenv

# Force find the .env file exactly where test.py is located
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Verification flag for your $1,000 live demo safety
print(f"DEBUG: Mistral API Key Auth Status -> {bool(os.getenv('MISTRAL_API_KEY'))}")


from utils.audio_processor import process_input
from core.transcriber import transcribe_all, transcribe_chunk
from core.summarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions 

source = "https://www.youtube.com/watch?v=lt4OsgmUTGI"

# Downloads the audio file path or chunks
data = process_input(source)

# NOTE: If 'data' is a single file string, change this to: transcribe_chunk(data)
transcript = transcribe_all(data)

print("\n" + "n" * 60)
print("TRANSCRIPT")
print("=" * 60)
print(transcript[:500] + "..." if len(transcript) > 500 else transcript)

# Mistral AI Generation Layer
title = generate_title(transcript)
summary = summarize(transcript)

print("\n" + "=" * 60)
print(f"📌 TITLE: {title}")
print("=" * 60)
print("\n📋 SUMMARY")
print("-" * 60)
print(summary)

# Downstream RAG Extractor Layers
action_items = extract_action_items(transcript)
decisions = extract_key_decisions(transcript)
questions = extract_questions(transcript)

print("\n" + "=" * 60)
print("✅ ACTION ITEMS")
print("=" * 60)
print(action_items)

print("\n" + "=" * 60)
print("🔑 KEY DECISIONS")
print("=" * 60)
print(decisions)

print("\n" + "=" * 60)
print("❓ OPEN QUESTIONS")
print("=" * 60)
print(questions)
