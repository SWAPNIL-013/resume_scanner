# helper for experience calculation
from datetime import datetime
def calculate_experience_readable(start_date: str, end_date: str) -> str:
    """
    Calculate human-readable duration between two dates.
    Supports multiple formats and 'Present'/'Current' as end date.
    Inclusive month counting is enabled.
    """
    try:
        if not start_date:
            return ""

        def parse_date(date_str):
            formats = [
                "%Y-%m",    # 2024-06
                "%m-%Y",    # 06-2024
                "%Y/%m",    # 2024/06
                "%m/%Y",    # 06/2024
                "%b %Y",    # Jun 2024
                "%B %Y",    # June 2024
                "%Y %b",    # 2024 Jun
                "%Y %B"     # 2024 June
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None

        start = parse_date(start_date)
        if not start:
            return ""

        if not end_date or end_date.lower() in ["present", "current"]:
            end = datetime.today()
        else:
            end = parse_date(end_date)
            if not end:
                return ""

        # Duration in months (do +1 for inclusive)
        months = (end.year - start.year) * 12 + (end.month - start.month) # + 1
        years, months = divmod(months, 12)

        parts = []
        if years:
            parts.append(f"{years} yr{'s' if years > 1 else ''}")
        if months:
            parts.append(f"{months} mo{'s' if months > 1 else ''}")

        return " ".join(parts) if parts else "0 mos"

    except Exception:
        return ""

# Extract dates from experience section
def extract_start_end(date_str: str, end_param: str = ""):
    """
    Split a single string like "Aug 2024– Jan 2025" or "Jun 2024 to Sep 2025" 
    into start and end dates.
    """
    if not date_str:
        return "", end_param

    # Normalize delimiters
    date_text = date_str.replace('–', '-').replace('to', '-')
    parts = date_text.split('-', 1)
    start = parts[0].strip()
    end = parts[1].strip() if len(parts) > 1 else end_param
    return start, end

# Wrapper to add duration to resume experiences
def add_experience_duration_readable(resume_json: dict) -> dict:
    """
    Adds duration_years to each experience entry in the resume JSON.
    Handles combined date strings automatically.
    """
    for exp in resume_json.get("experience", []):
        # Use combined string if present
        if "dates" in exp and (not exp.get("start_date") or not exp.get("end_date")):
            start, end = extract_start_end(exp["dates"])
        else:
            start = exp.get("start_date", "")
            end = exp.get("end_date", "")

        exp["start_date"] = start
        exp["end_date"] = end
        exp["duration_years"] = calculate_experience_readable(start, end)
    return resume_json

# helper to calculate total experience in float 
import re
from typing import List, Dict, Tuple
def total_experience_from_resume(resume_exp_list: List[Dict]) -> float:
    """
    Calculate total experience in years from resume experience list.
    Each experience should have 'duration_years' in format like '1 yr 2 mos' or '6 mos'.
    
    Returns total experience as float in years.
    """
    total_years = 0.0

    for exp in resume_exp_list:
        dur_str = exp.get("duration_years", "")
        if not dur_str:
            continue

        dur_str = dur_str.lower()
        years = 0.0

        # Extract years
        yr_match = re.search(r"(\d+)\s*yr", dur_str)
        if yr_match:
            years += int(yr_match.group(1))

        # Extract months
        mo_match = re.search(r"(\d+)\s*mo", dur_str)
        if mo_match:
            years += int(mo_match.group(1)) / 12.0

        total_years += years

    return round(total_years, 2)

# format experience years back to readable format 
def format_experience_years(exp_float: float) -> str:
    """
    Convert float years to human-readable format: e.g., 1.58 → "1 yr 7 mo"
    """
    if not exp_float or exp_float <= 0:
        return "0 yr"
    
    years = int(exp_float)
    months = round((exp_float - years) * 12)
    parts = []
    if years > 0:
        parts.append(f"{years} yr{'s' if years > 1 else ''}")
    if months > 0:
        parts.append(f"{months} mo{'s' if months > 1 else ''}")
    return " ".join(parts)

# ----------------------------------------------------------
# Helper: Validate resume JSON
# ----------------------------------------------------------
def validate_resume_json(resume_json: dict, filename: str):
    if not isinstance(resume_json, dict):
        return "Resume JSON generation failed: LLM returned non-dict"

    # Mandatory fields (experience removed — freshers won't have it)
    required_keys = ["name", "skills"]
    missing = [k for k in required_keys if k not in resume_json]
    if missing:
        return f"Resume JSON missing keys: {missing}"

    # Validate name
    name = resume_json.get("name")
    if not isinstance(name, str) or len(name.strip()) == 0:
        return "Resume JSON missing or invalid 'name' field"

    # Reject if LLM puts headings instead of name
    bad_keywords = ["experience", "skills", "summary", "qualification"]
    if any(bk in name.lower() for bk in bad_keywords):
        return "Invalid 'name' — LLM hallucinated a section heading"

    # Name length — relaxed
    if len(name) > 150:
        return "Invalid 'name' — too long or hallucinated"

    return None  # No issues


# LLM Helper 
import os
import json
from dotenv import load_dotenv
from google import genai
import time
import random

# Load env once
load_dotenv()
# default client uses env var if available
_GLOBAL_CLIENT = None
if os.getenv("GEMINI_API_KEY"):
    try:
        _GLOBAL_CLIENT = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    except Exception:
        _GLOBAL_CLIENT = None


def call_llm(prompt: str, model: str = "gemini-2.5-flash", *, api_key: str = None, max_retries: int = 3, backoff_factor: float = 1.0) -> dict:
    """
    Robust wrapper to call Gemini (or compatible) LLM clients.

    Behavior:
    - Retries transient errors with exponential backoff + jitter.
    - Returns a dict on success (parsed JSON) or a structured error dict on failure:
        {"error": {"message": str, "code": optional_int, "type": "llm_error"}}

    Callers should check for the presence of the top-level "error" key.
    """


    def _strip_markdown(s: str) -> str:
        s = s.strip()
        if s.startswith("```json"):
            s = s[len("```json"):].strip()
        if s.startswith("```"):
            s = s[len("```"):].strip()
        if s.endswith("```"):
            s = s[:-len("```")].strip()
        return s

    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            # choose client: prefer provided api_key, else global client
            if api_key:
                client = genai.Client(api_key=api_key)
            else:
                client = _GLOBAL_CLIENT

            if client is None:
                raise RuntimeError("No LLM client available. Provide an API key from the frontend or set GEMINI_API_KEY in env")

            response = client.models.generate_content(
                model=model,
                contents=[{"parts": [{"text": prompt}]}]
            )

            raw_output = _strip_markdown(response.text)
            raw_output = raw_output.replace("\\n", "\n")  # Convert literal backslash-n to real newline
            raw_output = raw_output.replace("\n", " ")    # Then convert all real newlines to spaces (optional)
            import re
            raw_output = re.sub(r"\s+", " ", raw_output).strip()


            # If the SDK surfaces an error structure, try to detect it
            # e.g., some clients may include status/code in attributes
            if hasattr(response, "status") and response.status >= 400:
                msg = getattr(response, "message", getattr(response, "status_text", "LLM returned error"))
                return {"error": {"message": str(msg), "code": int(getattr(response, "status", 0)), "type": "llm_error"}}

            # Parse JSON safely
            try:
                return json.loads(raw_output)
            except json.JSONDecodeError:
                # Return the raw string inside an error structure so callers can log it
                return {"error": {"message": "LLM returned non-JSON response", "raw": raw_output, "type": "llm_error"}}

        except Exception as e:
            # If the exception appears transient (network/503), retry with backoff
            last_exc = e
            err_str = str(e)
            # Basic heuristic: retry on 429 / 502 / 503 / connection issues
            retryable = any(code in err_str for code in ["429", "502", "503", "504"]) or "timed out" in err_str.lower() or "overloaded" in err_str.lower()
            print(f"[LLM ERROR] attempt {attempt}/{max_retries}: {e}")

            if attempt == max_retries or not retryable:
                # Return structured error
                code = None
                # Try to extract numeric code
                import re
                m = re.search(r"(\b\d{3}\b)", err_str)
                if m:
                    try:
                        code = int(m.group(1))
                    except Exception:
                        code = None

                return {"error": {"message": err_str, "code": code, "type": "llm_error"}}

            # Backoff with jitter
            sleep = backoff_factor * (2 ** (attempt - 1))
            sleep = sleep * (0.5 + random.random() * 0.5)  # add jitter between 50%-100%
            time.sleep(sleep)

    # Fallback structured error if loop exits unexpectedly
    return {"error": {"message": str(last_exc), "type": "llm_error"}}
