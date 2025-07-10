import requests, json, os

from rag.embedder import embed_schema, embed_query
from rag.retriever import build_faiss_index, search_top_k
from rag.prompt import build_prompt
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict

app = FastAPI()

endpoint = os.getenv("AI_BASE_URL", "http://localhost:11434")

class Prompt(BaseModel):
    question: str
    schema: Dict[str, str]

@app.post("/ai")
def ask_prompt(prompt: Prompt):
    schema = prompt.schema
    question = prompt.question

    schema_texts = list(schema.values())
    schema_embeddings = embed_schema(schema)
    index = build_faiss_index(schema_embeddings)

    query_vector = embed_query(question)
    top_chunks = search_top_k(index, schema_texts, query_vector)

    final_prompt = build_prompt(top_chunks, question)
    
    payload = {
        "model": "mannix/defog-llama3-sqlcoder-8b:q6_k",  
        "prompt": final_prompt,
        "stream" : False
    }

    print(payload["prompt"])

    response = requests.post(f"{endpoint}/api/generate", json=payload)

    return response.json()
