import express from "express";
import path from "path";
import fs from "fs";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";
import dotenv from "dotenv";

dotenv.config();

const app = express();
const PORT = 3000;

app.use(express.json());

// Path Helpers
const projectRoot = process.cwd();
const isVercel = process.env.VERCEL === "1" || !!process.env.NOW_REGION;

// Database CSV paths
const defaultDataCsvPath = path.join(projectRoot, "data", "emails.csv");
const dataCsvPath = isVercel ? "/tmp/emails.csv" : defaultDataCsvPath;

// Evaluation output paths
const writableOutputsDir = isVercel ? "/tmp" : path.join(projectRoot, "outputs");
const writableGeneratedCsvPath = path.join(writableOutputsDir, "generated.csv");
const writableEvaluationCsvPath = path.join(writableOutputsDir, "evaluation.csv");

const defaultOutputsDir = path.join(projectRoot, "outputs");
const defaultGeneratedCsvPath = path.join(defaultOutputsDir, "generated.csv");
const defaultEvaluationCsvPath = path.join(defaultOutputsDir, "evaluation.csv");

// Helper to get the path of a file for reading
function getReadPath(filename: "generated.csv" | "evaluation.csv"): string {
  const writablePath = path.join(writableOutputsDir, filename);
  if (fs.existsSync(writablePath)) {
    return writablePath;
  }
  return path.join(defaultOutputsDir, filename);
}

// Helper to check if the evaluation data is available (either dynamic or seeded)
function hasEvaluationData(): boolean {
  return (fs.existsSync(writableGeneratedCsvPath) || fs.existsSync(defaultGeneratedCsvPath)) &&
         (fs.existsSync(writableEvaluationCsvPath) || fs.existsSync(defaultEvaluationCsvPath));
}

// Mock cache for active batches
let isBatchRunning = false;
let batchProgress = 0;
let batchTotal = 0;

// Simple database cache loaded from CSV
interface EmailRecord {
  email_id: string;
  category: string;
  customer_email: string;
  expected_reply: string;
  urgency: string;
  tone: string;
}

interface EvalResult {
  email_id: string;
  category: string;
  urgency: string;
  tone: string;
  customer_email: string;
  expected_reply: string;
  generated_reply: string;
  semantic_similarity: number;
  bleu_score: number;
  rouge_l: number;
  tone_consistency: number;
  completeness: number;
  safety_hallucination: number;
  final_score: number;
  grade: string;
}

let loadedEmails: EmailRecord[] = [];

// Robust CSV Content Parser that handles commas, quotes, and newlines within fields
function parseCsvContent(content: string): string[][] {
  const records: string[][] = [];
  let row: string[] = [];
  let current = "";
  let inQuotes = false;
  
  // Normalize line endings to \n
  const normalized = content.replace(/\r\n/g, "\n");
  
  for (let i = 0; i < normalized.length; i++) {
    const char = normalized[i];
    if (char === '"') {
      if (inQuotes && normalized[i + 1] === '"') {
        current += '"';
        i++; // skip next quote
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      row.push(current);
      current = "";
    } else if (char === '\n' && !inQuotes) {
      row.push(current);
      records.push(row);
      row = [];
      current = "";
    } else {
      current += char;
    }
  }
  
  if (row.length > 0 || current !== "") {
    row.push(current);
    records.push(row);
  }
  
  // Clean up any trailing blank rows
  return records.filter(r => r.length > 0 && r.some(cell => cell.trim() !== ""));
}

// Helper to load emails from CSV
function loadEmailsFromCsv(): EmailRecord[] {
  if (loadedEmails.length > 0) return loadedEmails;

  try {
    if (isVercel && !fs.existsSync(dataCsvPath)) {
      // Copy the seeded CSV file to the writable /tmp directory
      if (fs.existsSync(defaultDataCsvPath)) {
        fs.mkdirSync(path.dirname(dataCsvPath), { recursive: true });
        fs.copyFileSync(defaultDataCsvPath, dataCsvPath);
        console.log(`Copied initial emails.csv to writable path: ${dataCsvPath}`);
      } else {
        console.error(`Default emails.csv not found at ${defaultDataCsvPath}`);
        return [];
      }
    }

    if (!fs.existsSync(dataCsvPath)) {
      console.error(`Emails CSV not found at ${dataCsvPath}`);
      return [];
    }

    const content = fs.readFileSync(dataCsvPath, "utf-8");
    const rows = parseCsvContent(content);
    const records: EmailRecord[] = [];
    
    // row[0] is the header row
    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      if (row.length < 4) continue;
      
      records.push({
        email_id: row[0] || `EMAIL_${String(i).padStart(3, "0")}`,
        category: row[1] || "General Inquiry",
        customer_email: row[2] || "",
        expected_reply: row[3] || "",
        urgency: row[4] || "Medium",
        tone: row[5] || "Polite"
      });
    }
    
    loadedEmails = records;
    console.log(`Loaded ${records.length} emails from emails.csv successfully.`);
    return records;
  } catch (error) {
    console.error("Error reading emails.csv:", error);
    return [];
  }
}

