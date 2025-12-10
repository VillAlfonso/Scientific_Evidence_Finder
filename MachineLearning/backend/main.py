from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path
import os
import re
import json

import requests
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from lxml import etree

# =========================
# PATHS & CONFIG
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent  # .../MachineLearning
PAPERS_DIR = BASE_DIR / "papers"  # not strictly needed now, but kept for future
PAPERS_DIR.mkdir(exist_ok=True)

EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

# Ollama config
OLLAMA_HOST = "http://127.0.0.1:11434"
OLLAMA_MODEL = "phi3"   # you already pulled this

# Retrieval settings
TOP_K = 5               # how many final papers to keep
MAX_PAPERS_PER_SOURCE = 30
SNIPPET_CHARS = 600     # how much of each paper to show as abstract/snippet

REQUEST_TIMEOUT = 10    # seconds per API request

app = FastAPI(title="AI Scientific Fact Checker (Multi-API + FAISS)")

# =========================
# Pydantic Models
# =========================

class AnalyzeRequest(BaseModel):
    claim: str

class PaperResult(BaseModel):
    title: str
    abstract: str
    authors: Optional[str] = None
    journal: Optional[str] = None
    published: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None

class AnalyzeResponse(BaseModel):
    claim: str
    verdict: str
    label: str
    confidence: Optional[int] = None
    truth_score: Optional[int] = None
    papers: List[PaperResult]



# =========================
# Internal Paper Candidate
# =========================

@dataclass
class PaperCandidate:
    title: str
    abstract: str
    url: Optional[str]
    source: str


# =========================
# Load Embedding Model
# =========================

print("Loading embedding model...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts: List[str]) -> np.ndarray:
    """Embed a list of texts and return float32 matrix (N, D)."""
    if not texts:
        return np.zeros((0, 768), dtype="float32")
    emb = embedding_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    emb = emb.astype("float32")
    return emb


def embed_query(text: str, dim: int) -> np.ndarray:
    """Embed a single query and reshape to (1, D)."""
    emb = embedding_model.encode([text], convert_to_numpy=True)
    emb = emb.astype("float32")
    if emb.shape[1] != dim:
        raise RuntimeError(f"Embedding dim mismatch: query {emb.shape[1]} vs index {dim}")
    return emb


# =========================
# API SEARCH HELPERS
# =========================

def clean_text(s: Optional[str]) -> str:
    if not s:
        return ""
    # Remove HTML tags
    s = re.sub(r"<[^>]+>", " ", s)
    # Normalize whitespace
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def search_europe_pmc(query: str) -> List[PaperCandidate]:
    """Search Europe PMC for biomedical papers."""
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": query,
        "format": "json",
        "pageSize": str(MAX_PAPERS_PER_SOURCE),
    }

    try:
        r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print("Europe PMC error:", e)
        return []

    results = []
    for item in data.get("resultList", {}).get("result", []):
        title = clean_text(item.get("title", ""))
        abstr = clean_text(item.get("abstractText", "")) or clean_text(item.get("description", ""))
        if not title and not abstr:
            continue

        # Try to build a link (often Europe PMC or PubMed)
        src_id = item.get("id") or ""
        src = item.get("source", "")
        if src and src_id:
            url_paper = f"https://europepmc.org/article/{src}/{src_id}"
        else:
            url_paper = None

        results.append(PaperCandidate(
            title=title,
            abstract=abstr,
            url=url_paper,
            source="EuropePMC",
        ))

    return results


