# === MOVIE SUMMARIES DICTIONARY ===
# Dicționar cu rezumate complete pentru filme comune în baza de date
# Utilizat ca fallback când un film este recomandat dar nu are rezumat în baza vector

movie_summaries_dict = {
    "The Matrix": (
        "Neo descoperă că lumea în care trăiește este o simulare digitală creată pentru a controla omenirea. "
        "Alături de Trinity și Morpheus, începe să pună la îndoială realitatea și să lupte pentru libertate. "
        "Filmul combină acțiune, filozofie și o poveste despre conștiință și alegere."
    ),
    "The Lord of the Rings: The Fellowship of the Ring": (
        "Frodo moștenește un inel puternic, iar o misiune periculoasă îl obligă să plece într-o călătorie care va decide soarta lumii. "
        "Alături de prietenii săi, el înfruntă pericole, sacrificiu și tradiții vechi. "
        "Este un epic fantasy despre prietenie, curaj și responsabilitate."
    ),
    "Harry Potter and the Sorcerer's Stone": (
        "Harry află că este vrăjitor și este trimis la Hogwarts, unde întâlnește prietenia, magia și pericole ascunse. "
        "Pe măsură ce descoperă cine este, învață că curajul și apartenența sunt la fel de importante ca puterea."
    ),
    "Inception": (
        "Dom Cobb este un specialist în furtul de informații din vise. Intră în inima subconștientului unei persoane pentru a planta o idee care să schimbe lumea. "
        "Filmul este un labirint de realitate, vis și memorie, plin de tensiune și revelații."
    ),
    "Spirited Away": (
        "Chihiro se pierde într-o lume magică plină de spirite și provocări ciudate. Pentru a-și salva părinții, trebuie să devină curajoasă și să învețe să se adapteze la un univers nou. "
        "Este un film despre creștere, imaginație și puterea de a găsi un loc al tău."
    ),
    "The Dark Knight": (
        "Batman se confruntă cu Jokerul, un criminal fără reguli care testează granițele dintre justiție și haos. "
        "Filmul explorează moralitatea, sacrificiul și costul unei lupte fără compromisuri."
    ),
    "Finding Nemo": (
        "Marlin pleacă într-o călătorie periculoasă prin ocean pentru a-și găsi fiul dispărut. "
        "Pe drum întâlnește prieteni neobișnuiți și descoperă că curajul și încrederea pot schimba totul."
    ),
    "The Lion King": (
        "Simba trebuie să se confrunte cu trecutul și să își asumne destinul de rege. "
        "Povestea explorează familia, responsabilitatea și dorința de a merge mai departe după pierdere."
    ),
    "Toy Story": (
        "Woody și Buzz se confruntă cu gelozia, prietenia și nevoia de a accepta schimbarea. "
        "Filmul are un ton cald și plin de umor, iar tema sa principală este că prietenia este mai puternică decât rivalitatea."
    ),
    "Interstellar": (
        "O echipă de exploratori pleacă în spațiu pentru a găsi un nou loc în care omenirea să supraviețuiască. "
        "Filmul combină știință, emoție și o poveste profundă despre iubire, sacrificiu și speranță."
    )
}


def get_summary_by_title(title: str) -> str:
    """Caută rezumatul unui film după titlu (case-insensitive).
    Dacă nu găsește, returnează mesaj de eroare.
    Folosit ca fallback la generare pentru filme care nu au rezumat în vectorDB.
    """
    if title in movie_summaries_dict:
        return movie_summaries_dict[title]

    lower_title = title.lower().strip()
    for stored_title, summary in movie_summaries_dict.items():
        if stored_title.lower() == lower_title:
            return summary

    return "Rezumatul complet nu a fost găsit pentru acest titlu."