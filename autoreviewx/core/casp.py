# autoreviewx/core/casp.py

import spacy
from sklearn.metrics.pairwise import cosine_similarity

# Load medium or large model with vectors for similarity scoring
nlp = spacy.load("en_core_web_md")  # make sure it's installed

# 🔹 Target phrases for CASP dimensions
casp_targets = {
    "casp_clear_aim": [
        "The aim of this study is to",
        "This research seeks to understand"
    ],
    "casp_methodology": [
        "This qualitative study",
        "We used qualitative methods",
        "A mixed-methods approach"
    ],
    "casp_recruitment": [
        "Participants were recruited",
        "We selected participants"
    ],
    "casp_ethics": [
        "Ethics approval was obtained",
        "Participants gave informed consent"
    ],
    "casp_analysis": [
        "Thematic analysis",
        "Grounded theory",
        "Content analysis"
    ],
    "casp_results_stated": [
        "Our findings indicate",
        "The results show",
        "The study found that"
    ],
    "casp_value": [
        "The implications of this study",
        "This research contributes to knowledge"
    ]
}

# 🔍 Compute similarity between text and CASP phrases
def score_similarity(text, targets, threshold=0.75):
    doc = nlp(text)
    best_score = 0.0
    for phrase in targets:
        target_doc = nlp(phrase)
        score = doc.similarity(target_doc)
        if score > best_score:
            best_score = score
    return round(best_score, 3), best_score >= threshold

# 🔍 Apply all CASP checks with scores
def evaluate_casp_semantic(text: str) -> dict:
    scores = {}
    for key, phrases in casp_targets.items():
        score, flag = score_similarity(text, phrases)
        scores[f"{key}_score"] = score
        scores[key] = flag
        #scores[f"{key}_pass"] = flag
    return scores
