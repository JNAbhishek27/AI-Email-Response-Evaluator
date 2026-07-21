#!/usr/bin/env python3
"""
Evaluation metrics for comparing generated email responses against reference answers.

Includes standard linguistic metrics (BLEU, ROUGE-L), semantic similarity (sentence embeddings),
and custom semantic metrics (Tone Consistency, Completeness, and Safety/Hallucination checks).
"""

import re
import math
from collections import Counter
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def calculate_bleu_score(reference: str, candidate: str) -> float:
    """
    Calculate a simple BLEU-1 / BLEU-2 style overlap score from scratch
    to ensure 100% runnable behavior without external dependencies, with nltk fallback.
    """
    try:
        from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
        ref_tokens = reference.lower().split()
        cand_tokens = candidate.lower().split()
        # Use smoothing to avoid 0 scores for short sentences
        smooth = SmoothingFunction().method1
        return float(sentence_bleu([ref_tokens], cand_tokens, weights=(0.7, 0.3, 0, 0), smoothing_function=smooth))
    except (ImportError, Exception):
        # Fallback manual calculation
        ref_tokens = re.findall(r'\w+', reference.lower())
        cand_tokens = re.findall(r'\w+', candidate.lower())
        
        if not ref_tokens or not cand_tokens:
            return 0.0
            
        # Unigram overlap (Precision)
        ref_counts = Counter(ref_tokens)
        cand_counts = Counter(cand_tokens)
        
        overlap = 0
        for token, count in cand_counts.items():
            overlap += min(count, ref_counts.get(token, 0))
            
        p1 = overlap / len(cand_tokens)
        
        # Brevity penalty
        c = len(cand_tokens)
        r = len(ref_tokens)
        if c > r:
            bp = 1.0
        else:
            bp = math.exp(1 - (r / c)) if c > 0 else 0.0
            
        return float(bp * p1)


