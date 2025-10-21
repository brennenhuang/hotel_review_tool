# 智能音箱對話分析平台 (Smart Speaker Conversation Analysis Platform)

一站式、可視化的智能音箱對話分析平台，用於提升營運效率、監控服務穩定性，並最終優化房客的住宿體驗。

## 功能特點

- **數據可視化**：將原始的對話日誌轉化為直觀的統計圖表
- **多維度篩選**：提供靈活的篩選與查詢功能
- **風險監控**：基於回應時間的風險監控機制
- **用戶洞察**：透過意圖和關鍵實體分析深入理解用戶行為
- **智能導出**：自動識別住宿時段並生成格式化報告

## 系統需求

- Python 3.8+
- 瀏覽器：Chrome, Firefox, Safari, Edge（最新版本）

## 安裝步驟

### 1. 安裝依賴套件

使用 conda 環境中的 pip 安裝依賴：

```bash
/Users/timshieh/Documents/aiello/apps/hotel_review_tool/.conda/bin/python -m pip install -r requirements.txt
```

### 2. 運行應用

```bash
/Users/timshieh/Documents/aiello/apps/hotel_review_tool/.conda/bin/python -m streamlit run app.py --server.port 8502
```

應用將在瀏覽器中自動打開，默認地址：http://localhost:8502

## 使用說明

### 1. 數據上傳

- 點擊「選擇檔案」按鈕或直接拖曳 CSV 檔案到上傳區域
- 檔案限制：
  - 格式：CSV
  - 最大筆數：10,000 筆
  - 必需包含 PRD 中定義的欄位

### 2. 數據分析

上傳成功後，您可以：

#### 全域篩選器（側邊欄）
- **時間區間**：選擇日期範圍
- **回應耗時**：設定耗時範圍（秒）
- **分類篩選**：
  - 飯店名稱
  - 房間號碼
  - 用戶意圖
  - 語言
  - 風險等級

#### 可視化分析
- **意圖分佈**：圓餅圖顯示用戶意圖分佈
- **風險分析**：
  - 每日回應時間風險累積柱狀圖
  - 可點擊查看特定風險等級的意圖分佈
- **關鍵實體**：
  - 條形圖：Top 20 關鍵實體
  - 詞雲：視覺化實體出現頻率

### 3. 導出報告

在「導出數據」標籤：
1. 設定標準入住時間（例如：14:00）
2. 設定標準退房時間（例如：11:00）
3. 點擊「生成並導出報告」
4. 系統自動識別住宿時段並生成報告
5. 下載 .txt 格式的報告文件

## 數據欄位映射

| 原始欄位 | 標準化名稱 | 說明 |
|---------|-----------|------|
| `final_output.metadata.queryText` | `user_query` | 用戶問句 |
| `final_output.res` | `chatbot_response` | 機器人回覆 |
| `performance.metadata.language_code` | `user_language` | 語言代碼 |
| `final_output.metadata.hotelName` | `hotel_name` | 飯店名稱 |
| `performance.service_info.total.timecost` | `response_timecost` | 回應耗時 |
| `final_output.intent_name_en` / `intent_name` | `user_intent` | 用戶意圖 |
| `final_output.metadata.roomName` | `room_name` | 房間號碼 |
| `time` | `request_timestamp` | 時間戳 |
| `final_output.metadata.conversation_id` | `conversation_id` | 對話ID |
| `final_output.key_entity` | `key_entity` | 關鍵實體 |

## 風險等級定義

- **安全 (<3s)**：回應時間小於 3 秒
- **低風險 (3-5s)**：回應時間 3-5 秒
- **中風險 (5-8s)**：回應時間 5-8 秒
- **高風險 (>8s)**：回應時間大於 8 秒

## 專案結構

```
hotel_review_tool/
├── app.py                  # 主應用程式
├── data_processor.py       # 數據處理模組
├── visualizations.py       # 可視化模組
├── export_manager.py       # 導出管理模組
├── requirements.txt        # 依賴套件清單
├── PRD.txt                 # 產品需求規格書
├── README.md              # 本文件
└── .gitignore             # Git 忽略清單
```

## 技術棧

- **前端框架**：Streamlit
- **數據處理**：Pandas
- **可視化**：Plotly, WordCloud, Matplotlib
- **Python版本**：3.8+

## 故障排除

### 問題：上傳檔案失敗
- 檢查檔案格式是否為 .csv
- 確認數據筆數不超過 10,000 筆
- 檢查必需欄位是否存在

### 問題：圖表無法顯示
- 檢查篩選條件是否過於嚴格導致無數據
- 嘗試重置篩選條件

### 問題：導出功能出錯
- 確認已選擇有效的時間範圍
- 檢查入住/退房時間格式是否正確

## 授權

請參考專案授權文件。

## 聯繫方式

如有問題或建議，請聯繫開發團隊。
