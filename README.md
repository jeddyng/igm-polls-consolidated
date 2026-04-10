# IGM Economist Expert Polls — Consensus Database

A self-updating static site that scrapes all [IGM/Clark Center](https://kentclarkcenter.org/) economist expert polls and displays consensus data with interactive charts.

## Features

- **552+ surveys, 1100+ questions** from the US, European, and Finance expert panels
- Searchable, filterable, sortable poll browser with consensus bar charts
- Consensus Insights page: strongest agreements, disagreements, most polarized, most uncertain
- Archive links (Web Archive + Archive.is) for every poll
- Auto-updates via GitHub Actions (checks for new polls twice a week)

## How it works

1. **`scraper.py`** — Incremental scraper. Reads the sitemap, compares against `polls_data.json`, and only fetches new surveys.
2. **`build_site.py`** — Reads `polls_data.json` and generates a self-contained `docs/index.html` with all data embedded.
3. **GitHub Actions** — Runs on schedule (Mon/Thu 08:00 UTC), scrapes new polls, rebuilds the site, deploys to GitHub Pages, and commits the updated data.

## Setup

1. Fork/clone this repo
2. Enable GitHub Pages (Settings → Pages → Source: `gh-pages` branch)
3. The Actions workflow will auto-run on schedule, or trigger manually via Actions tab

### Run locally

```bash
pip install requests beautifulsoup4
python scraper.py      # Fetch new polls
python build_site.py   # Build docs/index.html
open docs/index.html   # View locally
```

## Data format

`polls_data.json` contains an array of survey objects:

```json
{
  "title": "Minimum Wage",
  "url": "https://kentclarkcenter.org/surveys/minimum-wage/",
  "date": "February 26, 2013",
  "panel": "US",
  "questions": [
    {
      "label": "Question A",
      "text": "If the federal minimum wage is raised gradually to $15-per-hour...",
      "consensus": {
        "sa": 0, "a": 2, "u": 8, "d": 16, "sd": 3, "no": 1, "dna": 7,
        "p_sa": 0, "p_a": 6.7, "p_u": 26.7, "p_d": 53.3, "p_sd": 10.0, "p_no": 3.3,
        "total": 37, "maj": "Disagree"
      }
    }
  ]
}
```

## License

Data sourced from the [Kent A. Clark Center for Global Markets](https://kentclarkcenter.org/) at Chicago Booth. This tool is for research and educational use.
