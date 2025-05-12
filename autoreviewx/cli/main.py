# autoreviewx/cli/main.py
import argparse
import re
import pandas as pd
import os
import spacy
from tqdm import tqdm
from datetime import datetime
from autoreviewx.core.config import load_config, ConfigError
from autoreviewx.core.extractor import extract_text_from_pdf

from autoreviewx.core.grobid_extractor import extract_metadata_with_grobid
from autoreviewx.core.grobid_extractor import extract_batch_metadata_with_grobid
from autoreviewx.core.enhanced_extraction import enrich_metadata, extract_title_candidates
from autoreviewx.cli.graphs import generate_graphs

# Charge le modèle spaCy une seule fois
nlp = spacy.load("en_core_web_sm")

def extract_year_from_text(text: str) -> str:
    match = re.search(r"(20[0-2][0-9])", text)
    return match.group(1) if match else ""

def extract_doi(text: str) -> str:
    match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', text, re.IGNORECASE)
    return match.group(1) if match else ""

def extract_authors(lines: list) -> str:
    stopwords = ["license", "open access", "copyright", "rights", "university", "school", "learning", "department"]
    best_candidate = ""
    max_count = 0

    for line in lines[:50]:  # Analyse les 50 premières lignes
        lowered = line.lower()
        if any(word in lowered for word in stopwords):
            continue

        # Extraire les "Prénom Nom" avec majuscules
        names = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+(?:\b|,)", line)
        if len(names) > max_count:
            max_count = len(names)
            best_candidate = line

    # Nettoyage des noms
    author_list = [a.strip(" ,;") for a in re.split(r"\||,| and ", best_candidate) if len(a.strip()) > 3]
    return "; ".join(author_list)

def extract_authors_with_ner(text: str) -> str:
    # Prendre seulement le début du texte (généralement là où les auteurs apparaissent)
    header_text = "\n".join(text.split("\n")[:100])

    # Nettoyer les lignes inutiles (licence, éditeurs, etc.)
    filtered_lines = []
    stopwords = ["license", "journal", "publisher", "open access", "rights", "doi", "abstract", "©"]
    for line in header_text.split("\n"):
        if any(bad in line.lower() for bad in stopwords):
            continue
        filtered_lines.append(line.strip())

    clean_text = " ".join(filtered_lines)

    doc = nlp(clean_text)
    people = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    unique_people = list(set([p.strip() for p in people if len(p.strip()) > 5]))

    return "; ".join(unique_people[:8])

def extract_metadata_from_text(text: str, source_file: str) -> dict:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    title_candidates = sorted(lines[:10], key=len, reverse=True)
    title = title_candidates[0] if title_candidates else ""

    abstract = ""
    for i, line in enumerate(lines):
        if "abstract" in line.lower():
            abstract = " ".join(lines[i + 1:i + 6])
            break

    keywords = []
    for line in lines:
        lowered = line.lower()
        if "keywords" in lowered or "index terms" in lowered:
            keyword_line = re.split(r":|—", line, maxsplit=1)[-1]
            keywords = [kw.strip().strip('.') for kw in keyword_line.split(",")]
            break

    # Heuristique d’auteurs
    authors = extract_authors(lines)
    if not authors or len(authors.split()) < 2:
        authors = extract_authors_with_ner(text)
    return {
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "year": extract_year_from_text(text),
        "keywords": "; ".join(keywords),
        "doi": extract_doi(text),
        "source_file": os.path.basename(source_file)
    }

def run_review(config_path):
    print(f"📄 Loading config from {config_path}...")
    config = load_config(config_path)
    print("✅ Configuration loaded successfully:")
    print(config)

