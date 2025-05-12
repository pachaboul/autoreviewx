# autoreviewx/core/apa_formatter.py

def format_authors(authors_str):
    authors = authors_str.split(";")
    formatted = []
    for name in authors:
        parts = name.strip().split()
        if len(parts) >= 2:
            last = parts[-1]
            initials = " ".join([p[0] + "." for p in parts[:-1]])
            formatted.append(f"{last}, {initials}")
    return ", ".join(formatted)

def generate_apa_citation(entry):
    authors = format_authors(entry.get("authors", ""))
    year = entry.get("year", "n.d.")
    title = entry.get("title", "Untitled")
    journal = str(entry.get("journal") or entry.get("source_file") or "").replace("_", " ").replace(".pdf", "")
    doi = entry.get("doi", "")

    citation = f"{authors} ({year}). *{title}*. {journal}."
    if doi:
        citation += f" https://doi.org/{doi}"
    return citation
