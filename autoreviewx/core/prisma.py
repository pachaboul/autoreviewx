import re
import spacy
from sklearn.metrics.pairwise import cosine_similarity

nlp = spacy.load("en_core_web_md")

prisma_targets = {
    "prisma_objective": [
        "The objective of this review is",
        "This systematic review aims to"
    ],
    "prisma_eligibility_criteria": [
        "We included studies that",
        "Eligibility criteria were"
    ],
    "prisma_information_sources": [
        "Databases searched include",
        "We searched PubMed, Scopus"
    ],
    "prisma_search_strategy": [
        "The search strategy used was",
        "Boolean operators"
    ],
    "prisma_selection_process": [
        "Articles were screened",
        "Selection process was conducted"
    ],
    "prisma_data_collection": [
        "Data extraction was done",
        "Two reviewers extracted"
    ],
    "prisma_risk_of_bias": [
        "Risk of bias was assessed",
        "Using the ROB tool"
    ],
    "prisma_synthesis": [
        "Results were synthesized",
        "Meta-analysis was conducted"
    ],
    "prisma_limitations": [
        "This review has limitations",
        "We acknowledge potential biases"
    ],
    "prisma_registration": [
        "This review was registered",
        "PROSPERO ID"
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

def evaluate_prisma(text: str) -> dict:
    result = {}
    score = 0
    for key, phrases in prisma_targets.items():
        sim, passed = score_similarity(text, phrases)
        result[key] = passed
        score += 1 if passed else 0
    result["score_prisma"] = score  # Out of 10
    return result

def evaluate_prisma_semantic(text: str) -> dict:
    results = {}
    for key, phrases in prisma_targets.items():
        score, passed = score_similarity(text, phrases)
        results[f"{key}_score"] = score
        results[f"{key}_pass"] = passed
    return results

def prisma_global_score(metadata: dict) -> float:
    keys = [k for k in metadata if k.startswith("prisma_") and k.endswith("_pass")]
    return round(sum(metadata[k] for k in keys) / len(keys), 2) if keys else None
