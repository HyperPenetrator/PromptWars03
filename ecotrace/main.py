"""
EcoTrace — FastAPI application entry point.

A smart carbon footprint tracker powered by Gemini AI.
"""

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import lifespan
from routers import logs, goals, insights

app = FastAPI(
    title="EcoTrace",
    description="Your Personal Carbon Footprint Companion — powered by Gemini AI",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — restricted to localhost in dev
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(logs.router)
app.include_router(goals.router)
app.include_router(insights.router)

# ---------------------------------------------------------------------------
# Static files — serve the SPA frontend
# ---------------------------------------------------------------------------

import os
from pathlib import Path

# ... 
# later below ...
static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
