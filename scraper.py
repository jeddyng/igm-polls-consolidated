#!/usr/bin/env python3
"""
Incremental scraper for IGM/Clark Center economist expert polls.
Only fetches new surveys not already in polls_data.json.
"""

import requests
import re
import json
import time
import random
import os
from bs4 import BeautifulSoup
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

# Browser-like headers to get past Cloudflare/WAF on datacenter IPs.
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    ),
    'Accept': (
        'text/html,application/xhtml+xml,application/xml;q=0.9,'
        'image/avif,image/webp,image/apng,*/*;q=0.8'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

VALID_VOTES = {
    'Strongly Agree', 'Agree', 'Uncertain', 'Disagree',
    'Strongly Disagree', 'No Opinion', 'Did Not Answer',
}
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'polls_data.json')

# Single shared Session so cookies (incl. Cloudflare clearance) persist.
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# Pacing knobs — keep things slow and human-ish.
WARMUP_DELAY = (2.0, 4.0)         # before first real request
INTER_REQUEST_DELAY = (1.5, 3.5)  # between successful per-survey fetches
RETRY_BACKOFF = [5, 15, 30, 60]   # seconds; one entry per retry attempt
MAX_WORKERS = 2                   # was 10 — be gentle


def polite_sleep(low_high):
    low, high = low_high
    time.sleep(random.uniform(low, high))


def fetch_with_retries(url, timeout=30, attempts=4):
    """GET with retries and backoff. Returns Response or raises last error."""
    last_exc = None
    for i in range(attempts):
        try:
            r = SESSION.get(url, timeout=timeout)
            # Treat 403/429/5xx as retryable.
            if r.status_code in (403, 429) or 500 <= r.status_code < 600:
                raise requests.HTTPError(f'{r.status_code} for {url}', response=r)
            r.raise_for_status()
            return r
        except Exception as e:
            last_exc = e
            if i < attempts - 1:
                wait = RETRY_BACKOFF[min(i, len(RETRY_BACKOFF) - 1)]
                # Add jitter so retries don't sync up.
                wait += random.uniform(0, wait * 0.3)
                print(f'  retry {i+1}/{attempts-1} for {url} after {wait:.1f}s ({e})')
                time.sleep(wait)
    raise last_exc


def warmup():
    """Hit the homepage first so Cloudflare can set a clearance cookie."""
    try:
        SESSION.get('https://kentclarkcenter.org/', timeout=30)
    except Exception as e:
        print(f'warmup failed (continuing anyway): {e}')
    polite_sleep(WARMUP_DELAY)


def get_sitemap_urls():
    """Fetch all survey URLs from the WordPress sitemap."""
    r = fetch_with_retries('https://kentclarkcenter.org/survey-sitemap.xml')
    return set(re.findall(
        r'<loc>(https://kentclarkcenter\.org/surveys/[^<]+)</loc>', r.text
    ))


def compute_consensus(votes):
    total = len(votes)
    c = Counter(votes)
    d = {
        k: c.get(v, 0)
        for k, v in [
            ('sa', 'Strongly Agree'), ('a', 'Agree'), ('u', 'Uncertain'),
            ('d', 'Disagree'), ('sd', 'Strongly Disagree'),
            ('no', 'No Opinion'), ('dna', 'Did Not Answer'),
        ]
    }
    d['total'] = total
    active = total - d['dna']
    if active > 0:
        for k in ['sa', 'a', 'u', 'd', 'sd', 'no']:
            d[f'p_{k}'] = round(100 * d[k] / active, 1)
        ag = d['sa'] + d['a']
        dg = d['sd'] + d['d']
        if ag / active > 0.5:
            d['maj'] = 'Agree'
        elif dg / active > 0.5:
            d['maj'] = 'Disagree'
        elif d['u'] / active > 0.4:
            d['maj'] = 'Uncertain'
        else:
            d['maj'] = 'Mixed'
    else:
        for k in ['sa', 'a', 'u', 'd', 'sd', 'no']:
            d[f'p_{k}'] = 0
        d['maj'] = 'N/A'
    return d


def extract_votes_from_table(table):
    votes = []
    for row in table.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) >= 3:
            v = cells[2].get_text(strip=True)
            if v in VALID_VOTES:
                votes.append(v)
    return votes