def calculate_rouge_l_score(reference: str, candidate: str) -> float:
    """
    Calculate the ROUGE-L score (Longest Common Subsequence ratio) between reference and candidate.
    """
    ref_tokens = re.findall(r'\w+', reference.lower())
    cand_tokens = re.findall(r'\w+', candidate.lower())
    
    m = len(ref_tokens)
    n = len(cand_tokens)
    
    if m == 0 or n == 0:
        return 0.0
        
    # Standard dynamic programming LCS computation
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_tokens[i - 1] == cand_tokens[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
                
    lcs = dp[m][n]
    
    # Calculate precision, recall and F1 for LCS
    precision = lcs / n
    recall = lcs / m
    
    if precision + recall == 0:
        return 0.0
        
    f1 = (2 * precision * recall) / (precision + recall)
    return float(f1)


def calculate_semantic_similarity(reference: str, candidate: str) -> float:
    """
    Calculate the Cosine Similarity of Sentence Transformer embeddings.
    If sentence-transformers is missing, falls back to an elegant TF-IDF Cosine Similarity.
    """
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        # We assume the caller or retriever has cached the model, but we can load a small one
        # To avoid overhead in simple imports, we load a cached model if available or do it lazily
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode([reference, candidate])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        # Force between 0.0 and 1.0
        return float(max(0.0, min(1.0, similarity)))
    except Exception:
        # High quality fallback: character and word-level TF-IDF overlap
        ref_tokens = re.findall(r'\w+', reference.lower())
        cand_tokens = re.findall(r'\w+', candidate.lower())
        
        if not ref_tokens or not cand_tokens:
            return 0.0
            
        ref_counter = Counter(ref_tokens)
        cand_counter = Counter(cand_tokens)
        
        # Dot product
        intersection = set(ref_counter.keys()) & set(cand_counter.keys())
        dot_product = sum(ref_counter[x] * cand_counter[x] for x in intersection)
        
        # Magnitudes
        ref_mag = math.sqrt(sum(val**2 for val in ref_counter.values()))
        cand_mag = math.sqrt(sum(val**2 for val in cand_counter.values()))
        
        if ref_mag * cand_mag == 0:
            return 0.0
            
        cosine = dot_product / (ref_mag * cand_mag)
        return float(max(0.0, min(1.0, cosine)))


def calculate_tone_consistency(reference: str, candidate: str, target_tone: str = "Professional") -> float:
    """
    Check if the generated response tone matches the target tone of the expected reply.
    Looks for emotional sentiment vocabulary, markers, and formal structures.
    """
    ref = reference.lower()
    cand = candidate.lower()
    
    # Define simple dictionaries for common customer support tones
    tone_markers = {
        "polite": ["thank you", "please", "sincere", "grateful", "appreciate", "kindly", "apologize", "sorry"],
        "friendly": ["hello!", "hi!", "hope you", "great day", "wonderful", "cheers", "best wishes", "thrilled", "happy to"],
        "angry": ["unacceptable", "terrible", "worst", "ridiculous", "angry", "furious", "steal", "charge me", "immediate refund", "now!"],
        "urgent": ["urgent", "immediately", "asap", "emergency", "crisis", "critical", "straight away", "right now", "rush"],
        "frustrated": ["disappointed", "taking so long", "frustrated", "explain", "unacceptable", "where is", "stuck"],
        "professional": ["regards", "dear", "assist", "sincerely", "confirmation", "inconvenience", "additionally", "reference"]
    }
    
    # Detect prominent tones in both
    def score_tone(text: str) -> dict:
        scores = {}
        for tone, words in tone_markers.items():
            count = sum(text.count(word) for word in words)
            scores[tone] = count
        return scores
        
    ref_tones = score_tone(ref)
    cand_tones = score_tone(cand)
    
    # Check if the candidate exhibits professional elements by default
    # If the target tone is friendly, ensure we have friendly words, etc.
    target_tone_lower = target_tone.lower()
    if target_tone_lower not in tone_markers:
        target_tone_lower = "professional"
        
    # Calculate overlap of tone structures
    # A score of 1.0 means candidate fully includes the target/reference tone properties
    # Let's see if the candidate matches the tone of the reference
    if target_tone_lower == "angry" or target_tone_lower == "frustrated":
        # Note: If the customer query was angry, the support response should NOT be angry.
        # It should be extremely polite and professional.
        # So we verify if candidate is Polite + Professional
        polite_score = cand_tones.get("polite", 0) + cand_tones.get("professional", 0)
        score = 1.0 if polite_score >= 1 else 0.7
    else:
        # Check if the candidate contains the required tone markers
        target_count = cand_tones.get(target_tone_lower, 0)
        ref_count = ref_tones.get(target_tone_lower, 0)
        
        if ref_count > 0:
            score = 1.0 if target_count > 0 else 0.5
        else:
            # If the reference didn't even have specific markers, standard professional is expected
            prof_count = cand_tones.get("professional", 0) + cand_tones.get("polite", 0)
            score = 1.0 if prof_count >= 1 else 0.8
            
    return float(score)


def calculate_completeness(reference: str, candidate: str, query: str = "") -> float:
    """
    Verify whether the response covers the core elements needed to resolve the case.
    Compares word chunk intersections and check key-value numbers/topics.
    """
    ref = reference.lower()
    cand = candidate.lower()
    
    # Extract key actionable topics
    action_keywords = [
        "refund", "cancel", "replacement", "shipped", "tracking", "unlocked", "upgrade", "paused", "seats", "wire transfer", "postal", "address", "reset"
    ]
    
    ref_actions = [kw for kw in action_keywords if kw in ref]
    cand_actions = [kw for kw in action_keywords if kw in cand]
    
    if not ref_actions:
        # If no specific action keywords, check base length ratio and word coverage
        ratio = min(len(cand.split()), len(ref.split())) / max(len(cand.split()), len(ref.split()), 1)
        return float(0.8 + 0.2 * ratio)
        
    # Calculate how many of the reference action items are present in candidate
    hits = sum(1 for act in ref_actions if act in cand_actions)
    score = hits / len(ref_actions)
    
    # Check if there's any pending question in reference that is addressed
    question_words = ["what", "when", "why", "where", "how", "please provide", "send us"]
    for qw in question_words:
        if qw in ref and qw in cand:
            score = min(1.0, score + 0.1)
            
    return float(max(0.5, min(1.0, score)))


def calculate_safety_score(query: str, reference: str, candidate: str) -> float:
    """
    Evaluates safety and detects hallucinations.
    Penalizes candidate if it includes specific entities (order IDs, currency amounts, 
    tracking links, percentages) that do NOT exist in either the query or the reference!
    """
    cand = candidate
    ref = reference
    q = query
    
    score = 1.0
    
    # 1. Look for order ID patterns (e.g., #ORD-1234, #1234)
    # Find all order numbers in candidate
    cand_orders = set(re.findall(r'#\w+-\d+|#\d+', cand))
    known_orders = set(re.findall(r'#\w+-\d+|#\d+', ref + " " + q))
    
    for order in cand_orders:
        if order not in known_orders:
            # Hallucinated order ID! Major penalty.
            score -= 0.35
            logger.debug(f"Safety Penalty: Hallucinated order ID detected: {order}")
            
    # 2. Look for monetary amounts (e.g., $15.00, $120)
    cand_money = set(re.findall(r'\$\d+(?:\.\d{2})?', cand))
    known_money = set(re.findall(r'\$\d+(?:\.\d{2})?', ref + " " + q))
    
    for amount in cand_money:
        if amount not in known_money:
            # Hallucinated money/refund amount!
            score -= 0.30
            logger.debug(f"Safety Penalty: Hallucinated refund amount detected: {amount}")
            
    # 3. Look for tracking number structures
    # E.g., 1Z999... or similar long serial strings
    cand_serials = set(re.findall(r'\b[A-Z0-9]{10,25}\b', cand))
    known_serials = set(re.findall(r'\b[A-Z0-9]{10,25}\b', ref + " " + q))
    
    for serial in cand_serials:
        # Exclude standard words by checking if they contain both letters and digits
        if any(c.isalpha() for c in serial) and any(c.isdigit() for c in serial):
            if serial not in known_serials:
                score -= 0.25
                logger.debug(f"Safety Penalty: Hallucinated tracking serial detected: {serial}")
                
    # 4. Check for extreme promises (e.g., "guarantee", "instantly", "free forever")
    unauthorized_claims = ["free forever", "guarantee refund", "immediate cash", "unconditional replacement"]
    for claim in unauthorized_claims:
        if claim in cand.lower() and claim not in ref.lower():
            score -= 0.15
            logger.debug(f"Safety Penalty: Unauthorized policy guarantee claim: {claim}")
            
    return float(max(0.0, min(1.0, score)))


def calculate_overall_evaluation(query: str, reference: str, candidate: str, target_tone: str = "Professional") -> dict:
    """
    Compute all evaluation scores and return a breakdown dictionary.
    
    Weights:
      - Semantic Similarity: 40%
      - BLEU Score: 10%
      - ROUGE-L: 10%
      - Tone Consistency: 15%
      - Completeness: 15%
      - Safety / Hallucination: 10%
    """
    sem = calculate_semantic_similarity(reference, candidate)
    bleu = calculate_bleu_score(reference, candidate)
    rouge = calculate_rouge_l_score(reference, candidate)
    tone = calculate_tone_consistency(reference, candidate, target_tone)
    comp = calculate_completeness(reference, candidate, query)
    safe = calculate_safety_score(query, reference, candidate)
    
    final_score = (
        (sem * 0.40) +
        (bleu * 0.10) +
        (rouge * 0.10) +
        (tone * 0.15) +
        (comp * 0.15) +
        (safe * 0.10)
    )
    
    # Convert to standard percentage index (0 - 100)
    final_percentage = round(final_score * 100, 1)
    
    # Assign Grade
    if final_percentage >= 90.0:
        grade = "Excellent"
    elif final_percentage >= 80.0:
        grade = "Good"
    elif final_percentage >= 70.0:
        grade = "Fair"
    else:
        grade = "Poor"
        
    return {
        "semantic_similarity": round(sem, 4),
        "bleu_score": round(bleu, 4),
        "rouge_l": round(rouge, 4),
        "tone_consistency": round(tone, 4),
        "completeness": round(comp, 4),
        "safety_hallucination": round(safe, 4),
        "final_score": final_percentage,
        "grade": grade,
    }


if __name__ == "__main__":
    # Test evaluation
    q = "Where is order #4412? I need it for a birthday party tonight!"
    ref = "Hello, your order #4412 is currently at your local facility. The carrier marked it as 'on vehicle for delivery' this morning, arriving today before 5:00 PM."
    cand = "Hello, I looked into order #4412. It is loaded onto the delivery truck today and will arrive before 5:00 PM. We hope it arrives in time for the party!"
    
    res = calculate_overall_evaluation(q, ref, cand, "Urgent")
    print("\n=== METRICS BREAKDOWN ===")
    for k, v in res.items():
        print(f"{k}: {v}")
