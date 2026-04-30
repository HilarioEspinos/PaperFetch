from __future__ import annotations
from datetime import date

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich import box

from filter import ScoredPaper, get_star_rating

console = Console()

_STAR_STYLES = {
    "★★★": "bold gold1",
    "★★": "bold yellow",
    "★": "white",
}

_MAX_AUTHORS = 5


def _stars_text(stars: str) -> Text:
    t = Text()
    t.append(stars, style=_STAR_STYLES.get(stars, "white"))
    return t


def _panel_title(sp: ScoredPaper, stars: str) -> Text:
    t = Text()
    t.append(f"[{sp.paper.source}]", style="bold cyan")
    t.append("  ")
    t.append(stars, style=_STAR_STYLES.get(stars, "white"))
    if sp.matched_groups:
        t.append("  ", style="default")
        t.append(" · ".join(sp.matched_groups), style="italic dim")
    return t


def _format_authors(authors: list[str]) -> str:
    if not authors:
        return "Unknown"
    shown = authors[:_MAX_AUTHORS]
    extra = len(authors) - _MAX_AUTHORS
    result = ", ".join(shown)
    if extra > 0:
        result += f" +{extra} more"
    return result


def _display_paper(sp: ScoredPaper, scoring_config: dict) -> None:
    p = sp.paper
    stars = get_star_rating(sp.score, scoring_config)

    body = Text()
    body.append(p.title + "\n", style="bold white")
    body.append("Authors: ", style="dim")
    body.append(_format_authors(p.authors) + "\n", style="default")
    body.append("URL: ", style="dim")
    body.append(p.url, style=f"link {p.url} underline blue")
    body.append("\n")
    body.append("Keywords: ", style="dim")
    body.append(", ".join(sp.matched_terms), style="italic")

    console.print(
        Panel(
            body,
            title=_panel_title(sp, stars),
            title_align="left",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )


def display_digest(
    scored_papers: list[ScoredPaper],
    scoring_config: dict,
    config_path: str,
    total_fetched: int,
    feed_count: int,
    mode_label: str = "",
) -> None:
    today = date.today().isoformat()
    n = len(scored_papers)

    # Header
    header = Text(justify="center")
    header.append("PaperFetch digest", style="bold white")
    header.append(f"  —  {today}", style="dim")
    if mode_label:
        header.append(f"  —  {mode_label}", style="dim yellow")
    else:
        header.append(f"  —  {n} match{'es' if n != 1 else ''}", style="bold green")

    console.print(Panel(header, box=box.DOUBLE_EDGE, style="bold"))

    if not scored_papers:
        console.print("\n  [dim]No matching papers.[/dim]\n")
    else:
        # Sort: score desc, then source alpha
        sorted_papers = sorted(
            scored_papers, key=lambda s: (-s.score, s.paper.source)
        )
        for sp in sorted_papers:
            _display_paper(sp, scoring_config)

    # Footer
    console.print(
        Rule(
            f"Fetched [bold]{total_fetched}[/bold] papers from "
            f"[bold]{feed_count}[/bold] feeds  ·  Config: [dim]{config_path}[/dim]"
        )
    )
