 # Movie Recommender

 Un proiect web de recomandare de filme construit cu FastAPI, Google Gemini și ChromaDB. Aplicația primește un prompt de la utilizator, recomandă un film relevant, afișează un rezumat și încarcă o imagine potrivită pentru acel film.

 ## Funcționalități

 - Recomandare de filme pe bază de text
 - Transcriere voce → text (în UI este activă opțiunea de recunoaștere vocală)
 - Generare de text / recomandare în limbaj natural cu Gemini
 - Generare de imagini pentru posterul filmului
 - Afișare locală a posterelor din `generated_images`
 - Fallback la TMDb pentru posteruri reale dacă nu există un local match
 - Filtru de conținut pentru inputuri inadecvate (am integrat un filtru bazat pe expresii regulate - regex - pentru a opri limbajul urât)
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