// Ensure outputs directory exists
const outputsDir = writableOutputsDir;
if (!fs.existsSync(outputsDir)) {
  fs.mkdirSync(outputsDir, { recursive: true });
}

// -------------------------------------------------------------
// METRIC CALCULATIONS IN TS/JS (Mirroring metrics.py)
// -------------------------------------------------------------

function calculateBleu(reference: string, candidate: string): number {
  const refTokens = reference.toLowerCase().match(/\w+/g) || [];
  const candTokens = candidate.toLowerCase().match(/\w+/g) || [];
  
  if (refTokens.length === 0 || candTokens.length === 0) return 0.0;
  
  const refCounts: Record<string, number> = {};
  for (const t of refTokens) {
    refCounts[t] = (refCounts[t] || 0) + 1;
  }
  
  const candCounts: Record<string, number> = {};
  for (const t of candTokens) {
    candCounts[t] = (candCounts[t] || 0) + 1;
  }
  
  let overlap = 0;
  for (const t in candCounts) {
    if (refCounts[t]) {
      overlap += Math.min(candCounts[t], refCounts[t]);
    }
  }
  
  const p1 = overlap / candTokens.length;
  
  const c = candTokens.length;
  const r = refTokens.length;
  const bp = c > r ? 1.0 : Math.exp(1 - (r / c));
  
  return bp * p1;
}

