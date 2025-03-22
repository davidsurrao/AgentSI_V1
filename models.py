import os
import re
import json
import requests
from pathlib import Path
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Define paths
BASE_DIR = Path(__file__).resolve().parent
CHROMA_DB_DIR = BASE_DIR / "chroma_db"
CONFIG_FILE = BASE_DIR / "config.json"

# Ensure the database directory exists
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

# Initialize embedding model
embedding_model = HuggingFaceEmbeddings()

# Initialize vector store
vector_store = Chroma(persist_directory=str(CHROMA_DB_DIR), embedding_function=embedding_model)

def get_active_model():
    """Reads the currently active model from the config file."""
    print("DEBUG: CONFIG_FILE path:", CONFIG_FILE)
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("r") as f:
            config = json.load(f)
            print("DEBUG: Config content:", config)
            return config.get("active_model")
    print("DEBUG: config.json not found.")
    return None

def store_text(text: str, metadata: dict = None):
    """Stores text data in ChromaDB with optional metadata."""
    vector_store.add_texts([text], metadatas=[metadata] if metadata else None)
    vector_store.persist()

def list_stored_entries():
    """Returns all stored entries with ID, metadata, and text from ChromaDB."""
    results = vector_store._collection.get(include=["metadatas", "documents"])
    entries = []
    for doc_id, metadata, content in zip(results["ids"], results["metadatas"], results["documents"]):
        entries.append({
            "id": doc_id,
            "filename": metadata.get("filename", ""),
            "category": metadata.get("category", ""),
            "project": metadata.get("project", ""),
            "type": metadata.get("type", "text"),
            "text": content
        })
    return entries


def query_llm(prompt: str):
    """Queries the currently active model."""
    model_path = get_active_model()
    print("DEBUG: Active model is", model_path)

    if not model_path:
        return "No active model found."

    try:
        response = requests.post(
            "http://localhost:5000/v1/completions",
            json={
                "model": model_path,
                "prompt": prompt,
                "max_tokens": 4096
            }
        )
        raw_text = response.json().get("choices", [{}])[0].get("text", "No response from LLM")
        cleaned_text = re.sub(r'^[\s]+', '', raw_text, flags=re.MULTILINE)
        return cleaned_text.rstrip()
    except Exception as e:
        return f"LLM Query Error: {str(e)}"

def query_text(query: str, top_k: int = 5):
    """Queries ChromaDB and combines the results with LLM response."""
    stored_results = []
    try:
        results = vector_store.similarity_search(query, k=top_k)
        stored_results = [doc.page_content for doc in results] if results else []
    except Exception as e:
        stored_results = [f"Error retrieving stored results: {str(e)}"]

    llm_response = query_llm(query)
    combined = [{"page_content": r} for r in stored_results]
    combined.append({"page_content": f"{llm_response}"})
    return combined

# ✅ NEW: Helper functions for dropdown management via config.json

def load_dropdown_options():
    """Loads current category and project values from config.json."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return {
                "categories": config.get("categories", []),
                "projects": config.get("projects", [])
            }
    return {"categories": [], "projects": []}

def add_to_dropdown_list(list_type: str, new_value: str):
    """
    Adds a new value to a specified dropdown list in config.json.
    list_type should be either 'categories' or 'projects'.
    """
    if list_type not in ["categories", "projects"]:
        raise ValueError("list_type must be 'categories' or 'projects'")

    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

    existing = config.get(list_type, [])
    if new_value not in existing:
        existing.append(new_value)
        config[list_type] = existing

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)

        return True  # Success
    return False  # Already exists
