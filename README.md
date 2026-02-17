# Newsletter Bot

自動讀取 Gmail newsletter、用 Azure OpenAI 摘要後寄回給自己。

## 流程

```
Gmail (IMAP) → 抓取連結內容 → Azure OpenAI 摘要 → Gmail (SMTP) 寄回 → 刪除原信
```

## 安裝

```bash
pip install -r requirements.txt
```

## 設定

編輯 `config.json`：

| 欄位 | 說明 |
|------|------|
| `gmail.user` | 你的 Gmail 帳號 |
| `gmail.app_password` | Gmail 應用程式密碼（16碼） |
| `openai.provider` | `"azure"` 或 `"openai"` |
| `openai.api_key` | Azure OpenAI 或 OpenAI API Key |
| `openai.azure.endpoint` | Azure OpenAI endpoint URL |
| `openai.azure.deployment_name` | Azure 部署名稱 |
| `openai.azure.api_version` | API 版本（建議 `2024-08-01-preview`） |
| `senders` | Newsletter 寄件者清單 |

### 取得 Gmail App Password
1. Google 帳號 → 安全性 → 開啟兩步驟驗證
2. 搜尋「應用程式密碼」→ 產生 16 碼密碼
3. 填入 `config.json`

### 新增／停用 Newsletter 來源

編輯 `config.json` 的 `senders` 陣列：

```json
"senders": [
  {
    "name": "TechCrunch",
    "email": "newsletter@techcrunch.com",
    "enabled": true
  },
  {
    "name": "暫時停用",
    "email": "news@example.com",
    "enabled": false
  }
]
```

## 執行

```bash
python main.py
```

## 定期自動執行（cron）

```bash
# 每天早上 8 點執行
0 8 * * * cd /path/to/newsletter_bot && python main.py >> bot.log 2>&1
```

## 檔案結構

```
newsletter_bot/
├── config.json          # 設定檔（含機密，勿上傳 git）
├── config.py            # 讀取設定
├── gmail_client.py      # Gmail IMAP 讀取／刪除
├── scraper.py           # 網頁內容抓取
├── openai_client.py     # Azure OpenAI 摘要
├── email_sender.py      # Gmail SMTP 寄信
├── main.py              # 主程式
├── requirements.txt
└── .gitignore
```
