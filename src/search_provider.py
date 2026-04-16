from ddgs import DDGS
from typing import List

def find_job_urls(query:str, max_results: int=5) -> List[str]:
    """
    Scouts the web for job postings using DuckDuckGo.
    No keys, no cost, just raw results.
    """
    with DDGS() as ddgs:
        full_query = f"{query} (site:greenhouse.io OR site:lever.co)"

        results = list(ddgs.text(full_query, max_results=max_results))

        links = [r['href'] for r in results if 'href' in r]

        print(f"📡 Scout found {len(links)} candidate URLs: {links}")
        return links