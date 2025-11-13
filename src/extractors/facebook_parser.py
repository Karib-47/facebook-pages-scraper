thonimport hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from extractors.utils_time import now_unix_ms

logger = logging.getLogger(__name__)

@dataclass
class FacebookPageMetadata:
    facebookUrl: str
    pageId: str
    pageName: str
    category: Optional[str] = None
    followers: Optional[int] = None

@dataclass
class FacebookPost:
    post_id: str
    url: str
    text: str
    time: str
    timestamp: int
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    link: Optional[str] = None
    videoViews: Optional[int] = None

class FacebookPageScraper:
    """
    Lightweight HTML-based scraper for public Facebook Pages.

    This implementation does not rely on private APIs and instead attempts to
    gather basic metadata and post-like content from open graph tags and visible
    text elements. It is intended as a robust, end-to-end example that can be
    extended for more advanced use cases.
    """

    def __init__(
        self,
        timeout: int = 10,
        user_agent: str = "Mozilla/5.0 (compatible; FacebookPagesScraper/1.0)",
    ) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def scrape_page(self, page_url: str) -> List[Dict[str, Any]]:
        """
        Scrape a single Facebook Page URL and return a list of records
        (one or more posts) in a flat, analytics-friendly structure.
        """
        logger.info("Scraping Facebook page: %s", page_url)
        html = self._fetch_html(page_url)

        if not html:
            logger.warning("No HTML fetched for %s, returning empty result.", page_url)
            return []

        soup = BeautifulSoup(html, "html.parser")
        page_meta = self._parse_page_metadata(page_url, soup)
        posts = self._build_posts_from_html(page_url, soup, page_meta)

        records: List[Dict[str, Any]] = []
        for post in posts:
            record = {
                "facebookUrl": page_meta.facebookUrl,
                "pageId": page_meta.pageId,
                "pageName": page_meta.pageName,
                "postId": post.post_id,
                "url": post.url,
                "time": post.time,
                "timestamp": post.timestamp,
                "likes": post.likes,
                "comments": post.comments,
                "shares": post.shares,
                "text": post.text,
                "link": post.link,
                "videoViews": post.videoViews,
                "category": page_meta.category,
                "followers": page_meta.followers,
            }
            records.append(record)

        logger.info(
            "Scraped %d post-like records from page %s", len(records), page_url
        )
        return records

    def _fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch raw HTML from the given URL with basic error handling.
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            logger.debug("Fetched HTML (%d bytes) from %s", len(response.text), url)
            return response.text
        except requests.RequestException as exc:
            logger.error("Failed to fetch %s: %s", url, exc)
            return None

    def _parse_page_metadata(
        self, page_url: str, soup: BeautifulSoup
    ) -> FacebookPageMetadata:
        """
        Attempt to derive page-level metadata from open graph tags and the title.
        """
        og_title = soup.find("meta", attrs={"property": "og:title"})
        title_tag = soup.find("title")

        if og_title and og_title.get("content"):
            page_name = og_title["content"].strip()
        elif title_tag and title_tag.text:
            page_name = title_tag.text.strip()
            page_name = page_name.replace("Facebook", "").strip("-| \n\t")
        else:
            page_name = page_url.rstrip("/").split("/")[-1] or "Unknown Page"

        og_site_name = soup.find("meta", attrs={"property": "og:site_name"})
        category = og_site_name.get("content").strip() if og_site_name else None

        # Followers are often embedded in text; a robust extractor would search
        # localized patterns. Here, we keep it simple and leave it as None.
        followers: Optional[int] = None

        page_id = hashlib.md5(page_url.encode("utf-8")).hexdigest()[:10]

        meta = FacebookPageMetadata(
            facebookUrl=page_url,
            pageId=page_id,
            pageName=page_name,
            category=category,
            followers=followers,
        )
        logger.debug("Parsed page metadata: %s", meta)
        return meta

    def _build_posts_from_html(
        self, page_url: str, soup: BeautifulSoup, meta: FacebookPageMetadata
    ) -> List[FacebookPost]:
        """
        Build a small set of post-like objects based on visible metadata.

        This implementation uses open graph and description tags as a proxy for
        recent posts. It is designed to be robust and deterministic rather than
        perfectly replicating Facebook's internal APIs.
        """
        text_candidates: List[str] = []

        og_description = soup.find("meta", attrs={"property": "og:description"})
        if og_description and og_description.get("content"):
            desc = og_description["content"].strip()
            if desc:
                text_candidates.append(desc)

        meta_description = soup.find("meta", attrs={"name": "description"})
        if meta_description and meta_description.get("content"):
            desc = meta_description["content"].strip()
            if desc and desc not in text_candidates:
                text_candidates.append(desc)

        if not text_candidates:
            for p in soup.find_all("p")[:3]:
                text = p.get_text(strip=True)
                if text:
                    text_candidates.append(text)
            text_candidates = list(dict.fromkeys(text_candidates))  # dedupe

        if not text_candidates:
            logger.warning(
                "No obvious textual content found for %s, creating a synthetic summary.",
                page_url,
            )
            text_candidates = [
                f"Summary: Fetched page {meta.pageName} ({page_url}) but "
                f"did not detect post-level content. This record represents "
                f"high-level page metadata only."
            ]

        posts: List[FacebookPost] = []
        for idx, text in enumerate(text_candidates, start=1):
            ts = now_unix_ms()
            time_str = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc).isoformat()

            post_id = f"{meta.pageId}_{idx}"
            post_url = page_url

            post = FacebookPost(
                post_id=post_id,
                url=post_url,
                text=text,
                time=time_str,
                timestamp=ts,
                likes=None,
                comments=None,
                shares=None,
                link=None,
                videoViews=None,
            )
            posts.append(post)

        logger.debug("Built %d post-like objects for %s", len(posts), page_url)
        return posts