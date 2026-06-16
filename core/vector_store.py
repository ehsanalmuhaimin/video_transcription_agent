import os 
import shutil
from pathlib import Path
from langchain_chroma import Chroma 
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

CHROMA_DIR = "vector_db"
COLLECTION_NAME = "meeting_transcript"
EMBEDDING_MODEL  = "all-MiniLM-L6-v2"

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": 'cpu'}
    )

def clear_vector_store():
    """Wipes the local vector directory completely to eliminate cross-video memory leaks."""
    db_path = Path(CHROMA_DIR)
    if db_path.exists():
        print("Clearing old vector database memory...")
        try:
            # Safely recursively delete the old database folder
            shutil.rmtree(db_path)
            print("Old memory cleared successfully.")
        except Exception as e:
            print(f"Warning: Could not clear database folder automatically: {e}")

def build_vector_store(transcript: str) -> Chroma:
    # FIXED: Wipes any existing database records before building the new video context
    clear_vector_store()
    
    print("Building fresh vector store for current video...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_text(transcript)

    docs = [
        Document(page_content=chunk, metadata={'chunk_index': i})
        for i, chunk in enumerate(chunks)
    ]

    embeddings = get_embeddings()
    
    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR
    )
    return vector_store

def load_vector_store() -> Chroma:
    embeddings = get_embeddings()
    
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )
    return vector_store

def get_retriever(vector_store: Chroma, k: int = 4):
    return vector_store.as_retriever(
        search_type='similarity',
        search_kwargs={"k": k}
    )
