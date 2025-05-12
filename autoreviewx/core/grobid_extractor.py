# autoreviewx/core/grobid_extractor.py
import requests
from bs4 import BeautifulSoup
import os
import re

from autoreviewx.core.tapupas import evaluate_tapupas
from autoreviewx.core.casp import evaluate_casp_semantic
from autoreviewx.core.kitchenham import evaluate_kitchenham
from autoreviewx.core.kitchenham import evaluate_kitchenham_semantic
from autoreviewx.core.kitchenham import evaluate_kitchenham_all
from autoreviewx.core.prisma import evaluate_prisma_semantic, prisma_global_score
from autoreviewx.core.prisma import evaluate_prisma



def load_keywords(filename: str) -> list:
    path = os.path.join(os.path.dirname(__file__), "../resources/keywords", filename)
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]

# 🔍 Détection de lignes de type "auteurs"
def looks_like_author_line(text):
    name_count = len(re.findall(r"\b[A-Z][a-z]+\b", text))
    comma_count = text.count(',')
    return name_count > 4 and comma_count > 2

def extract_title_from_soup(soup):
    title = ""
    title_source = "unknown"

    analytic = soup.find('analytic')
    if analytic:
        title_tag = analytic.find('title')
        if title_tag:
            title = title_tag.text.strip()
            title_source = "analytic"

    if not title:
        title_stmt = soup.find('titleStmt')
        if title_stmt:
            title_tag = title_stmt.find('title')
            if title_tag:
                title = title_tag.text.strip()
                title_source = "titleStmt"

    if (
        not title or
        title.lower().startswith("date of publication") or
        "xxxx" in title.lower() or
        "citations" in title.lower() or
        "see profile" in title.lower() or
        "publications" in title.lower() or
        looks_like_author_line(title)
    ):
        body_text = soup.find('body').get_text(separator="\n") if soup.find('body') else ""
        body_lines = body_text.strip().split("\n")
        researchgate = any("researchgate" in line.lower() for line in body_lines[:30])
        if researchgate:
            for i in range(30, 100):
                line = body_lines[i].strip()
                if (
                    len(line.split()) >= 5 and
                    not looks_like_author_line(line) and
                    not line.lower().startswith("abstract")
                ):
                    next_line = body_lines[i + 1].lower() if i + 1 < len(body_lines) else ""
                    if "abstract" in next_line or "introduction" in next_line:
                        title = line
                        title_source = "fallback"
                        break

        if not title:
            title = "UNKNOWN TITLE"
            title_source = "unknown"

    return title, title_source

def evaluate_casp(text: str) -> dict:
    dimensions = {
        "casp_clear_aim": bool(re.search(r"\b(aim|purpose) of this (study|research)\b", text.lower())),
        "casp_methodology": "qualitative" in text.lower(),
        "casp_recruitment": "participants were" in text.lower() or "we recruited" in text.lower(),
        "casp_ethics": "ethics approval" in text.lower() or "informed consent" in text.lower(),
        "casp_analysis": re.search(r"(thematic analysis|content analysis|grounded theory)", text.lower()) is not None,
        "casp_results_stated": "results show" in text.lower() or "findings indicate" in text.lower(),
        "casp_value": "implications" in text.lower() or "contribution to knowledge" in text.lower()
    }
    return dimensions

def casp_global_score(metadata):
    keys = [k for k in metadata if k.startswith("casp_") and k.endswith("_pass")]
    return round(sum(metadata[k] for k in keys) / len(keys), 2) if keys else None

def kitchenham_global_score(metadata):
    keys = [k for k in metadata if k.startswith("kitch_") and k.endswith("_pass")]
    return round(sum(metadata[k] for k in keys) / len(keys), 2) if keys else None

def tapupas_score(metadata):
    tap_keys = ["transparency", "accuracy", "purposivity", "utility", "propriety", "accessibility", "specificity"]
    scores = [metadata.get(k, 0) for k in tap_keys]
    return round(sum(scores) / (2 * len(tap_keys)), 2) if scores else None

