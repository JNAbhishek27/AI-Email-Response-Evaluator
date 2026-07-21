import React, { useState, useEffect, useRef } from "react";
import { 
  Mail, 
  Settings, 
  Play, 
  Database, 
  FileText, 
  Download, 
  Activity, 
  ShieldCheck, 
  CheckCircle, 
  Clock, 
  HelpCircle, 
  ChevronRight, 
  Folder, 
  FileCode, 
  AlertCircle,
  TrendingUp,
  Cpu,
  RefreshCw,
  Sparkles
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

// Types
interface EmailRecord {
  email_id: string;
  category: string;
  customer_email: string;
  expected_reply: string;
  urgency: string;
  tone: string;
  status?: string;
  score?: number;
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

interface RAGReference {
  email_id: string;
  category: string;
  customer_email: string;
  expected_reply: string;
  urgency: string;
  tone: string;
  similarity_score: number;
}

interface SingleEvalResponse {
  evalResult: EvalResult;
  isGeminiUsed: boolean;
  retrieved_references: RAGReference[];
}

interface BatchStatus {
  isRunning: boolean;
  progress: number;
  total: number;
}

interface OverallStats {
  hasEvaluated: boolean;
  count: number;
  overallScore: number;
  systemGrade: string;
  avg_semantic: number;
  avg_bleu: number;
  avg_rouge: number;
  avg_tone: number;
  avg_completeness: number;
  avg_safety: number;
  grades: {
    Excellent: number;
    Good: number;
    Fair: number;
    Poor: number;
  };
}

// Project files structure for Sidebar file browser
const projectFiles = [
  { name: "data/generate_dataset.py", desc: "Generates the raw customer email benchmark containing 100 high-fidelity test threads across 15 operation categories.", type: "python" },
  { name: "data/emails.csv", desc: "The compiled benchmark CSV containing email records with distinct emotional tones and expected resolution responses.", type: "csv" },
  { name: "rag/build_index.py", desc: "Computes dense vectors of references using SentenceTransformers and builds FAISS Flat Inner Product indices.", type: "python" },
  { name: "rag/retriever.py", desc: "Calculates cosine similarities of dense vectors to return top-3 matching standard procedures, with built-in TF-IDF fallback.", type: "python" },
  { name: "generator/generate_reply.py", desc: "Prompts Google Gemini Flash/Pro server-side, forcing fact-grounding constraints and preventing order/money hallucinations.", type: "python" },
  { name: "evaluation/metrics.py", desc: "Implements scoring for Semantic Embedding Similarity, BLEU-2, ROUGE-L, Tone Match, completeness, and regex safety audits.", type: "python" },
  { name: "evaluation/evaluate.py", desc: "Orchestrates benchmark cycles, generating suggests and grading full datasets, saving metrics report outputs.", type: "python" },
  { name: "main.py", desc: "Main command-line orchestrator that executes the entire customer response evaluation pipeline end-to-end.", type: "python" }
];

export default function App() {
  const [emails, setEmails] = useState<EmailRecord[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<EmailRecord | null>(null);
  const [activeFileDesc, setActiveFileDesc] = useState<string>("Click on any file to inspect its architectural purpose.");
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isBatchRunning, setIsBatchRunning] = useState(false);
  const isBatchRunningRef = useRef(isBatchRunning);
  useEffect(() => {
    isBatchRunningRef.current = isBatchRunning;
  }, [isBatchRunning]);
  const [batchStatus, setBatchStatus] = useState<BatchStatus>({ isRunning: false, progress: 0, total: 0 });
  
  // Single Evaluation Result
  const [singleResult, setSingleResult] = useState<EvalResult | null>(null);
  const [retrievedRefs, setRetrievedRefs] = useState<RAGReference[]>([]);
  const [isGeminiUsed, setIsGeminiUsed] = useState(false);
  
  // Tab Switcher state
  const [activeTab, setActiveTab] = useState<"analysis" | "report">("analysis");
  const [evaluationResults, setEvaluationResults] = useState<EvalResult[]>([]);
  const [selectedReportResult, setSelectedReportResult] = useState<EvalResult | null>(null);

  // Add / Edit Modal state
  const [isAddEditModalOpen, setIsAddEditModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"add" | "edit">("add");
  const [formError, setFormError] = useState("");
  const [formValues, setFormValues] = useState({
    email_id: "",
    category: "",
    urgency: "Medium",
    tone: "Polite",
    customer_email: "",
    expected_reply: ""
  });

  // System Overall Stats
  const [stats, setStats] = useState<OverallStats>({
    hasEvaluated: false,
    count: 0,
    overallScore: 0,
    systemGrade: "N/A",
    avg_semantic: 0,
    avg_bleu: 0,
    avg_rouge: 0,
    avg_tone: 0,
    avg_completeness: 0,
    avg_safety: 0,
    grades: { Excellent: 0, Good: 0, Fair: 0, Poor: 0 }
  });

  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");

  // Fetch initial data
  useEffect(() => {
    fetchEmails();
    fetchStats();
    fetchEvaluationResults();
    
    // Poll batch status if running
    const interval = setInterval(() => {
      checkBatchStatus();
    }, 2000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchEmails = async () => {
    try {
      const res = await fetch("/api/emails");
      if (!res.ok) return;
      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) return;

      const data = await res.json();
      if (data.emails) {
        setEmails(data.emails);
        if (data.emails.length > 0 && !selectedEmail) {
          setSelectedEmail(data.emails[0]);
        }
      }
    } catch (err) {
      console.warn("Could not fetch emails, server might be restarting:", err);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await fetch("/api/get-evaluation-status");
      if (!res.ok) return;
      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) return;

      const data = await res.json();
      if (data.hasEvaluated) {
        setStats(data);
      }
    } catch (err) {
      console.warn("Could not fetch stats, server might be restarting:", err);
    }
  };

  const fetchEvaluationResults = async () => {
    try {
      const res = await fetch("/api/get-evaluation-results");
      if (!res.ok) return;
      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) return;

      const data = await res.json();
      if (data.hasEvaluated && data.results) {
        setEvaluationResults(data.results);
      }
    } catch (err) {
      console.warn("Could not fetch evaluation results:", err);
    }
  };

  const checkBatchStatus = async () => {
    try {
      const res = await fetch("/api/batch-status");
      if (!res.ok) return;
      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) return;

      const data: BatchStatus = await res.json();
      setBatchStatus(data);
      const wasRunning = isBatchRunningRef.current;
      setIsBatchRunning(data.isRunning);
      
      if (wasRunning && !data.isRunning) {
        // Just finished a batch
        fetchStats();
        fetchEmails();
        fetchEvaluationResults();
      }
    } catch (err) {
      // Quietly ignore polling failures during dev server reloads
    }
  };

  const handleAddEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    
    if (!formValues.category || !formValues.customer_email || !formValues.expected_reply) {
      setFormError("Please fill out all required fields.");
      return;
    }
    
    const url = modalMode === "add" ? "/api/add-email" : "/api/edit-email";
    
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formValues)
      });
      
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Failed to save support case");
      }
      
      fetchEmails();
      setIsAddEditModalOpen(false);
      
      if (modalMode === "edit" && selectedEmail?.email_id === formValues.email_id) {
        setSelectedEmail(data.email);
        setSingleResult(null);
        setRetrievedRefs([]);
      }
    } catch (err: any) {
      setFormError(err.message || "An unexpected error occurred.");
    }
  };

  const openEditModal = (email: EmailRecord) => {
    setModalMode("edit");
    setFormValues({
      email_id: email.email_id,
      category: email.category,
      urgency: email.urgency,
      tone: email.tone,
      customer_email: email.customer_email,
      expected_reply: email.expected_reply
    });
    setFormError("");
    setIsAddEditModalOpen(true);
  };

  const openAddModal = () => {
    setModalMode("add");
    setFormValues({
      email_id: "",
      category: "",
      urgency: "Medium",
      tone: "Polite",
      customer_email: "",
      expected_reply: ""
    });
    setFormError("");
    setIsAddEditModalOpen(true);
  };

  const triggerSingleEvaluation = async (emailId: string) => {
    setIsLoading(true);
    setSingleResult(null);
    setRetrievedRefs([]);
    
    try {
      const res = await fetch("/api/evaluate-single", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email_id: emailId })
      });
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        throw new Error("Response is not JSON format");
      }

      const data: SingleEvalResponse = await res.json();
      setSingleResult(data.evalResult);
      setRetrievedRefs(data.retrieved_references);
      setIsGeminiUsed(data.isGeminiUsed);
      
      // Update local emails list with score
      setEmails(prev => prev.map(e => e.email_id === emailId ? { ...e, status: "Evaluated", score: data.evalResult.final_score } : e));
      
      // Refresh system overall stats
      fetchStats();
    } catch (err) {
      console.error("Failed triggering evaluation:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const startBatchEvaluation = async (count: number) => {
    try {
      const res = await fetch("/api/run-batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ count })
      });
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const contentType = res.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        throw new Error("Response is not JSON format");
      }

      const data = await res.json();
      if (data.status === "started") {
        setIsBatchRunning(true);
        setBatchStatus({ isRunning: true, progress: 0, total: count });
      }
    } catch (err) {
      console.error("Failed running batch evaluation:", err);
    }
  };

  // Filter emails
  const filteredEmails = emails.filter(email => {
    const matchesSearch = email.email_id.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          email.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          email.customer_email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = categoryFilter === "All" || email.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const categories = ["All", ...Array.from(new Set(emails.map(e => e.category)))];

  const getUrgencyColor = (urgency: string) => {
    switch (urgency.toLowerCase()) {
      case "high":
      case "urgent":
        return "text-rose-400 bg-rose-500/10 border-rose-500/20";
      case "medium":
        return "text-amber-400 bg-amber-500/10 border-amber-500/20";
      default:
        return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col antialiased">
      {/* 1. Header Section */}
      <header className="bg-slate-900/80 backdrop-blur border-b border-slate-800 px-6 py-4 sticky top-0 z-50 shadow-lg shadow-slate-950/20">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-xl">
              <Mail className="w-6 h-6 text-indigo-400" id="header_icon" />
            </div>
            <div>
              <h1 className="text-xl font-display font-bold text-slate-100 tracking-tight flex items-center gap-2">
                AI Email Response Evaluator
                <span className="text-[10px] uppercase tracking-widest font-mono bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded border border-indigo-500/30">
                  RAG GROUNDED
                </span>
              </h1>
              <p className="text-xs text-slate-400 mt-0.5 font-sans">
                Unified SentenceTransformers embedding retrieval & Google Gemini Flash evaluation engine.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 w-full md:w-auto self-stretch md:self-auto justify-end">
            {/* System Status Dashboard */}
            {stats.hasEvaluated ? (
              <div className="flex items-center gap-3 bg-slate-950/60 border border-slate-800/80 px-4 py-2 rounded-xl">
                <div className="text-right">
                  <div className="text-[10px] uppercase font-mono text-slate-500 tracking-wider">System Accuracy Score</div>
                  <div className="text-sm font-mono font-bold text-slate-200">
                    {stats.overallScore}% <span className="text-xs font-sans text-slate-400 font-normal">({stats.count} cases)</span>
                  </div>
                </div>
                <div className="h-8 w-px bg-slate-800"></div>
                <div className="px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs font-mono font-bold text-emerald-400 tracking-wide">
                  GRADE: {stats.systemGrade}
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-500 italic flex items-center gap-2 bg-slate-950/40 border border-dashed border-slate-800 px-4 py-2.5 rounded-xl">
                <AlertCircle className="w-4 h-4 text-slate-500" />
                No benchmark reports compiled. Run a batch evaluation to generate analytics.
              </div>
            )}

            {/* API Status */}
            <div className="flex items-center gap-2 bg-slate-950/60 border border-slate-800/80 px-3 py-2 rounded-xl text-xs">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-slate-300 font-mono text-[11px]">Gemini API Active</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Grid Workspace */}
      <div className="max-w-7xl mx-auto px-6 py-6 flex-1 w-full grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left column (Sidebar: File browser & pipeline run card) - width 3 cols */}
        <aside className="lg:col-span-3 flex flex-col gap-6">
          
          {/* File structure browser */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col shadow-md">
            <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-400" /> Python Code Base
            </h2>
            <div className="space-y-1.5 flex-1">
              {projectFiles.map((file, i) => {
                const isActive = activeFile === file.name;
                return (
                  <button
                    key={i}
                    onClick={() => {
                      setActiveFile(file.name);
                      setActiveFileDesc(file.desc);
                    }}
                    className={`w-full text-left text-xs p-2 rounded-lg border flex items-start gap-2 transition-all ${
                      isActive 
                        ? "bg-indigo-600/10 border-indigo-500/40 text-indigo-300" 
                        : "bg-slate-950/40 border-transparent text-slate-300 hover:bg-slate-950/60"
                    }`}
                  >
                    <FileCode className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${isActive ? 'text-indigo-400' : 'text-slate-500'}`} />
                    <span className="font-mono truncate">{file.name}</span>
                  </button>
                );
              })}
            </div>
            
            <div className="mt-4 p-3 bg-slate-950 border border-slate-800/80 rounded-xl text-[11px] leading-relaxed text-slate-400">
              <span className="font-bold text-slate-300 block mb-1">Architecture Note:</span>
              {activeFileDesc}
            </div>
          </div>

          {/* Pipeline Controller Runner */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col gap-4 shadow-md">
            <div>
              <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" /> Pipeline Controller
              </h2>
              <p className="text-[11px] text-slate-500 mt-1">
                Execute orchestrated Python/Gemini batch evaluation runs.
              </p>
            </div>

            {isBatchRunning ? (
              <div className="p-3 bg-indigo-500/5 border border-indigo-500/20 rounded-xl flex flex-col gap-2">
                <div className="flex justify-between items-center text-[11px] font-mono">
                  <span className="text-indigo-400 flex items-center gap-1.5">
                    <RefreshCw className="w-3 h-3 animate-spin" /> Evaluating RAG...
                  </span>
                  <span className="text-slate-400">{batchStatus.progress} / {batchStatus.total} cases</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div 
                    className="bg-indigo-500 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${(batchStatus.progress / batchStatus.total) * 100}%` }}
                  ></div>
                </div>
                <p className="text-[10px] text-slate-500 italic truncate font-mono">
                  Running evaluation metrics metrics.py...
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => startBatchEvaluation(5)}
                  className="bg-slate-950 border border-slate-800 hover:bg-slate-800 text-[11px] font-medium py-2.5 px-3 rounded-xl transition-all text-slate-300 flex items-center justify-center gap-1.5"
                >
                  <Play className="w-3 h-3 text-emerald-400" /> Run Quick (5)
                </button>
                <button
                  onClick={() => startBatchEvaluation(100)}
                  className="bg-indigo-600 hover:bg-indigo-500 text-[11px] font-semibold py-2.5 px-3 rounded-xl transition-all text-white flex items-center justify-center gap-1.5 shadow-md shadow-indigo-600/20"
                >
                  <Sparkles className="w-3 h-3" /> Run Full (100)
                </button>
              </div>
            )}

            <div className="text-[10px] text-slate-500 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span>Full metrics compile results to outputs/ directory.</span>
            </div>
          </div>
          
        </aside>

        {/* Right side container spanning 9 columns */}
        <div className="lg:col-span-9 flex flex-col gap-6">
          {/* Tab Switcher at the top of the workspace */}
          <div className="flex border-b border-slate-800 pb-2 justify-between items-center">
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab("analysis")}
                className={`px-4 py-2 text-xs font-semibold rounded-xl border transition-all ${
                  activeTab === "analysis"
                    ? "bg-indigo-600/10 border-indigo-500/40 text-indigo-300 font-bold"
                    : "bg-transparent border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                Inquiry Analyzer & Playground
              </button>
              <button
                onClick={() => {
                  setActiveTab("report");
                  fetchEvaluationResults();
                }}
                className={`px-4 py-2 text-xs font-semibold rounded-xl border transition-all flex items-center gap-1.5 ${
                  activeTab === "report"
                    ? "bg-indigo-600/10 border-indigo-500/40 text-indigo-300 font-bold"
                    : "bg-transparent border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <TrendingUp className="w-3.5 h-3.5 text-indigo-400" />
                Global Evaluation Report ({stats.count} cases)
              </button>
            </div>
            
            {activeTab === "report" && stats.hasEvaluated && (
              <div className="flex gap-2">
                <a
                  href="/api/download-csv/evaluation.csv"
                  target="_blank"
                  className="bg-slate-900 border border-slate-800 hover:bg-slate-800 text-[10px] font-semibold text-slate-300 rounded-lg px-2.5 py-1.5 flex items-center gap-1.5 transition-all"
                >
                  <Download className="w-3 h-3 text-indigo-400" /> Export CSV Report
                </a>
              </div>
            )}
          </div>

          {activeTab === "analysis" ? (
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
              {/* Mid Column (Benchmark Inquiries Table) - width 5/12 */}
              <section className="md:col-span-5 flex flex-col gap-4">
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col h-[650px] shadow-md">
                  <div className="mb-3.5 flex justify-between items-center">
                    <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-indigo-400" /> Support Dataset
                    </h2>
                    <button
                      onClick={openAddModal}
                      className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-[10px] px-2.5 py-1 rounded-lg flex items-center gap-1 transition-all shadow-sm"
                    >
                      <span>+ Add Case</span>
                    </button>
                  </div>
                  <div className="mb-3">
                    <div className="flex flex-col gap-2">
                      {/* Search */}
                      <input
                        type="text"
                        placeholder="Search inquiries..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-indigo-500/50 transition-all font-sans"
                      />
                      
                      {/* Category Filter Pills */}
                      <div className="flex gap-1 overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
                        {categories.slice(0, 7).map((cat, i) => (
                          <button
                            key={i}
                            onClick={() => setCategoryFilter(cat)}
                            className={`text-[10px] font-medium px-2.5 py-1 rounded-full shrink-0 border transition-all ${
                              categoryFilter === cat 
                                ? "bg-indigo-500/20 border-indigo-500/30 text-indigo-300" 
                                : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-300"
                            }`}
                          >
                            {cat}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Inquiries List */}
                  <div className="flex-1 overflow-y-auto space-y-2 pr-1 scrollbar-thin scrollbar-thumb-slate-800">
                    {filteredEmails.length > 0 ? (
                      filteredEmails.map((email, i) => {
                        const isSelected = selectedEmail?.email_id === email.email_id;
                        return (
                          <button
                            key={i}
                            onClick={() => {
                              setSelectedEmail(email);
                              setSingleResult(null);
                              setRetrievedRefs([]);
                            }}
                            className={`w-full text-left p-3 rounded-xl border flex flex-col gap-1.5 transition-all ${
                              isSelected 
                                ? "bg-indigo-500/5 border-indigo-500/30 shadow-sm" 
                                : "bg-slate-950/30 border-slate-800/80 hover:bg-slate-950/50"
                            }`}
                          >
                            <div className="flex justify-between items-start w-full">
                              <span className="font-mono text-[11px] font-semibold text-slate-400">{email.email_id}</span>
                              <div className="flex items-center gap-1.5">
                                <span className={`text-[9px] font-semibold px-2 py-0.5 rounded-full border ${getUrgencyColor(email.urgency)}`}>
                                  {email.urgency}
                                </span>
                                {email.score && (
                                  <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded">
                                    {email.score}%
                                  </span>
                                )}
                              </div>
                            </div>
                            
                            <p className="text-xs font-semibold text-slate-200 truncate w-full">{email.category}</p>
                            <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">{email.customer_email}</p>
                            
                            <div className="flex items-center gap-1 text-[10px] text-slate-500 font-mono mt-0.5">
                              <Clock className="w-3 h-3" />
                              <span>Tone: <span className="text-indigo-400/80 font-semibold">{email.tone}</span></span>
                            </div>
                          </button>
                        );
                      })
                    ) : (
                      <div className="text-center text-xs text-slate-500 py-10">No inquiries match the active criteria.</div>
                    )}
                  </div>
                </div>
              </section>

              {/* Right Column (Single Inquiry Deep Analysis) - width 7/12 */}
              <main className="md:col-span-7 flex flex-col gap-6">
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col min-h-[650px] shadow-md">
                  {selectedEmail ? (
                    <div className="flex flex-col gap-5 flex-1">
                      {/* Header info */}
                      <div className="flex justify-between items-start border-b border-slate-800 pb-3">
                        <div>
                          <span className="text-xs font-mono text-indigo-400 font-semibold">{selectedEmail.email_id}</span>
                          <h3 className="text-base font-display font-bold text-slate-100">{selectedEmail.category}</h3>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => openEditModal(selectedEmail)}
                            className="bg-slate-800 hover:bg-slate-700 text-xs font-semibold px-3.5 py-2.5 rounded-xl border border-slate-700 text-slate-200 transition-all flex items-center gap-1 shadow-sm"
                          >
                            Edit Case
                          </button>
                          <button
                            onClick={() => triggerSingleEvaluation(selectedEmail.email_id)}
                            disabled={isLoading}
                            className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-xs font-semibold px-4 py-2.5 rounded-xl transition-all text-white flex items-center gap-2 shadow-md shadow-indigo-600/20"
                          >
                            {isLoading ? (
                              <>
                                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                Analyzing...
                              </>
                            ) : (
                              <>
                                <Play className="w-3.5 h-3.5" />
                                Generate & Evaluate
                              </>
                            )}
                          </button>
                        </div>
                      </div>

                      {/* Customer Query */}
                      <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-4">
                        <div className="flex justify-between items-center text-[10px] font-mono text-slate-400 mb-2 border-b border-slate-800/60 pb-1.5">
                          <span>CUSTOMER INQUIRY TEXT</span>
                          <span className="text-indigo-400 font-semibold uppercase">TONE: {selectedEmail.tone}</span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed italic">
                          "{selectedEmail.customer_email}"
                        </p>
                      </div>

                      {/* Grounded reference items */}
                      {retrievedRefs.length > 0 && (
                        <div className="flex flex-col gap-2">
                          <div className="text-[10px] font-mono font-semibold uppercase text-slate-400 tracking-wider flex items-center gap-1.5">
                            <Cpu className="w-3.5 h-3.5 text-indigo-400" /> Retrieved RAG Grounding Context
                          </div>
                          <div className="grid grid-cols-3 gap-2">
                            {retrievedRefs.map((ref, i) => (
                              <div key={i} className="bg-slate-950 border border-slate-800/60 p-2.5 rounded-xl flex flex-col gap-1 text-[10px] leading-snug">
                                <div className="flex justify-between font-mono text-slate-500">
                                  <span>#{ref.email_id}</span>
                                  <span className="text-emerald-400 font-semibold">{(ref.similarity_score * 100).toFixed(0)}% sim</span>
                                </div>
                                <p className="text-slate-300 font-semibold truncate mt-0.5">{ref.category}</p>
                                <p className="text-slate-400 line-clamp-2 text-[9px]">{ref.expected_reply}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Results Section */}
                      {singleResult ? (
                        <div className="space-y-5 flex-1 flex flex-col">
                          {/* Score Bar & Grade Badge */}
                          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 flex items-center justify-between gap-4">
                            <div className="flex-1">
                              <div className="flex justify-between items-center text-[11px] font-mono text-slate-400 mb-1">
                                <span>OVERALL ACCURACY SCORE</span>
                                <span className="text-emerald-400 font-bold">{singleResult.final_score}%</span>
                              </div>
                              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                                <div 
                                  className="bg-emerald-400 h-2 rounded-full"
                                  style={{ width: `${singleResult.final_score}%` }}
                                ></div>
                              </div>
                            </div>
                            <div className="text-center px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                              <div className="text-[9px] font-mono text-slate-400 uppercase tracking-wider">GRADE</div>
                              <div className="text-base font-mono font-bold text-emerald-400">{singleResult.grade.toUpperCase()}</div>
                            </div>
                          </div>

                          {/* Detailed Metric score grid */}
                          <div className="grid grid-cols-2 gap-3">
                            {[
                              { label: "Semantic Sim (40%)", score: singleResult.semantic_similarity * 100, color: "bg-indigo-500", text: "Measures underlying response meaning" },
                              { label: "BLEU Score (10%)", score: singleResult.bleu_score * 100, color: "bg-blue-500", text: "N-gram syntax overlap" },
                              { label: "ROUGE-L (10%)", score: singleResult.rouge_l * 100, color: "bg-cyan-500", text: "LCS structural flow match" },
                              { label: "Tone Match (15%)", score: singleResult.tone_consistency * 100, color: "bg-amber-500", text: "Checks politeness and empathy" },
                              { label: "Completeness (15%)", score: singleResult.completeness * 100, color: "bg-pink-500", text: "Asserts actionable details solved" },
                              { label: "Safety Audit (10%)", score: singleResult.safety_hallucination * 100, color: "bg-emerald-500", text: "Zero ungrounded data policies" }
                            ].map((met, i) => (
                              <div key={i} className="bg-slate-950 border border-slate-800 p-3 rounded-xl flex flex-col gap-1.5">
                                <div className="flex justify-between items-center font-mono text-[10px]">
                                  <span className="text-slate-400 font-medium">{met.label}</span>
                                  <span className="text-slate-200 font-bold">{met.score.toFixed(1)}%</span>
                                </div>
                                <div className="w-full bg-slate-800 rounded-full h-1">
                                  <div className={`${met.color} h-1 rounded-full`} style={{ width: `${met.score}%` }}></div>
                                </div>
                                <p className="text-[9px] text-slate-500 leading-snug">{met.text}</p>
                              </div>
                            ))}
                          </div>

                          {/* Replies comparison slider/box */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1">
                            {/* Expected standard */}
                            <div className="bg-slate-950 border border-slate-800 p-3.5 rounded-xl flex flex-col h-44 overflow-y-auto">
                              <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider mb-1.5 block">EXPECTED REPLY (STANDARD)</span>
                              <p className="text-xs text-slate-300 leading-relaxed font-sans">{singleResult.expected_reply}</p>
                            </div>

                            {/* Generated suggested */}
                            <div className="bg-slate-950 border border-indigo-500/20 p-3.5 rounded-xl flex flex-col h-44 overflow-y-auto">
                              <span className="text-[9px] font-mono text-indigo-400 uppercase tracking-wider mb-1.5 flex items-center justify-between">
                                GENERATED REPLY SUGGESTION
                                {isGeminiUsed && <span className="text-[8px] bg-indigo-500/10 border border-indigo-500/20 px-1 py-0.2 rounded font-semibold text-indigo-300">GEMINI POWERED</span>}
                              </span>
                              <p className="text-xs text-slate-200 leading-relaxed font-sans">{singleResult.generated_reply}</p>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-center p-10 bg-slate-950/20 border border-dashed border-slate-800/80 rounded-xl my-4">
                          <Cpu className="w-10 h-10 text-slate-600 mb-3 animate-pulse" />
                          <p className="text-xs text-slate-400 max-w-xs font-sans">
                            Select any customer support thread and click "Generate & Evaluate" to analyze retrieval grounding accuracy metrics.
                          </p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="flex-1 flex items-center justify-center text-slate-500 italic">
                      Loading support email benchmark dataset...
                    </div>
                  )}
                </div>
              </main>
            </div>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col gap-6 shadow-md min-h-[650px]">
              {/* Global Evaluation Report */}
              {stats.hasEvaluated ? (
                <div className="flex flex-col gap-6">
                  {/* Grid stats overview */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-slate-950 border border-slate-800/80 p-4 rounded-xl flex flex-col justify-between">
                      <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Overall Accuracy Score</div>
                      <div className="mt-2 flex items-baseline gap-1">
                        <span className="text-3xl font-mono font-extrabold text-indigo-400">{stats.overallScore}%</span>
                        <span className="text-xs text-slate-500 font-mono">({stats.count} cases)</span>
                      </div>
                      <span className="mt-2 text-[10px] font-mono bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 px-2.5 py-0.5 rounded w-max font-bold">
                        GRADE: {stats.systemGrade}
                      </span>
                    </div>

                    <div className="bg-slate-950 border border-slate-800/80 p-4 rounded-xl flex flex-col justify-between">
                      <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Grounding & Semantic Sim</div>
                      <div className="mt-2 flex items-baseline gap-1">
                        <span className="text-3xl font-mono font-extrabold text-emerald-400">{(stats.avg_semantic * 100).toFixed(1)}%</span>
                      </div>
                      <p className="mt-2 text-[10px] text-slate-500 font-sans">Retrieval factual correctness verification index.</p>
                    </div>

                    <div className="bg-slate-950 border border-slate-800/80 p-4 rounded-xl flex flex-col justify-between">
                      <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Linguistic BLEU & ROUGE</div>
                      <div className="mt-2 flex flex-col gap-1">
                        <div className="flex justify-between items-center text-[11px] font-mono">
                          <span className="text-slate-400">BLEU Score:</span>
                          <span className="text-slate-200 font-bold">{(stats.avg_bleu * 100).toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between items-center text-[11px] font-mono">
                          <span className="text-slate-400">ROUGE-L Score:</span>
                          <span className="text-slate-200 font-bold">{(stats.avg_rouge * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                      <p className="mt-2 text-[10px] text-slate-500 font-sans">Structural & sentence overlap matching.</p>
                    </div>

                    <div className="bg-slate-950 border border-slate-800/80 p-4 rounded-xl flex flex-col justify-between">
                      <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Tone, Completeness, Safety</div>
                      <div className="mt-1 flex flex-col gap-1 text-[11px] font-mono">
                        <div className="flex justify-between">
                          <span className="text-slate-400">Tone:</span>
                          <span className="text-slate-200">{(stats.avg_tone * 100).toFixed(0)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Completeness:</span>
                          <span className="text-slate-200">{(stats.avg_completeness * 100).toFixed(0)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Safety Check:</span>
                          <span className="text-emerald-400 font-bold">{(stats.avg_safety * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Split results list and details */}
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-2 border-t border-slate-800/60">
                    {/* List Table */}
                    <div className="lg:col-span-7 flex flex-col gap-3">
                      <div className="flex justify-between items-center">
                        <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                          <FileText className="w-4 h-4 text-indigo-400" />
                          Evaluation Cases
                        </h3>
                      </div>
                      
                      <div className="bg-slate-950 border border-slate-800/60 rounded-xl overflow-hidden max-h-[380px] overflow-y-auto scrollbar-thin scrollbar-thumb-slate-800">
                        <table className="w-full text-left border-collapse text-xs">
                          <thead>
                            <tr className="border-b border-slate-800 bg-slate-900/60 font-mono text-[10px] text-slate-400 uppercase tracking-wider">
                              <th className="p-3">ID</th>
                              <th className="p-3">Category</th>
                              <th className="p-3">Tone</th>
                              <th className="p-3 text-right">Score</th>
                              <th className="p-3 text-center">Grade</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60">
                            {evaluationResults.map((res, idx) => {
                              const isSelected = selectedReportResult?.email_id === res.email_id;
                              return (
                                <tr
                                  key={idx}
                                  onClick={() => setSelectedReportResult(res)}
                                  className={`cursor-pointer transition-colors ${
                                    isSelected 
                                      ? "bg-indigo-500/10 hover:bg-indigo-500/15" 
                                      : "hover:bg-slate-900/40"
                                  }`}
                                >
                                  <td className="p-3 font-mono text-indigo-400 font-semibold">{res.email_id}</td>
                                  <td className="p-3 font-medium text-slate-200">{res.category}</td>
                                  <td className="p-3 text-slate-400">{res.tone}</td>
                                  <td className="p-3 text-right font-mono font-bold text-slate-200">{res.final_score.toFixed(1)}%</td>
                                  <td className="p-3 text-center">
                                    <span className={`text-[9px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                                      res.grade === "Excellent" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                                      res.grade === "Good" ? "bg-blue-500/10 text-blue-400 border border-blue-500/20" :
                                      res.grade === "Fair" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" :
                                      "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                                    }`}>
                                      {res.grade}
                                    </span>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Report case breakdown panel */}
                    <div className="lg:col-span-5 flex flex-col gap-3">
                      {selectedReportResult ? (
                        <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-4 flex flex-col gap-3 h-[420px] overflow-y-auto scrollbar-thin scrollbar-thumb-slate-800">
                          <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                            <div>
                              <span className="text-[10px] font-mono text-indigo-400 font-bold">{selectedReportResult.email_id}</span>
                              <h4 className="text-xs font-bold text-slate-200">{selectedReportResult.category}</h4>
                            </div>
                            <div className="text-right">
                              <span className="text-xs font-mono font-bold text-emerald-400">{selectedReportResult.final_score}%</span>
                              <p className="text-[9px] font-mono text-slate-500 uppercase">{selectedReportResult.grade}</p>
                            </div>
                          </div>

                          {/* Customer Query */}
                          <div className="p-2.5 bg-slate-900 border border-slate-800/40 rounded-lg text-[11px] leading-relaxed">
                            <span className="text-[9px] font-mono text-slate-500 uppercase block mb-1">Incoming Query</span>
                            <p className="text-slate-300 italic">"{selectedReportResult.customer_email}"</p>
                          </div>

                          {/* expected reply */}
                          <div className="p-2.5 bg-slate-900 border border-slate-800/40 rounded-lg text-[11px] leading-relaxed">
                            <span className="text-[9px] font-mono text-slate-500 uppercase block mb-1">Expected Golden Standard</span>
                            <p className="text-slate-300">{selectedReportResult.expected_reply}</p>
                          </div>

                          {/* generated reply */}
                          <div className="p-2.5 bg-slate-900 border border-indigo-500/10 rounded-lg text-[11px] leading-relaxed text-indigo-100">
                            <span className="text-[9px] font-mono text-indigo-400 uppercase block mb-1">Generated Output Suggestion</span>
                            <p className="text-slate-200">{selectedReportResult.generated_reply}</p>
                          </div>

                          {/* Metrics breakdown */}
                          <div className="space-y-2 border-t border-slate-800 pt-3">
                            <span className="text-[9px] font-mono text-slate-500 uppercase block">Metric Scores</span>
                            <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                              <div className="flex justify-between border-b border-slate-900 pb-1">
                                <span className="text-slate-400">Semantic Sim:</span>
                                <span className="text-slate-200 font-bold">{(selectedReportResult.semantic_similarity * 100).toFixed(1)}%</span>
                              </div>
                              <div className="flex justify-between border-b border-slate-900 pb-1">
                                <span className="text-slate-400">BLEU syntax:</span>
                                <span className="text-slate-200 font-bold">{(selectedReportResult.bleu_score * 100).toFixed(1)}%</span>
                              </div>
                              <div className="flex justify-between border-b border-slate-900 pb-1">
                                <span className="text-slate-400">ROUGE-L:</span>
                                <span className="text-slate-200 font-bold">{(selectedReportResult.rouge_l * 100).toFixed(1)}%</span>
                              </div>
                              <div className="flex justify-between border-b border-slate-900 pb-1">
                                <span className="text-slate-400">Tone Match:</span>
                                <span className="text-slate-200 font-bold">{(selectedReportResult.tone_consistency * 100).toFixed(1)}%</span>
                              </div>
                              <div className="flex justify-between border-b border-slate-900 pb-1">
                                <span className="text-slate-400">Completeness:</span>
                                <span className="text-slate-200 font-bold">{(selectedReportResult.completeness * 100).toFixed(1)}%</span>
                              </div>
                              <div className="flex justify-between border-b border-slate-900 pb-1">
                                <span className="text-slate-400">Safety Audit:</span>
                                <span className="text-emerald-400 font-bold">{(selectedReportResult.safety_hallucination * 100).toFixed(1)}%</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="bg-slate-950/20 border border-dashed border-slate-800/80 rounded-xl p-6 text-center h-[420px] flex flex-col items-center justify-center text-slate-500">
                          <FileText className="w-8 h-8 text-slate-600 mb-2" />
                          <p className="text-xs max-w-xs font-sans leading-relaxed">
                            Select any case from the list on the left to inspect its complete input prompt, golden expected reply, generated reply, and specific performance metrics.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-10 bg-slate-950/10 border border-dashed border-slate-800/80 rounded-xl my-4">
                  <Activity className="w-12 h-12 text-slate-600 mb-3 animate-pulse" />
                  <h3 className="text-slate-300 font-bold text-sm mb-1 font-sans">No Evaluation Report Compiled</h3>
                  <p className="text-xs text-slate-400 max-w-sm font-sans mb-4 leading-relaxed">
                    A global batch report has not been built yet. Click the buttons below or in the sidebar to run the automated Pipeline Controller.
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => startBatchEvaluation(5)}
                      className="bg-slate-950 border border-slate-800 hover:bg-slate-800 text-xs font-semibold py-2.5 px-4 rounded-xl text-slate-300"
                    >
                      Run Quick (5)
                    </button>
                    <button
                      onClick={() => startBatchEvaluation(100)}
                      className="bg-indigo-600 hover:bg-indigo-500 text-xs font-bold py-2.5 px-5 rounded-xl text-white shadow-md shadow-indigo-600/20"
                    >
                      Run Full (100)
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

      </div>

      {/* 4. Add/Edit Support Case Modal */}
      <AnimatePresence>
        {isAddEditModalOpen && (
          <div className="fixed inset-0 bg-slate-950/85 backdrop-blur-sm flex items-center justify-center p-4 z-[100]">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-lg w-full flex flex-col gap-4 shadow-xl"
            >
              <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                <h3 className="text-sm font-mono font-bold text-slate-100 uppercase tracking-wider flex items-center gap-2">
                  <Mail className="w-4 h-4 text-indigo-400" />
                  {modalMode === "add" ? "Add Grounding Support Case" : "Edit Grounding Support Case"}
                </h3>
                <button
                  onClick={() => setIsAddEditModalOpen(false)}
                  className="text-slate-400 hover:text-slate-200 text-xs font-mono"
                >
                  [CLOSE]
                </button>
              </div>

              <form onSubmit={handleAddEditSubmit} className="space-y-4">
                {formError && (
                  <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-400 font-mono">
                    {formError}
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[10px] font-mono text-slate-400 uppercase tracking-wider mb-1.5">Category *</label>
                    <input
                      type="text"
                      placeholder="e.g. Refund, Order Status"
                      value={formValues.category}
                      onChange={(e) => setFormValues({ ...formValues, category: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500/50"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-[10px] font-mono text-slate-400 uppercase tracking-wider mb-1.5">Urgency</label>
                      <select
                        value={formValues.urgency}
                        onChange={(e) => setFormValues({ ...formValues, urgency: e.target.value })}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500/50"
                      >
                        <option value="Low">Low</option>
                        <option value="Medium">Medium</option>
                        <option value="High">High</option>
                        <option value="Critical">Critical</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[10px] font-mono text-slate-400 uppercase tracking-wider mb-1.5">Tone</label>
                      <select
                        value={formValues.tone}
                        onChange={(e) => setFormValues({ ...formValues, tone: e.target.value })}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500/50"
                      >
                        <option value="Polite">Polite</option>
                        <option value="Friendly">Friendly</option>
                        <option value="Angry">Angry</option>
                        <option value="Urgent">Urgent</option>
                        <option value="Frustrated">Frustrated</option>
                        <option value="Professional">Professional</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-slate-400 uppercase tracking-wider mb-1.5">Customer Email Body *</label>
                  <textarea
                    rows={4}
                    placeholder="Enter the incoming user question/complaint..."
                    value={formValues.customer_email}
                    onChange={(e) => setFormValues({ ...formValues, customer_email: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:border-indigo-500/50 resize-none leading-relaxed"
                    required
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-slate-400 uppercase tracking-wider mb-1.5">Expected Standard Reply (Golden Standard) *</label>
                  <textarea
                    rows={4}
                    placeholder="Enter the accurate, grounded answer that the AI should align with..."
                    value={formValues.expected_reply}
                    onChange={(e) => setFormValues({ ...formValues, expected_reply: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:border-indigo-500/50 resize-none leading-relaxed"
                    required
                  />
                </div>

                <div className="flex justify-end gap-2 border-t border-slate-800 pt-4 mt-2">
                  <button
                    type="button"
                    onClick={() => setIsAddEditModalOpen(false)}
                    className="bg-slate-950 hover:bg-slate-850 text-slate-400 text-xs px-4 py-2 rounded-xl transition-all font-semibold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-5 py-2 rounded-xl transition-all font-semibold shadow-md shadow-indigo-600/20"
                  >
                    {modalMode === "add" ? "Save Case" : "Update Case"}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Footer System Status Bar */}
      <footer className="bg-slate-900 border-t border-slate-800 px-6 py-4 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4 text-xs">
          <div className="flex items-center gap-6 text-slate-400 font-mono text-[11px]">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <CheckCircle className="w-4 h-4" /> pipeline online
            </span>
            <span className="h-4 w-px bg-slate-800"></span>
            <span>DATASET: <span className="text-slate-300">data/emails.csv</span></span>
            <span className="h-4 w-px bg-slate-800"></span>
            <span>MODEL: <span className="text-slate-300">all-MiniLM-L6-v2 + gemini-2.5-flash</span></span>
          </div>
          
          <div className="flex items-center gap-3">
            <a 
              href="/api/download-csv/generated.csv" 
              className="bg-slate-950 hover:bg-slate-850 text-[11px] font-semibold font-mono text-slate-300 border border-slate-800 rounded-lg px-3 py-1.5 transition-all flex items-center gap-1.5 shadow-sm"
              target="_blank"
            >
              <Download className="w-3.5 h-3.5" /> download generated.csv
            </a>
            <a 
              href="/api/download-csv/evaluation.csv" 
              className="bg-slate-950 hover:bg-slate-850 text-[11px] font-semibold font-mono text-slate-300 border border-slate-800 rounded-lg px-3 py-1.5 transition-all flex items-center gap-1.5 shadow-sm"
              target="_blank"
            >
              <Download className="w-3.5 h-3.5" /> download evaluation.csv
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
