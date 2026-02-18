import imaplib
import email
import re
from email.header import decode_header
from bs4 import BeautifulSoup


def get_gmail_service(username: str, app_password: str) -> imaplib.IMAP4_SSL:
    """Establish and return IMAP connection"""
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(username, app_password)
    print("✅ Gmail IMAP connection successful")
    return mail


def get_emails_by_sender(mail: imaplib.IMAP4_SSL, sender_email: str) -> list:
    """Search for all emails from sender using UIDs, return UID list"""
    mail.select("inbox")
    # Use UID search for stability
    result, data = mail.uid('search', None, f'(FROM "{sender_email}")')
    if result != 'OK':
        return []
    uids = data[0].split()
    return uids


def _decode_subject(raw_subject: str) -> str:
    """Decode email subject (handles various encodings)"""
    if not raw_subject:
        return "(No Subject)"
    decoded_parts = decode_header(raw_subject)
    subject = ""
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            subject += part.decode(charset or 'utf-8', errors='ignore')
        else:
            subject += part
    return subject


def _extract_links_from_html(html: str) -> list:
    """Extract all http/https links and their titles/descriptions from HTML content"""
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    # Keywords to filter out
    skip_keywords = ['unsubscribe', 'optout', 'opt-out', 'mailto:']
    
    all_links = soup.find_all('a', href=True)
    print(f"    [Debug] Total <a> tags in raw HTML: {len(all_links)}")
    
    for a in all_links:
        url = a['href']
        if not url.startswith('http'):
            continue
            
        # Filter by keywords
        is_skipped = False
        for kw in skip_keywords:
            if kw in url.lower():
                is_skipped = True
                break
        if is_skipped:
            continue
            
        # Filter links ending with /hclick
        url_path = url.split('?')[0].split('#')[0]
        if url_path.endswith('/hclick'):
            continue
            
        # Try to get title
        title = a.get_text(strip=True)
        
        # Try to get description
        description = ""
        parent = a.parent
        if parent:
            p_text = parent.get_text(separator=' ', strip=True)
            if len(p_text) > len(title):
                description = p_text.replace(title, "", 1).strip()
            
            if not description:
                next_node = parent.find_next_sibling(['p', 'div', 'span'])
                if next_node:
                    description = next_node.get_text(strip=True)

        if len(title) < 5:
            prev_h = a.find_previous(['h1', 'h2', 'h3', 'h4', 'b', 'strong'])
            if prev_h:
                title = prev_h.get_text(strip=True)

        if not title:
            title = url

        results.append({
            'url': url,
            'title': title[:150],
            'description': description[:300]
        })
        
    seen_urls = set()
    unique_results = []
    for res in results:
        if res['url'] not in seen_urls:
            unique_results.append(res)
            seen_urls.add(res['url'])
            
    print(f"    [Debug] Valid links after filtering: {len(unique_results)}")
    if len(unique_results) == 0 and len(all_links) > 0:
        print("    [Debug] Sample of rejected links (first 3):")
        count = 0
        for a in all_links[:10]:
            if count >= 3: break
            u = a['href']
            if u.startswith('http'):
                print(f"      - {u[:100]}...")
                count += 1
                
    return unique_results


def get_email_content(mail: imaplib.IMAP4_SSL, uid: bytes) -> dict:
    """Get subject and HTML link information using UID"""
    result, data = mail.uid('fetch', uid, "(RFC822)")
    if result != 'OK':
        return None
        
    raw = data[0][1]
    msg = email.message_from_bytes(raw)

    subject = _decode_subject(msg.get("Subject", ""))
    links_data = []

    for part in msg.walk():
        content_type = part.get_content_type()
        if content_type == "text/html":
            charset = part.get_content_charset() or 'utf-8'
            html = part.get_payload(decode=True).decode(charset, errors='ignore')
            links_data = _extract_links_from_html(html)
            break
        elif content_type == "text/plain" and not links_data:
            charset = part.get_content_charset() or 'utf-8'
            text = part.get_payload(decode=True).decode(charset, errors='ignore')
            raw_links = re.findall(r'https?://[^\s<>"\']+', text)
            links_data = [{'url': l, 'title': l, 'description': ''} for l in list(dict.fromkeys(raw_links))]

    return {
        'id': uid,
        'subject': subject,
        'links': links_data
    }


def delete_email(mail: imaplib.IMAP4_SSL, uid: bytes) -> None:
    """Move email to Gmail Trash using UID"""
    try:
        # Try common Gmail trash folder names
        trash_folders = ['"[Gmail]/Trash"', '"[Gmail]/&U04-T03P-&U94-T03P-"', '"Trash"']
        
        success = False
        for folder in trash_folders:
            result, _ = mail.uid('copy', uid, folder)
            if result == 'OK':
                # Mark original as deleted after successful copy
                mail.uid('store', uid, '+FLAGS', '\\Deleted')
                # We don't expunge here to avoid sequence shifts for other processes
                # Gmail will handle the cleanup
                print(f"🗑️  Email (UID: {uid.decode()}) moved to trash folder: {folder}")
                success = True
                break
        
        if not success:
            print(f"⚠️  Could not find trash folder, marking as deleted directly (UID: {uid.decode()})")
            mail.uid('store', uid, '+FLAGS', '\\Deleted')
            
    except Exception as e:
        print(f"❌ Error during deletion (UID: {uid.decode()}): {e}")


def close_connection(mail: imaplib.IMAP4_SSL) -> None:
    """Close IMAP connection and expunge deleted messages"""
    try:
        mail.expunge() # Final cleanup
        mail.close()
        mail.logout()
    except Exception:
        pass
