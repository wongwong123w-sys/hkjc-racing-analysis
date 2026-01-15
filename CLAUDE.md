# 🤖 CLAUDE 編碼指南 - HKJC 賽馬分析系統

**目的**: 本文檔教導 Claude (Sider / Claude API) 如何正確理解和修改本項目  
**適用版本**: v16.0+  
**最後更新**: 2026-01-15

---

## 📖 如何閱讀本項目

### 第 1 步：了解整體結構

1. 先讀 `PROJECT_CONTEXT.md` 了解系統整體架構
2. 系統分為 4 層：
   - **UI 層** (`pages/`) - Streamlit 頁面
   - **邏輯層** (`analyzers/`) - 分析 / 爬蟲模塊
   - **數據層** (`data/`) - SQLite 存儲
   - **配置層** (`app.py`) - 應用主入口

### 第 2 步：根據任務確定修改位置

**任務類型 → 修改文件**

| 任務 | 修改位置 | 複雜度 |
|------|---------|--------|
| 新增 UI 功能 | `pages/page_*.py` | 🟢 低 |
| 修改排位表邏輯 | `analyzers/racecard_analyzer.py` | 🔴 高 |
| 修改跑法預測 | `analyzers/runstyle_predictor.py` | 🟡 中 |
| 新增分析模塊 | 在 `analyzers/` 新增 `.py` | 🟡 中 |
| 修改數據庫結構 | `analyzers/db_manager.py` | 🟡 中 |
| 修改配速診斷 | `analyzers/pace_predictor.py` | 🟡 中 |

---

## 🔍 核心模塊速查

### 1️⃣ 排位表相關 (`racecard_analyzer.py`)

**責任**: 爬蟲 HKJC 排位表，集成馬匹往績

**核心方法**:
```python
def fetch_racecard(date_str, racecourse, race_no, fetch_history=True, max_races=6):
    """
    爬取排位表 + 往績
    
    輸入:
      date_str: "2026-01-15"
      racecourse: "沙田" 或 "跑馬地"
      race_no: 1-14
      fetch_history: 是否爬往績
      max_races: 往績最多幾場
    
    輸出:
      {
        'race_id': 'HV_20260115_1',
        'date': '2026-01-15',
        'racecourse': '沙田',
        'race_no': 1,
        'horses': [
          {
            'draw': 1,
            'horse_name': '勇敢馬',
            'jockey': '張家傑',
            'weight': 1000,
            ... (20+ 欄位)
            'history': [6 場往績]
          },
          ... (12 隻馬)
        ],
        'total_horses': 12
      }
    """
```

**修改指南**:
- 🔴 高風險：改爬蟲邏輯（會影響整個系統）
- 修改前務必在 `integration_test.py` 測試
- 常見問題：HTML 變更 → 更新 CSS selector

**相關文件**:
- 依賴: `horse_racing_history_parser.py` (往績爬蟲)
- 使用方: `page_racecard.py` (UI 層)

---

### 2️⃣ 跑法預測 (`runstyle_predictor.py`)

**責任**: 分析馬匹往績，預測路線 (FRONT/MID/BACK)

**核心方法**:
```python
def predict_runstyle(horse_data):
    """
    輸入: 馬匹數據 (dict 含 history)
    
    輸出: "FRONT" / "MID" / "BACK"
    
    邏輯:
      1. 解析往績數據
      2. 計算配速指數 (分析第一、中段、最後段跑位)
      3. 根據比例決定跑法
      
    例子:
      - 領先率 > 60% → FRONT (前驅)
      - 40% ~ 60% → MID (中遊)
      - < 40% → BACK (後上)
    """
```

**修改指南**:
- 🟡 中風險：改預測算法（影響分析結果準確度）
- 修改前要有歷史數據驗證
- 測試方式：在 `page_pace_prediction_integrated.py` 手動測試幾個馬匹
- 輸出必須是 "FRONT" / "MID" / "BACK" 三個值之一

