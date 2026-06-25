from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=5, max_length=254)
    company: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: str
    password: str


class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    company: str = Field(default="Acme Corp", max_length=200)
    location: str = Field(default="India", max_length=200)
    description: str = Field(min_length=40, max_length=50_000)
    salary_min_lpa: float = Field(default=20, ge=0, le=500)
    salary_max_lpa: float = Field(default=40, ge=0, le=500)


class RankingRunRequest(BaseModel):
    job_id: int
    scope: Literal["sample", "full"] = "full"
    max_candidates: int | None = Field(default=None, ge=1, le=100_000)
    limit: int = Field(default=100, ge=1, le=100)


class ShiftEvaluationRequest(BaseModel):
    description: str = Field(min_length=40, max_length=50_000)
    title: str = Field(default="Alternative role", max_length=200)
    location: str = Field(default="India", max_length=200)
    salary_min_lpa: float = Field(default=20, ge=0, le=500)
    salary_max_lpa: float = Field(default=40, ge=0, le=500)


class InterviewQuestionRequest(BaseModel):
    use_ollama: bool = False


class ReasoningAuditRequest(BaseModel):
    use_ollama: bool = True


class ApiMessage(BaseModel):
    message: str
    details: dict[str, Any] | None = None
