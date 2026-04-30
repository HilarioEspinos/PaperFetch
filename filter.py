from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Paper:
    id: str
    title: str
    abstract: str
    authors: list[str]
    url: str
    source: str
    date: str


@dataclass
class ScoredPaper:
    paper: Paper
    score: int
    matched_groups: list[str]
    matched_terms: list[str]


def get_star_rating(score: int, scoring_config: dict[str, int]) -> str:
    if score >= scoring_config.get("three_stars", 6):
        return "★★★"
    if score >= scoring_config.get("two_stars", 3):
        return "★★"
    return "★"


def score_paper(paper: Paper, config: dict[str, Any]) -> ScoredPaper | None:
    kw = config["keywords"]
    groups = kw["groups"]
    title_weight = kw.get("title_weight", 3)
    abstract_weight = kw.get("abstract_weight", 1)
    min_score = config.get("scoring", {}).get("min_score", 1)

    title_lower = paper.title.lower()
    abstract_lower = paper.abstract.lower()

    title_terms: set[str] = set()
    abstract_terms: set[str] = set()
    matched_groups: set[str] = set()

    for group in groups:
        for term in group["terms"]:
            t = term.lower()
            hit = False
            if t in title_lower:
                title_terms.add(t)
                hit = True
            if t in abstract_lower:
                abstract_terms.add(t)
                hit = True
            if hit:
                matched_groups.add(group["name"])

    score = len(title_terms) * title_weight + len(abstract_terms) * abstract_weight
    if score < min_score:
        return None

    all_terms = sorted(title_terms | abstract_terms)
    return ScoredPaper(
        paper=paper,
        score=score,
        matched_groups=sorted(matched_groups),
        matched_terms=all_terms,
    )


def score_papers(papers: list[Paper], config: dict[str, Any]) -> list[ScoredPaper]:
    results = []
    for paper in papers:
        sp = score_paper(paper, config)
        if sp is not None:
            results.append(sp)
    return results
