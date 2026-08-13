from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import get_connection, init_db
from app.scoring import (
    INDUSTRY_OPTIONS,
    INTENT_SIGNALS,
    classify,
    recommended_action,
    score_lead,
)

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Orbit GTM Lead Qualifier", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/")
def root():
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard")
def dashboard(request: Request):
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM leads ORDER BY created_at DESC").fetchall()
    finally:
        conn.close()

    leads = [dict(row) for row in rows]
    counts = {"High": 0, "Medium": 0, "Low": 0}
    for lead in leads:
        counts[lead["classification"]] += 1

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "leads": leads,
            "total": len(leads),
            "high": counts["High"],
            "medium": counts["Medium"],
            "low": counts["Low"],
        },
    )


@app.get("/leads/add")
def add_lead_form(request: Request):
    return templates.TemplateResponse(
        request,
        "add_lead.html",
        {
            "industries": INDUSTRY_OPTIONS,
            "intent_signals": INTENT_SIGNALS,
        },
    )


@app.post("/leads/add")
def add_lead_submit(
    company_name: str = Form(...),
    contact_name: str = Form(...),
    job_title: str = Form(...),
    company_size: int = Form(...),
    industry: str = Form(...),
    website: str = Form(""),
    intent_signal: str = Form(...),
):
    score = score_lead(company_size, job_title, industry, intent_signal)
    classification = classify(score)
    action = recommended_action(classification, job_title)

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO leads (
                company_name, contact_name, job_title, company_size,
                industry, website, intent_signal, score, classification, recommended_action
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_name,
                contact_name,
                job_title,
                company_size,
                industry,
                website,
                intent_signal,
                score,
                classification,
                action,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url="/dashboard", status_code=303)
