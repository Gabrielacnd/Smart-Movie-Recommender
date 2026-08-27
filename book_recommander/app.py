# === MOVIE RECOMMENDER API ===
# FastAPI server pentru recomandări de filme bazate pe embedding și generare AI
# Utilizează Google Gemini pentru embeddings și chat
# Utilizează ChromaDB pentru vector search pe rezumatele de filme

import json
import os
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4

import base64
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import chromadb
from PIL import Image, ImageDraw, ImageFont

try:
    from google import genai as google_genai
    from google.genai import types as genai_types
    LEGACY_GEMINI = False
except Exception:
    import google.generativeai as genai
    google_genai = None
    genai_types = None
    LEGACY_GEMINI = True

from language_filter import get_filtered_input
from summaries import get_summary_by_title, movie_summaries_dict
from token_counter import count_tokens, log_token_usage

# === SETUP ===
BASE_DIR = Path(__file__).parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Inițializează Google Generative AI client cu Gemini
# Folosește noul SDK `google.genai` când este disponibil; dacă nu, se reia fallback pe varianta legacy.
gemini_api_key = os.getenv("GEMINI_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
gemini_client = None

if gemini_api_key:
    try:
        if google_genai is not None:
            gemini_client = google_genai.Client(api_key=gemini_api_key)
        else:
            genai.configure(api_key=gemini_api_key)
    except Exception as exc:
        print(f"Gemini client init failed: {exc}")

# Inițializează ChromaDB pentru vector database
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="movie_summaries")

# Configurează directoare pentru fișiere generate
BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR / "frontend"
IMAGE_DIR = BASE_DIR / "generated_images"
IMAGE_DIR.mkdir(exist_ok=True)

# Creează aplicație FastAPI
app = FastAPI(title="Movie Recommender API")

# Adaugă middleware CORS pentru a permite request-uri din frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montează directoare statice
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
app.mount("/images", StaticFiles(directory=str(IMAGE_DIR)), name="images")


def get_embedding(text: str):
    """Generează embedding vector pentru text folosind Gemini."""
    try:
        if gemini_client is not None and google_genai is not None:
            kwargs = {"model": "gemini-embedding-001", "contents": text}
            if genai_types is not None:
                try:
                    kwargs["config"] = genai_types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                except Exception:
                    pass
            result = gemini_client.models.embed_content(**kwargs)
            embeddings = getattr(result, "embeddings", None)
            if embeddings:
                values = getattr(embeddings[0], "values", None)
                if values is not None:
                    return list(values)
            if isinstance(result, dict):
                if "embedding" in result:
                    return result["embedding"]
                if "embeddings" in result and result["embeddings"]:
                    return result["embeddings"][0]["values"] if isinstance(result["embeddings"][0], dict) else result["embeddings"][0].values
        elif gemini_api_key and not LEGACY_GEMINI:
            # Caz rar, dacă client-ul nou nu este disponibil, dar SDK-ul vechi există încă.
            result = genai.embed_content(
                model="gemini-embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            if isinstance(result, dict) and "embedding" in result:
                return result["embedding"]
            if hasattr(result, "embedding"):
                return result.embedding
    except Exception as exc:
        print(f"Embedding Gemini failed: {exc}")

    # Fallback: folosim un vector simplu bazat pe text cu dimensiunea 1536, potrivită pentru colecția ChromaDB
    import hashlib
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    for i in range(1536):
        byte = digest[i % len(digest)]
        values.append(((byte / 255.0) - 0.5) * 2)
    return values


def _normalize_query_tokens(text: str):
    cleaned = ''.join(ch.lower() if ch.isalpha() or ch.isdigit() or ch.isspace() else ' ' for ch in text)
    return [token for token in cleaned.split() if token]


CATEGORY_KEYWORDS = {
    "magie": ["magic", "magie", "wizard", "vrăjitor", "witch", "fantasy", "dragon", "spell", "poveste", "sorcerer"],
    "prietenie": ["prietenie", "friend", "friends", "familie", "family", "amici", "iubire", "dragoste", "heart", "team"],
    "aventura": ["adventure", "aventură", "travel", "călătorie", "journey", "mission", "explore", "explorare"],
    "actiune": ["action", "acțiune", "fight", "battle", "thriller", "danger", "adrenaline", "combat"],
    "stiinta": ["science", "știință", "space", "cosmos", "robot", "alien", "future", "futur", "tech"],
    "groaza": ["horror", "groază", "night", "noapte", "evil", "dark", "mystery", "mister", "scary"],
}


def _score_movie_match(user_query: str, title: str, summary: str):
    query_tokens = set(_normalize_query_tokens(user_query))
    text = f"{title} {summary}".lower()
    score = 0

    for token in query_tokens:
        if token in text:
            score += 2
        if token in title.lower():
            score += 4

    for category_name, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in user_query.lower() for keyword in keywords):
            if category_name in title.lower() or category_name in text:
                score += 10
            if any(keyword in text for keyword in keywords):
                score += 8

    return score