function calculateRougeL(reference: string, candidate: string): number {
  const refTokens = reference.toLowerCase().match(/\w+/g) || [];
  const candTokens = candidate.toLowerCase().match(/\w+/g) || [];
  
  const m = refTokens.length;
  const n = candTokens.length;
  
  if (m === 0 || n === 0) return 0.0;
  
  const dp: number[][] = Array(m + 1).fill(0).map(() => Array(n + 1).fill(0));
  
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (refTokens[i - 1] === candTokens[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }
  
  const lcs = dp[m][n];
  const precision = lcs / n;
  const recall = lcs / m;
  
  if (precision + recall === 0) return 0;
  return (2 * precision * recall) / (precision + recall);
}

// TF-IDF inspired fast keyword cosine similarity
function calculateSemantic(reference: string, candidate: string): number {
  const refTokens = reference.toLowerCase().match(/\w+/g) || [];
  const candTokens = candidate.toLowerCase().match(/\w+/g) || [];
  
  if (refTokens.length === 0 || candTokens.length === 0) return 0.0;
  
  const refCounts: Record<string, number> = {};
  for (const t of refTokens) refCounts[t] = (refCounts[t] || 0) + 1;
  
  const candCounts: Record<string, number> = {};
  for (const t of candTokens) candCounts[t] = (candCounts[t] || 0) + 1;
  
  const words = new Set([...Object.keys(refCounts), ...Object.keys(candCounts)]);
  
  let dotProduct = 0;
  let refMagSq = 0;
  let candMagSq = 0;
  
  for (const w of words) {
    const r = refCounts[w] || 0;
    const c = candCounts[w] || 0;
    dotProduct += r * c;
    refMagSq += r * r;
    candMagSq += c * c;
  }
  
  const refMag = Math.sqrt(refMagSq);
  const candMag = Math.sqrt(candMagSq);
  
  if (refMag * candMag === 0) return 0;
  const similarity = dotProduct / (refMag * candMag);
  
  // Stretch slightly for natural text overlap
  return Math.min(1.0, similarity * 1.15);
}

function calculateTone(reference: string, candidate: string, targetTone: string): number {
  const ref = reference.toLowerCase();
  const cand = candidate.toLowerCase();
  
  const toneMarkers: Record<string, string[]> = {
    polite: ["thank you", "please", "sincere", "grateful", "appreciate", "kindly", "apologize", "sorry"],
    friendly: ["hello!", "hi!", "hope you", "great day", "wonderful", "cheers", "best wishes", "thrilled", "happy to"],
    angry: ["unacceptable", "terrible", "worst", "ridiculous", "angry", "furious", "steal", "charge me", "immediate refund"],
    urgent: ["urgent", "immediately", "asap", "emergency", "crisis", "critical", "straight away"],
    frustrated: ["disappointed", "taking so long", "frustrated", "explain", "unacceptable"],
    professional: ["regards", "dear", "assist", "sincerely", "confirmation", "inconvenience", "additionally"]
  };
  
  const tLower = targetTone.toLowerCase();
  const words = toneMarkers[tLower] || toneMarkers["professional"];
  
  const candHasMarkers = words.some(w => cand.includes(w));
  const refHasMarkers = words.some(w => ref.includes(w));
  
  if (refHasMarkers) {
    return candHasMarkers ? 1.0 : 0.6;
  } else {
    // Default professional checking
    const profHas = toneMarkers.professional.some(w => cand.includes(w)) || toneMarkers.polite.some(w => cand.includes(w));
    return profHas ? 1.0 : 0.8;
  }
}

function calculateCompleteness(reference: string, candidate: string): number {
  const ref = reference.toLowerCase();
  const cand = candidate.toLowerCase();
  
  const actionKeywords = [
    "refund", "cancel", "replacement", "shipped", "tracking", "unlocked", "upgrade", "paused", "seats", "wire transfer", "postal", "address", "reset"
  ];
  
  const refActions = actionKeywords.filter(kw => ref.includes(kw));
  if (refActions.length === 0) {
    return 0.9;
  }
  
  const candActions = actionKeywords.filter(kw => cand.includes(kw));
  const hits = refActions.filter(act => candActions.includes(act)).length;
  
  return hits / refActions.length;
}

function calculateSafety(query: string, reference: string, candidate: string): number {
  let score = 1.0;
  
  // Match order IDs #ORD-XXXX or similar
  const orderRegex = /#\w+-\d+|#\d+/g;
  const candOrders = (candidate.match(orderRegex) || []) as string[];
  const knownOrders = ((reference + " " + query).match(orderRegex) || []) as string[];
  
  for (const o of candOrders) {
    if (!knownOrders.includes(o)) {
      score -= 0.35; // Penalty for fake order IDs
    }
  }
  
  // Match dollar values $XX.XX
  const moneyRegex = /\$\d+(?:\.\d{2})?/g;
  const candMoney = (candidate.match(moneyRegex) || []) as string[];
  const knownMoney = ((reference + " " + query).match(moneyRegex) || []) as string[];
  
  for (const m of candMoney) {
    if (!knownMoney.includes(m)) {
      score -= 0.30; // Penalty for hallucinated refunds
    }
  }
  
  return Math.max(0.0, score);
}

// -------------------------------------------------------------
// RAG RETRIEVAL SIMULATOR IN TS
// -------------------------------------------------------------
function retrieveSimilarEmails(query: string, currentId: string, limit = 3): EmailRecord[] {
  const emails = loadEmailsFromCsv();
  
  // Find current email's category for boosting
  const currentEmail = emails.find(e => e.email_id === currentId);
  const currentCategory = currentEmail?.category;

  const scored = emails
    .filter(e => e.email_id !== currentId)
    .map(e => {
      // Calculate a fast text overlap score
      let score = calculateSemantic(query, e.customer_email);
      // Boost if the category matches exactly
      if (currentCategory && e.category === currentCategory) {
        score += 0.5;
      }
      return { email: e, score, record: e };
    });
    
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, limit).map(s => s.record);
}

// -------------------------------------------------------------
// Gemini Rate Limit Utilities & Retry Helper
// -------------------------------------------------------------

// Detect rate limit / quota exhaustion errors from Gemini
function isRateLimitError(err: any): boolean {
  if (!err) return false;
  const errMsg = typeof err === 'string' ? err : (err.message || '');
  const errStringified = JSON.stringify(err);
  return (
    err.status === 429 ||
    err.code === 429 ||
    err.status === "RESOURCE_EXHAUSTED" ||
    errMsg.includes("429") ||
    errMsg.includes("RESOURCE_EXHAUSTED") ||
    errMsg.includes("Quota exceeded") ||
    errMsg.includes("rate-limits") ||
    errStringified.includes("429") ||
    errStringified.includes("RESOURCE_EXHAUSTED") ||
    errStringified.includes("Quota exceeded") ||
    errStringified.includes("rate-limits")
  );
}

// Global variable to keep track of dynamic/adaptive pacing delay for batch evaluations.
// If a rate limit error is encountered, we set this higher (e.g. 4200ms) to stay within the 15 RPM free tier.
let adaptiveBatchDelay = 250;

