import requests

def query_llm(prompt: str):
    """Queries the local LLM running at http://localhost:5000/"""
    response = requests.post("http://localhost:5000/v1/completions", json={"prompt": prompt})
    return response.json().get("choices", [{}])[0].get("text", "No response")
