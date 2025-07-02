import os, urllib
from fastapi import FastAPI, HTTPException, Body
from sqlalchemy import create_engine, inspect, text, quoted_name
from pydantic import BaseModel

app = FastAPI()

db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "1433")
db_name = os.getenv("DB_NAME")

driver_encoded = urllib.parse.quote_plus("ODBC Driver 18 for SQL Server")

DB_URL = f"mssql+pyodbc://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}?driver={driver_encoded}&Encrypt=no"
#DB_URL = f"mysql+mysqlconnector://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

engine = create_engine(DB_URL)

# Body Model for query payload
class Query(BaseModel):
    query: str

FORBIDDEN_KEYWORDS = {"drop", "delete", "update", "insert", "alter", "truncate"}

@app.get("/schema")
def get_schema():
    try:
        ddl_output = []
        with engine.connect() as conn:
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            result = {}

            for table in tables:
                ddl_lines = [f"CREATE TABLE {table} ("]
                columns = inspector.get_columns(table)

                col_defs = []
                for col in columns:
                    col_name = col["name"]
                    col_type = str(col["type"])
                    nullable = "" if col["nullable"] else " NOT NULL"
                    col_defs.append(f"    {col_name} {col_type}{nullable}")

                # Primary key
                pk = inspector.get_pk_constraint(table)
                if pk and pk.get("constrained_columns"):
                    pk_cols = ", ".join(pk["constrained_columns"])
                    col_defs.append(f"    PRIMARY KEY ({pk_cols})")

                ddl_lines.append(",\n".join(col_defs))
                ddl_lines.append(");")

                result[table] = "\n".join(ddl_lines)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Process Failure: {str(e)}")

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
        
