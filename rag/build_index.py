#!/usr/bin/env python3
"""
Build vector index for the RAG pipeline using Sentence Transformers and FAISS.

This script reads the customer support emails dataset, generates dense vector
embeddings for the customer emails using a sentence transformer model, and
saves a FAISS index to disk for fast retrieval.
"""

import os
import sys
import pandas as pd
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def build_index() -> None:
    """Build the FAISS index from the generated email CSV."""
    # Resolve paths relative to this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    data_path = os.path.join(project_root, "data", "emails.csv")
    index_dir = os.path.join(current_dir, "faiss_index")
    
    if not os.path.exists(data_path):
        logger.error(f"Emails dataset not found at {data_path}. Please run generate_dataset.py first.")
        sys.exit(1)
        
    logger.info(f"Loading dataset from: {data_path}")
    df = pd.read_csv(data_path)
    
    # Check for empty columns
    if "customer_email" not in df.columns:
        logger.error("Dataset is missing 'customer_email' column.")
        sys.exit(1)
        
    emails = df["customer_email"].astype(str).tolist()
    logger.info(f"Generating embeddings for {len(emails)} customer emails...")
    
    try:
        from sentence_transformers import SentenceTransformer
        import faiss
        import numpy as np
    except ImportError:
        logger.error(
            "Required libraries (sentence-transformers, faiss-cpu) are not installed. "
            "Please run: pip install sentence-transformers faiss-cpu"
        )
        # We will gracefully exit so other files can compile and load
        sys.exit(1)

    # Initialize model - using a lightweight, fast, and high-quality general-purpose model
    model_name = "all-MiniLM-L6-v2"
    logger.info(f"Loading sentence transformer model: {model_name}")
    model = SentenceTransformer(model_name)
    
    # Encode emails
    embeddings = model.encode(emails, show_progress_bar=True, convert_to_numpy=True)
    
    # FAISS expects float32
    embeddings = embeddings.astype("float32")
    
    # Normalize vectors for Cosine Similarity (Inner Product of L2 normalized vectors)
    faiss.normalize_L2(embeddings)
    
    # Dimension of embeddings
    dimension = embeddings.shape[1]
    logger.info(f"Embedding dimension: {dimension}")
    
    # IndexFlatIP is perfect for Cosine Similarity since vectors are normalized
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    
    os.makedirs(index_dir, exist_ok=True)
    index_path = os.path.join(index_dir, "index.faiss")
    faiss.write_index(index, index_path)
    
    logger.info(f"Successfully saved FAISS index to: {index_path}")


if __name__ == "__main__":
    build_index()