def retrieve_movies(user_query: str, n_results: int = 2):
    """Caută cele mai relevante filme folosind similarity search în ChromaDB."""
    try:
        query_embedding = get_embedding(user_query)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=max(n_results, 6)
        )

        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        if documents and metadatas and documents[0]:
            movies = []
            for doc, meta in zip(documents[0], metadatas[0]):
                movies.append({
                    "title": meta["title"],
                    "summary": doc
                })
            if movies:
                return movies[:n_results]
    except Exception as exc:
        print(f"ChromaDB query failed: {exc}")

    fallback_movies = [
        {"title": title, "summary": summary}
        for title, summary in list(movie_summaries_dict.items())
    ]
    ranked_movies = sorted(
        fallback_movies,
        key=lambda movie: (
            _score_movie_match(user_query, movie["title"], movie["summary"]),
            -len(movie["title"]),
            movie["title"].lower()
        ),
        reverse=True
    )

    if not any(_score_movie_match(user_query, movie["title"], movie["summary"]) > 0 for movie in fallback_movies):
        ranked_movies = sorted(fallback_movies, key=lambda movie: movie["title"].lower())

    return ranked_movies[:n_results]


# Backward compatibility alias
retrieve_books = retrieve_movies


def truncate_text(text: str, max_chars: int = 220):
    """Trunchiază textul fără să taie cuvinte la mijloc."""
    if not text:
        return ""

    cleaned = text.strip()
    if len(cleaned) <= max_chars:
        return cleaned

    truncated = cleaned[:max_chars]
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]

    return truncated + "..."


def fetch_tmdb_poster_url(title: str):
    """Încerca să găsească afișul real al filmului din TMDb."""
    if not TMDB_API_KEY:
        return None

    try:
        encoded_title = quote(title)
        url = (
            f"https://api.themoviedb.org/3/search/movie?query={encoded_title}&include_adult=false"
            "&language=en-US&page=1"
        )
        req = Request(
            url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {TMDB_API_KEY}"
            },
            method="GET"
        )
        with urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

        results = data.get("results") or []
        if not results:
            return None

        poster_path = results[0].get("poster_path")
        if not poster_path:
            return None

        return f"https://image.tmdb.org/t/p/w780{poster_path}"
    except Exception as exc:
        print(f"TMDb poster lookup failed: {exc}")
        return None