def pico_score(metadata):
    keys = ["population", "intervention", "comparison", "outcome"]
    present = sum(bool(metadata.get(k)) for k in keys)
    return round(present / len(keys), 2)

def extract_metadata_with_grobid(pdf_path: str) -> dict:
    url = "http://localhost:8070/api/processFulltextDocument"

    with open(pdf_path, 'rb') as file:
        files = {'input': file}
        response = requests.post(url, files=files)

    if response.status_code != 200:
        return {"error": f"GROBID extraction failed with status {response.status_code}"}

    soup = BeautifulSoup(response.text, 'xml')


    # 🔹 Titre via fonction unifiée
    #title = extract_title_from_soup(soup)
    title, title_source = extract_title_from_soup(soup)

    # 🔹 DOI
    doi_tag = soup.find('idno', {'type': 'DOI'})
    doi = doi_tag.text.strip() if doi_tag else ""

    # 🔹 Auteurs
    authors = []
    analytic = soup.find('analytic')
    if analytic:
        for author in analytic.find_all('author'):
            pers = author.find('persName')
            if pers:
                forename = " ".join(f.text for f in pers.find_all('forename'))
                surname = " ".join(s.text for s in pers.find_all('surname'))
                full_name = f"{forename} {surname}".strip()
                if full_name:
                    authors.append(full_name)

    # 🔹 Résumé
    abstract_tag = soup.find('abstract')
    abstract_text = abstract_tag.get_text(separator=" ") if abstract_tag else ""

    # 🔹 Texte complet pour NLP
    fulltext_node = soup.find('body')
    fulltext = fulltext_node.get_text(separator=" ") if fulltext_node else ""
    sample_info = extract_samples(fulltext)

    casp_info = evaluate_casp(fulltext)
    casp_semantic = evaluate_casp_semantic(fulltext)
    kitchenham_info = evaluate_kitchenham_all(fulltext)
    prisma_info = evaluate_prisma_semantic(fulltext)

    # ✅ Normalize the _pass fields to match expected column names
    for key in list(casp_semantic.keys()):
        if key.endswith("_pass"):
            base = key.replace("_pass", "")
            casp_semantic[base] = casp_semantic.pop(key)

    # 🔹 Année (simple heuristique sur <imprint> ou le corps)
    year_tag = soup.find('date')
    year = ""
    if year_tag:
        year = re.search(r"(20[0-2][0-9])", year_tag.text or "")
        year = year.group(1) if year else ""

    # 🔹 Journal ou conférence
    journal = ""
    monogr = soup.find('monogr')
    if monogr and monogr.find('title'):
        journal = monogr.find('title').text.strip()

    # 🔹 Mots-clés (keywords ou index terms)
    keywords = []
    for kw in soup.find_all('keywords'):
        for term in kw.find_all('term'):
            keywords.append(term.text.strip())

    # 🔹 Analyse sémantique
    semantic_info = extract_semantic_content(fulltext)
    sample_info = extract_samples(fulltext)
    pico_info = extract_pico(fulltext)

    return {
        "title": title,
        "abstract": abstract_text,
        "authors": "; ".join(authors),
        "doi": doi,
        "source_file": os.path.basename(pdf_path),
        **semantic_info,
        **sample_info,
        **pico_info,
       # **evaluate_casp_semantic(fulltext),
        **casp_info,
        **casp_semantic,
        **kitchenham_info,
        **evaluate_prisma(fulltext),
        **prisma_info,
        "score_prisma": prisma_global_score(prisma_info),
        "year": year,
        "journal": journal,
        "keywords": "; ".join(keywords),
        "abstract_length": len(abstract_text.split()),
        "title_source": title_source,
        **evaluate_tapupas(fulltext),
    }

    # ✅ Add global scores
    metadata["score_tapupas"] = tapupas_score(metadata)
    metadata["score_casp"] = casp_global_score(metadata)
    metadata["score_kitchenham"] = kitchenham_global_score(metadata)
    metadata["score_pico"] = pico_score(metadata)

    return metadata


