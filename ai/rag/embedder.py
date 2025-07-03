from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("BAAI/bge-m3")

def embed_schema(schema_dict):
    prefix = "Represent this sentence for retrieval: "
    texts = []

    for schema in schema_dict.values():
        texts.append(prefix + schema)

    embeddings =  model.encode(texts, normalize_embeddings=True)
    return np.array(embeddings)



