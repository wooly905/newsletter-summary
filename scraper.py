import requests
from bs4 import BeautifulSoup


MAX_CONTENT_LENGTH = 12000  # Avoid exceeding token limits


def fetch_article_content(url: str) -> str:
    """
    Fetch webpage content and return plain text.
    Returns error message string on failure (doesn't raise exception to keep flow going).
    """
    session = requests.Session()
    try:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/122.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        # Use Session and allow redirects to handle tracking links like ConvertKit or Medium
        response = session.get(url, headers=headers, timeout=20, allow_redirects=True)
        
        # Handle Medium's potential 403 by retrying with session cookies
        if "medium.com" in response.url and response.status_code == 403:
            response = session.get(response.url, headers=headers, timeout=20)
            
        if response.url != url:
            print(f"      [➔] Redirected to: {response.url[:80]}...")
            
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

        return cleaned[:MAX_CONTENT_LENGTH]

    except requests.exceptions.Timeout:
        return f"[Error] Connection timeout: {url}"
    except requests.exceptions.HTTPError as e:
        return f"[Error] HTTP Error {e.response.status_code}: {url}"
    except Exception as e:
        return f"[Error] Failed to fetch content: {e}"
