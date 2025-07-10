
PROMPT_TEMPLATE = """
        <|begin_of_text|><|start_header_id|>user<|end_header_id|>

        Generate a Microsoft SQL Server (T-SQL) query to answer this question: `{question}`

        Return one of the following:
        * A valid Microsoft SQL Server (T-SQL) query if the question is clear, relevant, and answerable using the provided schema.
        * A guidance message if the question cannot be answered due to missing information, ambiguity, or irrelevance.

        Evaluation Rules:
        1. Relevance Check: Determine whether the question pertains to the given schema.›
        2. Answerability Check: Confirm that the required tables and columns exist in the schema.
        3. Clarity Check: Ensure the question is specific and unambiguous.
        4. Schema-Based Inference: Use logical joins or filters only if supported by the schema.
        5. Always perform JOINs using foreign keys when they enrich the answer, especially for questions asking for "all information" or "complete details."
        6. Do not use syntax that is invalid in Microsoft SQL Server such as `LIMIT`, `AUTO_INCREMENT`, `!=`, `NOW()`, `IFNULL`, or `SERIAL`.
        7. Use `OFFSET ... FETCH NEXT` instead of `LIMIT` for pagination.
        8. Only use columns and tables that exist in the provided schema. Do not invent columns.
        9. Use `SELECT TOP N` or `OFFSET ... FETCH NEXT` when limiting rows.

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

        The following Microsoft SQL Server (T-SQL) query best answers the question `{question}`:
        ```sql
    """

def build_prompt(schema, question):
    ddl = "\n\n".join(schema)
    final_prompt = PROMPT_TEMPLATE.format(schema=ddl, question=question)

    return final_prompt