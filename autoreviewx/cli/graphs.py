import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from math import pi
from datetime import datetime
from pathlib import Path


def generate_graphs(input_file, output_dir=None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Automatically find project root by looking for setup.py
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "setup.py").exists() or (current / ".git").exists():
            project_root = current
            break
        current = current.parent
    else:
        project_root = Path.cwd()  # fallback

    # Construct default output path if not specified
    if output_dir is None:
        output_path = project_root / "data" / "visuels" / timestamp
    else:
        output_path = Path(output_dir)

    output_path.mkdir(parents=True, exist_ok=True)

    # Load dataset
    df = pd.read_csv(input_file)

    # === PRISMA Heatmap ===
    prisma_cols = [col for col in df.columns if col.startswith("prisma_") and col.endswith("_pass")]
    if prisma_cols:
        prisma_data = df[prisma_cols].mean().to_frame().T
        plt.figure(figsize=(12, 2))
        sns.heatmap(prisma_data, annot=True, cmap="YlGnBu", cbar=False)
        plt.title("PRISMA: Percentage of articles satisfying each item")
        plt.savefig(os.path.join(output_path, "prisma_heatmap.png"))
        plt.close()

    # === PICO Barplot ===
    pico_cols = ['population', 'intervention', 'comparison', 'outcome']
    if all(col in df.columns for col in pico_cols):
        pico_completeness = df[pico_cols].notnull().mean()
        plt.figure(figsize=(8, 6))
        sns.barplot(x=pico_completeness.index, y=pico_completeness.values)
        plt.title("PICO: Completeness rate per component")
        plt.ylabel("Completeness Rate")
        plt.ylim(0, 1)
        plt.savefig(os.path.join(output_path, "pico_barplot.png"))
        plt.close()

    # === CASP Radar Chart ===
    casp_cols = [col for col in df.columns if col.startswith("casp_") and col.endswith("_score")]
    if casp_cols:
        scores = df[casp_cols].mean().tolist()
        categories = casp_cols
        N = len(categories)
        angles = [n / float(N) * 2 * pi for n in range(N)]
        scores += scores[:1]
        angles += angles[:1]
        plt.figure(figsize=(8, 8))
        ax = plt.subplot(111, polar=True)
        plt.xticks(angles[:-1], categories, size=10)
        ax.plot(angles, scores, linewidth=1.5)
        ax.fill(angles, scores, alpha=0.3)
        plt.title("CASP: Semantic similarity by dimension")
        plt.savefig(os.path.join(output_path, "casp_radar.png"))
        plt.close()

    # === TAPUPAS Barplot ===
    tapupas_cols = ['transparency', 'accuracy', 'purposivity', 'utility', 'propriety', 'accessibility', 'specificity']
    if all(col in df.columns for col in tapupas_cols):
        tapupas_scores = df[tapupas_cols].mean()
        plt.figure(figsize=(10, 6))
        sns.barplot(x=tapupas_scores.index, y=tapupas_scores.values)
        plt.xticks(rotation=45, ha="right")
        plt.title("TAPUPAS: Score [0–2] per dimension")
        plt.ylabel("Average Score")
        plt.savefig(os.path.join(output_path, "tapupas_barplot.png"))
        plt.close()

    # === Kitchenham Radar Dual ===
    score_cols = [col for col in df.columns if col.startswith("kitch_") and col.endswith("_score")]
    bool_cols = [col for col in df.columns if col.startswith("kitch_") and col.endswith("_pass")]
    if score_cols and bool_cols:
        score_vals = df[score_cols].mean().tolist()
        bool_vals = df[bool_cols].mean().tolist()
        labels = [col.replace("kitch_", "").replace("_score", "") for col in score_cols]
        score_vals += score_vals[:1]
        bool_vals += bool_vals[:1]
        angles = [n / float(len(labels)) * 2 * pi for n in range(len(labels))]
        angles += angles[:1]
        plt.figure(figsize=(9, 9))
        ax = plt.subplot(111, polar=True)
        plt.xticks(angles[:-1], labels, size=10)
        ax.plot(angles, bool_vals, label="Heuristic (Boolean)", linestyle='dashed')
        ax.plot(angles, score_vals, label="Score (NLP)", linestyle='solid')
        ax.fill(angles, score_vals, alpha=0.2)
        plt.title("Kitchenham: Heuristic vs NLP scoring")
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        plt.savefig(os.path.join(output_path, "kitchenham_radar.png"))
        plt.close()

    print(f"✅ All graphs have been generated in: {output_path}")
