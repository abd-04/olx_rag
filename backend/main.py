from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

from retriever import retrieve
from llm import extract_filters, generate_answer

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# ─────────────────────────────
# FASTAPI APP
# ─────────────────────────────

app = FastAPI(
    title="OLX RAG Assistant",
    description="Ask questions about OLX Pakistan listings",
    version="1.0.0"
)


# ─────────────────────────────
# REQUEST + RESPONSE SHAPES
# ─────────────────────────────

class QuestionRequest(BaseModel):
    """
    Shape of request coming from Streamlit frontend.
    Frontend sends JSON like: {"question": "corolla under 20 lakh lahore"}
    """
    question: str


class AnswerResponse(BaseModel):
    """
    Shape of response going back to Streamlit frontend.
    """
    answer:   str
    listings: list   # top 5 listing dicts shown as cards in UI
    filters:  dict   # what filters LLM extracted — useful for debugging


# ─────────────────────────────
# ENDPOINTS
# ─────────────────────────────

@app.get("/")
def root():
    """
    Health check endpoint.
    Visit http://localhost:8000 to confirm backend is running.
    """
    return {"status": "OLX RAG backend is running"}


@app.post("/ask", response_model=AnswerResponse)
def ask(request: QuestionRequest):
    """
    Main endpoint. Streamlit calls this with the user question.

    Flow:
    1. extract filters from question using LLM
    2. retrieve top 5 listings using hybrid search
    3. generate natural language answer using LLM
    4. return answer + listings + filters
    """

    question = request.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    print(f"\nQuestion received: {question}")

    # step 1 — extract structured filters from question
    filters = extract_filters(question)
    print(f"Filters extracted: {filters}")

    # step 2 — hybrid retrieval
    listings = retrieve(question, filters, top_k=5)
    print(f"Listings retrieved: {len(listings)}")

    # step 3 — generate answer
    answer = generate_answer(question, listings)
    print(f"Answer generated")

    return AnswerResponse(
        answer=answer,
        listings=listings,
        filters=filters
    )


# ─────────────────────────────
# RUN
# ─────────────────────────────

if __name__ == "__main__":
    # runs the FastAPI server on port 8000
    # reload=True means server restarts automatically when you change code
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)