import sys
from gmail_client import (
    get_gmail_service,
    get_emails_by_sender,
    get_email_content,
    delete_email,
    close_connection,
)
from scraper import fetch_article_content
from openai_client import summarize_content
from email_sender import send_summary_email
from config import GMAIL_USER, GMAIL_APP_PASSWORD, SENDERS


def process_sender(mail, sender: dict) -> None:
    """處理單一寄件者的所有 newsletter"""
    name  = sender['name']
    email = sender['email']

    print(f"\n{'='*50}")
    print(f"📂 寄件者：{name} ({email})")
    print(f"{'='*50}")

    msg_ids = get_emails_by_sender(mail, email)
    if not msg_ids:
        print("📭 沒有新信件，跳過")
        return

    print(f"📬 找到 {len(msg_ids)} 封信件")

    for msg_id in msg_ids:
        email_data = get_email_content(mail, msg_id)
        subject    = email_data['subject']
        links      = email_data['links']

        print(f"\n  📧 信件主旨：{subject}")
        print(f"  🔗 找到 {len(links)} 個連結")

        if not links:
            print("  ⚠️  沒有找到任何連結，跳過此封信件")
            delete_email(mail, msg_id)
            continue

        summaries = []
        for i, url in enumerate(links, 1):
            print(f"    [{i}/{len(links)}] 抓取：{url}")
            content = fetch_article_content(url)
            print(f"    [{i}/{len(links)}] 摘要中...")
            summary = summarize_content(url, content)
            summaries.append({'url': url, 'summary': summary})

        send_summary_email(subject, name, summaries)
        delete_email(mail, msg_id)


def main() -> None:
    if not SENDERS:
        print("⚠️  config.json 中沒有啟用的寄件者，請檢查 senders 設定")
        sys.exit(1)

    print("🚀 Newsletter Bot 啟動")
    print(f"📋 共 {len(SENDERS)} 個啟用的寄件者：")
    for s in SENDERS:
        print(f"   - {s['name']} ({s['email']})")

    mail = None
    try:
        mail = get_gmail_service(GMAIL_USER, GMAIL_APP_PASSWORD)

        for sender in SENDERS:
            process_sender(mail, sender)

    except KeyboardInterrupt:
        print("\n⛔ 使用者中斷執行")
    except Exception as e:
        print(f"\n❌ 發生錯誤：{e}")
        raise
    finally:
        if mail:
            close_connection(mail)
            print("\n🔌 Gmail 連線已關閉")

    print("\n🎉 全部完成！")


if __name__ == "__main__":
    main()