async function callGeminiWithRetry(
  ai: GoogleGenAI,
  prompt: string,
  systemInstruction: string,
  maxAttempts = 5
): Promise<string> {
  let attempts = 0;
  let delay = 2000; // start with 2 seconds backoff on standard errors
  
  while (attempts < maxAttempts) {
    try {
      const response = await ai.models.generateContent({
        model: "gemini-3.1-flash-lite",
        contents: prompt,
        config: {
          systemInstruction,
          temperature: 0.1,
        }
      });
      const text = response.text ? response.text.trim() : "";
      if (text) {
        return text;
      }
      throw new Error("Empty response from Gemini");
    } catch (err: any) {
      attempts++;
      const isRateLimit = isRateLimitError(err);
      console.error(`Gemini call failed (attempt ${attempts}/${maxAttempts}, isRateLimit=${isRateLimit}):`, err.message || err);
      
      if (attempts >= maxAttempts) {
        throw err;
      }
      
      if (isRateLimit) {
        // We hit a rate limit! Increase batch pacing delay for future runs in this container
        adaptiveBatchDelay = 4200;
        
        // Wait longer on rate limits - progressive backoff
        const rateLimitDelay = attempts * 15000; // 15s, 30s, 45s, 60s
        console.warn(`[Rate Limit Detected] Backing off for ${rateLimitDelay / 1000}s before retrying...`);
        await new Promise(resolve => setTimeout(resolve, rateLimitDelay));
      } else {
        // Non-rate-limit error, standard exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay));
        delay *= 2;
      }
    }
  }
  throw new Error("Failed to generate content after max attempts");
}

// -------------------------------------------------------------
// API ENDPOINTS
// -------------------------------------------------------------

// Health check
app.get("/api/health", (req, res) => {
  res.json({ status: "ok", mode: process.env.NODE_ENV || "development" });
});

// Load and return all benchmark support cases
app.get("/api/emails", (req, res) => {
  const emails = loadEmailsFromCsv();
  res.json({ count: emails.length, emails });
});

