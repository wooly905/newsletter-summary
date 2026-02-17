import requests
from bs4 import BeautifulSoup


MAX_CONTENT_LENGTH = 8000  # 避免超過 token 限制


def fetch_article_content(url: str) -> str:
    """
    抓取網頁內容並回傳純文字。
    失敗時回傳錯誤訊息字串（不拋出例外，讓主流程繼續）。
    """
    try:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # 移除不必要的元素
        for tag in soup(['script', 'style', 'nav', 'footer',
                         'header', 'aside', 'form', 'iframe']):
            tag.decompose()

        # 優先嘗試取得 <article> 或 <main> 內容
        main_content = soup.find('article') or soup.find('main')
        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)

        # 清理多餘空白行
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned = '\n'.join(lines)

        return cleaned[:MAX_CONTENT_LENGTH]

    except requests.exceptions.Timeout:
        return f"[錯誤] 連線逾時：{url}"
    except requests.exceptions.HTTPError as e:
        return f"[錯誤] HTTP 錯誤 {e.response.status_code}：{url}"
    except Exception as e:
        return f"[錯誤] 無法抓取內容：{e}"
