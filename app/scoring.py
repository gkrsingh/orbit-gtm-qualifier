import re

TARGET_INDUSTRIES = ["SaaS", "Manufacturing", "Financial Services", "Healthcare"]
INDUSTRY_OPTIONS = TARGET_INDUSTRIES + ["Retail", "Other"]

INTENT_SIGNALS = ["strong", "medium", "weak"]

_SENIOR_KEYWORDS = ("vp", "vice president", "director", "head", "chief")
# Matches C-level abbreviations like CEO, CFO, CTO, COO, CMO, CIO, CISO, CHRO, etc.
_C_LEVEL_PATTERN = re.compile(r"\bc[a-z]{1,3}o\b", re.IGNORECASE)


def is_senior_title(job_title: str) -> bool:
    title = job_title.lower()
    if any(keyword in title for keyword in _SENIOR_KEYWORDS):
        return True
    return bool(_C_LEVEL_PATTERN.search(title))


def score_lead(company_size: int, job_title: str, industry: str, intent_signal: str) -> int:
    score = 0
    if company_size > 500:
        score += 20
    if is_senior_title(job_title):
        score += 30
    if intent_signal == "strong":
        score += 30
    if industry in TARGET_INDUSTRIES:
        score += 20
    return score


def classify(score: int) -> str:
    if score >= 100:
        return "High"
    if score >= 60:
        return "Medium"
    return "Low"


def recommended_action(classification: str, job_title: str) -> str:
    senior = is_senior_title(job_title)

    if classification == "High":
        if senior:
            return "Fast-track to sales — schedule a demo with this decision-maker immediately."
        return "Fast-track to sales — high-fit account, loop in a senior stakeholder."

    if classification == "Medium":
        if senior:
            return "Engage with targeted outreach — decision-maker, but needs further qualification."
        return "Nurture with targeted content — solid fit, build toward the decision-maker."

    if senior:
        return "Add to long-term nurture — senior contact, but low overall fit."
    return "Low priority — add to general nurture campaign."
