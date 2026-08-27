# Movie Recommender

A simple demo web application that recommends movies based on user input. Built with FastAPI, Google Gemini (via `google-genai`), and ChromaDB, the app returns a recommended title, a short summary, and an associated poster image.

## Features

- Text-based movie recommendations
- Optional voice-to-text transcription (UI supports speech input)
- Recommendation and summary generation via Gemini
- Image selection/generation for movie posters
- Local poster assets in `generated_images` with fallback to TMDb
- Content filtering for inappropriate inputs (a regular-expression based regex filter is integrated to block profanity)
- Minimal HTML/CSS/JS frontend for quick demos

## Example flow

1. The user types or says: "I want a movie about friendship and magic."
2. The backend searches for similar items in ChromaDB.
3. Gemini generates a recommendation and a short summary.
4. The app selects a relevant image from `generated_images` or falls back to TMDb.
5. The UI displays the movie, summary, and poster.

## Technologies

- Python 3.11+
- FastAPI
- Uvicorn
- ChromaDB
- Google Gemini / `google-genai`
- python-dotenv
- Pillow

## Project structure

```text
book_recommander/
├── app.py                # FastAPI application
├── chatbot.py            # utilities for ingesting data into ChromaDB
├── chroma_db/            # persistent vector store
├── frontend/
│   ├── index.html
│   ├── main.js
│   └── styles.css
├── generated_images/     # local poster images
├── language_filter.py    # input filtering logic (regex)
├── main.py               # local entry point / utilities
├── requirements.txt
├── summaries.py
├── token_counter.py
└── README.md
```

## Setup

1. Open a terminal in the project folder.

2. Create a virtual environment:

```powershell
python -m venv .venv
```

3. Activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

4. Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

5. Create a `.env` file from `.env.example` and add your API keys:

```env
GEMINI_API_KEY=your_gemini_key_here
TMDB_API_KEY=your_tmdb_key_here
```

## Run

Start the server locally:

```powershell
uvicorn app:app --reload
```

Open the UI at:

```text
http://127.0.0.1:8000
```

## API Endpoints

### POST /api/recommend

Request example:

```json
{
  "query": "i want a movie about friendship and magic"
}
```

Response example:

```json
{
  "flagged": false,
  "title": "The Lord of the Rings",
  "recommendation": "...",
  "summary": "...",
  "image_url": "/images/cover_xxx.png"
}
```

### POST /api/generate-image

Request example:

```json
{
  "title": "Inception",
  "summary": "A thief who steals secrets from dreams..."
}
```

### POST /api/transcribe

An optional endpoint for audio-to-text transcription (used by the demo UI).

## Notes

- Local images are preferred before any generative fallback.
- Keep API keys in `.env` and do not commit them to the repository.
- The project is intended as a local demo and for quick testing.