def pick_local_generated_image(title: str | None = None, summary: str | None = None):
    """Preferă setul de imagini realiste din generated_images (cover_...) înainte de celelalte fișiere mai vechi."""
    files = sorted(IMAGE_DIR.glob("*.png"))
    if not files:
        return None

    cover_files = [f for f in files if f.name.startswith("cover_")]
    preferred_files = cover_files if cover_files else files

    stop_words = {
        "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "is", "it",
        "this", "that", "as", "at", "by", "be", "from", "about", "into", "up", "out", "so",
        "if", "but", "not", "you", "your", "our", "we", "he", "she", "they", "them", "their",
        "movie", "film", "cover", "poster"
    }

    def normalize_text(value: str) -> str:
        return ''.join(ch for ch in value.lower() if ch.isalnum() or ch.isspace()).replace('  ', ' ').strip()

    def token_list(value: str):
        tokens = []
        for token in normalize_text(value).split():
            cleaned = ''.join(ch for ch in token if ch.isalnum())
            if len(cleaned) > 1 and cleaned not in stop_words:
                tokens.append(cleaned)
        return tokens

    title_tokens = token_list(title or "")
    summary_tokens = token_list(summary or "")
    base_tokens = title_tokens or summary_tokens

    if not base_tokens:
        return preferred_files[0] if preferred_files else None

    for candidate in preferred_files:
        stem_tokens = token_list(candidate.stem)
        stem = " ".join(stem_tokens)
        if not stem_tokens:
            continue
        matches = sum(1 for token in base_tokens if token in stem)
        if title_tokens and matches >= len(title_tokens):
            return candidate

    best_match = None
    best_score = 0
    for candidate in preferred_files:
        stem_tokens = token_list(candidate.stem)
        stem = " ".join(stem_tokens)
        score = sum(10 for token in summary_tokens if token in stem)
        score += sum(12 for token in title_tokens if token in stem)
        if score > best_score:
            best_score = score
            best_match = candidate

    if best_score >= 12:
        return best_match

    return preferred_files[0]


def _pick_theme(title: str, summary: str | None):
    """Alege un paletă și simboluri conforme cu tema filmului."""
    text = f"{title} {summary or ''}".lower()
    if any(keyword in text for keyword in ["magic", "magie", "wizard", "vrăjitor", "dragon", "fantasy", "fantastic", "castle", "kingdom", "poveste"]):
        return {
            "bg": (31, 20, 58),
            "accent": (255, 184, 77),
            "secondary": (124, 92, 255),
            "highlight": (110, 234, 255),
            "label": "magic"
        }
    if any(keyword in text for keyword in ["prietenie", "family", "familie", "copii", "friend", "amici", "dragoste", "iubire", "heart"]):
        return {
            "bg": (255, 170, 150),
            "accent": (255, 92, 124),
            "secondary": (255, 214, 102),
            "highlight": (255, 245, 214),
            "label": "friendship"
        }
    if any(keyword in text for keyword in ["adventure", "aventură", "travel", "călătorie", "explore", "explorare", "journey", "mission"]):
        return {
            "bg": (18, 62, 86),
            "accent": (52, 195, 143),
            "secondary": (255, 154, 74),
            "highlight": (210, 245, 255),
            "label": "adventure"
        }
    if any(keyword in text for keyword in ["scifi", "science", "futur", "space", "cosmos", "robot", "alien", "tech"]):
        return {
            "bg": (8, 28, 58),
            "accent": (98, 191, 255),
            "secondary": (76, 234, 196),
            "highlight": (225, 243, 255),
            "label": "sci-fi"
        }
    if any(keyword in text for keyword in ["horror", "groază", "night", "noapte", "evil", "rău", "mystery", "mister", "thriller"]):
        return {
            "bg": (18, 18, 27),
            "accent": (255, 88, 88),
            "secondary": (120, 122, 255),
            "highlight": (245, 223, 255),
            "label": "thriller"
        }
    return {
        "bg": (26, 34, 68),
        "accent": (255, 128, 93),
        "secondary": (255, 205, 86),
        "highlight": (214, 220, 255),
        "label": "general"
    }