def search_arxiv(query: str) -> List[PaperCandidate]:
    """Search arXiv via its Atom feed."""
    # Simple all-fields search
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": MAX_PAPERS_PER_SOURCE,
    }

    try:
        r = requests.get(base_url, params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        xml_text = r.text
    except Exception as e:
        print("arXiv error:", e)
        return []

    try:
        root = etree.fromstring(xml_text.encode("utf-8"))
    except Exception as e:
        print("arXiv XML parse error:", e)
        return []

    ns = {"a": "http://www.w3.org/2005/Atom"}
    results = []

    for entry in root.findall("a:entry", ns):
        title_el = entry.find("a:title", ns)
        summ_el = entry.find("a:summary", ns)
        link_el = entry.find("a:id", ns)

        title = clean_text(title_el.text if title_el is not None else "")
        abstr = clean_text(summ_el.text if summ_el is not None else "")
        url_paper = link_el.text.strip() if link_el is not None else None

        if not title and not abstr:
            continue

        results.append(PaperCandidate(
            title=title,
            abstract=abstr,
            url=url_paper,
            source="arXiv",
        ))

    return results


def search_crossref(query: str) -> List[PaperCandidate]:
    """Search Crossref for broad literature (many fields)."""
    url = "https://api.crossref.org/works"
    params = {
        "query": query,
        "rows": str(MAX_PAPERS_PER_SOURCE),
    }

    try:
        r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print("Crossref error:", e)
        return []

    items = data.get("message", {}).get("items", [])
    results = []

    for it in items:
        titles = it.get("title") or []
        title = clean_text(titles[0]) if titles else ""
        abstr = clean_text(it.get("abstract", ""))

        # Some Crossref abstracts are in HTML-ish JATS; we already stripped tags.
        if not title and not abstr:
            continue

        url_paper = it.get("URL")
        results.append(PaperCandidate(
            title=title,
            abstract=abstr,
            url=url_paper,
            source="Crossref",
        ))

    return results


def decode_openalex_abstract(inv_idx: dict) -> str:
    """
    OpenAlex stores abstracts as inverted index: {word: [pos1,pos2,...]}.
    We'll reconstruct a sequence based on positions.
    """
    try:
        # positions -> word
        pos_to_word = {}
        for word, positions in inv_idx.items():
            for pos in positions:
                pos_to_word[pos] = word
        if not pos_to_word:
            return ""
        max_pos = max(pos_to_word.keys())
        words = [pos_to_word.get(i, "") for i in range(max_pos + 1)]
        text = " ".join(words)
        return clean_text(text)
    except Exception:
        return ""


def search_openalex(query: str) -> List[PaperCandidate]:
    """Search OpenAlex for works with title/abstract matching query."""
    url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "per-page": str(MAX_PAPERS_PER_SOURCE),
    }

    try:
        r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print("OpenAlex error:", e)
        return []

    results_list = data.get("results", []) or data.get("results", [])
    if not isinstance(results_list, list):
        # Some responses may use 'results' key; fallback to 'data'
        results_list = data.get("data", [])

    results: List[PaperCandidate] = []

    for w in results_list:
        title = clean_text(w.get("display_name", ""))

        abstr_text = ""
        inv = w.get("abstract_inverted_index")
        if isinstance(inv, dict):
            abstr_text = decode_openalex_abstract(inv)

        if not abstr_text:
            # Sometimes OpenAlex doesn't have abstract; skip if completely empty
            continue

        doi = w.get("doi")
        if doi:
            url_paper = f"https://doi.org/{doi}"
        else:
            url_paper = w.get("primary_location", {}).get("source", {}).get("url_for_landing_page") or w.get("id")

        results.append(PaperCandidate(
            title=title,
            abstract=abstr_text,
            url=url_paper,
            source="OpenAlex",
        ))

    return results


# =========================
# COMBINED SEARCH + FAISS RERANK
# =========================

def retrieve_candidates(claim: str) -> List[PaperCandidate]:
    """Call all configured APIs and combine unique candidates."""
    candidates: List[PaperCandidate] = []

    # Call each source (errors are logged and skipped)
    candidates.extend(search_europe_pmc(claim))
    candidates.extend(search_arxiv(claim))
    candidates.extend(search_crossref(claim))
    candidates.extend(search_openalex(claim))

    if not candidates:
        return []

    # Deduplicate by (title, source) or (title, url)
    unique: List[PaperCandidate] = []
    seen = set()

    for c in candidates:
        key = (c.title.lower(), (c.url or "").lower())
        if not c.title and not c.abstract:
            continue
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)

    return unique


def rank_candidates_with_faiss(claim: str, candidates: List[PaperCandidate], top_k: int = TOP_K) -> List[PaperCandidate]:
    if not candidates:
        return []

    texts = [f"{c.title}\n\n{c.abstract}" for c in candidates]
    doc_emb = embed_texts(texts)
    if doc_emb.shape[0] == 0:
        return []

    # Normalize for cosine similarity, then use inner product
    faiss.normalize_L2(doc_emb)
    dim = doc_emb.shape[1]

    index = faiss.IndexFlatIP(dim)
    index.add(doc_emb)

    query_emb = embed_query(claim, dim)
    faiss.normalize_L2(query_emb)

    k = min(top_k, len(candidates))
    distances, indices = index.search(query_emb, k)

    top_candidates: List[PaperCandidate] = []
    for idx in indices[0]:
        top_candidates.append(candidates[int(idx)])

    return top_candidates


# =========================
# OLLAMA FACT-CHECKING
# =========================

