import re
import time
from curl_cffi import requests as curl_requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup


MAX_CONTENT_LENGTH = 12000  # Avoid exceeding token limits

# Browser to impersonate for TLS fingerprint
# curl_cffi supports: chrome, safari, firefox, etc.
IMPERSONATE_BROWSER = "chrome131"

# Known redirect/tracking domains
REDIRECT_DOMAINS = [
    'link.mail.beehiiv.com',
    'links.tldrnewsletter.com',
    'link.sbstck.com',
    'email.mg1.substack.com',
    'tracking.tldrnewsletter.com',
    'convertkit',
    'mailchi.mp',
    'click.convertkit-mail',
    'email.convertkit',
    't.co',
]


def _is_redirect_url(url: str) -> bool:
    """Check if the URL is a known tracking/redirect link."""
    parsed = urlparse(url)
    hostname = parsed.hostname or ''
    for domain in REDIRECT_DOMAINS:
        if domain in hostname:
            return True
    # Also check for common redirect path patterns
    path = parsed.path.lower()
    if '/ss/c/' in path or '/click' in path or '/track' in path:
        return True
    return False


def _extract_redirect_from_html(html: str) -> str | None:
    """
    Try to extract the redirect target URL from HTML content.
    Handles: meta refresh, JavaScript redirects (window.location, location.href, etc.)
    """
    if not html:
        return None

    # Strategy 1: <meta http-equiv="refresh" content="0;url=...">
    soup = BeautifulSoup(html, 'html.parser')
    meta_refresh = soup.find('meta', attrs={'http-equiv': re.compile(r'refresh', re.I)})
    if meta_refresh:
        content = meta_refresh.get('content', '')
        match = re.search(r'url\s*=\s*["\']?([^"\'>\s]+)', content, re.I)
        if match:
            target = match.group(1)
            if target.startswith('http'):
                return target

    # Strategy 2: JavaScript redirects
    js_patterns = [
        r'window\.location(?:\.href)?\s*=\s*["\']([^"\']+)["\']',
        r'window\.location\.replace\s*\(\s*["\']([^"\']+)["\']',
        r'(?<!\w)location\.href\s*=\s*["\']([^"\']+)["\']',
        r'(?<!\w)location\.replace\s*\(\s*["\']([^"\']+)["\']',
        r'document\.location\s*=\s*["\']([^"\']+)["\']',
    ]
    for pattern in js_patterns:
        match = re.search(pattern, html)
        if match:
            target = match.group(1)
            if target.startswith('http'):
                return target

    # Strategy 3: Look for canonical link
    canonical = soup.find('link', attrs={'rel': 'canonical'})
    if canonical and canonical.get('href', '').startswith('http'):
        return canonical['href']

    # Strategy 4: Single link in a very small page (redirect stub)
    body_text = soup.get_text(strip=True)
    if len(body_text) < 500:
        all_links = soup.find_all('a', href=True)
        http_links = [a['href'] for a in all_links if a['href'].startswith('http')]
        if len(http_links) == 1:
            return http_links[0]

    return None


