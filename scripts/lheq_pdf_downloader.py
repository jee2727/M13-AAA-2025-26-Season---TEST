#!/usr/bin/env python3
"""
lheq_pdf_downloader.py

Download game-sheet PDFs from LHEQ game schedule pages.
Attempts to find and download the PDF link from the LHEQ website.

Supports two download methods:
  1. Static HTML parsing with requests + BeautifulSoup (fast)
  2. Browser automation with Playwright (for JavaScript-rendered content)

Usage:
    python scripts/lheq_pdf_downloader.py <game_id> [--output FILE] [--method {auto,requests,playwright}]

Examples:
    # Game #1000 (gameId 614322)
    python scripts/lheq_pdf_downloader.py 614322
    python scripts/lheq_pdf_downloader.py 614322 --output game_1000.pdf
    python scripts/lheq_pdf_downloader.py 614322 --method playwright
"""

import argparse
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Optional: Playwright (only imported if needed)
try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Base LHEQ URLs for different regions/languages
LHEQ_BASE_URLS = {
    "masculin":  "https://masculin.lheq.ca",
    "feminin":   "https://feminin.lheq.ca",
}

# Common patterns for PDF links on LHEQ pages
PDF_LINK_PATTERNS = [
    # Direct PDF links (most common)
    lambda tag: tag.name == "a" and tag.get("href", "").endswith(".pdf"),
    
    # Links with text containing "feuille" (French for "sheet")
    lambda tag: tag.name == "a" and "feuille" in (tag.get_text().lower() or ""),
    
    # Links with text containing "gamesheet" or similar
    lambda tag: tag.name == "a" and any(
        term in tag.get_text().lower() 
        for term in ["gamesheet", "game sheet", "match sheet", "fiche", "résumé"]
    ),
    
    # Button-style links that trigger downloads
    lambda tag: tag.name in ["a", "button"] and "download" in (tag.get_text().lower() or ""),
    
    # Links with PDF in the title or data attributes
    lambda tag: tag.name == "a" and (
        "pdf" in tag.get_text().lower() 
        or "pdf" in str(tag.get("data-url", "")).lower()
    ),
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# ---------------------------------------------------------------------------
# Method 1: Static HTML parsing with requests + BeautifulSoup
# ---------------------------------------------------------------------------

def find_pdf_link_in_html(game_id: str, region: str = "masculin") -> str | None:
    """
    Fetch the LHEQ game page and extract the PDF download link.
    
    Returns the full PDF URL if found, None otherwise.
    """
    base_url = LHEQ_BASE_URLS.get(region, LHEQ_BASE_URLS["masculin"])
    game_url = f"{base_url}/fr/schedule/{game_id}?gameId={game_id}"
    
    print(f"Fetching game page: {game_url}")
    
    try:
        response = requests.get(
            game_url,
            timeout=10,
            headers={"User-Agent": USER_AGENT}
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch game page: {e}")
        return None
    
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Try each pattern to find a PDF link
    for pattern in PDF_LINK_PATTERNS:
        try:
            candidates = soup.find_all(pattern)
            for candidate in candidates:
                href = candidate.get("href") or candidate.get("data-url") or ""
                if href and ("pdf" in href.lower() or ".pdf" in href.lower()):
                    pdf_url = urljoin(base_url, href)
                    print(f"  Found PDF link: {pdf_url}")
                    return pdf_url
        except Exception as e:
            # Pattern matching can fail for some lambda edge cases
            continue
    
    # Fallback: look for any link containing the game ID and .pdf
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if str(game_id) in href and ".pdf" in href.lower():
            pdf_url = urljoin(base_url, href)
            print(f"  Found PDF link (fallback): {pdf_url}")
            return pdf_url
    
    print("  No PDF link found in static HTML")
    return None


# ---------------------------------------------------------------------------
# Method 2: Browser automation with Playwright
# ---------------------------------------------------------------------------

async def find_pdf_link_with_playwright(game_id: str, region: str = "masculin") -> str | None:
    """
    Use Playwright to render the page with JavaScript and extract the PDF link.
    
    Returns the full PDF URL if found, None otherwise.
    """
    if not HAS_PLAYWRIGHT:
        print("ERROR: Playwright not installed. Install with: pip install playwright")
        return None
    
    base_url = LHEQ_BASE_URLS.get(region, LHEQ_BASE_URLS["masculin"])
    game_url = f"{base_url}/fr/schedule/{game_id}?gameId={game_id}"
    
    print(f"Launching browser (Playwright)...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        try:
            print(f"Navigating to: {game_url}")
            await page.goto(game_url, wait_until="networkidle", timeout=30000)
            
            # Wait for potential PDF link to appear
            await page.wait_for_timeout(2000)
            
            # Extract all links from the rendered page
            links = await page.query_selector_all("a[href]")
            
            for link in links:
                href = await link.get_attribute("href")
                text = await link.text_content()
                
                if href and (".pdf" in href.lower() or "pdf" in (text or "").lower()):
                    pdf_url = urljoin(base_url, href)
                    print(f"  Found PDF link: {pdf_url}")
                    await browser.close()
                    return pdf_url
            
            print("  No PDF link found after rendering")
            await browser.close()
            return None
            
        except Exception as e:
            print(f"ERROR: Browser automation failed: {e}")
            await browser.close()
            return None


# ---------------------------------------------------------------------------
# PDF Download
# ---------------------------------------------------------------------------

def download_pdf(pdf_url: str, output_path: Path) -> bool:
    """
    Download the PDF from *pdf_url* and save to *output_path*.
    
    Returns True if successful, False otherwise.
    """
    print(f"\nDownloading PDF from: {pdf_url}")
    
    try:
        response = requests.get(
            pdf_url,
            timeout=30,
            headers={"User-Agent": USER_AGENT},
            stream=True
        )
        response.raise_for_status()
        
        # Verify content type
        content_type = response.headers.get("content-type", "").lower()
        if "pdf" not in content_type:
            print(f"WARNING: Content-Type is {content_type}, expected application/pdf")
        
        # Write to file
        total_size = int(response.headers.get("content-length", 0))
        with open(output_path, "wb") as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = (downloaded / total_size) * 100
                        print(f"  Downloaded {downloaded} / {total_size} bytes ({pct:.1f}%)", end="\r")
        
        print(f"\n✓ Saved PDF → {output_path}")
        actual_size = output_path.stat().st_size
        print(f"  File size: {actual_size / 1024:.1f} KB")
        
        return True
        
    except requests.RequestException as e:
        print(f"ERROR: Failed to download PDF: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to save PDF: {e}")
        return False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main_async(game_id: str, method: str, output_path: Path):
    """Async main for Playwright support."""
    if method in ("auto", "playwright"):
        pdf_url = await find_pdf_link_with_playwright(game_id)
        if pdf_url:
            return download_pdf(pdf_url, output_path)
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Download game-sheet PDFs from LHEQ game schedule pages.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/lheq_pdf_downloader.py 614322
  python scripts/lheq_pdf_downloader.py 614322 --output game_1000.pdf
  python scripts/lheq_pdf_downloader.py 614322 --method playwright
        """,
    )
    
    parser.add_argument(
        "game_id",
        help="LHEQ game ID (e.g., 614322 for game #1000)",
    )
    
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output file path (default: {game_id}.pdf)",
    )
    
    parser.add_argument(
        "--method",
        choices=["auto", "requests", "playwright"],
        default="auto",
        help=(
            "Download method. 'auto' tries requests first, then Playwright. "
            "'requests' uses only requests+BeautifulSoup. "
            "'playwright' uses browser automation. (default: auto)"
        ),
    )
    
    parser.add_argument(
        "--region",
        choices=list(LHEQ_BASE_URLS.keys()),
        default="masculin",
        help="LHEQ region (default: masculin)",
    )
    
    args = parser.parse_args()
    
    game_id = args.game_id
    output_path = args.output or Path(f"{game_id}.pdf")
    method = args.method
    
    print(f"LHEQ PDF Downloader")
    print(f"  Game ID: {game_id}")
    print(f"  Output:  {output_path}")
    print(f"  Method:  {method}")
    print()
    
    # Try requests-based method first
    if method in ("auto", "requests"):
        pdf_url = find_pdf_link_in_html(game_id, args.region)
        if pdf_url and download_pdf(pdf_url, output_path):
            return 0
        
        if method == "requests":
            print("ERROR: Could not find or download PDF with requests method")
            return 1
    
    # Fall back to Playwright
    if method in ("auto", "playwright"):
        if not HAS_PLAYWRIGHT:
            print("ERROR: Playwright not installed. Install with: pip install playwright")
            print("Then install browsers: playwright install")
            return 1
        
        try:
            import asyncio
            success = asyncio.run(main_async(game_id, method, output_path))
            return 0 if success else 1
        except Exception as e:
            print(f"ERROR: Playwright method failed: {e}")
            return 1
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
