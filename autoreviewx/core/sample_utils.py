# autoreviewx/core/sample_utils.py
import re


def extract_samples(text: str) -> dict:
    """
    Try to extract number of participants or sample size from full text.
    """
    participants = ""
    matches = re.findall(r"(?:\b[Nn]\s*=?\s*|participants\s*=\s*|sample size\s*[:=]?\s*)(\d{2,5})", text)
    if matches:
        participants = max(matches, key=len)  # largest number found (heuristic)

    return {
        "participants": participants
    }