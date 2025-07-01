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
        inspector = inspect(engine)
        for table_name in inspector.get_table_names():
            safe_name = quoted_name(table_name, quote=True)
            sql = conn.execute(text(f"SHOW CREATE TABLE `{safe_name}`")).fetchone()
            result[table_name] = sql[1]
        return result
    
    # inspector = inspect(engine)
    # schema = {}

    # for table_name in inspector.get_table_names():
    #     columns = inspector.get_columns(table_name)
    #     pk_info = inspector.get_pk_constraint(table_name)
    #     fk_info = inspector.get_foreign_keys(table_name)

    #     pk_columns = set(pk_info.get("constrained_columns", []))
    #     fk_columns = {
    #         fk["constrained_columns"][0]: fk["referred_table"] + "." + fk["referred_columns"][0]
    #         for fk in fk_info if fk.get("constrained_columns") and fk.get("referred_columns")
    #     }

    #     column_definitions = []
    #     for col in columns:
    #         col_name = col["name"]
    #         col_entry = {
    #             "name": col_name,
    #             "type": str(col["type"]),
    #         }
    #         if col_name in pk_columns:
    #             col_entry["PK"] = True
    #         if col_name in fk_columns:
    #             col_entry["FK"] = fk_columns[col_name]

    #         column_definitions.append(col_entry)

    #     schema[table_name] = column_definitions

    # return schema

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
            raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")
