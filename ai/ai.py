from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()

class Prompt():
    model: str
    prompt: str

@app.get("/ai")
def ask_prompt(prompt: Prompt):
    payload = prompt.prompt.json()
    response = requests.post("http://localhost:11434/api/generate", json=payload)
    return response.json()