**相關文件**:
- 依賴: `horse_racing_history_parser.py` (往績)
- 使用方: `page_pace_prediction_integrated.py` (UI 層)

---

### 3️⃣ 配速診斷 (`pace_predictor.py`)

**責任**: 5 級配速分析 (A 快 → E 慢)

**核心方法**:
```python
def analyze_pace(race_data):
    """
    輸入: 整場賽次數據
    
    輸出: {
      '馬匹名': 'A' / 'B' / 'C' / 'D' / 'E',
      ...
    }
    
    級別說明:
      A: 極快 (< 標準時間 1%)
      B: 快 (1% ~ 25%)
      C: 中等 (25% ~ 75%)
      D: 慢 (75% ~ 99%)
      E: 極慢 (> 99%)
    """
```

**修改指南**:
- 依賴標準時間 (`standard_times_lookup.py`)
- 修改前確認標準時間數據是否正確
- 5 個級別須均勻分佈

**相關文件**:
- 依賴: `standard_times_lookup.py`, `base_analyzer.py`
- 使用方: `page_pace_prediction_integrated.py`

---

### 4️⃣ 檔位統計 (`draw_statistics_parser.py`)

**責任**: 爬蟲馬會檔位統計 (1-14 檔)

**核心方法**:
```python
def fetch_draw_statistics():
    """
    爬取馬會最新檔位統計
    
    輸出: {
      '1': {'wins': 100, 'places': 250, 'strike_rate': 0.25},
      '2': {...},
      ...
      '14': {...}
    }
    
    欄位說明:
      wins: 勝場數
      places: 入位數
      strike_rate: 勝率
      win_rate: 獲利率 (可選)
    """
```

**修改指南**:
- 高度依賴馬會網站 HTML 結構
- 網站改版時會失效
- 測試工具: `draw_scraper_test.py`

**相關文件**:
- 測試: `draw_scraper_test.py`
- 使用方: `page_draw_statistics.py` (UI 層)
- 數據存儲: `db_manager.py`

---

### 5️⃣ 往績爬蟲 (`horse_racing_history_parser.py`)

**責任**: 爬取個別馬匹的歷史紀錄

**核心方法**:
```python
def fetch_horse_history(horse_name, max_races=6):
    """
    爬取某隻馬的歷史紀錄
    
    輸入: 
      horse_name: "勇敢馬"
      max_races: 最多爬幾場 (預設 6 場)
    
    輸出: [
      {
        'date': '2026-01-10',
        'race_no': 5,
        'place': '沙田',
        'distance': 1600,
        'position': 3,        # 第 3 名
        'time': '1:38.50',
        'weight': 1000,
        'odds': 12.5
      },
      ... (最多 6 場)
    ]
    """
```

**修改指南**:
- 每場往績須包含完整 17 欄數據
- 位置排序：最新的在前
- 爬取超時 → 主動返回空或部分數據

**相關文件**:
- 使用方: `racecard_analyzer.py` (排位表爬蟲會調用)

---

### 6️⃣ 數據庫管理 (`db_manager.py`)

**責任**: SQLite 數據持久化

**核心表結構**:
```python
# 賽次表
races (race_id, date, racecourse, race_no, ...)

# 馬匹表
horses (horse_id, horse_name, race_id, draw, weight, ...)

# 預測表
predictions (pred_id, horse_id, runstyle, pace_level, ...)

# 檔位統計表
draw_statistics (draw_num, wins, places, strike_rate, ...)
```

**核心方法**:
```python
def save_racecard(race_id, horses_data) -> bool:
    """保存整場排位表"""
    
def query_horse_history_from_db(horse_name) -> list:
    """查詢馬匹歷史（從本地 DB）"""
    
def save_draw_statistics(stats_data) -> bool:
    """保存檔位統計"""
```

**修改指南**:
- 每次添加新表都要在 `CREATE TABLE` 和 `save_*()` 中實現
- 務必設定 PRIMARY KEY 和 FOREIGN KEY
- SQLite 不支持複雜數據類型，用 JSON 文本存複雜結構

