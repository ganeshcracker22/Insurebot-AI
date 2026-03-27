"""
Web Crawler for Insurance Policy PDFs.

Crawls insurance websites, extracts internal links up to depth 2,
filters pages with insurance-related keywords, downloads PDFs into
/data/policies/{company}/.
"""

import os
import re
import time
import logging
import hashlib
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data", "policies")

INSURANCE_KEYWORDS = {"policy", "download", "brochure", "insurance", "coverage", "premium", "claim"}
PDF_KEYWORDS = {"policy", "wording", "brochure"}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; InsureBotCrawler/1.0; +https://github.com/insurebot)"
    )
}

REQUEST_DELAY = 1.0  # seconds between requests


def is_same_domain(base_url: str, url: str) -> bool:
    return urlparse(base_url).netloc == urlparse(url).netloc


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed._replace(fragment="").geturl()


def page_has_keywords(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in INSURANCE_KEYWORDS)


def pdf_url_has_keywords(url: str) -> bool:
    url_lower = url.lower()
    return any(kw in url_lower for kw in PDF_KEYWORDS)


def get_links(base_url: str, html: str):
    """Return all internal links and PDF links from the given HTML."""
    soup = BeautifulSoup(html, "html.parser")
    internal_links = set()
    pdf_links = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        full_url = normalize_url(urljoin(base_url, href))

        if not full_url.startswith("http"):
            continue

        if not is_same_domain(base_url, full_url):
            continue

        if full_url.lower().endswith(".pdf"):
            if pdf_url_has_keywords(full_url):
                pdf_links.add(full_url)
        else:
            internal_links.add(full_url)

    return internal_links, pdf_links


def crawl_site(start_url: str, max_depth: int = 2):
    """Crawl a website up to max_depth and return all discovered PDF links."""
    visited = set()
    pdf_links = set()
    queue = [(start_url, 0)]

    session = requests.Session()
    session.headers.update(HEADERS)

    while queue:
        url, depth = queue.pop(0)
        url = normalize_url(url)

        if url in visited or depth > max_depth:
            continue
        visited.add(url)

        try:
            logger.info(f"Crawling [{depth}]: {url}")
            response = session.get(url, timeout=15)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")

            if "html" not in content_type:
                continue

            html = response.text
            if not page_has_keywords(html):
                logger.debug(f"Skipping (no keywords): {url}")
                time.sleep(REQUEST_DELAY)
                continue

            links, pdfs = get_links(url, html)
            pdf_links.update(pdfs)

            if depth < max_depth:
                for link in links:
                    if link not in visited:
                        queue.append((link, depth + 1))

            time.sleep(REQUEST_DELAY)

        except requests.RequestException as exc:
            logger.warning(f"Error fetching {url}: {exc}")
            continue

    return pdf_links


def get_company_name(url: str) -> str:
    """Extract a clean company name from URL."""
    netloc = urlparse(url).netloc
    name = netloc.replace("www.", "").split(".")[0]
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name)


def compute_md5(filepath: str) -> str:
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def download_pdf(pdf_url: str, company_dir: str) -> bool:
    """Download a single PDF file. Returns True if downloaded, False if skipped/error."""
    filename = os.path.basename(urlparse(pdf_url).path) or "document.pdf"
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    filepath = os.path.join(company_dir, filename)

    if os.path.exists(filepath):
        logger.info(f"Already exists, skipping: {filename}")
        return False

    try:
        response = requests.get(pdf_url, headers=HEADERS, timeout=30, stream=True)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Downloaded: {filename} → {company_dir}")
        return True

    except requests.RequestException as exc:
        logger.warning(f"Failed to download {pdf_url}: {exc}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return False


def crawl_and_download(start_url: str):
    """Crawl a site and download all relevant PDFs."""
    company = get_company_name(start_url)
    company_dir = os.path.join(DATA_DIR, company)
    os.makedirs(company_dir, exist_ok=True)

    logger.info(f"Starting crawl for: {start_url} (company={company})")
    pdf_links = crawl_site(start_url, max_depth=2)
    logger.info(f"Found {len(pdf_links)} PDF links for {company}")

    downloaded = 0
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(download_pdf, url, company_dir): url for url in pdf_links
        }
        for future in as_completed(futures):
            if future.result():
                downloaded += 1

    logger.info(f"Done: {downloaded}/{len(pdf_links)} PDFs downloaded for {company}")
    return downloaded


INSURANCE_SITES = [
    "https://www.lici.in",
    "https://www.hdfclife.com",
    "https://www.starhealth.in",
    "https://www.bajajallianz.com",
]


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    total = 0
    for site in INSURANCE_SITES:
        try:
            count = crawl_and_download(site)
            total += count
        except Exception as exc:
            logger.error(f"Error processing {site}: {exc}")
    logger.info(f"Crawl complete. Total PDFs downloaded: {total}")
