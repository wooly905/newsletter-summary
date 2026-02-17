import imaplib
import email
import re
from email.header import decode_header


def get_gmail_service(username: str, app_password: str) -> imaplib.IMAP4_SSL:
    """建立並回傳 IMAP 連線"""
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(username, app_password)
    print("✅ Gmail IMAP 連線成功")
    return mail


def get_emails_by_sender(mail: imaplib.IMAP4_SSL, sender_email: str) -> list:
    """根據寄件者 email 搜尋未讀信件，回傳 msg_id list"""
    mail.select("inbox")
    _, data = mail.search(None, f'(FROM "{sender_email}" UNSEEN)')
    msg_ids = data[0].split()
    return msg_ids


def _decode_subject(raw_subject: str) -> str:
    """解碼信件主旨（處理各種編碼）"""
    decoded_parts = decode_header(raw_subject)
    subject = ""
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            subject += part.decode(charset or 'utf-8', errors='ignore')
        else:
            subject += part
    return subject


def _extract_links_from_html(html: str) -> list:
    """從 HTML 內容中提取所有 http/https 連結"""
    links = re.findall(r'href=["\']([^"\']+)["\']', html)
    links = [l for l in links if l.startswith('http')]
    # 過濾常見的追蹤/取消訂閱連結
    skip_keywords = ['unsubscribe', 'optout', 'opt-out', 'mailto', 'tracking']
    links = [l for l in links if not any(kw in l.lower() for kw in skip_keywords)]
    return list(dict.fromkeys(links))  # 去重並保持順序


def get_email_content(mail: imaplib.IMAP4_SSL, msg_id: bytes) -> dict:
    """取得單封信件的主旨與 HTML 連結"""
    _, data = mail.fetch(msg_id, "(RFC822)")
    raw = data[0][1]
    msg = email.message_from_bytes(raw)

    subject = _decode_subject(msg.get("Subject", "(無主旨)"))
    links = []

    for part in msg.walk():
        content_type = part.get_content_type()
        if content_type == "text/html":
            charset = part.get_content_charset() or 'utf-8'
            html = part.get_payload(decode=True).decode(charset, errors='ignore')
            links = _extract_links_from_html(html)
            break  # 優先用 HTML part
        elif content_type == "text/plain" and not links:
            # fallback: 純文字也嘗試抓連結
            charset = part.get_content_charset() or 'utf-8'
            text = part.get_payload(decode=True).decode(charset, errors='ignore')
            raw_links = re.findall(r'https?://[^\s<>"\']+', text)
            links = list(dict.fromkeys(raw_links))

    return {
        'id': msg_id,
        'subject': subject,
        'links': links
    }


def delete_email(mail: imaplib.IMAP4_SSL, msg_id: bytes) -> None:
    """將信件移至垃圾桶（標記刪除並 expunge）"""
    mail.store(msg_id, '+FLAGS', '\\Deleted')
    mail.expunge()
    print(f"🗑️  信件已刪除: {msg_id.decode()}")


def close_connection(mail: imaplib.IMAP4_SSL) -> None:
    """關閉 IMAP 連線"""
    try:
        mail.close()
        mail.logout()
    except Exception:
        pass