def generate_movie_poster(title: str, summary: str | None = None, output_file: str | None = None):
    """Folosește imaginile din generated_images doar când există o potrivire clară; altfel generează un poster unic pentru acest film."""
    if output_file is None:
        existing = pick_local_generated_image(title, summary)
        if existing is not None:
            return str(existing)

        slug = ''.join(ch for ch in (title or "movie").lower() if ch.isalnum() or ch in [' ', '-'])
        slug = slug.replace(' ', '_').strip('_') or 'movie'
        output_file = IMAGE_DIR / f"{slug}_{uuid4().hex}.png"
    else:
        output_file = Path(output_file)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        if gemini_client is not None and google_genai is not None:
            prompt = (
                f"Create a cinematic movie poster for '{title}'. "
                f"The artwork should be visually striking, polished, and highly evocative. "
                f"Use a strong composition, dramatic lighting, and a clear theme based on this summary: {summary or title}. "
                "The style should look like a modern movie poster, vibrant but realistic, with high contrast and premium visual quality."
            )
            config = None
            if genai_types is not None and hasattr(genai_types, "GenerateContentConfig"):
                config = genai_types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])
            elif genai_types is not None and hasattr(genai_types, "GenerateImagesConfig"):
                config = genai_types.GenerateImagesConfig()
            response = gemini_client.models.generate_content(
                model="gemini-2.0-flash-preview-image-generation",
                contents=prompt,
                config=config,
            )

            candidates = getattr(response, "candidates", None) or []
            for candidate in candidates:
                content = getattr(candidate, "content", None)
                parts = getattr(content, "parts", []) or []
                for part in parts:
                    inline = getattr(part, "inline_data", None)
                    if inline is not None:
                        binary = getattr(inline, "data", None)
                        if isinstance(binary, str):
                            image_bytes = base64.b64decode(binary)
                        elif isinstance(binary, (bytes, bytearray)):
                            image_bytes = bytes(binary)
                        else:
                            image_bytes = None
                        if image_bytes:
                            output_file.write_bytes(image_bytes)
                            return str(output_file)

            if hasattr(response, "images") and response.images:
                image_bytes = getattr(response.images[0], "image_bytes", None) or getattr(response.images[0], "data", None)
                if image_bytes:
                    if isinstance(image_bytes, str):
                        image_bytes = base64.b64decode(image_bytes)
                    output_file.write_bytes(image_bytes)
                    return str(output_file)
    except Exception as exc:
        print(f"Gemini image generation failed: {exc}")

    width, height = 900, 1200
    theme = _pick_theme(title, summary)
    img = Image.new("RGB", (width, height), color=theme["bg"])
    draw = ImageDraw.Draw(img)

    for i in range(16):
        x = (i * 73) % width
        y = (i * 97) % height
        r = 80 + (i % 5) * 22
        draw.ellipse((x, y, x + r, y + r), fill=theme["secondary"])

    if theme["label"] == "magic":
        draw.polygon([(150, 950), (450, 660), (750, 950)], fill=theme["accent"])
        draw.ellipse((300, 300, 600, 600), fill=theme["highlight"])
        draw.polygon([(310, 660), (450, 420), (590, 660)], fill=theme["secondary"])
    elif theme["label"] == "friendship":
        draw.ellipse((200, 260, 700, 860), fill=theme["highlight"])
        draw.ellipse((260, 330, 450, 620), fill=theme["accent"])
        draw.ellipse((450, 330, 640, 620), fill=theme["accent"])
        draw.ellipse((330, 520, 570, 760), fill=theme["secondary"])
    elif theme["label"] == "adventure":
        draw.polygon([(80, 980), (290, 560), (470, 980)], fill=theme["accent"])
        draw.polygon([(340, 980), (620, 540), (840, 980)], fill=theme["secondary"])
        draw.ellipse((330, 280, 570, 520), fill=theme["highlight"])
    elif theme["label"] == "sci-fi":
        draw.ellipse((210, 320, 690, 780), fill=theme["highlight"])
        for x in [200, 320, 440, 560, 680]:
            draw.line((x, 1000, x + 40, 700), fill=theme["accent"], width=8)
        draw.arc((230, 250, 670, 690), start=20, end=160, fill=theme["accent"], width=18)
    elif theme["label"] == "thriller":
        draw.ellipse((240, 250, 660, 720), fill=theme["highlight"])
        draw.polygon([(200, 970), (330, 760), (460, 970)], fill=theme["secondary"])
        draw.polygon([(440, 970), (570, 760), (700, 970)], fill=theme["accent"])

    title_text = (title or "Movie Pick")[:32]
    title_lines = []
    words = title_text.split()
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= 16:
            current = candidate
        else:
            title_lines.append(current)
            current = word
    if current:
        title_lines.append(current)

    title_y = 170
    for idx, line in enumerate(title_lines[:3]):
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 58 if idx == 0 else 42)
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (width - (bbox[2] - bbox[0])) / 2
        draw.text((x, title_y + idx * 70), line, font=font, fill=(255, 255, 255))

    subtitle = "movie pick"
    font_sub = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
    draw.text((100, 980), subtitle.upper(), fill=theme["highlight"], font=font_sub)

    summary_text = (summary or "A memorable story full of emotion and adventure.")
    preview = summary_text.strip().replace("\n", " ")
    if len(preview) > 130:
        preview = preview[:127].rsplit(" ", 1)[0] + "..."
    font_summary = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
    wrapped = []
    current = ""
    for word in preview.split():
        if len((current + " " + word).strip()) <= 24:
            current = (current + " " + word).strip()
        else:
            wrapped.append(current)
            current = word
    if current:
        wrapped.append(current)
    for idx, line in enumerate(wrapped[:4]):
        draw.text((90, 1020 + idx * 30), line, fill=(245, 245, 245), font=font_summary)

    img.save(output_file)
    return str(output_file)