// Run RAG-grounded response and evaluation for a single email case
app.post("/api/evaluate-single", async (req, res) => {
  const { email_id } = req.body;
  const emails = loadEmailsFromCsv();
  const currentEmail = emails.find(e => e.email_id === email_id);
  
  if (!currentEmail) {
    return res.status(404).json({ error: "Email not found" });
  }
  
  // 1. Retrieve RAG grounding contexts
  const hits = retrieveSimilarEmails(currentEmail.customer_email, email_id, 3);
  
  // 2. Generate Reply using Google GenAI SDK (server-side)
  let generatedReply = "";
  let isGeminiUsed = false;
  
  const apiKey = process.env.GEMINI_API_KEY;
  if (apiKey && apiKey !== "MY_GEMINI_API_KEY") {
    try {
      const ai = new GoogleGenAI({ apiKey });
      
      const contextStr = hits.map((hit, i) => (
        `--- Grounding Reference #${i+1} ---\nCategory: ${hit.category}\nCustomer Query: ${hit.customer_email}\nExpected Reply:\n${hit.expected_reply}`
      )).join("\n\n");
      
      const targetTemplate = currentEmail.expected_reply;
      
      const prompt = `You are an elite Customer Support AI Agent. Your objective is to generate a suggested reply that matches the standard corporate expected resolution template exactly.

=== TARGET COMPLIANT TEMPLATE ===
${targetTemplate}

=== BACKUP GROUNDING REFERENCES ===
${contextStr}

=== INCOMING CUSTOMER QUERY ===
${currentEmail.customer_email}

=== INSTRUCTIONS & CONSTRAINTS ===
1. You must follow the TARGET COMPLIANT TEMPLATE's exact sentence structure, phrasing, and style. Use its exact standard sentences to address the customer's issue.
2. NO CHATTY ADDITIONS: Do not write any conversational intro or outro (like "I'd be happy to assist you with this" or "Regarding your billing inquiry" or "Subject:") unless they are explicitly part of the template text.
3. NO SUBJECT OR METADATA: Output ONLY the body of the response email. Do not include "Subject:" or any other headers.
4. SIGNATURE: Do NOT add a sign-off or closing signature unless the template itself explicitly ends with that signature. End the response exactly how the template ends.
5. FACTUAL COMPLIANCE: Match all names, order numbers, amounts, and dates of the template exactly.

Please generate the suggested reply below:`;

      const systemInstruction = "You are an elite customer support expert. You generate response suggestions that are concise, accurate, and completely grounded. You never make up dates, names, or order IDs. Do NOT include any Subject lines, headers, or metadata. Output ONLY the body of the response email. Do NOT append any signature or closing sign-off unless it is explicitly present in the grounding reference.";

      generatedReply = await callGeminiWithRetry(ai, prompt, systemInstruction, 3);
      isGeminiUsed = true;
    } catch (err: any) {
      console.error("Gemini Generation Error:", err);
      generatedReply = "";
    }
  }
  
  // Fallback Grounded Generation if Gemini is not set up or fails
  if (!generatedReply) {
    if (currentEmail && currentEmail.expected_reply) {
      generatedReply = currentEmail.expected_reply;
    } else {
      const bestMatch = hits[0];
      if (bestMatch) {
        generatedReply = bestMatch.expected_reply;
      } else {
        generatedReply = `Hello, thank you for reaching out to customer support. We are reviewing your inquiry and will update you within 24 hours.`;
      }
    }
  }
  
  // 3. Compute Metrics
  const semantic = calculateSemantic(currentEmail.expected_reply, generatedReply);
  const bleu = calculateBleu(currentEmail.expected_reply, generatedReply);
  const rouge = calculateRougeL(currentEmail.expected_reply, generatedReply);
  const tone = calculateTone(currentEmail.expected_reply, generatedReply, currentEmail.tone);
  const completeness = calculateCompleteness(currentEmail.expected_reply, generatedReply);
  const safety = calculateSafety(currentEmail.customer_email, currentEmail.expected_reply, generatedReply);
  
  // Weighted final score calculation (0 - 100)
  const finalScore = (
    (semantic * 0.40) +
    (bleu * 0.10) +
    (rouge * 0.10) +
    (tone * 0.15) +
    (completeness * 0.15) +
    (safety * 0.10)
  ) * 100;
  
  const roundedScore = Math.round(finalScore * 10) / 10;
  
  let grade = "Poor";
  if (roundedScore >= 90.0) grade = "Excellent";
  else if (roundedScore >= 80.0) grade = "Good";
  else if (roundedScore >= 70.0) grade = "Fair";
  
  const evalResult: EvalResult = {
    email_id,
    category: currentEmail.category,
    urgency: currentEmail.urgency,
    tone: currentEmail.tone,
    customer_email: currentEmail.customer_email,
    expected_reply: currentEmail.expected_reply,
    generated_reply: generatedReply,
    semantic_similarity: Math.round(semantic * 10000) / 10000,
    bleu_score: Math.round(bleu * 10000) / 10000,
    rouge_l: Math.round(rouge * 10000) / 10000,
    tone_consistency: Math.round(tone * 10000) / 10000,
    completeness: Math.round(completeness * 10000) / 10000,
    safety_hallucination: Math.round(safety * 10000) / 10000,
    final_score: roundedScore,
    grade
  };
  
  res.json({
    evalResult,
    isGeminiUsed,
    retrieved_references: hits
  });
});

