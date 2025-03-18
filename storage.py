import os
from pathlib import Path
from langchain.vectorstores import Chroma

# Define storage directory
STORAGE_DIR = Path("./chroma_db")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize vector store
vector_store = Chroma(persist_directory=str(STORAGE_DIR))

def store_data(text: str):
    """Stores data in the vector database."""
    vector_store.add_texts([text])
    vector_store.persist()

def retrieve_data(query: str, top_k: int = 5):
    """Retrieves similar documents from the vector database."""
    return vector_store.similarity_search(query, k=top_k)
