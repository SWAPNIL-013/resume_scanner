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



# ----- LLM HELPER ------
import os
import json
from dotenv import load_dotenv
from google import genai
# Load env once
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def call_llm(prompt: str, model: str = "gemini-2.5-flash") -> dict:
    """
    Generic helper to call Gemini API with a prompt and return parsed JSON.
    Strips markdown fences and safely loads JSON.
    """
    try:
        response = client.models.generate_content(
            model=model,
            contents=[{"parts": [{"text": prompt}]}]
        )
        raw_output = response.text.strip()

        # Strip markdown fences if present
        if raw_output.startswith("```json"):
            raw_output = raw_output[len("```json"):].strip()
        if raw_output.startswith("```"):
            raw_output = raw_output[len("```"):].strip()
        if raw_output.endswith("```"):
            raw_output = raw_output[:-len("```")].strip()

        return json.loads(raw_output)
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return {}
