import os
from pathlib import Path
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import OpenAI

# Define paths
BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DB_DIR = BASE_DIR / "chroma_db"

# Ensure the database directory exists
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

# Initialize embedding model
embedding_model = HuggingFaceEmbeddings()

# Initialize vector store
vector_store = Chroma(persist_directory=str(CHROMA_DB_DIR), embedding_function=embedding_model)

# Initialize LLM
llm = OpenAI(model_name="gpt-4")

def store_text(text: str, metadata: dict = None):
    """Stores text data in ChromaDB with optional metadata."""
    vector_store.add_texts([text], metadatas=[metadata] if metadata else None)
    vector_store.persist()

def query_text(query: str, top_k: int = 5):
    """Queries ChromaDB for similar documents."""
    return vector_store.similarity_search(query, k=top_k)
