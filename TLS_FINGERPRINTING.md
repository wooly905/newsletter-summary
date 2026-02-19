# 深入淺出 TLS 指紋辨識 (TLS Fingerprinting)

在開發爬蟲或自動化工具時，你可能會發現即使偽造了完美的 `User-Agent` 和 `Headers`，有些網站（如 beehiiv, Cloudflare 保護下的網站）仍然會對你的請求回傳 **403 Forbidden**。這通常是因為網站使用了 **TLS 指紋辨識** 技術。

---

## 什麼是 TLS 指紋？

當你的程式（客戶端）透過 HTTPS 連線到伺服器時，在傳送任何 HTTP 資料之前，必須先進行 **TLS 握手 (TLS Handshake)**。在這個階段，客戶端會發送一個 `Client Hello` 訊息。

**TLS 指紋** 就是根據 `Client Hello` 訊息中所包含的各種參數組合而成的「特徵碼」。

### TLS 握手包含哪些特徵？

在握手過程中，客戶端會告訴伺服器：
1. **TLS 版本**：支援 1.2 還是 1.3？
2. **密碼套件 (Cipher Suites)**：支援哪些加密演算法？它們的**排列順序**為何？
3. **擴充功能 (Extensions)**：例如 SNI, ALPN, Supported Groups 等。
4. **擴充功能的順序**：即使功能相同，不同客戶端排列它們的順序也不同。
5. **壓縮方法**。

---

## 為什麼傳統方法會失敗？

### 傳統 Bot 偵測：User-Agent 檢查
以前的伺服器只檢查 HTTP Headers 中的 `User-Agent`。
- **解決方案**：簡單地把 `User-Agent` 改成 Chrome 的字串即可。

### 現代 Bot 偵測：TLS 指紋比對
現在的伺服器會在 TLS 層級就進行識別。
- **問題**：Python 的 `requests` 庫底層使用的 `urllib3` 或 `ssl` 模組，其生成的 TLS 握手參數與真正的瀏覽器（Chrome/Firefox）有顯著差異。
- **結果**：伺服器看到：
    - HTTP Header 說：「我是 Chrome」
    - TLS 指紋說：「我是 Python」
    - **衝突！伺服器判斷為 Bot 並直接封鎖 (403)。**

---

## 如何解決？使用 `curl_cffi` 與 Impersonation

要繞過 TLS 指紋辨識，你的工具必須能夠**模擬 (Impersonate)** 真正瀏覽器的 TLS 握手行為。

### `curl_requests` vs `requests`

在本项目中，我們將 `requests` 替換成了 `curl_cffi`，這是一個基於 `curl-impersonate` 的強大工具。

```python
from curl_cffi import requests

# 使用 impersonate 參數，模仿真實瀏覽器的 TLS 指紋
response = requests.get(
    "https://example.com", 
    impersonate="chrome131" # 關鍵：模仿真實 Chrome 131 的握手特徵
)
```

### 為什麼這有效？
當設定 `impersonate="chrome131"` 時，`curl_cffi` 會調整其底層的 TLS 參數（如 Cipher Suites 的順序、Extensions 的組合），使其在伺服器端看來與真正的 Chrome 瀏覽器完全一致。

---

## 常見的 TLS 指紋演算法
- **JA3**: 目前最流行的 TLS 指紋算法。它將 TLS 握手中的核心參數拼接後做 MD5 哈希，生成一個唯一的字串。
- **JA4**: JA3 的進化版，包含更多層級的指紋資訊（如 TCP, HTTP 層）。

## 總結
在對抗現代反爬蟲機制時，單純偽造 HTTP 層級的資訊已經不夠了。**TLS 指紋辨識** 讓伺服器能從底層網路行為識別出自動化腳本。使用如 `curl_cffi` 這樣支援 TLS 模擬的工具，是目前繞過此類保護最有效的方法。
