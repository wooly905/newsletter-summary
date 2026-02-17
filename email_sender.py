import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_USER, GMAIL_APP_PASSWORD


def _build_html(subject: str, sender_name: str, summaries: list[dict]) -> str:
    """組合摘要信件的 HTML 內容"""
    now = datetime.now().strftime("%Y/%m/%d %H:%M")

    articles_html = ""
    for i, item in enumerate(summaries, 1):
        summary_html = item['summary'].replace('\n', '<br>')
        articles_html += f"""
        <div style="margin-bottom:32px; padding:20px; background:#ffffff;
                    border-radius:8px; border:1px solid #e0e0e0;">
            <div style="font-size:13px; color:#888; margin-bottom:6px;">文章 {i}</div>
            <div style="margin-bottom:12px;">
                <a href="{item['url']}" style="color:#1a73e8; word-break:break-all;
                   font-size:14px;">{item['url']}</a>
            </div>
            <div style="font-size:15px; line-height:1.8; color:#333;">
                {summary_html}
            </div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: 'Helvetica Neue', Arial, sans-serif;
                 background:#f5f5f5; margin:0; padding:24px;">
        <div style="max-width:720px; margin:0 auto;">

            <!-- Header -->
            <div style="background:#1a73e8; color:white; padding:24px;
                        border-radius:8px 8px 0 0; margin-bottom:4px;">
                <div style="font-size:12px; opacity:0.8; margin-bottom:4px;">
                    Newsletter 摘要 · {now}
                </div>
                <div style="font-size:22px; font-weight:bold;">
                    📰 {subject}
                </div>
                <div style="font-size:13px; opacity:0.8; margin-top:6px;">
                    來源：{sender_name} · 共 {len(summaries)} 篇文章
                </div>
            </div>

            <!-- Articles -->
            <div style="background:#f9f9f9; padding:20px;
                        border-radius:0 0 8px 8px; border:1px solid #e0e0e0;">
                {articles_html}
            </div>

            <!-- Footer -->
            <div style="text-align:center; font-size:12px; color:#aaa; margin-top:16px;">
                此摘要由 Newsletter Bot 自動產生
            </div>
        </div>
    </body>
    </html>
    """


def send_summary_email(subject: str, sender_name: str, summaries: list[dict]) -> None:
    """
    將摘要結果以 HTML 格式寄送給自己。

    :param subject:     原始信件主旨
    :param sender_name: Newsletter 寄件者名稱（顯示用）
    :param summaries:   [{'url': '...', 'summary': '...'}, ...]
    """
    if not summaries:
        print("⚠️  沒有可寄送的摘要內容，跳過寄信")
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"📰 [摘要] {subject}"
    msg['From']    = GMAIL_USER
    msg['To']      = GMAIL_USER

    html_content = _build_html(subject, sender_name, summaries)
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())

    print(f"✉️  摘要信件已寄出：{subject}（共 {len(summaries)} 篇）")
