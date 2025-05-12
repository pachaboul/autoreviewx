# enhanced_extraction.py (corrigé)

import re
import spacy
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# ✅ Load larger spaCy model for better similarity (has vectors)
nlp = spacy.load("en_core_web_md")  # Assure-toi que ce modèle est installé

# Clusters manuels
CLUSTERS = {
    "multimodal_sensing": ["eye tracking", "EEG", "biosignal", "sensor"],
    "LLMs": ["gpt", "bert", "transformer", "llm", "language model"],
    "AI_in_Education": ["adaptive learning", "feedback", "engagement"]
}


def find_keywords_scored(text, keywords):
    doc = nlp(text)
    results = []
    for kw in keywords:
        kw_vec = nlp(kw)
        sim = doc.similarity(kw_vec)
        if sim > 0.75:
            results.append(kw)
    return {k: 1.0 for k in results}

def assign_cluster_from_keywords(keywords):
    assigned = set()
    for cluster, terms in CLUSTERS.items():
        if any(k in terms for k in keywords):
            assigned.add(cluster)
    return "; ".join(sorted(assigned)) or "unclustered"


def detect_goal(text):
    patterns = [
        r"(this|the) (paper|study|work).*?(aims|seeks|attempts) to ([^.\\n]+)",
        r"we (propose|present|develop) ([^.\\n]+)",
        r"our (goal|objective).*?is to ([^.\\n]+)",
        r"the purpose of this (paper|study).*?is to ([^.\\n]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return "not detected"


def detect_field(text):
    fields = ["education", "health", "engineering", "linguistics", "psychology", "robotics"]
    doc = nlp(text.lower())
    field_scores = [(f, doc.similarity(nlp(f))) for f in fields]
    return max(field_scores, key=lambda x: x[1])[0] if field_scores else "unknown"


def extract_title_candidates(lines):
    joined = [l.strip() for l in lines[:150] if len(l.strip().split()) >= 5]
    for i, line in enumerate(joined):
        if any(x in line.lower() for x in ["abstract", "introduction", "citations", "conference paper"]):
            continue
        doc = nlp(line)
        if sum(1 for token in doc if token.pos_ == "VERB") == 0:
            return line.strip(), "fallback_body"
    return "UNKNOWN TITLE", "unknown"

def enrich_metadata(text):
    lower_text = text.lower()

    biological_terms = ["genome", "dna", "rna", "biomarker", "proteomics"]
    physio_terms = ["eye tracking", "eeg", "sensor", "gaze"]
    model_terms = ["gpt", "bert", "transformer", "cnn", "lstm"]
    tool_terms = ["tensorflow", "pytorch", "moodle", "opencv", "excel"]

    bio_scores = find_keywords_scored(lower_text, biological_terms)
    physio_scores = find_keywords_scored(lower_text, physio_terms)
    model_scores = find_keywords_scored(lower_text, model_terms)
    tool_scores = find_keywords_scored(lower_text, tool_terms)

    all_keywords = list(bio_scores.keys() | physio_scores.keys() | model_scores.keys() | tool_scores.keys())
    clusters = assign_cluster_from_keywords(all_keywords)
    goal = detect_goal(text)
    field = detect_field(text)

    return {
        "biological_keywords": "; ".join(bio_scores.keys()),
        "physiological_keywords": "; ".join(physio_scores.keys()),
        "models_used": "; ".join(model_scores.keys()),
        "tools_used": "; ".join(tool_scores.keys()),
        "clusters": clusters,
        "research_goal": goal,
        "field": field,
    }
