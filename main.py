#!/usr/bin/env python3
"""
Main entry point for the AI Email Suggested Response Evaluation System.

Orchestrates the entire pipeline end-to-end:
  1. Data Generation (generates benchmark support email dataset)
  2. Vector Indexing (builds dense retrieval database with SentenceTransformers & FAISS)
  3. Grounded Generation & Metric Evaluation (generates replies with Gemini and scores results)
  4. Reporting and Visualization (saves reports and outputs performance plots)
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

from utils.helpers import format_cli_header, generate_evaluation_charts
from data.generate_dataset import generate_dataset
from rag.build_index import build_index
from evaluation.evaluate import run_evaluation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the command line controller to orchestrate the evaluation engine."""
    parser = argparse.ArgumentParser(
        description="AI Email Suggested Response System - Benchmark and Evaluation Engine."
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run evaluation over the complete 100+ email dataset instead of a fast subset."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of support emails to generate and evaluate (default is 5 for testing)."
    )
    parser.add_argument(
        "--skip-dataset",
        action="store_true",
        help="Skip generating a fresh emails.csv dataset."
    )
    parser.add_argument(
        "--skip-index",
        action="store_true",
        help="Skip rebuilding the vector database index."
    )
    
    args = parser.parse_args()
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(project_root, "data", "emails.csv")
    evaluation_csv = os.path.join(project_root, "outputs", "evaluation.csv")
    outputs_dir = os.path.join(project_root, "outputs")
    
    print(format_cli_header("Email AI Suggested Response Pipeline"))
    logger.info("Starting orchestrated pipeline runs...")
    
    # Step 1: Dataset compilation
    if not args.skip_dataset or not os.path.exists(data_path):
        print(format_cli_header("1. Generating Dataset"))
        generate_dataset(data_path)
    else:
        logger.info("Skipping dataset generation. Using existing emails.csv.")
        
    # Step 2: Index building
    if not args.skip_index:
        print(format_cli_header("2. Building Vector Index"))
        build_index()
    else:
        logger.info("Skipping vector indexing.")
        
    # Step 3: Run Generation and Multi-Metric Evaluation
    print(format_cli_header("3. Running RAG Generation & Evaluation"))
    limit_value = None if args.full else args.limit
    run_evaluation(sample_limit=limit_value)
    
    # Step 4: Charts and visualizations
    print(format_cli_header("4. Generating Performance Analytics Charts"))
    generate_evaluation_charts(evaluation_csv, outputs_dir)
    
    print(format_cli_header("Pipeline Completed Successfully"))
    logger.info("All products and evaluation reports reside securely in outputs/ directory.")


if __name__ == "__main__":
    main()