def extract_samples(text: str) -> dict:
    lower_text = text.lower()

    # Look for patterns with a number followed by participant terms
    patterns = [
        r"\b(?:n\s*=\s*|N\s*=\s*)(\d+)",                     # n = 30
        r"\b(\d+)\s+(participants|students|subjects|learners|respondents|teachers)\b",  # 30 participants
        r"\ba total of (\d+)\s+(participants|students|subjects|respondents)\b",         # a total of 15 students
    ]

    matches = []
    for pattern in patterns:
        found = re.findall(pattern, lower_text)
        if found:
            for m in found:
                if isinstance(m, tuple):
                    matches.append(m[0])
                else:
                    matches.append(m)

    # Keep the max count as the likely sample size
    numbers = [int(m) for m in matches if m.isdigit()]
    participants_count = max(numbers) if numbers else ""

    # Also capture keywords (non-numeric info)
    keywords = set()
    for word in ["participants", "students", "subjects", "learners", "respondents", "teachers"]:
        if word in lower_text:
            keywords.add(word)

    return {
        "participants": "; ".join(sorted(keywords)),
        "participants_count": participants_count
    }

def extract_pico(text: str) -> dict:
    pico = {
        "population": "",
        "intervention": "",
        "comparison": "",
        "outcome": ""
    }

    lower_text = text.lower()

    # Simple heuristics to extract basic phrases (expand later)
    # These are just starting points
    pop_match = re.search(r"(students|learners|participants|teachers|subjects|children|users|respondents)", lower_text)
    int_match = re.search(r"(using|with|through|via) ([a-zA-Z\- ]{3,30})", lower_text)
    comp_match = re.search(r"(compared to|versus|vs\.|without) ([a-zA-Z\- ]{3,30})", lower_text)
    out_match = re.search(r"(measured|evaluated|assessed|improved) ([a-zA-Z\- ]{3,30})", lower_text)

    if pop_match:
        pico["population"] = pop_match.group(1)
    if int_match:
        pico["intervention"] = int_match.group(2).strip()
    if comp_match:
        pico["comparison"] = comp_match.group(2).strip()
    if out_match:
        pico["outcome"] = out_match.group(2).strip()

    return pico

def extract_semantic_content(text: str) -> dict:
    lower_text = text.lower()

    def find_keywords(keywords):
        return "; ".join(sorted(set([
            k for k in keywords if k.lower() in lower_text
        ])))

    biological_keywords = load_keywords("biological_data.txt")
    physiological_keywords = load_keywords("physiological_data.txt")
    data_used_keywords = load_keywords("data_used_keywords.txt")
    models_keywords = load_keywords("models_keywords.txt")
    tools_keywords = load_keywords("tools_keywords.txt")
    levels_keywords = load_keywords("levels_keywords.txt")
    countries_keywords = load_keywords("countries_keywords.txt")

    # Méthodologie améliorée
    if any(word in lower_text for word in ["interview", "focus group", "observation", "qualitative"]):
        methodology = "qualitative"
    elif any(word in lower_text for word in ["experiment", "survey", "controlled", "quantitative", "statistical analysis"]):
        methodology = "quantitative"
    elif "mixed method" in lower_text or "mixed-method" in lower_text:
        methodology = "mixed"
    else:
        methodology = "unknown"

    return {
        "data_used": find_keywords(data_used_keywords),
        "models_used": find_keywords(models_keywords),
        "tools_used": find_keywords(tools_keywords),
        "target_education_level": find_keywords(levels_keywords),
        "countries": find_keywords(countries_keywords),
        "methodology": methodology,
        "biological_data": find_keywords(biological_keywords),
        "physiological_data": find_keywords(physiological_keywords),
    }

def extract_batch_metadata_with_grobid(folder_path: str) -> list:
    results = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(folder_path, filename)
            try:
                print(f"🔍 Processing {filename}...")
                data = extract_metadata_with_grobid(pdf_path)
                results.append(data)
            except Exception as e:
                print(f"❌ Failed to process {filename}: {e}")
    return results