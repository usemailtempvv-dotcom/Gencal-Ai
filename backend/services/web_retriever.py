"""
Web Retriever: Real-time fallback retrieval from superior.edu.pk.
Used when structured CSV datasets do not contain the requested information.
"""

import logging
import re
from collections import OrderedDict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SuperiorWebRetriever:
    """Fetch and rank relevant snippets from Superior University website."""

    BASE_URL = "https://www.superior.edu.pk/"

    def __init__(self, timeout=6):
        self.timeout = timeout
        self._cache = OrderedDict()
        self._max_cache = 24

    def _is_allowed_url(self, url):
        """Allow only superior.edu.pk pages (including subdomains)."""
        if not url:
            return False
        parsed = urlparse(url)
        host = (parsed.netloc or '').lower()
        return host == 'superior.edu.pk' or host.endswith('.superior.edu.pk')

    def _normalize_text(self, text):
        text = (text or "").lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _query_tokens(self, query):
        stopwords = {
            "the", "is", "a", "an", "and", "or", "of", "to", "for", "in", "on",
            "i", "me", "my", "you", "we", "us", "what", "how", "when", "where",
            "please", "tell", "about", "details", "info", "information", "university",
        }
        normalized = self._normalize_text(query)
        return [tok for tok in normalized.split() if tok and tok not in stopwords and len(tok) > 2]

    def _fetch_html(self, url):
        if not self._is_allowed_url(url):
            raise ValueError(f"Blocked non-Superior URL: {url}")

        if url in self._cache:
            return self._cache[url]

        resp = requests.get(url, timeout=self.timeout, headers={
            "User-Agent": "Mozilla/5.0 (compatible; GenCallAI/1.0)"
        })
        if not self._is_allowed_url(resp.url):
            raise ValueError(f"Blocked redirected URL outside superior.edu.pk: {resp.url}")
        resp.raise_for_status()
        html = resp.text

        self._cache[url] = html
        if len(self._cache) > self._max_cache:
            self._cache.popitem(last=False)
        return html

    def _extract_candidate_links(self, home_html, query_tokens):
        soup = BeautifulSoup(home_html, "html.parser")
        links = []

        keyword_hints = [
            "admission", "program", "scholarship", "fee", "financial", "apply", "undergraduate",
            "postgraduate", "entry-test", "news", "announcement",
        ] + query_tokens

        for tag in soup.find_all("a", href=True):
            href = tag.get("href", "").strip()
            if not href:
                continue
            absolute = urljoin(self.BASE_URL, href)
            if not self._is_allowed_url(absolute):
                continue
            absolute = absolute.split("#")[0]
            score = 0
            lower_url = absolute.lower()
            for hint in keyword_hints:
                if hint and hint in lower_url:
                    score += 1
            if score > 0:
                links.append((score, absolute))

        # Keep unique links in descending score.
        links.sort(key=lambda x: x[0], reverse=True)
        unique = []
        seen = set()
        for score, link in links:
            if link in seen:
                continue
            seen.add(link)
            unique.append(link)
            if len(unique) >= 10:
                break

        return unique

    def _extract_sentences(self, html):
        soup = BeautifulSoup(html, "html.parser")

        # Remove non-content tags.
        for bad in soup(["script", "style", "noscript", "svg"]):
            bad.extract()

        text = soup.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text)

        # Split into sentence-like chunks.
        parts = re.split(r"(?<=[.!?])\s+", text)
        sentences = []
        for part in parts:
            cleaned = part.strip()
            if len(cleaned) < 40:
                continue
            if len(cleaned) > 360:
                continue
            sentences.append(cleaned)
        return sentences

    def _rank_sentences(self, sentences, query_tokens):
        ranked = []
        for sent in sentences:
            normalized = self._normalize_text(sent)
            score = 0
            for tok in query_tokens:
                if tok in normalized:
                    score += 1
            if score > 0:
                ranked.append((score, sent))

        ranked.sort(key=lambda x: x[0], reverse=True)
        return ranked

    def _fallback_home_snippets(self, home_html):
        """Return general-purpose snippets from homepage when query match is weak."""
        sentences = self._extract_sentences(home_html)
        if not sentences:
            return []

        preferred = []
        keywords = [
            'superior', 'university', 'admission', 'program', 'scholarship',
            'faculty', 'campus', 'student',
        ]
        for sent in sentences:
            normalized = self._normalize_text(sent)
            if any(k in normalized for k in keywords):
                preferred.append(sent)
            if len(preferred) >= 3:
                break

        if preferred:
            return preferred
        return sentences[:3]

    def search(self, query):
        """Return best matching snippets from website for the given query."""
        try:
            tokens = self._query_tokens(query)
            home_html = self._fetch_html(self.BASE_URL)

            if not tokens:
                snippets = self._fallback_home_snippets(home_html)
                return {
                    "found": bool(snippets),
                    "source": self.BASE_URL,
                    "snippets": snippets,
                    "message": "Used homepage context fallback.",
                }

            links = self._extract_candidate_links(home_html, tokens)
            links = [self.BASE_URL] + [link for link in links if link != self.BASE_URL]

            best_link = self.BASE_URL
            all_ranked = []
            for link in links[:6]:
                try:
                    html = self._fetch_html(link)
                    sentences = self._extract_sentences(html)
                    ranked = self._rank_sentences(sentences, tokens)
                    if ranked:
                        all_ranked.extend([(score, sent, link) for score, sent in ranked[:8]])
                except Exception as e:
                    logger.warning(f"Web page fetch failed for {link}: {str(e)}")

            if not all_ranked:
                snippets = self._fallback_home_snippets(home_html)
                return {
                    "found": bool(snippets),
                    "source": self.BASE_URL,
                    "snippets": snippets,
                    "message": "Used homepage context fallback.",
                }

            all_ranked.sort(key=lambda x: x[0], reverse=True)
            top = all_ranked[:3]
            best_link = top[0][2]
            snippets = [item[1] for item in top]

            return {
                "found": True,
                "source": best_link,
                "snippets": snippets,
                "message": "Matched from superior.edu.pk",
            }
        except Exception as e:
            logger.warning(f"Real-time web search failed: {str(e)}")
            return {
                "found": False,
                "source": self.BASE_URL,
                "snippets": [],
                "message": str(e),
            }
