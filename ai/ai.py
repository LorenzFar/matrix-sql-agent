from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Optional

app = FastAPI()

class ColumnDefinition(BaseModel):
    name: str
    type: str
    PK: Optional[bool] = None
    FK: Optional[str] = None

class Prompt(BaseModel):
    question: str
    schema: Dict[str, List[ColumnDefinition]]

# Convert schema JSON to a human-readable string
def convert_schema_to_string(schema: Prompt) -> str:
    lines = []
    for table_name, columns in schema.items():
        lines.append(f"Table: {table_name}")
        for col in columns:
            col_line = f"  - {col.name} ({col.type})"
            if col.PK:
                col_line += " [PK]"
            if col.FK:
                col_line += f" [FK -> {col.FK}]"
            lines.append(col_line)
    return "\n".join(lines)

# Function to generate prompt combining external txt with schema + user question
def generate_prompt(schema: str, question: str) -> str:
    prompt_parts = []

    try:
        with open("prompt_message.txt", 'r', encoding='utf-8') as f:
            external_context = f.read().strip()
            prompt_parts.append(external_context)
    except FileNotFoundError:
        prompt_parts.append("[WARNING: Context file not found]")

    prompt_parts.append("# Database Schema:\n" + schema)
    prompt_parts.append("# User Question:\n" + question)

    return "\n\n".join(prompt_parts)

@app.post("/ai")
def ask_prompt(prompt: Prompt):
    schema_str = convert_schema_to_string(prompt.schema)
    final_prompt = generate_prompt(schema_str, prompt.question)
    print(final_prompt)
    

    payload = {
        "model": "deepseek-r1:7b-qwen-distill-q4_K_M",  
        "prompt": final_prompt,
        "stream" : false
    }

    response = requests.post("http://192.168.18.104:11434/api/generate", json=payload)
    return response.json()
