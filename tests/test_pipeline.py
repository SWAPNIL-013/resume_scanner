import sys
import os

# -----------------------------------------------------
# Ensure backend imports work exactly like pipeline.py
# -----------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from backend.pipeline import run_pipeline
from unittest.mock import patch


# # -------------------------------
# # Test: Empty or invalid text
# # -------------------------------
# @patch("backend.pipeline.os.path.exists", return_value=True)
# @patch("backend.pipeline.extract_text_and_links")
# def test_pipeline_text_extraction_invalid(mock_extract, mock_exists):
#     # Simulate parser returning empty text
#     mock_extract.return_value = ("", [])

#     result = run_pipeline("/fake/resume.pdf")

#     assert result["status"] == "failed"
#     assert result["error"] == "Empty or invalid text extracted"


# resume json
# @patch("backend.pipeline.os.path.exists", return_value=True)
# @patch("backend.pipeline.extract_text_and_links")
# @patch("backend.pipeline.generate_resume_json")
# @patch("backend.pipeline.validate_resume_json")
# def test_pipeline_validation_fails(mock_validate, mock_gen, mock_extract, mock_exists):
#     mock_extract.return_value = ("This is valid resume text with enough length.", [])
#     mock_gen.return_value = {"name": "", "skills": [], "experience": []}  # dummy json
#     mock_validate.return_value = "Invalid JSON format"

#     result = run_pipeline("/fake/resume.pdf")

#     assert result["status"] == "failed"
#     assert result["error"] == "Invalid JSON format"

# llm error
@patch("backend.pipeline.os.path.exists", return_value=True)
@patch("backend.pipeline.extract_text_and_links")
@patch("backend.pipeline.generate_resume_json")
def test_pipeline_llm_error(mock_gen, mock_extract, mock_exists):
    mock_extract.return_value = ("A" * 200, [])


    # Simulate LLM failing to return JSON
    mock_gen.side_effect = Exception("LLM returned non JSON response")

    result = run_pipeline("/fake/resume.pdf")

    assert result["status"] == "failed"
    assert "LLM returned non JSON response" in result["error"]
