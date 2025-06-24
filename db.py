from fastapi import FastAPI
from sqlalchemy import create_engine, inspect

app = FastAPI()

DB_URL = "mysql+mysqlconnector://root:root@localhost:3306/book"
engine = create_engine(DB_URL)

@app.get("/schema")
def get_schema():
    inspector = inspect(engine)
    schema = {}

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)

        column_names = []
        for col in columns:
            column_names.append(col["name"])

        schema[table_name] = column_names

    return schema
