INTERROGATIVES = {
    "what", "why", "how", "when", "where",
    "which", "who"
}

AUXILIARY_VERBS = {
    "do", "does", "did",
    "have", "has",
    "can", "could",
    "would", "will",
    "should", "are", "is"
}

IMPERATIVE_PREFIXES = (
    "explain",
    "describe",
    "tell me",
    "walk me through",
    "talk about",
)

def confidence_score(text: str) -> float:
    score = 0.0
    t = text.lower()
    words = t.split()

    if len(words) >= 6:
        score += 0.2

    if any(w in t for w in INTERROGATIVES):
        score += 0.3
        
    if any(v in words for v in AUXILIARY_VERBS):
        score += 0.3
    
    if t.startswith(IMPERATIVE_PREFIXES):
        score += 0.2      
    
    return min(score, 1.0)
