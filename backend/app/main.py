from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="DataTalk — Conversational Text-to-SQL + RAG + Visual Analytics",
    version="0.1.0",
    description="Stage 1+2 MVP. See docs/architecture.md for the full staged roadmap.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok", "message": "DataTalk backend is running. See /docs for the API."}
