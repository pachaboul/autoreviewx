# autoreviewx/core/kitchenham.py

import spacy
from sklearn.metrics.pairwise import cosine_similarity

# Load medium model with word vectors
nlp = spacy.load("en_core_web_md")

kitch_targets = {
    "kitch_research_question": [
        "The research question is clearly stated",
        "This study investigates..."
    ],
    "kitch_search_strategy": [
        "We used a systematic search strategy",
        "Databases searched include..."
    ],
    "kitch_inclusion_criteria": [
        "Inclusion criteria were defined as...",
        "Studies were included based on..."
    ],
    "kitch_data_extraction": [
        "Data were extracted using a predefined form",
        "Two researchers extracted data independently"
    ],
    "kitch_quality_assessment": [
        "We assessed the quality of each study",
        "Risk of bias was evaluated"
    ],
    "kitch_data_synthesis": [
        "Data synthesis was performed using...",
        "We conducted a meta-analysis"
    ],
    "kitch_limitations": [
        "This study has some limitations",
        "We acknowledge limitations such as..."
    ]
}

def score_similarity(text, targets, threshold=0.75):
    doc = nlp(text)
    best_score = 0.0
    for phrase in targets:
        phrase_doc = nlp(phrase)
        score = doc.similarity(phrase_doc)
        if score > best_score:
            best_score = score
    return round(best_score, 3), best_score >= threshold

def evaluate_kitchenham_semantic(text: str) -> dict:
    results = {}
    for key, phrases in kitch_targets.items():
        score, passed = score_similarity(text, phrases)
        results[f"{key}_score"] = score
        results[f"{key}_pass"] = passed
    return results

def evaluate_kitchenham(text: str) -> dict:
    lower = text.lower()
    return {
        "kitch_research_question": "research question" in lower or "we investigate" in lower,
        "kitch_study_context": "in this context" in lower or "study was conducted" in lower,
        "kitch_data_collection": "data were collected" in lower or "survey" in lower or "interview" in lower,
        "kitch_data_analysis": "we analyzed" in lower or "data analysis" in lower,
        "kitch_validity": "threat to validity" in lower or "internal validity" in lower,
        "kitch_replication": "replicated" in lower or "replication" in lower,
        "kitch_contribution": "our contribution" in lower or "we propose" in lower
    }

def evaluate_kitchenham_all(text: str) -> dict:
    return {
        **evaluate_kitchenham(text),
        **evaluate_kitchenham_semantic(text)
    }