**相關文件**:
- 所有爬蟲模塊都會調用 `save_*()` 方法

---

## 🛠 常見修改場景

### 場景 1：修改排位表顯示欄位

**步驟**:
1. 打開 `analyzers/racecard_analyzer.py`
2. 找到 `fetch_racecard()` 方法
3. 修改 `return` 前的 `horses` 列表，調整欄位
4. 在 `pages/page_racecard.py` 更新 `st.dataframe()` 顯示欄位
5. 執行 `integration_test.py` 驗證

**範例**:
```python
# 修改前：返回 27 欄
horses_data = {...全部 27 欄...}

# 修改後：只返回關鍵 10 欄
horses_data = {
    'draw': ...,
    'horse_name': ...,
    'weight': ...,
    'jockey': ...,
    # ... (只要 10 欄)
}
```

---

### 場景 2：優化跑法預測準確度

**步驟**:
1. 打開 `analyzers/runstyle_predictor.py`
2. 修改 `predict_runstyle()` 的邏輯（第 1 段佔比、中段佔比等）
3. 手動測試 5-10 個歷史馬匹，驗證預測是否合理
4. 在 `page_pace_prediction_integrated.py` 的 "診斷" 功能試驗

**常見改進點**:
```python
# 修改前：固定比例
front_ratio = history.count(位置 < 4) / len(history)
if front_ratio > 0.6: return "FRONT"

# 修改後：考慮距離、場地、馬齡
front_ratio = weighted_avg(歷史跑位, 權重=最近 3 場)
if front_ratio > 0.65 and 馬齡 > 3: return "FRONT"
```

---

### 場景 3：新增一個 UI 頁面

**步驟**:
1. 在 `pages/` 新增 `page_newfeature.py`
2. 定義 `def render():` 函數
3. 在 `pages/__init__.py` 導入
4. 在 `app.py` 的 Tab 區塊添加

**模板**:
```python
# pages/page_newfeature.py
import streamlit as st
from analyzers import SomeAnalyzer  # 調用邏輯層

def render():
    st.set_page_config(page_title="新功能", layout="wide")
    st.title("🎯 新功能標題")
    
    # 側邊欄輸入
    with st.sidebar:
        param1 = st.text_input("參數 1")
        if st.button("執行"):
            analyzer = SomeAnalyzer()
            result = analyzer.some_method(param1)
            st.dataframe(result)
```

```python
# app.py 中
tab1, tab2, ..., tab_new = st.tabs([...新 Tab...])
with tab_new:
    from pages import page_newfeature
    page_newfeature.render()
```

---

### 場景 4：修改數據庫結構

**步驟**:
1. 在 `analyzers/db_manager.py` 的 `CREATE TABLE` 區塊添加新表
2. 實現 `save_newtable()` 和 `query_newtable()` 方法
3. 在相關模塊調用這兩個方法
4. 測試 `integration_test.py`

**範例**:
```python
# 新增表
CREATE TABLE user_preferences (
    user_id TEXT PRIMARY KEY,
    favorite_horses TEXT,  # JSON 格式
    alert_settings JSON,
    created_at TIMESTAMP
);

# 實現保存
def save_user_preferences(user_id, settings):
    sql = "INSERT OR REPLACE INTO user_preferences ..."
    
# 實現查詢
def query_user_preferences(user_id):
    sql = "SELECT * FROM user_preferences WHERE user_id = ?"
```

---

## 🔐 重要規範

### 1. 數據驗證

所有爬蟲返回前必須驗證數據完整性：

```python
def fetch_data(...):
    # 爬取數據
    data = scrape(...)
    
    # 驗證
    if not data or len(data) == 0:
        logger.warning("數據爬取失敗或為空")
        return None
    
    # 檢查關鍵欄位
    for item in data:
        if 'required_field' not in item:
            logger.error(f"缺少關鍵欄位: {item}")
            return None
    
    return data  # 通過驗證
```

### 2. 錯誤處理

