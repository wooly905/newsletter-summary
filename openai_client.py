from openai import AzureOpenAI, OpenAI
from config import (
    OPENAI_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    AZURE_ENDPOINT,
    AZURE_DEPLOYMENT_NAME,
    AZURE_API_VERSION,
)

# 根據 provider 初始化對應的 client
if OPENAI_PROVIDER == "azure":
    client = AzureOpenAI(
        api_key=OPENAI_API_KEY,
        azure_endpoint=AZURE_ENDPOINT,
        azure_deployment=AZURE_DEPLOYMENT_NAME,
        api_version=AZURE_API_VERSION,
    )
    _model = AZURE_DEPLOYMENT_NAME  # Azure 以 deployment name 作為 model 參數
else:
    client = OpenAI(api_key=OPENAI_API_KEY)
    _model = OPENAI_MODEL


def summarize_content(url: str, content: str) -> str:
    """
    呼叫 OpenAI / Azure OpenAI API，將文章內容摘要成台灣中文。
    若內容為錯誤訊息（抓取失敗），直接回傳該訊息。
    """
    if content.startswith("[錯誤]"):
        return content

    prompt = f"""你是一位專業的文章摘要助理，請用**台灣中文**將以下來自 {url} 的文章整理成摘要。

請依照以下格式輸出：

📌 **主題**：（一句話說明文章主旨）

🔑 **重點摘要**：
1. 
2. 
3. 
（視內容列出 3-5 點）

💡 **結論**：（2-3 句話總結）

---
文章內容：
{content}
"""

    response = client.chat.completions.create(
        model=_model,
        messages=[
            {
                "role": "system",
                "content": "你是一位專業的文章摘要助理，擅長用台灣中文撰寫簡潔清楚的摘要。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=1500,
        temperature=0.3,
    )

    return response.choices[0].message.content
