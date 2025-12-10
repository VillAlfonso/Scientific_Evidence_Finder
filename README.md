# Scientific_Evidence_Finder

PHP Frontend + FastAPI Backend + FAISS Retrieval + Ollama LLM

A full-stack AI system that evaluates scientific claims using real research papers. The pipeline retrieves papers from multiple scientific APIs, ranks them using vector embeddings + FAISS, and sends the best evidence to an LLM (Ollama) to generate a verdict with confidence.



Scientific Paper Retrieval

Automatically collects papers from:

-EuropePMC

-Crossref

-arXiv

-OpenAlex




Evidence-Based Fact Checking

-Embeds claims + papers using SentenceTransformers (all-mpnet-base-v2)

-Ranks papers with FAISS cosine similarity

-Passes top papers to Ollama LLM (phi3 or any model)





LLM Verdict

Returns:

-Verdict: True / False / Mixed / Uncertain

-Confidence Score (0–100)

-Explanation referencing papers


Database Persistence

Stored in MySQL:

-Claim text

-Verdict text

-Retrieved papers (title, abstract, authors, etc.)

-Timestamps




Frontend UI (PHP)


-Claim submission page

-Results page with verdict + evidence

-Full History Viewer with details for each claim

-Delete entries

-View full analysis



System Architecture

<img width="489" height="330" alt="image" src="https://github.com/user-attachments/assets/486f3a24-5c9c-437c-b8f6-786bc0b6477c" />


Project Folder Structure

<img width="488" height="337" alt="image" src="https://github.com/user-attachments/assets/5d7062e3-5781-446b-ba2f-15a0d04537f7"/>

