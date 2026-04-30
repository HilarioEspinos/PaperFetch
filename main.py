from __future__ import annotations
import argparse
import sys
from pathlib import Path

import yaml

from filter import Paper, score_papers
from storage import PaperStore
from output import console, display_digest
from fetchers import fetch_arxiv, fetch_rss

_DEFAULT_CONFIG = Path(__file__).parent / "config.yaml"


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        print(f"Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="paperfetch",
        description="Daily academic paper digest from RSS feeds.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all fetched papers regardless of score.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear the seen database before running.",
    )
    parser.add_argument(
        "--since",
        metavar="YYYY-MM-DD",
        help="Re-display papers stored in the database since this date.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=_DEFAULT_CONFIG,
        metavar="PATH",
        help=f"Path to config.yaml (default: {_DEFAULT_CONFIG})",
    )
    args = parser.parse_args()
    if args.since and args.all:
        parser.error("--since and --all are mutually exclusive.")
    return args


def fetch_all(config: dict) -> tuple[list[Paper], int, int]:
    all_papers: list[Paper] = []
    feeds = config.get("feeds", {})

    arxiv_feeds = feeds.get("arxiv", [])
    for feed in arxiv_feeds:
        papers = fetch_arxiv(feed["url"], feed["label"])
        all_papers.extend(papers)

    rss_feeds = feeds.get("rss", [])
    for feed in rss_feeds:
        papers = fetch_rss(feed["url"], feed["label"])
        all_papers.extend(papers)

    total_feeds = len(arxiv_feeds) + len(rss_feeds)
    return all_papers, len(all_papers), total_feeds


def run_normal(
    config: dict,
    store: PaperStore,
    show_all: bool,
    config_path: Path,
) -> None:
    all_papers, total_fetched, feed_count = fetch_all(config)

    scoring_config = config.get("scoring", {})
    min_score = scoring_config.get("min_score", 1)

    # Score
    if show_all:
        # score everything but don't filter by min_score
        from filter import score_paper
        scored = []
        for p in all_papers:
            # temporarily set min_score=0
            sp = score_paper(p, {**config, "scoring": {**scoring_config, "min_score": 0}})
            if sp is not None:
                scored.append(sp)
    else:
        scored = score_papers(all_papers, config)

    # Deduplicate against seen DB
    new_papers = [sp for sp in scored if not store.is_seen(sp.paper.id)]

    # Save new papers
    for sp in new_papers:
        store.save(sp)

    display_digest(
        scored_papers=new_papers,
        scoring_config=scoring_config,
        config_path=str(config_path.resolve()),
        total_fetched=total_fetched,
        feed_count=feed_count,
    )


def run_since(
    config: dict,
    store: PaperStore,
    since_date: str,
    config_path: Path,
) -> None:
    papers = store.get_since(since_date)
    scoring_config = config.get("scoring", {})
    display_digest(
        scored_papers=papers,
        scoring_config=scoring_config,
        config_path=str(config_path.resolve()),
        total_fetched=len(papers),
        feed_count=0,
        mode_label=f"since {since_date}",
    )


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    store = PaperStore()

    try:
        if args.reset:
            store.clear()
            console.print("[yellow]Seen database cleared.[/yellow]")

        if args.since:
            run_since(config, store, args.since, args.config)
        else:
            run_normal(config, store, args.all, args.config)
    finally:
        store.close()


if __name__ == "__main__":
    main()
