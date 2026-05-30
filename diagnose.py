"""Diagnostic: run this ON GitHub Actions to see what it can actually reach.
Add a temporary workflow step `python diagnose.py` (or run via workflow_dispatch).
It prints a table; copy the output back. It changes nothing and saves nothing.
"""
import re
import requests
from urllib.parse import quote

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml',
}
SITEMAP = 'https://kentclarkcenter.org/survey-sitemap.xml'
PAGE = 'https://kentclarkcenter.org/surveys/america-versus-europe/'


def survey_count(text):
    u = set(re.findall(
        r'https://kentclarkcenter\.org/surveys/[A-Za-z0-9_\-]+/', text))
    u.discard('https://kentclarkcenter.org/surveys/')
    return len(u)


def has_votes(text):
    return 'Strongly Agree' in text or 'Agree' in text


def try_get(label, url, headers=None, parse='sitemap'):
    try:
        r = requests.get(url, headers=headers or HEADERS, timeout=60)
        if parse == 'sitemap':
            metric = f'survey_urls={survey_count(r.text)}'
        else:
            metric = f'has_votes={has_votes(r.text)}'
        print(f'{label:24}: HTTP {r.status_code}  len={len(r.text):>7}  {metric}')
    except Exception as e:
        print(f'{label:24}: ERROR {str(e)[:60]}')


print('=' * 70)
print('SITEMAP (the list of all polls)')
print('=' * 70)
try_get('direct', SITEMAP)
try_get('proxy allorigins', 'https://api.allorigins.win/raw?url=' + quote(SITEMAP, safe=''))
try_get('proxy codetabs', 'https://api.codetabs.com/v1/proxy/?quest=' + SITEMAP)
try_get('proxy corsproxy', 'https://corsproxy.io/?url=' + quote(SITEMAP, safe=''))

print()
print('=' * 70)
print('POLL PAGE (one individual survey)')
print('=' * 70)
try_get('direct', PAGE, parse='page')
try_get('proxy allorigins', 'https://api.allorigins.win/raw?url=' + quote(PAGE, safe=''), parse='page')
try_get('proxy codetabs', 'https://api.codetabs.com/v1/proxy/?quest=' + PAGE, parse='page')

print()
print('Done. Copy everything above back into the chat.')