def main():
    parser = argparse.ArgumentParser(
        prog="autoreviewx",
        description="AutoReviewX: Automate your systematic literature reviews"
    )
    subparsers = parser.add_subparsers(dest="command")

    parser_enhanced = subparsers.add_parser("extract-intelligent",
                                            help="Extract metadata using intelligent heuristics and NLP")
    parser_enhanced.add_argument("--pdf", type=str, required=True, help="Path to PDF file")

    parser_validate = subparsers.add_parser("validate-config", help="Validate a YAML protocol config file")
    parser_validate.add_argument("--path", type=str, default="config.yaml", help="Path to config file")

    parser_extract_with_config = subparsers.add_parser(
        "extract-with-config",
        help="Extract and filter metadata from PDFs using a review protocol config"
    )
    parser_extract_with_config.add_argument(
        "--config", type=str, default="config.yaml", help="Path to config file"
    )
    parser_extract_with_config.add_argument(
        "--dir", type=str, required=True, help="Directory containing PDFs to extract"
    )
    # Subcommand: run
    parser_run = subparsers.add_parser("run", help="Run AutoReviewX pipeline with config.yaml")
    parser_run.add_argument("--config", type=str, default="config.yaml", help="Path to YAML config file")

    parser_extract_grobid_batch = subparsers.add_parser("extract-grobid-batch",
                                                        help="Batch extract metadata using GROBID")
    parser_extract_grobid_batch.add_argument("--dir", type=str, required=True, help="Directory containing PDF files")

    # Subcommand: extract
    parser_extract = subparsers.add_parser("extract", help="Extract metadata from a PDF")
    parser_extract.add_argument("--pdf", type=str, required=True, help="Path to PDF file")

    # Subcommand: extract-grobid
    parser_extract_grobid = subparsers.add_parser("extract-grobid", help="Extract metadata using GROBID")
    parser_extract_grobid.add_argument("--pdf", type=str, required=True, help="Path to PDF file")

    parser_extract_grobid_batch_percent = subparsers.add_parser(
        "extract-grobid-batch-percent", help="Batch extract metadata using GROBID with progress feedback"
    )
    parser_extract_grobid_batch_percent.add_argument("--dir", type=str, required=True,
                                                     help="Directory containing PDF files")

    #APA generator
    parser_apa = subparsers.add_parser("generate-apa", help="Generate APA 7 references from metadata CSV")
    parser_apa.add_argument("--input", type=str, required=True, help="Path to extracted metadata CSV")

    # Command: graphs
    parser_graphs = subparsers.add_parser('graphs', help='Generate quality framework visualizations')
    parser_graphs.add_argument('--input', '-i', required=True, help='CSV file with metadata')
    parser_graphs.add_argument('--output', '-o', default='output/graphs', help='Output directory for graphs')

    args = parser.parse_args()

    if args.command == 'graphs':
        generate_graphs(args.input, args.output)
    else:
        parser.print_help()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

    args = parser.parse_args()

    os.makedirs("data/extracted", exist_ok=True)

    columns = [
        "title", "data_used", "models_used", "tools_used", "keywords",
        "participants", "participants_count",
        "biological_data", "physiological_data", "methodology",
        "transparency", "accuracy", "purposivity",
        "utility", "propriety", "accessibility", "specificity",
        "score_tapupas",
        "population", "intervention", "comparison", "outcome",
        "score_pico",
        "casp_clear_aim", "casp_methodology", "casp_recruitment",
        "casp_ethics", "casp_analysis", "casp_results_stated", "casp_value",
        "casp_clear_aim_score", "casp_clear_aim_pass",
        "casp_methodology_score", "casp_methodology_pass",
        "casp_recruitment_score", "casp_recruitment_pass",
        "casp_ethics_score", "casp_ethics_pass",
        "casp_analysis_score", "casp_analysis_pass",
        "casp_results_stated_score", "casp_results_stated_pass",
        "casp_value_score", "casp_value_pass",
        "score_casp",
        "kitch_research_question", "kitch_study_context", "kitch_data_collection",
        "kitch_data_analysis", "kitch_validity", "kitch_replication", "kitch_contribution",
        "kitch_research_question_score", "kitch_research_question_pass",
        "kitch_search_strategy_score", "kitch_search_strategy_pass",
        "kitch_inclusion_criteria_score", "kitch_inclusion_criteria_pass",
        "kitch_data_extraction_score", "kitch_data_extraction_pass",
        "kitch_quality_assessment_score", "kitch_quality_assessment_pass",
        "kitch_data_synthesis_score", "kitch_data_synthesis_pass",
        "kitch_limitations_score", "kitch_limitations_pass",
        "score_kitchenham",
        # Add to your CSV export columns list
        "score_prisma",
        "prisma_objective_pass",
        "prisma_eligibility_criteria_pass",
        "prisma_information_sources_pass",
        "prisma_search_strategy_pass",
        "prisma_selection_process_pass",
        "prisma_data_collection_pass",
        "prisma_risk_of_bias_pass",
        "prisma_synthesis_pass",
        "prisma_limitations_pass",
        "prisma_registration_pass",
        "title_source", "authors", "abstract", "abstract_length",
        "doi", "year", "journal", "keywords",
        "target_education_level",   "countries",
        "source_file",
    ]

    if args.command == "run":
        run_review(args.config)

    elif args.command == "extract":
        text = extract_text_from_pdf(args.pdf)
        metadata = extract_metadata_from_text(text, args.pdf)

        print("\n✅ Metadata extracted:")
        for key, value in metadata.items():
            print(f"{key.capitalize()}: {value}")

        output_path = f"data/extracted/metadata_{timestamp}.csv"
        df = pd.DataFrame([metadata])
        if os.path.exists(output_path):
            df.to_csv(output_path, mode="a", header=False, index=False)
        else:
            df.to_csv(output_path, index=False)
        print(f"\n📄 Saved to {output_path}")

    elif args.command == "generate-apa":
        from autoreviewx.core.apa_formatter import generate_apa_citation
        df = pd.read_csv(args.input)
        citations = df.apply(generate_apa_citation, axis=1)

        output_path = f"data/extracted/apa_references_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            for c in citations:
                f.write(c + "\n\n")
        print(f"📚 APA references saved to {output_path}")

    elif args.command == "extract-grobid":
        metadata = extract_metadata_with_grobid(args.pdf)

        print("\n✅ GROBID Metadata extracted:")
        for key, value in metadata.items():
            print(f"{key.capitalize()}: {value}")

        output_path = f"data/extracted/metadata_grobid_{timestamp}.csv"
        #output_path = "data/extracted/metadata_enriched.csv"

        df = pd.DataFrame([metadata], columns=columns)
        if os.path.exists(output_path):
            df.to_csv(output_path, mode="a", header=False, index=False)
        else:
            df.to_csv(output_path, index=False)
        print(f"\n📄 Saved to {output_path}")

    elif args.command == "extract-with-config":
        try:
            config = load_config(args.config)
        except Exception as e:
            print(f"❌ Config error: {e}")
            return

        results = []
        for file in os.listdir(args.dir):
            if not file.lower().endswith(".pdf"):
                continue
            path = os.path.join(args.dir, file)
            print(f"🔍 Processing {file}...")
            data = extract_metadata_with_grobid(path)

            # Filtres d’inclusion basés sur config (ex: langue, outil, etc.)
            text = " ".join([data.get("abstract", ""), data.get("title", "")]).lower()
            skip = False
            for excl in config.get("exclusion_criteria", []):
                if excl.lower() in text:
                    skip = True
            if skip:
                print(f"⚠️  Excluded by criteria → {file}")
                continue

            results.append(data)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"data/extracted/filtered_metadata_{timestamp}.csv"
        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False)
        print(f"\n📄 Saved filtered metadata to {output_path}")


    elif args.command == "validate-config":
        try:
            cfg = load_config(args.path)
            print("✅ Config is valid.")
        except ConfigError as e:
            print(f"❌ Config validation failed:\n{e}")

    elif args.command == "extract-grobid-batch":

        results = extract_batch_metadata_with_grobid(args.dir)

        print(f"\n✅ Batch metadata extracted for {len(results)} files.")

        os.makedirs("data/extracted", exist_ok=True)
        output_path = f"data/extracted/metadata_grobid_enriched_{timestamp}.csv"

        df = pd.DataFrame(results, columns=columns)
        df.to_csv(output_path, index=False)
        print(f"📄 Saved batch metadata to {output_path}")

    elif args.command == "extract-grobid-batch-percent":
        pdf_files = [f for f in os.listdir(args.dir) if f.lower().endswith(".pdf")]
        total_files = len(pdf_files)
        results = []

        print(f"\n📦 Found {total_files} PDF(s) in: {args.dir}")

        for i, file in enumerate(tqdm(pdf_files, desc="🔄 Extracting", unit="pdf"), 1):
            pdf_path = os.path.join(args.dir, file)
            try:
                data = extract_metadata_with_grobid(pdf_path)
                results.append(data)
            except Exception as e:
                print(f"\n❌ Failed to process {file}: {e}")
                continue

            percent = (i / total_files) * 100
            print(f"✅ {i}/{total_files} processed ({percent:.1f}%) → {file}")

        os.makedirs("data/extracted", exist_ok=True)
        output_path = f"data/extracted/metadata_grobid_enriched_{timestamp}.csv"

        df = pd.DataFrame(results, columns=columns)
        df.to_csv(output_path, index=False)
        print(f"\n📄 Saved batch metadata to {output_path}")

    elif args.command == "extract-intelligent":
        text = extract_text_from_pdf(args.pdf)
        lines = text.split("\n")
        title, title_source = extract_title_candidates(lines)
        semantic = enrich_metadata(text)

        metadata = {
            "title": title,
            "title_source": title_source,
            **semantic,
            "source_file": os.path.basename(args.pdf)
        }

        print("\n✅ Enhanced Metadata extracted:")
        for key, value in metadata.items():
            print(f"{key}: {value}")

        os.makedirs("data/extracted", exist_ok=True)
        output_path = f"data/extracted/intelligent_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df = pd.DataFrame([metadata])
        df.to_csv(output_path, index=False)
        print(f"\n📄 Saved to {output_path}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
