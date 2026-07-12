"""
news.py
=======
Cerca i classifica titulars de noticies recents d'una accio, utilitzant el
feed RSS gratuit de Google News (no cal API key ni cap servei de pagament).
"""

from typing import List

import feedparser

from config import (
    NEWS_MAX_HEADLINES,
    NEWS_LANGUAGE,
    NEWS_REGION,
    NEWS_CATEGORY_SCORES,
    NEWS_CATEGORY_KEYWORDS,
    NEWS_ROUNDUP_BLOCKLIST,
    NEWS_ROUNDUP_COMMA_THRESHOLD,
)
from models import NewsItem, NewsAnalysis

NO_NEWS_CATEGORY: str = "Sense noticia"
GOOGLE_NEWS_RSS_TEMPLATE: str = (
    "https://news.google.com/rss/search?q={query}&hl={lang}&gl={region}&ceid={region}:{lang}"
)


def _build_query(company_name: str) -> str:
    """Construeix la query de cerca a partir del nom de l'empresa."""
    return company_name.replace(" ", "+")


def fetch_headlines(company_name: str, max_headlines: int = NEWS_MAX_HEADLINES) -> List[NewsItem]:
    """Descarrega titulars recents sobre una empresa via Google News RSS.

    Args:
        company_name: terme de cerca (p.ex. "Indra", "Grifols").
        max_headlines: nombre maxim de titulars a recollir.

    Returns:
        Llista de NewsItem sense categoria assignada encara (es fa despres
        amb classify_headline). Llista buida si el feed no respon.
    """
    url = GOOGLE_NEWS_RSS_TEMPLATE.format(
        query=_build_query(company_name), lang=NEWS_LANGUAGE, region=NEWS_REGION
    )
    try:
        feed = feedparser.parse(url)
    except Exception:
        return []

    items: List[NewsItem] = []
    for entry in feed.entries[:max_headlines]:
        title = getattr(entry, "title", "").strip()
        source_obj = getattr(entry, "source", None)
        source = getattr(source_obj, "title", "Google News") if source_obj else "Google News"
        link = getattr(entry, "link", None)
        if title:
            items.append(NewsItem(headline=title, source=source, category="", link=link))
    return items


def _is_promotional_roundup(headline: str) -> bool:
    """Detecta si un titular es un article de tipus 'roundup' promocional
    (llistat d'ofertes que esmenta moltes marques de passada) en lloc
    d'una noticia real sobre l'empresa concreta.

    Args:
        headline: text del titular (ja en minuscules).

    Returns:
        True si sembla un roundup generic i s'ha de descartar com a
        noticia rellevant, independentment de si conte alguna paraula clau.
    """
    for phrase in NEWS_ROUNDUP_BLOCKLIST:
        if phrase in headline:
            return True
    if headline.count(",") >= NEWS_ROUNDUP_COMMA_THRESHOLD:
        return True
    return False


def classify_headline(headline: str) -> str:
    """Classifica un titular en una de les categories predefinides.

    Args:
        headline: text del titular.

    Returns:
        Nom de la categoria (clau de NEWS_CATEGORY_KEYWORDS), o NO_NEWS_CATEGORY.
    """
    text = headline.lower()
    if _is_promotional_roundup(text):
        return NO_NEWS_CATEGORY
    for category, keywords in NEWS_CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return category
    return NO_NEWS_CATEGORY


def _best_category(categories: List[str]) -> str:
    """Escull la categoria de mes impacte entre les trobades."""
    if not categories:
        return NO_NEWS_CATEGORY
    return max(categories, key=lambda c: NEWS_CATEGORY_SCORES.get(c, 0.0))


def _summarize(items: List[NewsItem], best_category: str) -> str:
    """Genera un resum molt curt de la situacio de noticies.

    Args:
        items: titulars ja classificats.
        best_category: la categoria de mes impacte detectada.

    Returns:
        Una linia de resum.
    """
    if not items or best_category == NO_NEWS_CATEGORY:
        return "Sense noticies rellevants avui."
    matching = [i for i in items if i.category == best_category]
    example = matching[0].headline if matching else items[0].headline
    return f"{best_category}: {example[:90]}"


def analyze_news(company_name: str) -> NewsAnalysis:
    """Pipeline complet d'analisi de noticies: cercar, classificar, puntuar, resumir.

    Args:
        company_name: terme de cerca de l'empresa (p.ex. "Indra").

    Returns:
        NewsAnalysis amb els items classificats, la millor categoria,
        el resum i el score.
    """
    raw_items = fetch_headlines(company_name)
    for item in raw_items:
        item.category = classify_headline(item.headline)

    categories_found = [i.category for i in raw_items]
    best_category = _best_category(categories_found)
    score = NEWS_CATEGORY_SCORES.get(best_category, 0.0)
    summary = _summarize(raw_items, best_category)

    return NewsAnalysis(items=raw_items, best_category=best_category, summary=summary, score=score)
