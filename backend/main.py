"""
FastAPI backend for InsureBot AI.

Endpoints:
  POST /chat         → RAG + Ollama question answering
  POST /recommend    → Insurance recommendations
  GET  /policies     → List policies
  POST /policy       → Create a policy
  DELETE /policy/{id} → Cancel a policy
"""

from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db.models import init_db, get_db
from backend.db import crud
from backend.rag.qa import answer
from backend.agents.recommender import recommend


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="InsureBot AI",
    description="Offline Insurance AI powered by Ollama + ChromaDB",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Schemas ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(default="mistral")
    top_k: int = Field(default=3, ge=1, le=10)


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list


class RecommendRequest(BaseModel):
    age: int = Field(..., ge=0, le=120)
    income: float = Field(..., ge=0)
    dependents: int = Field(default=0, ge=0)
    has_vehicle: bool = Field(default=False)
    has_house: bool = Field(default=False)


class PolicyCreateRequest(BaseModel):
    user_name: str = Field(..., min_length=1, max_length=100)
    policy_type: str = Field(..., min_length=1, max_length=50)
    premium: float = Field(..., gt=0)


class PolicyResponse(BaseModel):
    id: int
    user_name: str
    policy_type: str
    premium: float
    status: str
    created_at: str

    @classmethod
    def from_orm_policy(cls, policy):
        return cls(
            id=policy.id,
            user_name=policy.user_name,
            policy_type=policy.policy_type,
            premium=policy.premium,
            status=policy.status,
            created_at=policy.created_at.isoformat(),
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "InsureBot AI"}


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(request: ChatRequest):
    """RAG-powered Q&A using ChromaDB context and Ollama LLM."""
    result = answer(
        question=request.question,
        top_k=request.top_k,
        model=request.model,
    )
    return ChatResponse(
        question=result["question"],
        answer=result["answer"],
        sources=result["sources"],
    )


@app.post("/recommend", tags=["Recommendations"])
def get_recommendations(request: RecommendRequest):
    """Return personalized insurance recommendations."""
    profile = {
        "age": request.age,
        "income": request.income,
        "dependents": request.dependents,
        "has_vehicle": request.has_vehicle,
        "has_house": request.has_house,
    }
    result = recommend(profile)
    return result


@app.get("/policies", response_model=List[PolicyResponse], tags=["Policies"])
def list_policies(
    user_name: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all policies, optionally filtered by user_name or status."""
    policies = crud.list_policies(db, user_name=user_name, status=status)
    return [PolicyResponse.from_orm_policy(p) for p in policies]


@app.post("/policy", response_model=PolicyResponse, tags=["Policies"])
def create_policy(request: PolicyCreateRequest, db: Session = Depends(get_db)):
    """Create a new insurance policy."""
    policy = crud.create_policy(
        db,
        user_name=request.user_name,
        policy_type=request.policy_type,
        premium=request.premium,
    )
    return PolicyResponse.from_orm_policy(policy)


@app.delete("/policy/{policy_id}", response_model=PolicyResponse, tags=["Policies"])
def cancel_policy(policy_id: int, db: Session = Depends(get_db)):
    """Cancel a policy by ID."""
    policy = crud.cancel_policy(db, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    return PolicyResponse.from_orm_policy(policy)
