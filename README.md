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

設定拆成兩份，**密鑰不進版控**：

- **`config.json`**：可提交到 Git。放 OpenAI 型號、senders 等非敏感設定。
- **`config.secrets.json`**：不提交（已在 `.gitignore`）。放 Gmail 帳密、API Key 等。

第一次使用請：

1. 複製 `config.secrets.example.json` 為 `config.secrets.json`
2. 在 `config.secrets.json` 填入你的 Gmail、OpenAI/Azure API key 等

### config.secrets.json 欄位

| 欄位 | 說明 |
|------|------|
| `gmail.user` | 你的 Gmail 帳號 |
| `gmail.app_password` | Gmail 應用程式密碼（16碼） |
| `openai.api_key` | Azure OpenAI 或 OpenAI API Key |
| `openai.azure.endpoint` | Azure OpenAI endpoint URL |

### config.json 欄位（可公開）

| 欄位 | 說明 |
|------|------|
| `openai.provider` | `"azure"` 或 `"openai"` |
| `openai.model` | 模型名稱 |
| `openai.azure.deployment_name` | Azure 部署名稱 |
| `openai.azure.api_version` | API 版本 |
| `senders` | Newsletter 寄件者清單 |

### 取得 Gmail App Password
1. Google 帳號 → 安全性 → 開啟兩步驟驗證
2. 搜尋「應用程式密碼」→ 產生 16 碼密碼
3. 填入 `config.secrets.json` 的 `gmail.app_password`

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
├── config.json              # 一般設定（可提交）
├── config.secrets.json      # 密鑰（勿提交，從 config.secrets.example.json 複製）
├── config.secrets.example.json  # 密鑰範本
├── config.py                # 讀取設定
├── gmail_client.py      # Gmail IMAP 讀取／刪除
├── scraper.py           # 網頁內容抓取
├── openai_client.py     # Azure OpenAI 摘要
├── email_sender.py      # Gmail SMTP 寄信
├── main.py              # 主程式
├── requirements.txt
└── .gitignore
```
