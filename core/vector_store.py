from langchain_chroma import Chroma 
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

COLLECTION_NAME = "meeting_transcript"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

def get_embeddings():
    """Loads the local HuggingFace embedding model."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": 'cpu'}
    )

def build_vector_store(transcript: str) -> Chroma:
    """
    Builds a fresh, 100% IN-MEMORY vector database.
    This eliminates all SQLite file lock (1032) and OS permission errors.
    """
    print("Building fresh in-memory vector store for current video...")
    
    # 1. Split the text into manageable chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_text(transcript)

    # 2. Convert text chunks into LangChain Documents
    docs = [
        Document(page_content=chunk, metadata={'chunk_index': i})
        for i, chunk in enumerate(chunks)
    ]

    # 3. Initialize Chroma completely in RAM (Notice: NO persist_directory)
    # Every time this function is called, it creates a fresh, isolated database block in memory.
    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=get_embeddings(),
        collection_name=COLLECTION_NAME
    )
    
    return vector_store

def get_retriever(vector_store: Chroma, k: int = 4):
    """Converts the vector store into a retriever for the RAG chain."""
    return vector_store.as_retriever(
        search_type='similarity',
        search_kwargs={"k": k}
    )