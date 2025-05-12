# 🤖 AutoReviewX

**An Intelligent, Modular, and Multi-Framework Platform for Automating Systematic Literature Reviews (SLRs)**

---

## 🔍 Overview

**AutoReviewX** is an open-source platform that automates the complete workflow of conducting a Systematic Literature Review (SLR), from protocol definition to final report generation. It supports multiple methodological frameworks (e.g., PRISMA, PICO, TAPUPAS) and is tailored for engineering and applied research domains, including:

- 🧠 Artificial Intelligence in Education
- 🖥️ Human-Computer Interaction (HCI)
- 💻 Software Engineering
- 📊 Multimodal Learning Analytics

The platform is modular and scalable — usable via CLI (v1.0), GUI (v1.5), or Web API (v2.0+).

---

## 🧠 Core Features

| Feature                      | Description                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| ✅ Protocol-based reviews    | Define structure using a YAML config (questions, inclusion/exclusion, etc.) |
| 📄 Metadata extraction       | Automatic from PDF/DOI using GROBID, CrossRef, or NLP enrichment            |
| 📚 Citation formatting       | APA 7 (v1.0), IEEE/ACM/MLA (v2.0)                                           |
| 🧪 Quality assessment        | TAPUPAS, CASP, Kitchenham, PRISMA scoring                                   |
| 📊 Graph generation          | PRISMA Flow, PICO bar chart, CASP radar, TAPUPAS score chart                |
| 📤 Report export             | Output in Markdown, CSV, BibTeX, JSON, PDF                                  |
| 🔌 Extensibility             | Add your own screening rubrics, graphs, formats                             |
| 🧪 Testing support           | Unit tests included for key modules                                         |

---

## 🏗️ Project Structure

```text
AutoReviewX/
├── cli/              # CLI commands (e.g., run, extract, cite, report)
├── core/             # Core processing modules (extractor, prisma, etc.)
│   ├── extractor.py
│   ├── screening.py
│   ├── visualizer.py
│   ├── prisma.py
│   ├── citations/
│   └── protocols/
├── gui/              # Streamlit-based GUI (v1.5+)
├── web/              # FastAPI Web backend (v2.0+)
├── data/             # Input/output data: PDFs, metadata, graphs
├── tests/            # Unit and integration tests
├── config.yaml       # YAML configuration file for your review
├── requirements.txt  # Python dependencies
├── setup.py          # Packaging info for pip installation
└── README.md         # Project documentation


🧾 Step 1 – Metadata Extraction
# Basic batch extraction using GROBID
autoreviewx extract-grobid-batch --dir data/raw_pdfs/

# Enriched extraction with NLP (tools, participants, models used, etc.)
autoreviewx extract-intelligent --pdf path/to/document.pdf

# Config-based extraction using filters and review protocol
autoreviewx extract-with-config --config config.yaml --dir data/raw_pdfs/

📝 Step 2 – Generate APA References
autoreviewx generate-apa --input data/extracted/metadata_file.csv

📈 Step 3 – Generate Graphs and Visual Insights
autoreviewx graphs --input data/extracted/metadata_enriched.csv

Supported charts include:

    PRISMA checklist heatmaps
    PICO bar charts
    CASP radar graphs
    TAPUPAS trustworthiness bars
    Kitchenham-style radar charts


📦 Step 4 – Generate Full Report
autoreviewx report --format markdown

🧪 Testing
pytest tests/

🛠️ Installation
git clone https://github.com/pachaboul/autoreviewx.git
cd autoreviewx
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

🤝 Contributing

We welcome contributions! To contribute:

    Fork the repo

    Create a branch: git checkout -b my-feature

    Commit your changes

    Push to the branch: git push origin my-feature

    Create a pull request

📄 License

This project is licensed under the MIT License – see the LICENSE file for details.
🙏 Acknowledgements

    Kitchenham & Charters (2007) for SLR methodology

    PRISMA 2020 Reporting Guideline

    GROBID for PDF metadata extraction

    CrossRef & OpenAlex for citation enrichment

    spaCy NLP for semantic analysis

📬 Contact

Created by @pachaboul
Feel free to open an issue or send a message for support or collaboration.