使用 try-except 和 logging：

```python
try:
    result = analyzer.analyze(data)
except TimeoutError:
    logger.error("爬蟲超時，請重試")
    st.error("連接超時，請稍後再試")
except ValueError as e:
    logger.error(f"數據格式錯誤: {str(e)}")
    st.error("數據格式不正確")
except Exception as e:
    logger.error(f"未預期的錯誤: {str(e)}")
    st.error("發生未知錯誤，請聯繫開發者")
```

### 3. 命名規範

- **函數**: `snake_case` (fetch_racecard, analyze_pace)
- **類**: `PascalCase` (RaceCardAnalyzer, RunstylePredictor)
- **常數**: `UPPER_SNAKE_CASE` (MAX_RETRIES, TIMEOUT)
- **私有方法**: `_snake_case` (_parse_html, _validate_data)

### 4. 註釋規範

每個函數必須有 docstring：

```python
def fetch_racecard(date_str, racecourse, race_no):
    """
    爬取排位表及馬匹往績
    
    Args:
        date_str (str): 日期，格式 "YYYY-MM-DD"
        racecourse (str): 賽場，"沙田" 或 "跑馬地"
        race_no (int): 賽次，1-14
    
    Returns:
        dict: 排位表數據 {'race_id', 'horses', 'total_horses', ...}
        None: 爬取失敗
    
    Raises:
        TimeoutError: 連接超時
        ValueError: 數據格式不合法
    
    Examples:
        >>> result = fetch_racecard("2026-01-15", "沙田", 1)
        >>> print(result['total_horses'])
        12
    """
```

---

## 📝 測試指南

### 單個模塊測試

```bash
# 測試排位表爬蟲
python -c "from analyzers import RaceCardAnalyzer; a = RaceCardAnalyzer(); print(a.fetch_racecard('2026-01-15', '沙田', 1))"
```

### 集成測試

```bash
# 執行完整集成測試
python integration_test.py
```

### 爬蟲測試

```bash
# 測試檔位統計爬蟲
python draw_scraper_test.py
```

---

## 💾 本地開發工作流

### 1. 拉取最新代碼
```bash
git pull origin main
```

### 2. 修改代碼
```bash
# 修改某個檔案
vim analyzers/runstyle_predictor.py
```

### 3. 測試
```bash
# 運行集成測試
python integration_test.py

# 或在 Streamlit 上測試
streamlit run app.py
```

### 4. 提交更改
```bash
git add .
git commit -m "改善: 跑法預測算法精度提高 2%"
git push origin main
```

---

## 🚨 常見陷阱

| 問題 | 症狀 | 解決方案 |
|------|------|---------|
| 爬蟲失敗 | `TimeoutError` 或 HTML 解析錯誤 | 檢查 User-Agent、更新 CSS selector |
| 往績為空 | 馬匹無往績顯示 | 檢查馬匹名稱是否正確（繁體、空格） |
| 配速異常 | 級別全是 "C" | 檢查標準時間數據是否加載 |
| DB 鎖定 | `OperationalError: database is locked` | 關閉其他 DB 連接，重啟應用 |
| 內存溢出 | 加載大量往績卡頓 | 限制 `max_races` 參數 (預設 6) |

---

## 📞 快速索引

| 問題 | 查看文件 |
|------|---------|
| "系統整體結構是什麼？" | `PROJECT_CONTEXT.md` |
| "怎樣修改跑法預測？" | 本文 § 場景 2 |
| "爬蟲超時怎辦？" | `analyzers/race_crawler.py` (retry 邏輯) |
| "怎樣新增數據庫表？" | 本文 § 場景 4 |
| "測試代碼怎樣寫？" | `integration_test.py` |
| "Streamlit 怎樣用？" | `pages/page_racecard.py` (範例) |

---

**本文檔作為 Claude 的編碼指南，應該讓你快速理解和修改項目的任何部分。有問題直接讀本文 / PROJECT_CONTEXT.md。**

最後更新: 2026-01-15 ✅