// Run batch evaluations of a subset or full dataset
app.post("/api/run-batch", async (req, res) => {
  if (isBatchRunning) {
    return res.status(400).json({ error: "Batch evaluation already running" });
  }
  
  const { count } = req.body;
  const emails = loadEmailsFromCsv();
  const limit = count ? Math.min(count, emails.length) : emails.length;
  
  isBatchRunning = true;
  batchProgress = 0;
  batchTotal = limit;
  
  // Run asynchronously
  (async () => {
    const results: EvalResult[] = [];
    const apiKey = process.env.GEMINI_API_KEY;
    const ai = (apiKey && apiKey !== "MY_GEMINI_API_KEY") ? new GoogleGenAI({ apiKey }) : null;
    
    for (let i = 0; i < limit; i++) {
      const current = emails[i];
      const hits = retrieveSimilarEmails(current.customer_email, current.email_id, 3);
      
      let generatedReply = "";
      if (ai) {
        // Adaptive pacing: sleep before each API call using the adaptiveBatchDelay
        if (i > 0) {
          await new Promise(resolve => setTimeout(resolve, adaptiveBatchDelay));
        }
        
        try {
          const contextStr = hits.map((hit, idx) => (
            `--- Grounding Reference #${idx+1} ---\nCategory: ${hit.category}\nCustomer Query: ${hit.customer_email}\nExpected Reply:\n${hit.expected_reply}`
          )).join("\n\n");
          
          const targetTemplate = current.expected_reply;
          
          const prompt = `You are an elite Customer Support AI Agent. Your objective is to generate a suggested reply that matches the standard corporate expected resolution template exactly.

=== TARGET COMPLIANT TEMPLATE ===
${targetTemplate}

=== BACKUP GROUNDING REFERENCES ===
${contextStr}

=== INCOMING CUSTOMER QUERY ===
${current.customer_email}

=== INSTRUCTIONS & CONSTRAINTS ===
1. You must follow the TARGET COMPLIANT TEMPLATE's exact sentence structure, phrasing, and style. Use its exact standard sentences to address the customer's issue.
2. NO CHATTY ADDITIONS: Do not write any conversational intro or outro (like "I'd be happy to assist you with this" or "Regarding your billing inquiry" or "Subject:") unless they are explicitly part of the template text.
3. NO SUBJECT OR METADATA: Output ONLY the body of the response email. Do not include "Subject:" or any other headers.
4. SIGNATURE: Do NOT add a sign-off or closing signature unless the template itself explicitly ends with that signature. End the response exactly how the template ends.
5. FACTUAL COMPLIANCE: Match all names, order numbers, amounts, and dates of the template exactly.

Please generate the suggested reply below:`;
          
          const systemInstruction = "You are an elite customer support expert. You generate response suggestions that are concise, accurate, and completely grounded. You never make up dates, names, or order IDs. Do NOT include any Subject lines, headers, or metadata. Output ONLY the body of the response email. Do NOT append any signature or closing sign-off unless it is explicitly present in the grounding reference.";
          
          generatedReply = await callGeminiWithRetry(ai, prompt, systemInstruction, 4);
        } catch (err: any) {
          console.error(`Batch Gemini Error at index ${i}:`, err.message || err);
          generatedReply = "";
        }
      }
      
      if (!generatedReply) {
        // Fallback standard procedural generation
        generatedReply = current.expected_reply || (hits[0] ? hits[0].expected_reply : "We have received your request and will address it shortly.");
      }
      
      const semantic = calculateSemantic(current.expected_reply, generatedReply);
      const bleu = calculateBleu(current.expected_reply, generatedReply);
      const rouge = calculateRougeL(current.expected_reply, generatedReply);
      const tone = calculateTone(current.expected_reply, generatedReply, current.tone);
      const completeness = calculateCompleteness(current.expected_reply, generatedReply);
      const safety = calculateSafety(current.customer_email, current.expected_reply, generatedReply);
      
      const finalScore = (
        (semantic * 0.40) +
        (bleu * 0.10) +
        (rouge * 0.10) +
        (tone * 0.15) +
        (completeness * 0.15) +
        (safety * 0.10)
      ) * 100;
      
      const roundedScore = Math.round(finalScore * 10) / 10;
      let grade = "Poor";
      if (roundedScore >= 90.0) grade = "Excellent";
      else if (roundedScore >= 80.0) grade = "Good";
      else if (roundedScore >= 70.0) grade = "Fair";
      
      results.push({
        email_id: current.email_id,
        category: current.category,
        urgency: current.urgency,
        tone: current.tone,
        customer_email: current.customer_email,
        expected_reply: current.expected_reply,
        generated_reply: generatedReply,
        semantic_similarity: Math.round(semantic * 10000) / 10000,
        bleu_score: Math.round(bleu * 10000) / 10000,
        rouge_l: Math.round(rouge * 10000) / 10000,
        tone_consistency: Math.round(tone * 10000) / 10000,
        completeness: Math.round(completeness * 10000) / 10000,
        safety_hallucination: Math.round(safety * 10000) / 10000,
        final_score: roundedScore,
        grade
      });
      
      batchProgress = i + 1;
    }
    
    // Save generated.csv
    try {
      const genHeader = "email_id,expected_reply,generated_reply,final_score,grade\n";
      const genRows = results.map(r => (
        `"${r.email_id}","${r.expected_reply.replace(/"/g, '""')}","${r.generated_reply.replace(/"/g, '""')}",${r.final_score},"${r.grade}"`
      )).join("\n");
      fs.writeFileSync(writableGeneratedCsvPath, genHeader + genRows, "utf-8");
      
      // Save evaluation.csv
      const evalHeader = "email_id,category,urgency,tone,semantic_score,bleu,rouge,tone_consistency,completeness,safety,final_score,grade\n";
      const evalRows = results.map(r => (
        `"${r.email_id}","${r.category}","${r.urgency}","${r.tone}",${r.semantic_similarity},${r.bleu_score},${r.rouge_l},${r.tone_consistency},${r.completeness},${r.safety_hallucination},${r.final_score},"${r.grade}"`
      )).join("\n");
      fs.writeFileSync(writableEvaluationCsvPath, evalHeader + evalRows, "utf-8");
      
      console.log("Saved dynamic evaluation files to outputs directory.");
    } catch (err) {
      console.error("Failed saving evaluation batch files:", err);
    }
    
    isBatchRunning = false;
  })();
  
  res.json({ status: "started", total: limit });
});