def call_ollama_factcheck(claim: str, papers: List[PaperResult]) -> str:
    """Send claim + evidence to Ollama and get a fact-checking analysis."""
    if not papers:
        context = "No relevant papers were found in the scientific APIs."
    else:
        context_parts = []
        for i, p in enumerate(papers, start=1):
            context_parts.append(
                f"[Paper {i}] Source: {p.source or 'unknown'}\n"
                f"Title: {p.title}\n"
                f"Abstract/snippet: {p.abstract}\n"
                f"URL: {p.url or 'N/A'}"
            )
        context = "\n\n".join(context_parts)

    prompt = f"""
You are a scientific fact-checking assistant.

Task:
Evaluate the factual claim below using ONLY the evidence provided from scientific papers.
Do NOT use any outside knowledge that is not in the evidence.

Claim:
\"\"\"{claim}\"\"\"


Evidence from retrieved papers:
{context}


Instructions:
1. Decide if the claim is:
   - True
   - False
   - Mixed/Partially True
   - Uncertain (insufficient or conflicting evidence)

2. Write your answer in this structured format:

Verdict: <True/False/Mixed/Uncertain>

Confidence: <0-100>  (how confident you are in the verdict)

Explanation:
<2-5 sentences explaining your reasoning, directly citing the evidence above by paper number when possible.>
"""

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "You are a rigorous scientific fact-checking assistant."},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
    }

    try:
        r = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=180)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Ollama connection failed: {e}")

    if r.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Ollama error: {r.text}")

    data = r.json()
    content = data.get("message", {}).get("content", "")
    if not content:
        raise HTTPException(status_code=500, detail="Empty response from Ollama")

    return content


def parse_verdict_text(text: str) -> (str, str, Optional[int]):
    """
    Parse Ollama response to extract:
    - label: true/false/mixed/uncertain
    - verdict_text: the full explanation, returned as 'verdict'
    - confidence: int or None
    """
    verdict_match = re.search(r"Verdict:\s*(.+)", text, re.IGNORECASE)
    label_raw = verdict_match.group(1).strip() if verdict_match else text[:50]

    label_norm = label_raw.lower()
    if "true" in label_norm and "false" not in label_norm:
        label = "true"
    elif "false" in label_norm:
        label = "false"
    elif "mixed" in label_norm or "partially" in label_norm:
        label = "mixed"
    elif "uncertain" in label_norm or "insufficient" in label_norm:
        label = "uncertain"
    else:
        label = "unknown"

    conf_match = re.search(r"Confidence:\s*([0-9]{1,3})", text, re.IGNORECASE)
    confidence = None
    if conf_match:
        try:
            confidence = int(conf_match.group(1))
        except ValueError:
            confidence = None

    verdict_text = text.strip()
    return label, verdict_text, confidence


# =========================
# ROUTES
# =========================

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "AI Scientific Fact Checker backend (multi-API + FAISS) is running.",
        "model": OLLAMA_MODEL,
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_claim(req: AnalyzeRequest):
    claim = req.claim.strip()
    if not claim:
        raise HTTPException(status_code=400, detail="Claim must not be empty.")

    # 1) Retrieve candidate papers from APIs
    candidates = retrieve_candidates(claim)
    if not candidates:
        # Still ask Ollama, but with explicit "no evidence" context
        analysis_text = call_ollama_factcheck(claim, [])
        label, verdict_text, confidence = parse_verdict_text(analysis_text)
        return AnalyzeResponse(
    claim=claim,
    verdict=verdict_text,
    label=label,
    confidence=confidence,
    truth_score=confidence,   # NEW: Use same number for bar
    papers=paper_results,
)


    # 2) Rank with FAISS using local embeddings
    top_candidates = rank_candidates_with_faiss(claim, candidates, top_k=TOP_K)

    # 3) Convert to PaperResult for API output and Ollama context
    paper_results: List[PaperResult] = [
        PaperResult(
            title=c.title,
            abstract=(c.abstract[:SNIPPET_CHARS] + ("..." if len(c.abstract) > SNIPPET_CHARS else "")),
            url=c.url,
            source=c.source,
        )
        for c in top_candidates
    ]

    # 4) Ask Ollama to fact-check using those papers
    analysis_text = call_ollama_factcheck(claim, paper_results)

    # 5) Parse verdict/label/confidence
    label, verdict_text, confidence = parse_verdict_text(analysis_text)

    return AnalyzeResponse(
    claim=claim,
    verdict=verdict_text,
    label=label,
    confidence=confidence,
    truth_score=confidence,
    papers=paper_results,
)

