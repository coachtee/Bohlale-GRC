"""
Framework Studio extraction (spec §18): turns uploaded/pasted source
text into a DRAFT domain/requirement structure for human review. This
uses a simple heading-detection heuristic (numbered headings such as
"4.3 Determining the scope") rather than any external ML — the AI
service is additionally asked for a short structural summary purely as
an aid to the reviewer, and is itself logged via AIGeneration for
traceability. Nothing here is trusted directly into a live Framework;
a human always reviews `extracted_data` before publish.
"""

import re

HEADING_RE = re.compile(r"^(?P<code>\d+(?:\.\d+)*)[\.\)]?\s+(?P<title>[A-Z][^\n]{2,120})$")


def extract_structure(text):
    """
    Returns {"domains": [{"code", "title", "requirements": [{"ref_code","title"}]}]}
    Top-level numbers (e.g. "4", "5") become domains; sub-numbers
    (e.g. "4.1", "4.2") become requirements under the nearest domain.
    Falls back to a single 'General' domain with no requirements if no
    numbered headings are detected, so review still has something to
    correct rather than erroring out.
    """
    domains = []
    domain_by_code = {}
    current_domain = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        code = match.group("code")
        title = match.group("title").strip()
        depth = code.count(".")
        if depth == 0:
            current_domain = {"code": code, "title": title, "requirements": []}
            domains.append(current_domain)
            domain_by_code[code] = current_domain
        else:
            parent_code = code.split(".")[0]
            parent = domain_by_code.get(parent_code, current_domain)
            if parent is None:
                parent = {"code": parent_code, "title": f"Section {parent_code}", "requirements": []}
                domains.append(parent)
                domain_by_code[parent_code] = parent
            parent["requirements"].append({"ref_code": code, "title": title})

    if not domains:
        domains = [{"code": "1", "title": "General", "requirements": []}]

    return {"domains": domains}
