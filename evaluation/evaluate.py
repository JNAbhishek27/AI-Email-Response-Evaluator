#!/usr/bin/env python3
"""
Evaluation Runner.

Coordinates the RAG-grounded response generation for the support dataset,
runs the evaluation metrics suite over every generated response, aggregates the
results, and outputs structured analytical CSVs.
"""

import os
import sys
import csv
import pandas as pd
import logging
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

# Resolve project imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from rag.retriever import EmailRetriever
from generator.generate_reply import ResponseGenerator
from evaluation.metrics import calculate_overall_evaluation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_evaluation(sample_limit: int = None) -> None:
    """
    Run response generation and comprehensive metric evaluation across the support dataset.
    
    Args:
        sample_limit: Optional limit to restrict evaluation to a smaller subset of emails.
    """
    logger.info("Initializing AI Email Suggested Response Evaluation Engine...")
    
    data_path = os.path.join(project_root, "data", "emails.csv")
    outputs_dir = os.path.join(project_root, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    
    if not os.path.exists(data_path):
        logger.error(f"Required emails dataset missing at: {data_path}. Run generate_dataset.py first.")
        sys.exit(1)
        
    df = pd.read_csv(data_path)
    total_records = len(df)
    
    if sample_limit:
        logger.info(f"Sample limit set. Evaluating first {sample_limit} out of {total_records} emails.")
        df_subset = df.head(sample_limit)
    else:
        logger.info(f"Running full evaluation over all {total_records} emails.")
        df_subset = df

    # Initialize RAG & Generation components
    retriever = EmailRetriever()
    generator = ResponseGenerator()
    
    results = []
    
    for idx, row in df_subset.iterrows():
        email_id = str(row["email_id"])
        category = str(row["category"])
        customer_email = str(row["customer_email"])
        expected_reply = str(row["expected_reply"])
        urgency = str(row["urgency"])
        tone = str(row["tone"])
        
        logger.info(f"[{idx+1}/{len(df_subset)}] Processing {email_id} ({category}) | Urgency: {urgency}")
        
        # 1. Retrieve RAG grounding context
        # We retrieve similar cases, but we make sure the current email is not included in RAG reference
        raw_hits = retriever.retrieve(customer_email, top_k=4)
        hits = [h for h in raw_hits if h["email_id"] != email_id][:3]
        
        # 2. Generate Suggested Reply
        generated_reply = generator.generate(customer_email, hits)
        
        # 3. Compute Evaluation Metrics
        eval_scores = calculate_overall_evaluation(
            query=customer_email,
            reference=expected_reply,
            candidate=generated_reply,
            target_tone=tone
        )
        
        # Assemble analytical row
        record = {
            "email_id": email_id,
            "category": category,
            "urgency": urgency,
            "tone": tone,
            "customer_email": customer_email,
            "expected_reply": expected_reply,
            "generated_reply": generated_reply,
            "semantic_score": eval_scores["semantic_similarity"],
            "bleu": eval_scores["bleu_score"],
            "rouge": eval_scores["rouge_l"],
            "tone_consistency": eval_scores["tone_consistency"],
            "completeness": eval_scores["completeness"],
            "safety": eval_scores["safety_hallucination"],
            "final_score": eval_scores["final_score"],
            "grade": eval_scores["grade"]
        }
        results.append(record)
        
    # Save Outputs
    eval_df = pd.DataFrame(results)
    
    # Generate generated.csv (Abridged summary report)
    generated_path = os.path.join(outputs_dir, "generated.csv")
    generated_columns = ["email_id", "expected_reply", "generated_reply", "final_score", "grade"]
    eval_df[generated_columns].to_csv(generated_path, index=False)
    logger.info(f"Saved generated response summaries to: {generated_path}")
    
    # Generate evaluation.csv (Comprehensive scoring breakdown)
    evaluation_path = os.path.join(outputs_dir, "evaluation.csv")
    eval_df.to_csv(evaluation_path, index=False)
    logger.info(f"Saved complete evaluation reports to: {evaluation_path}")
    
    # Calculate overall aggregate metrics
    avg_semantic = eval_df["semantic_score"].mean()
    avg_bleu = eval_df["bleu"].mean()
    avg_rouge = eval_df["rouge"].mean()
    avg_tone = eval_df["tone_consistency"].mean()
    avg_completeness = eval_df["completeness"].mean()
    avg_safety = eval_df["safety"].mean()
    system_score = eval_df["final_score"].mean()
    
    # Determine overall system grade
    if system_score >= 90.0:
        system_grade = "EXCELLENT"
    elif system_score >= 80.0:
        system_grade = "GOOD"
    elif system_score >= 70.0:
        system_grade = "FAIR"
    else:
        system_grade = "POOR"
        
    grade_counts = eval_df["grade"].value_counts().to_dict()
    
    print("\n" + "="*50)
    print("      EMAIL AI SYSTEM EVALUATION REPORT")
    print("="*50)
    print(f"Total Emails Evaluated:  {len(eval_df)}")
    print(f"Overall System Score:    {system_score:.2f} / 100")
    print(f"System Performance:      {system_grade}")
    print("-"*50)
    print(f"Avg Semantic Similarity: {avg_semantic:.4f} (Weight 40%)")
    print(f"Avg BLEU Score:          {avg_bleu:.4f} (Weight 10%)")
    print(f"Avg ROUGE-L Score:       {avg_rouge:.4f} (Weight 10%)")
    print(f"Avg Tone Consistency:    {avg_tone:.4f} (Weight 15%)")
    print(f"Avg Completeness:        {avg_completeness:.4f} (Weight 15%)")
    print(f"Avg Safety & Grounding:  {avg_safety:.4f} (Weight 10%)")
    print("-"*50)
    print("Grade Distribution:")
    for grade, count in grade_counts.items():
        print(f"  - {grade}: {count}")
    print("="*50 + "\n")


if __name__ == "__main__":
    # If no arguments provided, run a quick evaluation of 5 samples
    # If 'all' provided, run full dataset.
    limit = 5
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "all":
            limit = None
        elif arg.isdigit():
            limit = int(arg)
            
    run_evaluation(sample_limit=limit)
