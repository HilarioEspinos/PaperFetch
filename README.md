# PaperFetch

Fetches new papers from arXiv and major physics journals every time you run it, scores them by keyword relevance, and prints a color-coded digest in the terminal. Only papers you haven't seen before are shown.

## Setup (first time only)

You need Python 3.10 or newer.

```
python -m venv venv
venv\Scripts\activate.bat       # Windows
# source venv/bin/activate      # Mac / Linux
pip install -r requirements.txt
```

## Running

```
venv\Scripts\activate.bat
python main.py
```

Run it whenever you want — morning, after lunch, whenever. Papers are only shown once; if you run it twice in a row the second run will show nothing new.

**Useful flags:**

| Flag | Effect |
|---|---|
| `python main.py --all` | Show every fetched paper, even unmatched ones |
| `python main.py --reset` | Forget all previously seen papers and start fresh |
| `python main.py --since 2025-01-15` | Re-display papers stored since that date |

## Covered journals

arXiv (quant-ph, cond-mat.mes-hall, cond-mat.mtrl-sci) · PRX Quantum · PRL · PRA · PRB · PRApplied · PRX · Nature Communications · npj Quantum Information · New Journal of Physics · Nano Letters · Science Advances · Optica Express

---

## Customising keywords (`config.yaml`)

Open `config.yaml`. The `keywords` section controls what papers are shown.

```yaml
keywords:
  title_weight: 3      # a match in the title counts 3×
  abstract_weight: 1   # a match in the abstract counts 1×
  groups:
    - name: "NV centers"
      terms:
        - "nitrogen-vacancy"
        - "NV center"
        - "ODMR"
        # add or remove terms here
    - name: "My new topic"   # add a whole new group like this
      terms:
        - "my keyword"
        - "another keyword"
```

**Scoring:** each distinct matched term adds `title_weight` or `abstract_weight` points. The thresholds for the star rating are also in `config.yaml` under `scoring`:

```yaml
scoring:
  min_score: 1    # papers below this are hidden
  two_stars: 3    # ★★
  three_stars: 6  # ★★★
```

Lower `min_score` to see more papers; raise the star thresholds to make them harder to earn.

### Adding or removing journals

Each feed is listed under `feeds` in `config.yaml`. Remove a line to stop fetching that journal; add a new entry if you find another RSS feed you want:

```yaml
feeds:
  rss:
    - url: https://example.com/feed.rss
      label: "Journal Name"
```

---

## Where seen papers are stored

`~/.paperbot/seen.db` — a small SQLite database. Delete it or run `python main.py --reset` if you want to see everything again from scratch.
