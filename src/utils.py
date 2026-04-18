import re

def is_dead_link(markdown: str) -> bool:
    """Detects 404s, expired jobs, and empty pages."""
    dead_signals = [
        "404", "page not found", "job no longer available",
        "this job has expired", "error 404", "site maintenance", "The job you are looing for is no longer open."
    ]
    content = markdown.lower()
    if any(signal in content for signal in dead_signals) or len(content) < 300:
        return True
    return False

def is_index_page(url: str, markdown: str) -> bool:
    """Detects job boards/list pages."""
    index_patterns = [
        r"\?location=",
        r"\?department=",
        r"\?team=",
        r"/jobs/?$",
        r"search\?",
        r"/open-positions/?$",
        r"/careers/?$",
        r"\?error=true",
        r"/apply/?$",
        r"/form/"
    ]
    if any(re.search(p, url, re.IGNORECASE) for p in index_patterns):
        return True
    content = markdown.lower()
    if content.count("apply") > 4 or content.count("view job") > 3:
        return True
    return False

def clean_llm_json(raw_text: str) -> str:
    start = raw_text.find('{')
    end = raw_text.rfind('}')
    return raw_text[start:end + 1] if start != -1 and end != -1 else raw_text
