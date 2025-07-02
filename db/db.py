import os, urllib
from fastapi import FastAPI, HTTPException, Body
from sqlalchemy import create_engine, inspect, text, quoted_name
from pydantic import BaseModel

app = FastAPI()

db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "3306")
db_name = os.getenv("DB_NAME")
db_driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")

driver_encoded = urllib.parse.quote_plus(f"driver={db_driver}")

# DB_URL = f"mssql+pyodbc://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}?driver={driver_encoded}"
DB_URL = f"mysql+mysqlconnector://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

engine = create_engine(DB_URL)

# Body Model for query payload
class Query(BaseModel):
    query: str

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
            raise HTTPException(status_code=500, detail="Process Failure. Please try again.")

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
            raise HTTPException(status_code=500, detail="Process Failure. Please try again.")
        
