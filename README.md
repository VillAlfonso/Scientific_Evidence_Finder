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



Pre requisites:

Python version: 3.13.7

Ollama  (Make Ollama run in your GPU)
and then pull your model (phi 3)





What to type in the terminals:

pip install -r requirements.txt


(then create a virtual environment)

python -m venv venv


venv\Scripts\activate


cd backend


(run the uvicorn backend)
uvicorn main:app --reload --port 8001


<img width="748" height="298" alt="image" src="https://github.com/user-attachments/assets/49618e14-9ffd-4780-8b32-c3ba0efd0f9d" />


In another terminal run this:




<img width="1241" height="380" alt="image" src="https://github.com/user-attachments/assets/3aaa2a0f-7fc4-46f6-ba39-3b630c85ab4e" />
just type in "ollama serve"

.

.

.

.

.

.

.

.

Screenshots Of the System:


<img width="978" height="710" alt="image" src="https://github.com/user-attachments/assets/a7a40c80-cdc1-4a2f-a059-07e133a77004" />

<img width="975" height="699" alt="image" src="https://github.com/user-attachments/assets/6ac3b55e-89d4-4ada-8f5c-295236b4a46b" />


<img width="973" height="710" alt="image" src="https://github.com/user-attachments/assets/945e8347-6693-4bcb-afa6-e1ea595e7b5d" />

<img width="1917" height="949" alt="image" src="https://github.com/user-attachments/assets/d83931d0-8c38-4679-8762-9115f105c0f8" />

<img width="1898" height="989" alt="image" src="https://github.com/user-attachments/assets/5822941d-a888-48e3-9eab-0cbb5e505c88" />

.

.

.

.

.

.
Link to powerpoint presentation:
https://www.canva.com/design/DAG66nh50bo/634hQXiBUOaUXqQKYDSI_g/edit?utm_content=DAG66nh50bo&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton

