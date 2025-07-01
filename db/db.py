from fastapi import FastAPI, HTTPException, Body
from sqlalchemy import create_engine, inspect, text, quoted_name
from pydantic import BaseModel

app = FastAPI()

# Body Model for query payload
class Query(BaseModel):
    query: str

DB_URL = "mysql+mysqlconnector://root:root@host.docker.internal:3306/AI"
engine = create_engine(DB_URL)

FORBIDDEN_KEYWORDS = {"drop", "delete", "update", "insert", "alter", "truncate"}

@app.get("/schema")
def get_schema():
    with engine.connect() as conn:
        result = {}
        try:
            inspector = inspect(engine)
            for table_name in inspector.get_table_names():
                safe_name = quoted_name(table_name, quote=True)
                sql = conn.execute(text(f"SHOW CREATE TABLE `{safe_name}`")).fetchone()
                result[table_name] = sql[1]
            return result
        
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": "Process Failure, Please try again."})

@app.post("/query")
def get_result(query: Query):

    #Check for any prohibited SQL Query
    lowered_query = query.query.lower()
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in lowered_query:
            raise HTTPException(status_code=400, detail="Prohibited SQL statement detected.")

    with engine.connect() as connection:
        try:
            result = connection.execute(text(query.query))
            rows = result.mappings().all()

            return rows

        except Exception as e:
            return JSONResponse(status_code=500, content={"error": "Process Failure. Please try again."})
        
