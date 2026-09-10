from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.advisor import generate_offline_answer
from src.llm_answer import improve_answer_with_llm


app = FastAPI(
    title="Wind Turbine Maintenance Advisor API",
    version="1.0.0",
)


# Allow the Next.js frontend during local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AdvisorRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
    )

    mode: Literal["offline", "llm"] = "offline"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/advisor")
def ask_advisor(request: AdvisorRequest) -> dict[str, Any]:
    try:
        result = generate_offline_answer(request.question)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="The offline advisor could not process the question.",
        ) from exc

    result["answer_mode"] = "offline_advisor"

    if request.mode == "llm":
        try:
            improved_answer = improve_answer_with_llm(
                question=request.question,
                advisor_result=result,
            )

            if improved_answer:
                result["answer"] = improved_answer
                result["answer_mode"] = (
                    "offline_advisor_with_llm_rewriting"
                )

        except Exception as exc:
            # Keep the grounded offline answer if the LLM fails
            result["answer_mode"] = "offline_advisor"
            result["llm_warning"] = str(exc)

    return result