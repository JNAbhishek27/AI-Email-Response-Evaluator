#!/usr/bin/env python3
"""
Utility helper functions.

Provides helper routines for printing formatted tables, loading configuration details,
and plotting performance metrics visually using matplotlib.
"""

import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def generate_evaluation_charts(evaluation_csv_path: str, output_image_dir: str) -> None:
    """
    Generates analytics visualization charts from the evaluation metrics report.
    Creates a visual breakdown of scores per category and saves it as an image.
    """
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
        
        if not os.path.exists(evaluation_csv_path):
            logger.warning(f"Evaluation report not found at {evaluation_csv_path}. Skipping chart generation.")
            return
            
        df = pd.read_csv(evaluation_csv_path)
        
        os.makedirs(output_image_dir, exist_ok=True)
        chart_path = os.path.join(output_image_dir, "performance_summary.png")
        
        # Configure layout style
        plt.style.use("ggplot")
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # Chart 1: Average Metric Scores
        metrics = ["semantic_score", "bleu", "rouge", "tone_consistency", "completeness", "safety"]
        metric_labels = ["Semantic", "BLEU", "ROUGE-L", "Tone Match", "Completeness", "Safety"]
        avg_scores = [df[m].mean() * 100 for m in metrics]
        
        axes[0].bar(metric_labels, avg_scores, color="indigo", width=0.5)
        axes[0].set_title("Average Metrics Performance (%)", fontsize=12, fontweight="bold")
        axes[0].set_ylim(0, 105)
        axes[0].set_ylabel("Score %")
        for i, val in enumerate(avg_scores):
            axes[0].text(i, val + 2, f"{val:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")
            
        # Chart 2: Score distribution by Category
        category_means = df.groupby("category")["final_score"].mean().sort_values()
        category_means.plot(kind="barh", ax=axes[1], color="teal")
        axes[1].set_title("Performance by Email Category", fontsize=12, fontweight="bold")
        axes[1].set_xlabel("Average Score / 100")
        axes[1].set_xlim(0, 105)
        
        plt.tight_layout()
        plt.savefig(chart_path, dpi=300)
        plt.close()
        
        logger.info(f"Successfully generated analytical performance charts at: {chart_path}")
        
    except ImportError:
        logger.warning("matplotlib is not installed. Visual chart generation skipped.")
    except Exception as e:
        logger.error(f"Error producing evaluation charts: {e}")


def format_cli_header(title: str) -> str:
    """Return a visual header for command line reports."""
    width = 60
    border = "=" * width
    padding = " " * ((width - len(title) - 2) // 2)
    return f"\n{border}\n{padding} {title.upper()} {padding}\n{border}"