def parse_survey(url):
    """Parse a single survey page. Returns dict or None."""
    try:
        r = fetch_with_retries(url, timeout=20, attempts=3)
        soup = BeautifulSoup(r.text, 'html.parser')
    except Exception as e:
        print(f'  fetch failed for {url}: {e}')
        return None
    finally:
        # Slow down regardless of success/failure.
        polite_sleep(INTER_REQUEST_DELAY)

    h1 = soup.find('h1')
    title = h1.get_text(strip=True) if h1 else 'Unknown'

    # Date
    date_text = ''
    for t in (soup.find('main') or soup).stripped_strings:
        if re.match(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', t):
            date_text = t.strip()
            break

    # Panel
    panel = 'US'
    for a in soup.find_all('a', href=True):
        if '/survey_group/' in a['href']:
            panel = a.get_text(strip=True)
            break

    # Question texts (multi-question polls)
    qtexts = {}
    for h3 in soup.find_all('h3'):
        m = re.match(r'Question\s+([A-Z]):', h3.get_text(strip=True))
        if m:
            h4 = h3.find_next('h4')
            if h4:
                qtexts[m.group(1)] = h4.get_text(strip=True)

    # Single-question fallback
    if not qtexts:
        for h4 in soup.find_all('h4'):
            t = h4.get_text(strip=True)
            if len(t) > 30 and not any(
                x in t.lower() for x in ['participant', 'recent', 'clark center']
            ):
                qtexts['solo'] = t
                break

    # Find vote tables
    vote_tables = []
    for table in soup.find_all('table'):
        header_row = table.find('tr')
        if header_row:
            headers = [c.get_text(strip=True) for c in header_row.find_all(['th', 'td'])]
            if 'Vote' in headers or 'Confidence' in headers:
                vote_tables.append(table)

    questions = []

    # Strategy 1: match "Question X Participant Responses" headers to tables
    for h3 in soup.find_all('h3'):
        txt = h3.get_text(strip=True)
        m = re.match(r'(Question\s+[A-Z])\s+Participant Responses', txt)
        if not m and txt == 'Participant Responses':
            m_label = ''
        elif m:
            m_label = m.group(1)
        else:
            continue
        table = h3.find_next('table')
        if not table:
            continue
        votes = extract_votes_from_table(table)
        if votes:
            letter_match = re.match(r'Question\s+([A-Z])', m_label)
            qtext = ''
            if letter_match:
                qtext = qtexts.get(letter_match.group(1), '')
            elif 'solo' in qtexts:
                qtext = qtexts['solo']
            questions.append({
                'label': m_label,
                'text': qtext,
                'consensus': compute_consensus(votes),
            })

    # Strategy 2: fallback — match tables to question letters by position
    if not questions and vote_tables:
        if 'solo' not in qtexts and qtexts:
            letters = sorted(qtexts.keys())
            for i, letter in enumerate(letters):
                if i < len(vote_tables):
                    votes = extract_votes_from_table(vote_tables[i])
                    if votes:
                        questions.append({
                            'label': f'Question {letter}',
                            'text': qtexts[letter],
                            'consensus': compute_consensus(votes),
                        })
        elif vote_tables:
            votes = extract_votes_from_table(vote_tables[0])
            if votes:
                questions.append({
                    'label': '',
                    'text': qtexts.get('solo', ''),
                    'consensus': compute_consensus(votes),
                })

    if not questions:
        return None

    return {
        'title': title,
        'url': url,
        'date': date_text,
        'panel': panel,
        'questions': questions,
    }


def main():
    # Load existing data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            existing = json.load(f)
    else:
        existing = []

    existing_urls = {d['url'] for d in existing}
    print(f'Existing surveys: {len(existing)}')

    # Warm up the session against Cloudflare.
    print('Warming up session...')
    warmup()

    # Get all URLs from sitemap
    all_urls = get_sitemap_urls()
    print(f'Sitemap URLs: {len(all_urls)}')

    new_urls = all_urls - existing_urls
    if not new_urls:
        print('No new surveys found. Data is up to date.')
        return

    print(f'New surveys to scrape: {len(new_urls)}')

    # Scrape new surveys — small worker pool, polite delays inside parse_survey.
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(parse_survey, u): u for u in new_urls}
        for f in as_completed(futs):
            r = f.result()
            if r:
                results.append(r)
                print(f'  ✓ {r["title"]}')
            else:
                print(f'  ✗ Failed: {futs[f]}')

    # Merge
    existing.extend(results)
    print(f'Total surveys after merge: {len(existing)}')

    # Save
    with open(DATA_FILE, 'w') as f:
        json.dump(existing, f, indent=2)
    print(f'Saved to {DATA_FILE}')


if __name__ == '__main__':
    main()
