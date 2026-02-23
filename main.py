import sys
import time
from gmail_client import (
    get_gmail_service,
    get_emails_by_sender,
    get_email_content,
    delete_email,
    close_connection,
)
from scraper import fetch_article_content, resolve_redirect_url
from openai_client import summarize_content
from email_sender import send_summary_email
from config import GMAIL_USER, GMAIL_APP_PASSWORD, SENDERS


def process_sender(mail, sender: dict) -> None:
    """Process all newsletters from a single sender"""
    name  = sender['name']
    email = sender['email']

    print(f"\n{'='*50}")
    print(f"📂 Sender: {name} ({email})")
    print(f"{'='*50}")

    msg_ids = get_emails_by_sender(mail, email)
    if not msg_ids:
        print("📭 No new emails, skipping")
        return

    print(f"📬 Found {len(msg_ids)} emails")

    for msg_id in msg_ids:
        print(f"\n  🔍 Reading email ID: {msg_id.decode()}...")
        email_data = get_email_content(mail, msg_id)
        subject    = email_data['subject']
        links_data = email_data['links']  # Now a list of dicts

        print(f"  📧 Subject: {subject}")
        
        # Pre-filter links for TLDR newsletters
        if "TLDR" in name:
            original_count = len(links_data)
            links_data = [
                item for item in links_data 
                if "linkedin.com" not in item['url'].lower()
            ]
            filter_count = original_count - len(links_data)
            if filter_count > 0:
                print(f"  ✂️  Filtered out {filter_count} LinkedIn links for TLDR")

        print(f"  🔗 Found {len(links_data)} valid links")

        if not links_data:
            print("  ⚠️  No links found, skipping this email")
            delete_email(mail, msg_id)
            continue

        COMMERCIAL_KEYWORDS = [
            'advertis',
            'sponsor',
            'sponser',
            'promoted',
            'promotion',
            'partner',
            'affiliate',
            'commercial',
            'advert',
        ]

        summaries = []
        seen_resolved_urls = set()  # Track resolved article URLs to avoid duplicate articles
        for i, item in enumerate(links_data, 1):
            url = item['url']
            title = item['title']
            desc = item['description']
            
            print(f"    [{i}/{len(links_data)}] Processing: {title[:50]}...")
            print(f"    [➔] Original URL: {url[:80]}...")

            # Skip commercial/sponsored links based on URL or title
            url_lower = url.lower()
            title_lower = title.lower()
            if any(kw in url_lower or kw in title_lower for kw in COMMERCIAL_KEYWORDS):
                print(f"    ⚠️  Skipping commercial/sponsored link: {title[:60]}")
                continue

            # Resolve tracking/redirect URL to the final article URL first
            resolved_url = resolve_redirect_url(url)

            # Normalize: strip query string and fragment — same hostname+path = same article
            resolved_url_key = resolved_url.split('?')[0].split('#')[0].rstrip('/')

            # Skip if we've already processed this article
            if resolved_url_key in seen_resolved_urls:
                print(f"    ⚠️  Skipping duplicate article: {resolved_url_key[:80]}...")
                continue
            seen_resolved_urls.add(resolved_url_key)

            # Pass the already-resolved URL so fetch_article_content doesn't re-resolve it
            content = fetch_article_content(resolved_url)
            
            if content.startswith("[Error]"):
                if "too short" in content or "429" in content:
                    print(f"    ⚠️  Skipping: {content}")
                    continue
                print(f"    ❌ Fetch failed: {content[:100]}")
                summary = content
            else:
                print(f"    ✅ Fetch successful ({len(content)} chars), summarizing...")
                summary = summarize_content(url, content)
                print(f"    📝 Summary complete")
                
            summaries.append({
                'url': url, 
                'title': title, 
                'description': desc, 
                'summary': summary
            })

            # Add delay to avoid Azure OpenAI rate limits
            if i < len(links_data):
                print(f"    ⏳ Waiting 5 seconds before next link...")
                time.sleep(5)

        print(f"  📤 Sending summary email...")
        send_summary_email(subject, name, summaries)
        delete_email(mail, msg_id)


def main() -> None:
    if not SENDERS:
        print("⚠️  No enabled senders in config.json, please check senders settings")
        sys.exit(1)

    print("🚀 Newsletter Bot Started")
    print(f"📋 Total {len(SENDERS)} enabled senders:")
    for s in SENDERS:
        print(f"   - {s['name']} ({s['email']})")

    mail = None
    try:
        mail = get_gmail_service(GMAIL_USER, GMAIL_APP_PASSWORD)

        for sender in SENDERS:
            process_sender(mail, sender)

    except KeyboardInterrupt:
        print("\n⛔ Execution interrupted by user")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        raise
    finally:
        if mail:
            close_connection(mail)
            print("\n🔌 Gmail connection closed")

    print("\n🎉 All done!")


if __name__ == "__main__":
    main()
