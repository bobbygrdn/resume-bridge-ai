from ddgs import DDGS
from typing import List
import random

JOB_DOMAINS = [
    "site:greenhouse.io",
    "site:boards.greenhouse.io",
    "site:lever.co",
    "site:jobs.lever.co",
    "site:workable.com",
    "site:jobs.smartrecruiters.com",
    "site:ashbyhq.com",
    "site:jobvite.com",
    "site:icims.com",
    "site:recruiterbox.com"
]

def build_domain_query(domains, n=4):
    selected = random.sample(domains, min(n, len(domains)))
    return " OR ".join(selected)

def find_job_urls(query:str, max_results: int=5) -> List[str]:
    """
    Scouts the web for job postings using DuckDuckGo.
    No keys, no cost, just raw results.
    """
    with DDGS() as ddgs:
        full_query = f"{query} {build_domain_query(JOB_DOMAINS)}"

        results = list(ddgs.text(full_query, max_results=max_results))

        links = [r['href'] for r in results if 'href' in r]

        print(f"📡 Scout found {len(links)} candidate URLs: {links}")
        return links