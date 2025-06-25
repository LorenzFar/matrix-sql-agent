from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, inspect, text

app = FastAPI()

DB_URL = "mysql+mysqlconnector://root:root@localhost:3306/book"
engine = create_engine(DB_URL)

FORBIDDEN_KEYWORDS = {"drop", "delete", "update", "insert", "alter", "truncate"}

@app.get("/schema")
def get_schema():
    inspector = inspect(engine)
    schema = {}

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        pk_info = inspector.get_pk_constraint(table_name)
        fk_info = inspector.get_foreign_keys(table_name)

        pk_columns = set(pk_info.get("constrained_columns", []))
        fk_columns = {fk["constrained_columns"][0]: fk["referred_table"] + "." + fk["referred_columns"][0]
                      for fk in fk_info if fk.get("constrained_columns") and fk.get("referred_columns")}

        column_definitions = []
        for col in columns:
            col_name = col["name"]
            col_entry = {
                "name": col_name,
                "type": str(col["type"]),
            }

            if col_name in pk_columns:
                col_entry["PK"] = True
            if col_name in fk_columns:
                col_entry["FK"] = fk_columns[col_name]

            column_definitions.append(col_entry)

        schema[table_name] = column_definitions

    return schema

@app.get("/query")
def get_result(query):

    #Convert query to lowercase and check for keyword
    lowered_query = query.lower()
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in lowered_query:
            raise HTTPException(status_code=400, detail="Prohibited SQL statement detected.")
        
    with engine.connect() as connection:
        try:
            result = connection.execute(text(query))
            
            rows = result.fetchall()
            cols = result.keys()

            result_list = []

            for row in rows:
                row_dict = {}
                for i in range(len(cols)):
                    row_dict[cols[i]] = row[i]
                result_list.append(row_dict)

            return result_list
        except Exception as e:
            raise HTTPException(status_code = 500, detail = f"Query execution failed: {str(e)}")