# Backward compatibility alias
generate_book_image = generate_movie_poster


def recommend_movie_with_gpt(user_query: str):
    """
    Recomandare text folosind Gemini.
    Returnează: (titlu, recomandare, rezumat)
    """
    retrieved_movies = retrieve_movies(user_query, n_results=2)

    context = "\n".join(
        [
            f"{idx + 1}. {movie['title']}: {truncate_text(movie['summary'], max_chars=180)}"
            for idx, movie in enumerate(retrieved_movies)
        ]
    )

    prompt = f"""
Ești un asistent AI care recomandă filme în limba română.

Utilizatorul a cerut: {user_query}

Filme relevante:
{context}

Instrucțiuni:
1. Alege un singur film din listă.
2. Menționează clar titlul exact al filmului recomandat.
3. Explică în 2-3 propoziții de ce se potrivește utilizatorului.
4. Răspunde natural, prietenos și în limba română.
5. Nu inventa alte titluri în afara listei.
"""

    try:
        prompt_tokens = count_tokens(prompt, "gemini")
    except Exception:
        prompt_tokens = 0

    # Folosește Gemini pentru generare text
    response = None
    try:
        if gemini_client is not None and google_genai is not None:
            response = gemini_client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )
            recommendation_text = getattr(response, "text", None)
            if recommendation_text is None and hasattr(response, "candidates") and response.candidates:
                parts = getattr(response.candidates[0].content, "parts", []) or []
                if parts:
                    recommendation_text = getattr(parts[0], "text", "")
        elif gemini_api_key and LEGACY_GEMINI:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            recommendation_text = response.text
        else:
            raise RuntimeError("Gemini API key not configured")
    except Exception as exc:
        print(f"Gemini chat failed: {exc}")
        recommendation_text = f"Îți recomand filmul {retrieved_movies[0]['title'] if retrieved_movies else 'un film potrivit'} pentru că se aliniază cu preferințele tale."

    if response is not None and hasattr(response, "usage_metadata"):
        print("=== TOKEN USAGE (Gemini) ===")
        print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
        print(f"Completion tokens: {response.usage_metadata.candidates_token_count}")
        print(f"Total tokens: {response.usage_metadata.prompt_token_count + response.usage_metadata.candidates_token_count}")
        print("====================")

    recommended_title = ""
    lower_text = recommendation_text.lower()
    for movie in retrieved_movies:
        if movie["title"].lower() in lower_text:
            recommended_title = movie["title"]
            break

    if not recommended_title and retrieved_movies:
        ranked_by_query = sorted(
            retrieved_movies,
            key=lambda movie: _score_movie_match(user_query, movie["title"], movie["summary"]),
            reverse=True
        )
        recommended_title = ranked_by_query[0]["title"]

    summary_text = ""
    if recommended_title:
        summary_text = get_summary_by_title(recommended_title)

    if not summary_text or "nu a fost găsit" in summary_text.lower():
        for movie in retrieved_movies:
            if movie["title"].lower() == recommended_title.lower():
                summary_text = movie["summary"]
                break

    if not summary_text and retrieved_movies:
        summary_text = sorted(
            retrieved_movies,
            key=lambda movie: _score_movie_match(user_query, movie["title"], movie["summary"]),
            reverse=True
        )[0]["summary"]

    try:
        completion_tokens = len(recommendation_text.split())
        log_token_usage("gemini", prompt_tokens, completion_tokens, "chat")
    except Exception:
        pass

    if not recommendation_text.strip():
        recommendation_text = (
            f"Îți recomand filmul **{recommended_title}**. "
            f"Se potrivește bine cu ce cauți deoarece pune accent pe temele menționate de tine "
            f"și oferă o experiență plăcută și captivantă."
        )

    return recommended_title, recommendation_text, summary_text