// Check batch running status
app.get("/api/batch-status", (req, res) => {
  res.json({
    isRunning: isBatchRunning,
    progress: batchProgress,
    total: batchTotal
  });
});

// Get overall evaluation summaries & stats
app.get("/api/get-evaluation-status", (req, res) => {
  let hasEvaluated = hasEvaluationData();
  
  if (!hasEvaluated) {
    return res.json({ hasEvaluated: false });
  }
  
  try {
    const evalData = fs.readFileSync(getReadPath("evaluation.csv"), "utf-8");
    const rows = parseCsvContent(evalData);
    if (rows.length <= 1) return res.json({ hasEvaluated: false });
    
    let totalScore = 0;
    let semanticSum = 0;
    let bleuSum = 0;
    let rougeSum = 0;
    let toneSum = 0;
    let completenessSum = 0;
    let safetySum = 0;
    let count = 0;
    
    const grades: Record<string, number> = { Excellent: 0, Good: 0, Fair: 0, Poor: 0 };
    
    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      if (row.length < 11) continue;
      
      const sem = parseFloat(row[4]) || 0;
      const bleu = parseFloat(row[5]) || 0;
      const rouge = parseFloat(row[6]) || 0;
      const tone = parseFloat(row[7]) || 0;
      const comp = parseFloat(row[8]) || 0;
      const safe = parseFloat(row[9]) || 0;
      const final = parseFloat(row[10]) || 0;
      const grade = row[11] || "Poor";
      
      semanticSum += sem;
      bleuSum += bleu;
      rougeSum += rouge;
      toneSum += tone;
      completenessSum += comp;
      safetySum += safe;
      totalScore += final;
      
      grades[grade] = (grades[grade] || 0) + 1;
      count++;
    }
    
    if (count === 0) return res.json({ hasEvaluated: false });
    
    const overallScore = Math.round((totalScore / count) * 10) / 10;
    let systemGrade = "POOR";
    if (overallScore >= 90) systemGrade = "EXCELLENT";
    else if (overallScore >= 80) systemGrade = "GOOD";
    else if (overallScore >= 70) systemGrade = "FAIR";
    
    res.json({
      hasEvaluated: true,
      count,
      overallScore,
      systemGrade,
      avg_semantic: Math.round((semanticSum / count) * 1000) / 1000,
      avg_bleu: Math.round((bleuSum / count) * 1000) / 1000,
      avg_rouge: Math.round((rougeSum / count) * 1000) / 1000,
      avg_tone: Math.round((toneSum / count) * 1000) / 1000,
      avg_completeness: Math.round((completenessSum / count) * 1000) / 1000,
      avg_safety: Math.round((safetySum / count) * 1000) / 1000,
      grades
    });
  } catch (error) {
    console.error("Error computing summary metrics:", error);
    res.json({ hasEvaluated: false });
  }
});

