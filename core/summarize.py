from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

import os 

#This is the function that you need to modify to use the local slm(small language model) instead of the mistral api. 
def get_llm():
    return ChatMistralAI(model="mistral-small-latest",mistral_api_key=os.getenv("MISTRAL_API_KEY"),temperature=0.3)


#you might need to modify this method to use the local slm properly instead of the mistral api 
def split_transcript(transcript:str)-> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=200
        )
    return splitter.split_text(transcript)


#this is the method to be modified for the summarization acording to the use case of physicians or lawyers or any other particular use case
def summarize(transcript:str)-> str:
    llm = get_llm()
    map_prompt=ChatPromptTemplate.from_messages(
        [
            ("system","You are a helpful assistant that summarizes meeting transcripts."),#modify this specifically for the better outcomes
            ("human","{text}")
        ]
    )
    map_chain = map_prompt | llm | StrOutputParser()

    chunks = split_transcript(transcript)

    chunk_summaries = [map_chain.invoke({"text":chunk}) for chunk in chunks]

    combined = "\n\n".join(chunk_summaries)

    combined_prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             "You are an expert summarizer. You will be given summaries of different sections of a transcript. Your task is to combine them into a single coherent summary that captures the main points and key details. Make sure the final summary is concise, clear, and well-structured."),
            ("human", "{text}")
        ]
    )

    combined_chain = (
        RunnablePassthrough() | RunnableLambda(lambda x: {"text": x}) | combined_prompt | llm | StrOutputParser()
    )
  
    return combined_chain.invoke(combined)

def generate_title(transcript:str)-> str:
    llm = get_llm()
    
    title_prompt = (
        RunnablePassthrough() | RunnableLambda(lambda x: {"text": x}) | ChatPromptTemplate.from_messages(
            ("system",
             "Based on the meeting transcript , generate a short professional meeting title"
             "(max 8 words). Only return the title, nopthing else"
             ),
            ("human", "{text}")
        ) | llm | StrOutputParser()
    )

    return title_prompt.invoke(transcript[:2000])