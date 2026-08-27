# Movie Recommender

This folder contains the demo application that recommends movies based on user prompts. The backend uses FastAPI, ChromaDB, and Google Gemini to find similar titles, generate natural-language recommendations and summaries, and serve poster images.

## Features

- Text-based movie recommendations
- Voice-to-text support in the UI (optional)
- Gemini-powered recommendation and summary generation
- Local poster selection with fallback to TMDb
- Input filtering for inappropriate content (a regex-based filter is integrated to block profanity)
- Lightweight HTML/CSS/JS frontend

## Example flow

1. The user types or speaks a request (e.g., "I want a movie about friendship and magic").
2. The backend queries ChromaDB for similar entries.
3. Gemini generates the final recommendation and a short summary.
4. The app chooses a poster from `generated_images` or falls back to TMDb.
5. The UI displays the recommendation, summary, and poster.

## Technologies

- Python 3.11+
- FastAPI
- Uvicorn
- ChromaDB
- Google Gemini / `google-genai`
- python-dotenv
- Pillow

## Layout

```text
book_recommander/
├── app.py
├── chatbot.py
├── chroma_db/
├── frontend/
│   ├── index.html
│   ├── main.js
│   └── styles.css
├── generated_images/
├── language_filter.py
├── main.py
├── requirements.txt
└── README.md
```

## Setup & Run

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a `.env` file from `.env.example` and add your `GEMINI_API_KEY` and `TMDB_API_KEY`.

4. Start the app:

```powershell
uvicorn app:app --reload
```

5. Open `http://127.0.0.1:8000` in your browser.

## API Endpoints

- `POST /api/recommend` — returns a recommendation for a given `query` string.
- `POST /api/generate-image` — generates or returns a poster for a given title/summary.
- `POST /api/transcribe` — optional audio-to-text transcription endpoint.

## Notes

- Local images are preferred before any generative fallback.
- Keep API keys in `.env` and do not commit them.
- The project is intended as a local demo and for quick testing.
# Movie Recommender

Un proiect web de recomandare de filme construit cu FastAPI, Google Gemini și ChromaDB. Aplicația primește un prompt de la utilizator, recomandă un film relevant, afișează un rezumat și încarcă o imagine potrivită pentru acel film.

## Funcționalități

- Recomandare de filme pe bază de text
- Transcriere voce → text (în UI este activă opțiunea de recunoaștere vocală)
- Generare de text / recomandare în limbaj natural cu Gemini
- Generare de imagini pentru posterul filmului
- Afișare locală a posterelor din `generated_images`
- Fallback la TMDb pentru posteruri reale dacă nu există un local match
- Filtru de conținut pentru inputuri inadecvate
- Interfață web simplă în HTML/CSS/JS

## Exemple de flux

1. Utilizatorul scrie sau spune: „Vreau un film cu prietenie și magie.”
2. Backend-ul analizează query-ul și caută filme similare din ChromaDB.
3. Gemini generează recomandarea și rezumatul.
4. Aplicația selectează o imagine relevantă din `generated_images` sau fallback la TMDb.
5. UI-ul afișează filmul, rezumatul și posterul.

## Tehnologii

- Python 3.11+
- FastAPI
- Uvicorn
- ChromaDB
- Google Gemini / `google-genai`
- python-dotenv
- Pillow
- HTML / CSS / JavaScript

## Structura proiectului

```text
book_recommander/
├── app.py                  # aplicația FastAPI principală
├── chatbot.py              # utilități pentru ingestiarea datelor în ChromaDB
├── chroma_db/              # date persistente vectoriale
├── frontend/
│   ├── index.html
│   ├── main.js
│   └── styles.css
├── generated_images/       # imagini locale pentru posteruri relevante
├── language_filter.py      # filtrare inputuri neadecvate
├── main.py                 # entry point local / utilitar
├── requirements.txt        # dependențe Python
├── summaries.py            # rezumate de filme / fallback
├── token_counter.py        # logare consum de tokeni
├── .env.example            # model pentru variabile de mediu
├── .gitignore              # fișiere ignorate în Git
├── .env                    # chei reale locale (nu se publică)
├── README.md               # documentație proiectului
└── requirements.txt
```

## Configurare

1. Deschide terminalul în directorul proiectului:


2. Creează un mediu virtual:

```powershell
python -m venv .venv
```

3. Activează mediul virtual:

```powershell
.venv\Scripts\Activate.ps1
```

4. Instalează dependențele:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

5. Creează fișierul `.env` pe baza modelului din `.env.example`:

```env
GEMINI_API_KEY=your_gemini_key_here
TMDB_API_KEY=your_tmdb_key_here
```

## Rulare

În terminal, din directorul proiectului:

```powershell
uvicorn app:app --reload
```

Apoi deschide browserul la:

```text
http://127.0.0.1:8000
```

## Endpoints principale

### POST /api/recommend

Primește o cerere de tip text și returnează recomandarea filmului.

Request:

```json
{
  "query": "vreau un film cu prietenie și magie"
}
```

Response:

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

Generează sau returnează o imagine pentru un film dat.

Request:

```json
{
  "title": "Inception",
  "summary": "A thief who steals secrets from dreams..."
}
```

### POST /api/transcribe

Endpoint dedicat pentru transcriere audio → text. În această versiune poate fi folosit ca extensie, dar nu este necesar pentru fluxul principal.

## Observații

- Imaginile locale sunt preferate înainte de orice fallback generativ.
- Proiectul este conceput pentru demo local și pentru testare rapidă.
- Cheile API trebuie păstrate în `.env` și nu trebuie trimise în Git.



