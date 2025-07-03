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
        with engine.connect() as conn:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            result = {}

            for table in tables:
                lines = [f"Tabel: {table}", "Kolom:"]

                columns = inspector.get_columns(table)
                pk = inspector.get_pk_constraint(table).get("constrained_columns", [])

                for col in columns:
                    name = col["name"]
                    sql_type = str(col["type"]).lower()
                    nullable = col["nullable"]
                    is_pk = name in pk

                    if "varchar" in sql_type or "char" in sql_type or "text" in sql_type:
                        col_type = "teks"
                    elif "int" in sql_type:
                        col_type = "bilangan bulat"
                    elif "decimal" in sql_type or "numeric" in sql_type or "float" in sql_type:
                        col_type = "angka desimal"
                    elif "date" in sql_type or "time" in sql_type:
                        col_type = "tanggal/waktu"
                    elif "bool" in sql_type:
                        col_type = "boolean"
                    else:
                        col_type = sql_type  # fallback

                    description = f"- {name}: {col_type}"
                    if is_pk:
                        description += ", kunci utama"
                    if not nullable and not is_pk:
                        description += ", wajib diisi"

                    lines.append(description)

                result[table] = "\n".join(lines)

            return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses skema: {str(e)}")

def safe_encode_row(row_dict):
    for key, value in row_dict.items():
        if isinstance(value, bytes):
            row_dict[key] = base64.b64encode(value).decode("utf-8")
    return row_dict

@app.post("/query")
def get_result(query: Query):
    lowered_query = query.query.lower()

    print(lowered_query)

    # Check for forbidden SQL keywords
    if any(keyword in lowered_query for keyword in FORBIDDEN_KEYWORDS):
        raise HTTPException(status_code=400, detail="Prohibited SQL statement detected.")

    try:
        with engine.connect() as connection:
            result = connection.execute(text(query.query))
            rows = result.mappings().all()

            # Encode binary fields to avoid JSON serialization errors
            safe_rows = [safe_encode_row(dict(row)) for row in rows]

            return safe_rows

    except Exception as e:
        print("SQL Execution Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Process Failure: {str(e)}")
        
