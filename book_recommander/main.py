import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
import chromadb
from summaries import get_summary_by_title

load_dotenv()

# Configurează Google Generative AI
gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="movie_summaries")


def get_embedding(text: str):
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        if isinstance(result, dict) and "embedding" in result:
            return result["embedding"]
        if hasattr(result, "embedding"):
            return result.embedding
    except Exception as exc:
        print(f"Embedding Gemini failed: {exc}")

    import hashlib
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    for i in range(1536):
        byte = digest[i % len(digest)]
        values.append(((byte / 255.0) - 0.5) * 2)
    return values


def retrieve_movies(user_query: str, n_results: int = 3):
    query_embedding = get_embedding(user_query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    movies = []
    docs = results["documents"][0]
    metas = results["metadatas"][0]

    for doc, meta in zip(docs, metas):
        movies.append({
            "title": meta["title"],
            "summary": doc
        })

    return movies


tools = [
    {
        "type": "function",
        "name": "get_summary_by_title",
        "description": "Returnează rezumatul complet pentru un titlu exact de film.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Titlul exact al filmului"
                }
            },
            "required": ["title"],
            "additionalProperties": False
        },
        "strict": True
    }
]


def recommend_movie(user_query: str):
    retrieved = retrieve_movies(user_query, n_results=3)

    context = "\n\n".join(
        [f"Title: {m['title']}\nSummary: {m['summary']}" for m in retrieved]
    )

    prompt = f"""
Ești un asistent AI care recomandă filme în limba română.

Întrebarea utilizatorului:
{user_query}

Filme relevante din vector store:
{context}

Instrucțiuni:
1. Recomandă un singur film.
2. Spune clar titlul.
3. Explică pe scurt, în 2-3 propoziții, de ce se potrivește.
4. Apoi apelează funcția get_summary_by_title folosind titlul exact.
5. Răspunde în limba română.
"""

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
        tools=tools,
        max_output_tokens=180
    )

    if hasattr(response, "usage") and response.usage:
        print("\n=== TOKEN USAGE ===")
        print(f"Input tokens: {response.usage.input_tokens}")
        print(f"Output tokens: {response.usage.output_tokens}")
        print(f"Total tokens: {response.usage.total_tokens}")
        print("===================\n")

    return response, retrieved


def run_chatbot():
    print("Movie Recommender CLI")
    print("Scrie o întrebare despre ce fel de film cauți.")
    print("Scrie 'exit' sau 'quit' pentru ieșire.")

    while True:
        user_query = input("\nTu: ").strip()

        if user_query.lower() in ["exit", "quit"]:
            print("La revedere!")
            break

        if not user_query:
            print("Te rog introdu o întrebare.")
            continue

        try:
            response, retrieved = recommend_movie(user_query)

            called_title = None

            for item in response.output:
                if item.type == "message":
                    for content in item.content:
                        if content.type == "output_text":
                            print("\nBot:")
                            print(content.text)

                elif item.type == "function_call":
                    arguments = json.loads(item.arguments)
                    called_title = arguments["title"]
                    full_summary = get_summary_by_title(called_title)

                    print("\n--- Rezumat complet ---")
                    print(full_summary)

            if called_title is None and retrieved:
                fallback_title = retrieved[0]["title"]
                print("\n--- Rezumat complet (fallback) ---")
                print(get_summary_by_title(fallback_title))

        except Exception as e:
            print(f"\nEroare: {e}")


if __name__ == "__main__":
    run_chatbot()