def resolve_redirect_url(url: str, max_depth: int = 5) -> str:
    """
    Resolve a tracking/redirect URL to its final destination.
    Uses curl_cffi with browser TLS impersonation to bypass bot detection.
    Returns the resolved URL, or the original URL if resolution fails.
    """
    if not _is_redirect_url(url):
        return url

    current_url = url
    visited = set()

    for depth in range(max_depth):
        if current_url in visited:
            break
        visited.add(current_url)

        # Strategy 1: Try HEAD request (lightweight, follows HTTP redirects)
        try:
            resp = curl_requests.head(
                current_url, timeout=15,
                allow_redirects=True,
                impersonate=IMPERSONATE_BROWSER,
            )
            final_url = str(resp.url)
            if final_url != current_url and not _is_redirect_url(final_url):
                print(f"      [➔] Resolved (HEAD): {final_url[:80]}...")
                return final_url
        except Exception:
            pass

        # Strategy 2: Try GET request (follows HTTP redirects + can parse body)
        try:
            resp = curl_requests.get(
                current_url, timeout=15,
                allow_redirects=True,
                impersonate=IMPERSONATE_BROWSER,
            )
            final_url = str(resp.url)

            # If HTTP-level redirect resolved to a non-redirect URL
            if final_url != current_url and not _is_redirect_url(final_url):
                print(f"      [➔] Resolved (GET redirect): {final_url[:80]}...")
                return final_url

            # If we got a 200 but it might be a JS/meta redirect page
            if resp.status_code == 200:
                html_redirect = _extract_redirect_from_html(resp.text)
                if html_redirect and html_redirect != current_url:
                    if not _is_redirect_url(html_redirect):
                        print(f"      [➔] Resolved (HTML parse): {html_redirect[:80]}...")
                        return html_redirect
                    else:
                        current_url = html_redirect
                        continue

            # If we got 403 but the response body has a redirect
            if resp.status_code == 403:
                html_redirect = _extract_redirect_from_html(resp.text)
                if html_redirect and html_redirect != current_url:
                    if not _is_redirect_url(html_redirect):
                        print(f"      [➔] Resolved (403 body parse): {html_redirect[:80]}...")
                        return html_redirect
                    else:
                        current_url = html_redirect
                        continue

        except Exception:
            pass

        break  # No progress, stop trying

    # If we ended up at a different URL (even if still a redirect domain), use it
    if current_url != url:
        print(f"      [➔] Partially resolved: {current_url[:80]}...")
        return current_url

    print(f"      [⚠] Could not resolve redirect, using original URL")
    return url


def fetch_article_content(url: str) -> str:
    """
    Fetch webpage content and return plain text.
    First resolves any tracking/redirect links, then fetches the actual article.
    Uses curl_cffi to impersonate browser TLS fingerprint (bypass 403 bot detection).
    Returns error message string on failure (doesn't raise exception to keep flow going).
    """
    # Step 1: Resolve redirect/tracking URL to the actual article URL
    resolved_url = resolve_redirect_url(url)

    # Step 2: Fetch the actual article content with retry
    max_retries = 2
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            response = curl_requests.get(
                resolved_url, timeout=20,
                allow_redirects=True,
                impersonate=IMPERSONATE_BROWSER,
            )

            # If we got redirected further, update the URL
            if str(response.url) != resolved_url:
                print(f"      [➔] Redirected to: {str(response.url)[:80]}...")

            if response.status_code == 429:
                return f"[Error] HTTP Error 429 (Too Many Requests): {resolved_url}"

            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove unnecessary elements
            for tag in soup(['script', 'style', 'nav', 'footer',
                             'header', 'aside', 'form', 'iframe']):
                tag.decompose()

            # Try to get <article> or <main> content first
            main_content = soup.find('article') or soup.find('main')
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)

            # Clean up extra blank lines
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            cleaned = '\n'.join(lines)

            # Check for minimum content length
            if len(cleaned) < 3000:
                return f"[Error] Content too short ({len(cleaned)} characters)"

            return cleaned[:MAX_CONTENT_LENGTH]

        except curl_requests.errors.RequestsError as e:
            last_error = f"[Error] Request failed: {e}"
        except Exception as e:
            error_str = str(e)
            if '403' in error_str:
                last_error = f"[Error] HTTP Error 403: {resolved_url}"
            elif 'timeout' in error_str.lower():
                last_error = f"[Error] Connection timeout: {resolved_url}"
            else:
                last_error = f"[Error] Failed to fetch content: {e}"

        # Retry with backoff (only if not last attempt)
        if attempt < max_retries:
            wait_time = 2 * (attempt + 1)
            print(f"      [🔄] Retry {attempt + 1}/{max_retries} in {wait_time}s...")
            time.sleep(wait_time)

    return last_error
