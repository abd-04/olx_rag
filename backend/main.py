import logging

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from llm import LLMUnavailable, extract_filters, generate_answer
from retriever import RetrievalUnavailable, retrieve

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="OLX RAG Assistant",
    description="Grounded hybrid retrieval for OLX Pakistan vehicle listings",
    version="2.0.0",
)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class AnswerResponse(BaseModel):
    answer: str
    listings: list[dict]
    filters: dict


class SearchRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    filters: dict = Field(default_factory=dict)
    top_k: int = Field(default=5, ge=1, le=20)


@app.get("/")
def root():
    return {"status": "ok", "service": "olx-rag-backend"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AnswerResponse)
def ask(request: QuestionRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        filters = extract_filters(question)
    except LLMUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    try:
        listings = retrieve(question, filters, top_k=5)
    except RetrievalUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return AnswerResponse(
        answer=generate_answer(question, listings),
        listings=listings,
        filters=filters,
    )


@app.post("/search")
def search(request: SearchRequest):
    """Deterministic retrieval endpoint used by evals and debugging."""
    try:
        listings = retrieve(request.question.strip(), request.filters, request.top_k)
    except RetrievalUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {"listings": listings, "filters": request.filters}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
