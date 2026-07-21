#!/usr/bin/env python3
"""
Retriever component of the RAG pipeline.

Loads the compiled FAISS vector index and uses the Sentence Transformer model
to perform semantic search, returning top-3 matching items with their similarity scores.
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


class EmailRetriever:
    """Handles loading the FAISS index and querying similar emails."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(self.current_dir)
        self.data_path = os.path.join(self.project_root, "data", "emails.csv")
        self.index_path = os.path.join(self.current_dir, "faiss_index", "index.faiss")
        
        self.df = None
        self.model = None
        self.index = None
        
        self._load_dependencies()

    def _load_dependencies(self) -> None:
        """Load CSV data, model, and FAISS index into memory."""
        # Load dataset
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Emails dataset not found at {self.data_path}. Run generate_dataset.py first.")
        self.df = pd.read_csv(self.data_path)
        
        # Load index and model
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
            import numpy as np
            
            self.np = np
            self.faiss = faiss
            
            if not os.path.exists(self.index_path):
                logger.warning(f"FAISS index not found at {self.index_path}. Building index first...")
                # Try to build it dynamically
                from rag.build_index import build_index
                build_index()
                
            self.index = faiss.read_index(self.index_path)
            self.model = SentenceTransformer(model_name)
            logger.info("Successfully loaded SentenceTransformer model and FAISS index.")
            
        except ImportError:
            logger.warning(
                "SentenceTransformer or FAISS is missing. "
                "Falling back to simple TF-IDF / keyword similarity matcher for demonstration."
            )
            self._setup_fallback_retriever()

    def _setup_fallback_retriever(self) -> None:
        """Set up a simple python TF-IDF or token-overlap retriever in case models cannot be loaded."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        emails = self.df["customer_email"].astype(str).tolist()
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.tfidf_matrix = self.vectorizer.fit_transform(emails)
        logger.info("Fallback TF-IDF matcher configured successfully.")

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        """
        Search for top_k most similar customer support emails.
        
        Returns:
            List of dictionaries containing matching details.
        """
        if self.index is not None and self.model is not None:
            # Generate query embedding
            query_vector = self.model.encode([query], convert_to_numpy=True).astype("float32")
            self.faiss.normalize_L2(query_vector)
            
            # Search index
            scores, indices = self.index.search(query_vector, top_k)
            
            results = []
            for score, index_id in zip(scores[0], indices[0]):
                if index_id < 0 or index_id >= len(self.df):
                    continue
                row = self.df.iloc[index_id]
                results.append({
                    "email_id": str(row["email_id"]),
                    "category": str(row["category"]),
                    "customer_email": str(row["customer_email"]),
                    "expected_reply": str(row["expected_reply"]),
                    "urgency": str(row["urgency"]),
                    "tone": str(row["tone"]),
                    "similarity_score": float(score),
                })
            return results
        else:
            # Fallback keyword/TF-IDF retrieval
            query_vec = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            top_indices = similarities.argsort()[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                row = self.df.iloc[idx]
                score = float(similarities[idx])
                # Ensure scores are normalized/positive
                score = max(0.0, min(1.0, score))
                results.append({
                    "email_id": str(row["email_id"]),
                    "category": str(row["category"]),
                    "customer_email": str(row["customer_email"]),
                    "expected_reply": str(row["expected_reply"]),
                    "urgency": str(row["urgency"]),
                    "tone": str(row["tone"]),
                    "similarity_score": score,
                })
            return results


if __name__ == "__main__":
    # Command line test of retriever
    retriever = EmailRetriever()
    test_query = "Can I get my money back? I made a wrong subscription purchase yesterday."
    logger.info(f"Test Query: '{test_query}'")
    hits = retriever.retrieve(test_query, top_k=3)
    for i, hit in enumerate(hits):
        print(f"\n--- MATCH #{i+1} (Score: {hit['similarity_score']:.4f}) ---")
        print(f"ID: {hit['email_id']} | Category: {hit['category']}")
        print(f"Email: {hit['customer_email'][:120]}...")
        print(f"Expected Reply: {hit['expected_reply'][:120]}...")
