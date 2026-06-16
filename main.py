import os
import shutil
from dotenv import load_dotenv
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

def run_pipeline(source: str, language: str = "english") -> dict:
    print("\n🚀 Starting AI Video Assistant Pipeline...")

    # Processes your audio chunks (now optimized at your preferred 4-5 minute chunk size!)
    chunks = process_input(source)

    should_translate = True if language.lower() == "hinglish" else False
    transcript = transcribe_all(chunks, translate=should_translate)
    
    print(f"\nRaw transcription (first 300 characters):\n{transcript[:300]}...\n")

    title = generate_title(transcript)
    summary = summarize(transcript)
    action_item = extract_action_items(transcript)
    decisions = extract_key_decisions(transcript)
    questions = extract_questions(transcript)
    
    # This automatically triggers your new build_vector_store inside rag_engine in RAM
    rag_chain = build_rag_chain(transcript)

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_item,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }

def pipeline_reset_workspace():
    """
    Unified cleanup handle exposed to UI layers.
    Since Chroma runs entirely in RAM now, we don't have disk files to lock up.
    We just clean up any local temporary video/audio files left behind by downloads.
    """
    temp_dir = "./temp"
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print("Temporary media cache cleared safely.")
        except Exception as e:
            print(f"Non-critical workspace reset warning: {e}")

if __name__ == "__main__":
    source = input("Enter YouTube URL or local file path: ").strip()
    language = input("Language (english/hinglish) [default: english]: ").strip() or "english"
    
    result = run_pipeline(source, language)

    print("\n" + "=" * 60)
    print(f"📌 Title: {result['title']}")
    print(f"\n📋 Summary:\n{result['summary']}")
    print(f"\n✅ Action Items:\n{result['action_items']}")
    print(f"\n🔑 Key Decisions:\n{result['key_decisions']}")
    print(f"\n❓ Open Questions:\n{result['open_questions']}")
    print("=" * 60)

    print("\n💬 Chat with your meeting (type 'exit' to quit)\n")
    rag_chain = result["rag_chain"]
    while True:
        question = input("You: ").strip()
        if question.lower() in ["exit", "quit", "q"]:
            print("👋 Goodbye!")
            break
        if not question:
            continue
        
        print("\n🤖 Assistant is thinking...")
        ask_question(rag_chain, question)