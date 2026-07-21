# AI Email Suggested Response & Evaluation System

An advanced, production-grade **Retrieval-Augmented Generation (RAG) and Multi-Metric Evaluation system** built to generate and rigorously benchmark customer support email responses using Google Gemini models.

This system provides a complete end-to-end evaluation pipeline that moves beyond simplistic "exact match" assessments to measure semantic similarity, lexical overlap, tone consistency, query completeness, and hallucination safety.

---

## Table of Contents
- [Project Overview](#project-overview)
- [System Architecture](#system-architecture)
- [Folder Structure](#folder-structure)
- [Dataset Details](#dataset-details)
- [RAG Pipeline](#rag-pipeline)
- [Evaluation Methodology & Justification](#evaluation-methodology--justification)
- [How to Run](#how-to-run)
- [Trade-offs & Limitations](#trade-offs--limitations)
- [Future Improvements](#future-improvements)
- [How AI Tools Were Used](#how-ai-tools-were-used)

---

## Project Overview

In commercial customer support contexts, relying blindly on raw generative LLMs often yields inconsistent styling, inaccurate assertions, or hallucinated facts (like imaginary order numbers). 

This system resolves this challenge by:
1. **Grounding generations** using a vector store (FAISS) populated with 100 highly realistic reference email threads across 15 operational categories.
2. **Generating suggested answers** with Google Gemini Pro / Flash models utilizing custom instructions, grounding documents, and context constraints.
3. **Evaluating outputs** using 6 distinct linguistic and custom semantic metrics to grade quality, verify safety, and audit tone alignment.

---

## System Architecture

```
                                  +-------------------+
                                  |   Incoming Query  |
                                  +---------+---------+
                                            |
                                            v
                                  +---------+---------+
                                  |SentenceTransformer|
                                  +---------+---------+
                                            | (Query Vector)
                                            v
+-------------------+             +---------+---------+
|  Reference CSV    |             |    FAISS L2       |
| (100 Support Cases)+----------->|   Vector Store    |
+-------------------+             +---------+---------+
                                            | (Retrieve Top-3 Cases)
                                            v
                                  +---------+---------+
                                  |   Prompt Builder  |
                                  +---------+---------+
                                            | (Grounded Context + Rules)
                                            v
                                  +---------+---------+
                                  |  Google Gemini    |
                                  +---------+---------+
                                            | (Suggested Reply)
                                            v
                                  +---------+---------+
                                  | Evaluation Engine | <--- (6 Scoring Metrics)
                                  +---------+---------+
                                            |
                                            v
                                  +---------+---------+
                                  |  Summary Reports  |
                                  |   & CSV Reports   |
                                  +-------------------+
```

---

## Folder Structure

```
email-ai-assistant/
├── data/
│   ├── generate_dataset.py       # Generates the 100+ support case benchmark CSV
│   └── emails.csv                # Compiled reference dataset
├── rag/
│   ├── build_index.py            # Generates and saves the FAISS index
│   └── retriever.py              # Semantic vector search and fallback TF-IDF retriever
├── generator/
│   └── generate_reply.py         # Google Gemini prompt constructor and API caller
├── evaluation/
│   ├── metrics.py                # Implementations of 6 grading metrics (BLEU, ROUGE-L, etc.)
│   └── evaluate.py               # Coordinates evaluation and saves reports
├── utils/
│   └── helpers.py                # Table formatting, configuration guides, and plotting
├── outputs/
│   ├── generated.csv             # Summary of generated answers and scores
│   ├── evaluation.csv            # Detailed multi-metric analytical report
│   └── performance_summary.png   # Performance plots per metric and category
├── main.py                       # Orchestrator CLI entry point
├── requirements.txt              # Production Python dependencies
├── .env.example                  # Environment configuration template
└── README.md                     # Documentation
```

---

## Dataset Details

The benchmark dataset consists of approximately 100 customer support threads distributed across **15 realistic support categories** representing complex commercial business flows:
- Refund, Order Status, Late Delivery, Cancellation, Damaged Product, Wrong Item, Payment Failure, Subscription, Account Access, Password Reset, Shipping Address, Technical Issue, Feature Request, Complaint, and General Inquiry.

Each support case is detailed with:
- `email_id`: Unique identifier (`EMAIL_001` to `EMAIL_100`)
- `category`: Core operational concern
- `customer_email`: Short, medium, or long natural text inquiries expressing various emotional tones (Angry, Frustrated, Polite, Friendly, Urgent, Professional) and urgency scores.
- `expected_reply`: High-quality, professional, and empathetic standard golden reference reply.

---

## RAG Pipeline

1. **Embedding Generator**: Uses SentenceTransformers (`all-MiniLM-L6-v2`) to translate reference support emails into 384-dimensional dense vector spaces.
2. **Indexing**: Dense vectors are stored in a FAISS Flat Inner Product index for highly accurate cosine similarity retrieval.
3. **Retrieval**: For any incoming query, the top-3 nearest-neighbor reference cases (customer email + expected reply) are extracted.
4. **Resiliency Fallback**: If SentenceTransformers or FAISS are unavailable, the pipeline falls back to a custom word-level TF-IDF Cosine Similarity retriever built from scratch, ensuring zero operational downtime.

---

## Evaluation Methodology & Justification

The system computes **6 performance metrics** that form a weighted overall quality score (0 - 100%) and awards a letter grade (`Excellent`, `Good`, `Fair`, `Poor`):

### 1. Semantic Similarity (40% Weight)
- **Justification**: Traditional lexical overlap (BLEU/ROUGE) fails to capture when two responses mean the same thing but use different vocabulary.
- **Implementation**: Computes cosine similarity of dense SentenceTransformer embeddings between the generated reply and the golden expected answer.

### 2. BLEU Score (10% Weight)
- **Justification**: Validates local phrasing precision and n-gram lexical overlap.
- **Implementation**: Calculates unigram/bigram overlap precision with a brevity penalty.

### 3. ROUGE-L (10% Weight)
- **Justification**: Measures recall of sequence order, verifying whether the response steps follow the same structural flow as the reference.
- **Implementation**: Computes Longest Common Subsequence (LCS) ratio.

### 4. Tone Consistency (15% Weight)
- **Justification**: Ensure support agents do not reply with inappropriate frustration, or skip crucial empathetic/polite statements.
- **Implementation**: Audits key lexical markers corresponding to the target tone (e.g. polite and professional structures like "thank you", "please", "sincerely", "apologize").

### 5. Completeness (15% Weight)
- **Justification**: A reply can be highly similar but skip a crucial instructions list or a requested item.
- **Implementation**: Verifies the presence of key operational keywords (refund, cancel, replacement, etc.) and analyzes coverage of questions and statements.

### 6. Safety / Hallucination (10% Weight)
- **Justification**: Generating fake order IDs, promising unapproved free trials, or inventing random refunds is a critical compliance liability.
- **Implementation**: Uses precise regex audits to penalize the generation of numeric entities (order IDs, monetary values, tracking serials) that do not appear in either the customer's query or the retrieved grounding cases.

---

## How to Run

### 1. Setup Environment
Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```

Create a `.env` file containing your Google AI Studio Gemini API Key:
```bash
cp .env.example .env
# Edit .env and set: GEMINI_API_KEY="your-api-key-here"
```

### 2. Run the Pipeline End-to-End
Execute the main orchestrator script:
```bash
# Run a quick test evaluation on 5 emails (Default)
python3 main.py

# Run full evaluation over all 100 emails in the dataset
python3 main.py --full

# Configure specific parameters
python3 main.py --limit 10 --skip-index
```

The system will:
1. Compile the 100-email dataset (`data/emails.csv`).
2. Build the vector database indices (`rag/faiss_index/`).
3. Generate grounded replies and run evaluation metrics on the samples.
4. Save analytical reports to `outputs/generated.csv` and `outputs/evaluation.csv`.
5. Generate performance plots in `outputs/performance_summary.png`.

---

## Trade-offs & Limitations

- **Lightweight Embeddings vs. LLM Eval**: To keep the framework fully runnable on any consumer laptop, the system uses sentence embeddings for semantic similarity rather than expensive LLM-as-a-judge APIs. This saves substantial costs and runs in milliseconds but lacks deep logical reasoning evaluation.
- **Linguistic Overlap Rigidness**: Lexical metrics like BLEU can penalize creative but highly professional rephrasings. This is balanced by assigning a larger weight (40%) to the semantic similarity embedding score.
- **FAISS vs. Production Vector DBs**: FAISS index is stored locally as a flat file, which is perfect for this offline dataset but does not support real-time CRUD operations natively as would cloud-hosted solutions like Pinecone or PGVector.

---

## Future Improvements

- **LLM-as-a-Judge integration**: Optionally proxy evaluation to a specialized Gemini model for reasoning-intensive completeness scoring.
- **Dynamic Semantic Guardrails**: Incorporate NeMo Guardrails to block prompt injections or malicious requests before they reach the generator.
- **Hybrid Search**: Combine lexical BM25 matching and dense vector search for optimal keyword and conceptual retrieval.

---

## How AI Tools Were Used

This project was built with the support of Google AI Studio. The structure, benchmark support emails, and multi-metric grading formulas were refined using advanced model interactions to ensure realistic corporate compliance checking.
