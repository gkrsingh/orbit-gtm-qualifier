from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.exceptions import RequestValidationError
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


def _add_lead_form_response(request: Request, error: str, status_code: int = 400):
    return templates.TemplateResponse(
        request,
        "add_lead.html",
        {
            "industries": INDUSTRY_OPTIONS,
            "intent_signals": INTENT_SIGNALS,
            "error": error,
        },
        status_code=status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Without this, a bad Form value (e.g. non-numeric company_size) bubbles up
    # as FastAPI's default raw JSON 422 body instead of a page a user can read.
    if request.url.path == "/leads/add":
        return _add_lead_form_response(
            request, "Please check your input — one or more fields were invalid."
        )
    raise exc


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
            "error": None,
        },
    )


@app.post("/leads/add")
def add_lead_submit(
    request: Request,
    company_name: str = Form(..., min_length=1, max_length=200),
    contact_name: str = Form(..., min_length=1, max_length=200),
    job_title: str = Form(..., min_length=1, max_length=200),
    company_size: int = Form(..., gt=0),
    industry: str = Form(...),
    # website is intentionally free-text with no format validation for this demo's scope.
    website: str = Form(""),
    intent_signal: str = Form(...),
):
    company_name = company_name.strip()
    contact_name = contact_name.strip()
    job_title = job_title.strip()
    if not company_name or not contact_name or not job_title:
        return _add_lead_form_response(request, "Text fields can't be blank or whitespace only.")

    # The HTML <select> constrains these in the browser, but a direct POST
    # (curl, another client) can send anything, so re-check server-side.
    if industry not in INDUSTRY_OPTIONS:
        return _add_lead_form_response(request, "Please select a valid industry.")
    if intent_signal not in INTENT_SIGNALS:
        return _add_lead_form_response(request, "Please select a valid intent signal.")

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
