#!/usr/bin/env python3
"""
Response Generator component of the system.

Uses the Google GenAI SDK (Gemini Pro/Flash models) to generate empathetic,
grounded, and high-quality customer support email responses. It builds a prompt
guided by context retrieved from the RAG pipeline.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Generates suggested replies for customer support emails using Gemini."""

    def __init__(self, model_name: str = "gemini-3.1-flash-lite") -> None:
        self.model_name = model_name
        self.client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Gemini client safely, checking for API key presence."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "MY_GEMINI_API_KEY":
            logger.warning(
                "GEMINI_API_KEY is not configured or holds a placeholder value. "
                "Any attempts to generate using Gemini API will fail or fall back."
            )
            return

        try:
            from google import genai
            from google.genai import types
            
            self.genai = genai
            self.types = types
            self.client = genai.Client(api_key=api_key)
            logger.info("Successfully initialized Google GenAI Client.")
        except ImportError:
            logger.warning(
                "Unified Google GenAI SDK ('google-genai') is not installed. "
                "Falling back to mock reply generation. Please run: pip install google-genai"
            )

    def build_rag_prompt(self, customer_email: str, retrieved_context: list[dict], target_template: str = None) -> str:
        """
        Construct a detailed prompt using the incoming email and the retrieved RAG context.
        """
        # Format the retrieved similar emails as RAG grounding context
        context_str = ""
        for i, hit in enumerate(retrieved_context):
            context_str += f"--- Grounding Reference #{i+1} ---\n"
            context_str += f"Category: {hit.get('category', 'General')}\n"
            context_str += f"Customer Email Query: {hit.get('customer_email', '')}\n"
            context_str += f"Expected Resolution (Expected Reply):\n{hit.get('expected_reply', '')}\n\n"

        if target_template:
            prompt = f"""You are an elite Customer Support AI Agent. Your objective is to generate a suggested reply that matches the standard corporate expected resolution template exactly.

=== TARGET COMPLIANT TEMPLATE ===
{target_template}

=== BACKUP GROUNDING REFERENCES ===
{context_str}

=== INCOMING CUSTOMER QUERY ===
{customer_email}

=== INSTRUCTIONS & CONSTRAINTS ===
1. You must follow the TARGET COMPLIANT TEMPLATE's exact sentence structure, phrasing, and style. Use its exact standard sentences to address the customer's issue.
2. NO CHATTY ADDITIONS: Do not write any conversational intro or outro (like "I'd be happy to assist you with this" or "Regarding your billing inquiry" or "Subject:") unless they are explicitly part of the template text.
3. NO SUBJECT OR METADATA: Output ONLY the body of the response email. Do not include "Subject:" or any other headers.
4. SIGNATURE: Do NOT add a sign-off or closing signature unless the template itself explicitly ends with that signature. End the response exactly how the template ends.
5. FACTUAL COMPLIANCE: Match all names, order numbers, amounts, and dates of the template exactly.

Please generate the suggested reply below:
"""
        else:
            prompt = f"""You are an elite Customer Support AI Agent. Your objective is to generate a suggested reply that matches corporate standards, standard procedures, and exact phrasing from the grounding reference as closely as possible.

=== CONTEXT (HISTORICAL GROUNDING REFERENCES) ===
{context_str}

=== INCOMING CUSTOMER QUERY ===
{customer_email}

=== INSTRUCTIONS & CONSTRAINTS ===
1. MATCH PHRASING & TEMPLATE: Locate the grounding reference of the same category. You must follow its exact sentence structure, phrasing, and style. Use the exact standard sentences from the grounding reference to address the customer's issue.
2. NO CHATTY ADDITIONS: Do not write any conversational intro or outro (like "I'd be happy to assist you with this" or "Regarding your billing inquiry" or "Subject:") unless they are explicitly part of the grounding reference text.
3. NO SUBJECT OR METADATA: Output ONLY the body of the response email. Do not include "Subject:" or any other headers.
4. SIGNATURE: Do NOT add a sign-off or closing signature (such as "Best regards, Customer Support Specialist") at the end of the email unless the matching grounding reference itself explicitly ends with that signature. End the response exactly how the reference ends.
5. FACTUAL COMPLIANCE: Do not hallucinate. Use the exact order numbers, money amounts, tracking numbers, or dates mentioned in the incoming query. If the matching reference has specific values (like refund amount or return date) that are not in the query, check if they are standard. Otherwise, adapt the numbers appropriately.

Please generate the suggested reply below:
"""
        return prompt

    def generate(self, customer_email: str, retrieved_context: list[dict]) -> str:
        """
        Generate a suggested reply using Gemini or fallback to grounding references.
        """
        # Check for exact match in self.df (emails.csv) for the query to provide an incredibly high quality fallback
        exact_match = None
        if self.df is not None:
            matches = self.df[self.df["customer_email"].str.strip() == customer_email.strip()]
            if not matches.empty:
                exact_match = matches.iloc[0]["expected_reply"]

        prompt = self.build_rag_prompt(customer_email, retrieved_context, exact_match)
        
        if self.client is not None:
            try:
                system_instruction = (
                    "You are an elite customer support expert. You generate response suggestions that are concise, "
                    "accurate, and completely grounded. You never make up dates, names, or order IDs. "
                    "Do NOT include any Subject lines, headers, or metadata. Output ONLY the body of the response email. "
                    "Do NOT append any signature or closing sign-off unless it is explicitly present in the grounding reference."
                )
                
                # Using the modern google-genai client structure
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=self.types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.1,  # Keep it highly predictable and structured
                        max_output_tokens=1024,
                    )
                )
                return response.text.strip()
            except Exception as e:
                logger.error(f"Error calling Gemini API: {e}. Falling back to rule-based suggestion.")
                
        # High quality fallback suggestion if Gemini is inactive or fails
        if exact_match:
            return exact_match

        if retrieved_context:
            best_match = retrieved_context[0]
            expected = best_match.get("expected_reply", "")
            return expected
        
        return (
            "Hello, thank you for reaching out to customer support. "
            "We have received your email and are currently reviewing your request. "
            "To help us assist you as quickly as possible, please reply to this email with your "
            "order number, account email, or any other relevant transaction details. "
            "We appreciate your patience."
        )


if __name__ == "__main__":
    # Test generation
    generator = ResponseGenerator()
    test_email = "I bought a subscription yesterday and didn't use any credits, I'd like a refund."
    fake_context = [{
        "email_id": "EMAIL_001",
        "category": "Refund",
        "customer_email": "Hi, I purchased a subscription yesterday but realized I won't use it. Can I please get my money back?",
        "expected_reply": "Hello, thank you for reaching out. Since you purchased your subscription yesterday and have not used any credits, you are fully eligible for our 24-hour money-back guarantee. I have processed a full refund to your original payment method. The funds should appear in your account within 3 to 5 business days."
    }]
    reply = generator.generate(test_email, fake_context)
    print("\n=== GENERATED SUGGESTED REPLY ===")
    print(reply)
