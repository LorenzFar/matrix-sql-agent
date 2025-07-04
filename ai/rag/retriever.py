import faiss
import numpy as np

index = None
stored_texts = []

def build_faiss_index(embeddings):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    return index

def search_top_k(index, texts, query_embedding, max_k=5, min_score=0.7):
    query_embedding = np.array([query_embedding])
    scores, indices = index.search(query_embedding, max_k)

    results = []
    for i, score in zip(indices[0], scores[0]):
        if score < min_score:
            continue
        results.append(texts[i])
    return results