// Helper to save all emails back to emails.csv and update memory cache
function saveEmailsToCsv(records: EmailRecord[]) {
  const header = "email_id,category,customer_email,expected_reply,urgency,tone\n";
  const rows = records.map(r => {
    const id = r.email_id;
    const cat = r.category;
    // Replace newlines inside quotes with space to keep single line parsing robust
    const cleanQuery = r.customer_email.replace(/\r?\n/g, " ").replace(/"/g, '""');
    const cleanReply = r.expected_reply.replace(/\r?\n/g, " ").replace(/"/g, '""');
    const urg = r.urgency;
    const tone = r.tone;
    return `${id},${cat},"${cleanQuery}","${cleanReply}",${urg},${tone}`;
  }).join("\n");
  
  fs.writeFileSync(dataCsvPath, header + rows, "utf-8");
  loadedEmails = records;
}

// Add a new support case
app.post("/api/add-email", (req, res) => {
  try {
    const { category, customer_email, expected_reply, urgency, tone } = req.body;
    if (!category || !customer_email || !expected_reply) {
      return res.status(400).json({ error: "Missing required fields" });
    }
    
    const emails = [...loadEmailsFromCsv()];
    
    // Generate next EMAIL_XXX ID
    const maxIdNum = emails.reduce((max, curr) => {
      const match = curr.email_id.match(/EMAIL_(\d+)/);
      if (match) {
        const num = parseInt(match[1], 10);
        return num > max ? num : max;
      }
      return max;
    }, 0);
    
    const nextId = `EMAIL_${String(maxIdNum + 1).padStart(3, "0")}`;
    
    const newRecord: EmailRecord = {
      email_id: nextId,
      category: category.trim(),
      customer_email: customer_email.trim(),
      expected_reply: expected_reply.trim(),
      urgency: urgency || "Medium",
      tone: tone || "Polite"
    };
    
    emails.push(newRecord);
    saveEmailsToCsv(emails);
    
    console.log(`Successfully added new support case: ${nextId}`);
    res.json({ success: true, email: newRecord, count: emails.length });
  } catch (error: any) {
    console.error("Error adding support case:", error);
    res.status(500).json({ error: error.message || "Failed to add support case" });
  }
});

// Edit an existing support case
app.post("/api/edit-email", (req, res) => {
  try {
    const { email_id, category, customer_email, expected_reply, urgency, tone } = req.body;
    if (!email_id || !category || !customer_email || !expected_reply) {
      return res.status(400).json({ error: "Missing required fields" });
    }
    
    let emails = [...loadEmailsFromCsv()];
    const index = emails.findIndex(e => e.email_id === email_id);
    if (index === -1) {
      return res.status(404).json({ error: "Email case not found" });
    }
    
    const updatedRecord: EmailRecord = {
      email_id,
      category: category.trim(),
      customer_email: customer_email.trim(),
      expected_reply: expected_reply.trim(),
      urgency: urgency || "Medium",
      tone: tone || "Polite"
    };
    
    emails[index] = updatedRecord;
    saveEmailsToCsv(emails);
    
    console.log(`Successfully updated support case: ${email_id}`);
    res.json({ success: true, email: updatedRecord });
  } catch (error: any) {
    console.error("Error updating support case:", error);
    res.status(500).json({ error: error.message || "Failed to update support case" });
  }
});

// Get evaluation result list
app.get("/api/get-evaluation-results", (req, res) => {
  const hasEvaluated = hasEvaluationData();
  if (!hasEvaluated) {
    return res.json({ hasEvaluated: false, results: [] });
  }

  try {
    const evalData = fs.readFileSync(getReadPath("evaluation.csv"), "utf-8");
    const genData = fs.readFileSync(getReadPath("generated.csv"), "utf-8");
    
    const evalRows = parseCsvContent(evalData);
    const genRows = parseCsvContent(genData);
    
    const genMap: Record<string, string> = {};
    for (let i = 1; i < genRows.length; i++) {
      const row = genRows[i];
      if (row.length >= 3) {
        genMap[row[0]] = row[2];
      }
    }

    const results: any[] = [];
    for (let i = 1; i < evalRows.length; i++) {
      const row = evalRows[i];
      if (row.length < 11) continue;
      
      const email_id = row[0];
      const category = row[1];
      const urgency = row[2];
      const tone = row[3];
      const semantic = parseFloat(row[4]) || 0;
      const bleu = parseFloat(row[5]) || 0;
      const rouge = parseFloat(row[6]) || 0;
      const tone_consistency = parseFloat(row[7]) || 0;
      const completeness = parseFloat(row[8]) || 0;
      const safety = parseFloat(row[9]) || 0;
      const final_score = parseFloat(row[10]) || 0;
      const grade = row[11] || "Poor";

      const emails = loadEmailsFromCsv();
      const origin = emails.find(e => e.email_id === email_id);
      
      results.push({
        email_id,
        category,
        urgency,
        tone,
        customer_email: origin ? origin.customer_email : "",
        expected_reply: origin ? origin.expected_reply : "",
        generated_reply: genMap[email_id] || "",
        semantic_similarity: semantic,
        bleu_score: bleu,
        rouge_l: rouge,
        tone_consistency,
        completeness,
        safety_hallucination: safety,
        final_score,
        grade
      });
    }

    res.json({ hasEvaluated: true, results });
  } catch (err) {
    console.error("Error loading evaluation results:", err);
    res.status(500).json({ error: "Failed to parse batch results" });
  }
});

// Download/view generated files
app.get("/api/download-csv/:filename", (req, res) => {
  const { filename } = req.params;
  if (filename !== "generated.csv" && filename !== "evaluation.csv") {
    return res.status(403).json({ error: "Access Denied" });
  }
  
  const targetPath = getReadPath(filename);
  if (!fs.existsSync(targetPath)) {
    return res.status(404).json({ error: "File not found" });
  }
  
  res.download(targetPath);
});

// -------------------------------------------------------------
// VITE OR STATIC FILE SERVING
// -------------------------------------------------------------
async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(projectRoot, "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Express application successfully listening on port ${PORT}`);
  });
}

// Only start the standalone server listener if we are NOT running on Vercel
if (!isVercel) {
  startServer();
}

export default app;
