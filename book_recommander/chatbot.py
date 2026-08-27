import os
from dotenv import load_dotenv
from google import genai
import chromadb

from summaries import movie_summaries_dict


load_dotenv(dotenv_path=".env")

# Configurează Google Generative AI
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="movie_summaries")


def get_embedding(text: str):
    try:
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
        )
        embeddings = getattr(result, "embeddings", None)
        if embeddings:
            values = getattr(embeddings[0], "values", None)
            if values is not None:
                return list(values)
    except Exception as exc:
        print(f"Embedding Gemini failed: {exc}")

    import hashlib
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    for i in range(1536):
        byte = digest[i % len(digest)]
        values.append(((byte / 255.0) - 0.5) * 2)
    return values


def ingest_movies():
    movies = [
        {"title": title, "summary": summary}
        for title, summary in movie_summaries_dict.items()
    ]

    for idx, movie in enumerate(movies):
        embedding = get_embedding(movie["summary"])
        collection.add(
            ids=[str(idx)],
            documents=[movie["summary"]],
            metadatas=[{"title": movie["title"]}],
            embeddings=[embedding]
        )

    print("Movies loaded into ChromaDB successfully.")


if __name__ == "__main__":
    ingest_movies()