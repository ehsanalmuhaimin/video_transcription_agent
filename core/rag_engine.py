import os
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# Cleaned up in-memory import - completely matching your updated vector_store.py
from core.vector_store import build_vector_store, get_retriever

def get_llm():
    """Initializes the Mistral AI large language model client securely."""
    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.3,
    )

def format_docs(docs):
    """Formats retrieved vector document segments into a unified context block."""
    return "\n\n".join([doc.page_content for doc in docs])

def build_rag_chain(transcript: str):
    """
    Builds the vector database in-memory from the transcript text and 
    constructs a complete LangChain Expression Language (LCEL) execution pipeline.
    """
    # 1. Build fresh in-memory collection and get its search retriever
    vector_store = build_vector_store(transcript)
    retriever = get_retriever(vector_store, k=4)
    llm = get_llm()

    # 2. Set up the strict system prompt rules
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert meeting assistant. Answer the user's question 
based ONLY on the meeting transcript context provided below.

If the answer is not found in the context, say: 
"I could not find this information in the meeting transcript."

Always be concise and precise. If quoting someone, mention it clearly.

Context from meeting transcript:
{context}""",
        ),
        ("human", "{question}"),
    ])

    # 3. Assemble full LCEL Rag pipeline in RAM
    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def ask_question(rag_chain, question: str) -> str:
    """Invokes the active LCEL RAG chain to answer user queries."""
    print(f"\nQuestion: {question}")
    answer = rag_chain.invoke(question)
    print(f"Answer: {answer}")
    return answer