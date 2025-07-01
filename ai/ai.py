import requests, json
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Optional

app = FastAPI()

PROMPT_TEMPLATE = """
        <|begin_of_text|><|start_header_id|>user<|end_header_id|>

        Generate a SQL query to answer this question: `{question}`

        Return one of the following:
        * A valid MySQL query if the question is clear, relevant, and answerable using the provided schema.
        * A guidance message if the question cannot be answered due to missing information, ambiguity, or irrelevance.

        Evaluation Rules:
        1. Relevance Check: Determine whether the question pertains to the given schema.
        2. Answerability Check: Confirm that the required tables and columns exist in the schema.
        3. Clarity Check: Ensure the question is specific and unambiguous.
        4. Schema-Based Inference: Use logical joins or filters only if supported by the schema.
        5. Always perform JOINs using foreign keys when they enrich the answer, especially for questions asking for "all information" or "complete details."

        Output Format:
        - If the question is relevant and answerable, return:
        ```sql
        SELECT ...;

        - If the question is not answerable, return one of:
            1. The question is unclear. Please specify what you mean.
            2. The question is not relevant to the given database schema. Please revise it to match the available information.
            3. Cannot answer the question because required information is not available in the schema.

        Do not return explanations or anything outside the specified output format.

        DDL statements:
        {schema}

        <|eot_id|><|start_header_id|>assistant<|end_header_id|>
    """

class Prompt(BaseModel):
    question: str
    schema: Dict[str, str]

# Convert schema JSON to a human-readable string
# def convert_schema_to_string(schema: Prompt) -> str:
#     lines = []
#     for table_name, columns in schema.items():
#         lines.append(f"Table: {table_name}")
#         for col in columns:
#             col_line = f"  - {col.name} ({col.type})"
#             if col.PK:
#                 col_line += " [PK]"
#             if col.FK:
#                 col_line += f" [FK -> {col.FK}]"
#             lines.append(col_line)
#     return "\n".join(lines)

@app.post("/ai")
def ask_prompt(prompt: Prompt):
    schema = prompt.schema
    question = prompt.question
    
    ddl = "\n\n".join(schema.values())
    final_prompt = PROMPT_TEMPLATE.format(schema=ddl, question=question)
    
    payload = {
        "model": "mannix/defog-llama3-sqlcoder-8b:q6_k",  
        "prompt": final_prompt,
        "stream" : False
    }

    print(json.dumps(payload, indent=2)) 

    response = requests.post("http://192.168.18.104:11434/api/generate", json=payload)
    print(response.json()["response"])
    return response.json()
