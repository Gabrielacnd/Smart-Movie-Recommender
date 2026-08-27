"""
Language filter module for detecting and handling inappropriate content.
Provides functionality to detect offensive words and respond politely without sending to LLM.
"""

import re
from typing import Tuple

# List of offensive/profane words in Romanian and English
# Organized by category for easier maintenance
OFFENSIVE_WORDS = {
    # Romanian profanities
    "romanian": [
        "rahat", "căcat", "cacat", "caca", "pipă", "pizdă", "pizda", "pizdos", "pulă", "pula", "futu", "futut",
        "futuți", "futu-ti", "muie", "cur", "curvă", "curva", "curve", "curvă", "tâmpit", "tâmpită", "prost",
        "proastă", "proști", "proaste", "idiot", "idioată", "imbecil", "cretin", "cretină", "nenorocit",
        "nenorocită", "drac", "drace", "dracul", "dracului", "blestem", "jeg", "jegul", "marcă", "gunoi",
        "porc", "porcă", "scroafă", "mârlan", "mârlană", "golan", "golană", "găozar", "golănaș", "babă",
        "muist", "muistă", "pulă", "șmecher", "tâmpenie", "măgăoaie", "păcătos", "dracului", "sictir",
        "jegos", "trădător", "țâță", "curvar", "penis", "pizdar", "boschetar", "idiotule", "proștilor"
    ],
    # English profanities
    "english": [
        "shit", "damn", "crap", "ass", "bitch", "bastard", "idiot", "stupid", "dumb",
        "fuck", "fucked", "fucking", "cock", "pussy", "cunt", "whore", "slut",
        "dick", "asshole", "motherfucker", "hell", "piss", "bullshit", "fart"
    ]
}

def create_pattern() -> re.Pattern:
    """
    Create a compiled regex pattern for detecting offensive words.
    Uses word boundaries to avoid partial matches.
    """
    # Combine all offensive words from all categories
    all_words = []
    for category in OFFENSIVE_WORDS.values():
        all_words.extend(category)
    
    # Create a pattern with word boundaries and case-insensitive matching
    pattern_str = r"\b(" + "|".join(re.escape(word) for word in all_words) + r")\b"
    return re.compile(pattern_str, re.IGNORECASE)

# Precompile the pattern for efficiency
OFFENSIVE_PATTERN = create_pattern()

# Răspunsuri politoase când se detectează limbaj nepotrivit
# Selectate aleatoriu pentru variație
POLITE_RESPONSES = [
    "Apreciez că vrei să obții o recomandare, dar aș prefera ca mesajul tău să nu conțină cuvinte ofensatoare. 🎬 Poți reformula, te rog?",
    "Înțeleg că ai emoții, dar aș aprecia un ton mai politicos. 😊 Poți reformula întrebarea fără cuvinte dure?",
    "Sunt aici să te ajut cu recomandări de filme, dar cu un limbaj respectuos. 🎬 Ce tip de film îți interesează?",
    "Cuvintele dure nu ne ajută în conversație. 💭 Poți cere un film în mod politicos?",
]

def contains_inappropriate_language(text: str) -> Tuple[bool, str]:
    """
    Check if text contains inappropriate/offensive language.
    
    Args:
        text (str): The text to check
        
    Returns:
        Tuple[bool, str]: (has_inappropriate_content, polite_response)
    """
    # Check if the text contains offensive words
    if OFFENSIVE_PATTERN.search(text):
        return True, POLITE_RESPONSES[0]
    return False, ""

def get_filtered_input(text: str) -> Tuple[bool, str, str]:
    """
    Process user input and check for inappropriate language.
    
    Args:
        text (str): User input text
        
    Returns:
        Tuple[bool, str, str]: (is_inappropriate, response, cleaned_text)
                              - is_inappropriate: Whether content is flagged
                              - response: Polite response if flagged, empty otherwise
                              - cleaned_text: Original text for processing
    """
    is_inappropriate, response = contains_inappropriate_language(text)
    return is_inappropriate, response, text