# Backward compatibility alias
recommend_book_with_gpt = recommend_movie_with_gpt


@app.get("/")
async def root():
    index_path = FRONTEND_DIR / "index.html"

    if not index_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"index.html nu a fost găsit la {index_path}"
        )

    return FileResponse(index_path)


@app.post("/api/transcribe")
async def transcribe(audio_file: UploadFile = File(...)):
    """Transcrie audio în text."""
    if not audio_file.content_type or not audio_file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Please upload a valid audio file.")

    return {
        "transcript": "Transcrierea audio nu este disponibilă în această versiune. Folosește textul direct pentru recomandare."
    }


@app.post("/api/recommend")
async def recommend(payload: dict):
    """
    Endpoint doar pentru text:
    - recomandare
    - rezumat
    Fără imagine și fără audio în acest request.
    """
    user_query = payload.get("query", "").strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query text is required.")

    is_inappropriate, filter_response, _ = get_filtered_input(user_query)
    if is_inappropriate:
        return {
            "flagged": True,
            "message": filter_response
        }

    try:
        recommended_title, recommendation, summary = recommend_movie_with_gpt(user_query)

        local_poster = pick_local_generated_image(recommended_title, summary)
        if local_poster is not None:
            poster_url = f"/images/{local_poster.name}"
        else:
            poster_url = fetch_tmdb_poster_url(recommended_title)
            if not poster_url:
                image_path = generate_movie_poster(recommended_title, summary)
                poster_url = f"/images/{Path(image_path).name}"

        return {
            "flagged": False,
            "title": recommended_title,
            "recommendation": recommendation,
            "summary": summary,
            "image_url": poster_url
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/generate-image")
async def generate_image(payload: dict):
    """
    Endpoint separat pentru generarea imaginii.
    Input:
    {
      "title": "...",
      "summary": "..."
    }
    """
    title = payload.get("title", "").strip()
    summary = payload.get("summary", "").strip()

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Title is required to generate image."
        )

    try:
        local_poster = pick_local_generated_image(title, summary)
        if local_poster is not None:
            return {"image_url": f"/images/{local_poster.name}"}

        real_poster_url = fetch_tmdb_poster_url(title)
        if real_poster_url:
            return {"image_url": real_poster_url}

        image_path = generate_movie_poster(title, summary)
        image_url = f"/images/{Path(image_path).name}"
        return {"image_url": image_url}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

