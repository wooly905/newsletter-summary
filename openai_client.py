from openai import AzureOpenAI, OpenAI
from config import (
    OPENAI_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    AZURE_ENDPOINT,
    AZURE_DEPLOYMENT_NAME,
    AZURE_API_VERSION,
)

# Initialize the corresponding client based on provider
if OPENAI_PROVIDER == "azure":
    client = AzureOpenAI(
        api_key=OPENAI_API_KEY,
        azure_endpoint=AZURE_ENDPOINT,
        azure_deployment=AZURE_DEPLOYMENT_NAME,
        api_version=AZURE_API_VERSION,
    )
    _model = AZURE_DEPLOYMENT_NAME  # Azure uses deployment name as model parameter
else:
    client = OpenAI(api_key=OPENAI_API_KEY)
    _model = OPENAI_MODEL


def summarize_content(url: str, content: str) -> str:
    """
    Call OpenAI / Azure OpenAI API to summarize article content into Traditional Chinese (Taiwan).
    If content is an error message (fetch failed), return the message directly.
    """
    if content.startswith("[Error]"):
        return content

    prompt = f"""你是一位專業的文章摘要助理，請用**台灣中文**將以下來自 {url} 的文章整理成摘要。

請依照以下格式輸出：

📌 **主題**：（一句話說明文章主旨）
    **TLDR**：（回答文章的 TLDR 結論）

🔑 **分段重點與結論**：
1. 
2. 
3. 
（視內容列出 3-10 段）

💡 **結論**：（五句話總結）

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
        max_tokens=4096,
        temperature=0.3,
    )

    return response.choices[0].message.content
