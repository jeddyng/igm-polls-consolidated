#!/usr/bin/env python3
"""
Incremental scraper for IGM/Clark Center economist expert polls.
Only fetches new surveys not already in polls_data.json.
"""

import requests
import re
import json
import time
import os
from bs4 import BeautifulSoup
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html',
}
VALID_VOTES = {
    'Strongly Agree', 'Agree', 'Uncertain', 'Disagree',
    'Strongly Disagree', 'No Opinion', 'Did Not Answer',
}
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'polls_data.json')


def get_sitemap_urls():
    """Fetch all survey URLs from the WordPress sitemap."""
    r = requests.get(
        'https://kentclarkcenter.org/survey-sitemap.xml',
        headers=HEADERS, timeout=30,
    )
    r.raise_for_status()
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
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, 'html.parser')
    except Exception:
        return None

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
            # Find matching question text
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

    # Get all URLs from sitemap
    all_urls = get_sitemap_urls()
    print(f'Sitemap URLs: {len(all_urls)}')

    new_urls = all_urls - existing_urls
    if not new_urls:
        print('No new surveys found. Data is up to date.')
        return

    print(f'New surveys to scrape: {len(new_urls)}')

    # Scrape new surveys
    results = []
    with ThreadPoolExecutor(max_workers=10) as ex:
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
