# 🐴 HKJC 賽馬分析系統 - 項目上下文

**版本**: v16.0 (完整整合版)  
**最後更新**: 2026-01-15  
**GitHub**: https://github.com/wongwong123w-sys/hkjc-racing-analysis  
**狀態**: ✅ 生產環境就緒

---

## 📋 快速概覽

HKJC 賽馬分析系統是一個基於 **Streamlit** 的實時賽馬分析工具，整合了：

- **爬蟲層**: HKJC 官網實時數據抓取
- **分析層**: 20+ 分析模組（跑法預測、配速診斷、檔位統計等）
- **UI 層**: 7 個交互式分析頁面
- **數據層**: SQLite 持久化存儲

---

## 🎯 核心功能模塊

| 功能 | 模塊 | 版本 | 狀態 | 說明 |
|------|------|------|------|------|
| **排位表分析** | `racecard_analyzer.py` | v2.0 | ✅ | 爬蟲 HKJC 排位表 (27 欄) + 往績集成 |
| **跑法預測** | `runstyle_predictor.py` | v4.1 | ✅ | 預測馬匹路線 (FRONT/MID/BACK) |
| **配速診斷** | `pace_predictor.py` | v3.0 | ✅ | 5 級配速分析 (A-E) |
| **檔位統計** | `draw_statistics_parser.py` | v1.0 | ✅ | 1-14 檔歷史統計爬蟲 |
| **往績爬蟲** | `horse_racing_history_parser.py` | v2 | ✅ | 馬匹 6 場歷史紀錄提取 |
| **分段時間** | `hkjc_sectional.py` | v2 | ✅ | 完整步速分析工具 |
| **數據庫** | `db_manager.py` | v2.0 | ✅ | SQLite 持久化管理 |
| **配腳評分** | `leg_fitness_*.py` (4 個模塊) | v1.0 | ✅ | 4 層配腳評分系統 |

---

## 📁 項目結構

```
hkjc_app/
│
├── app.py                          # 🏠 主應用入口 (v14.0)
│   └─ 7 個 Tab 導航 + 共用狀態管理
│
├── pages/                          # 🎨 UI 層 (8 個頁面)
│   ├── __init__.py                 # 模塊初始化
│   ├── page_segment.py             # Tab1: 分段時間分析
│   ├── page_pace.py                # Tab2: 步速分析 (預留)
│   ├── page_report.py              # Tab3: 完整分析報告
│   ├── page_racecard.py            # Tab4: 排位表分析 (v3.10) ⭐
│   ├── page_pace_prediction.py      # Tab5: 跑法預測 (基礎版)
│   ├── page_pace_prediction_integrated.py  # Tab5: 跑法預測 (診斷版 v5.7) ⭐
│   ├── page_draw_statistics.py     # Tab7: 檔位統計 (v1.0) ✨
│   └── page_database_monitor.py    # Tab6: 數據庫監控 (v1.0) ✨
│
├── analyzers/                      # 🧠 邏輯層 (20+ 模塊)
│   ├── __init__.py                 # 初始化 + 導入
│   │
│   # ▶ 核心爬蟲模塊
│   ├── racecard_analyzer.py        # 排位表爬蟲 (v2.0) ⭐
│   ├── horse_racing_history_parser.py  # 往績爬蟲 ⭐
│   ├── race_crawler.py             # 賽次爬蟲 (v2) ✨
│   ├── draw_statistics_parser.py   # 檔位統計爬蟲 (v1.0) ✨
│   │
│   # ▶ 核心分析模塊
│   ├── runstyle_predictor.py       # 跑法預測 (v4.1) ⭐
│   ├── pace_predictor.py           # 配速預測 (v3.0) ✨
│   ├── pace_analysis.py            # 步速分析工具 (v2) ✨
│   │
│   # ▶ 配腳評分模塊 (4 層)
│   ├── leg_fitness_data_prep.py    # 數據預處理 ✨
│   ├── leg_fitness_calculator.py   # 分值計算 ✨
│   ├── leg_fitness_tag_identifier.py # 標籤識別 ✨
│   ├── leg_fitness_scorer_realtime.py # 實時評分 ✨
│   │
│   # ▶ 輔助模塊
│   ├── base_analyzer.py            # 基類 (標準時間查詢) ✅
│   ├── race_details_extractor.py   # 賽次詳情提取 (v2.1) ⭐
│   ├── report_analyzer.py          # 報告生成
│   ├── standard_times_lookup.py    # 標準時間查詢
│   ├── horse_racing_html_analyzer.py  # HTML 分析工具
│   ├── db_manager.py               # 數據庫管理 (v2.0) ✨
│   ├── error_handler.py            # 錯誤處理 ✨
│   └── data_manager.py             # 數據管理中心
│
├── data/                           # 💾 數據存儲
│   ├── hkjc_data.db                # SQLite 主數據庫 ✨
│   ├── draw_statistics.json        # 檔位統計 (備用)
│   ├── race_data.json              # 賽馬數據
│   └── betting_history.json        # 投注歷史
│
└── [爬蟲工具]
    ├── run_crawler.py              # 爬蟲啟動器
    ├── crawler_gui.py              # 爬蟲 GUI
    ├── integration_test.py         # 集成測試
    └── draw_scraper_test.py        # 檔位統計測試
```

**圖例**:
- ⭐ = 核心模塊 (重點修改對象)
- ✨ = v16.0 新增 / 增強模塊
- ✅ = 有詳細文檔記錄

---

## 🔗 關鍵依賴關係

### 1. **排位表工作流**

```
page_racecard.py (UI)
    ↓
racecard_analyzer.fetch_racecard()
    ├─ 爬蟲排位表 (27 欄)
    └─ 調用 horse_racing_history_parser (往績)
        ├─ 每隻馬爬 6 場歷史紀錄
        └─ 集成回排位表
    ↓
返回完整馬匹數據 (排位表 + 往績)
```

### 2. **跑法預測工作流**

```
page_pace_prediction_integrated.py (UI)
    ↓
runstyle_predictor.predict_runstyle()
    ├─ 分析馬匹往績
    ├─ 計算配速指數
    └─ 預測路線 (FRONT/MID/BACK)
    ↓
pace_predictor.analyze_pace()
    ├─ 5 級配速評估
    └─ 生成配速診斷
```

### 3. **檔位統計工作流**

```
page_draw_statistics.py (UI)
    ↓
draw_statistics_parser.fetch_draw_stats()
    ├─ 爬蟲 HKJC 檔位統計
    └─ 按檔位 (1-14) 分類
    ↓
db_manager.save_draw_statistics()
    └─ SQLite 存儲
    ↓
leg_fitness_scorer_realtime.score()
    └─ 配腳評分計算
```

### 4. **數據庫層**

```
所有爬蟲 → db_manager.save_*()
    ↓
SQLite (hkjc_data.db)
    ├─ races 表
    ├─ horses 表
    ├─ draw_statistics 表
    └─ predictions 表
    ↓
data_manager.query_*()
    ↓
UI 層顯示
```

---

## 🛠 開發規範

### 爬蟲模塊 (Scraper Modules)

**位置**: `analyzers/race_crawler.py`, `racecard_analyzer.py` 等

**職責**:
- 連接 HKJC 官網，爬取原始 HTML
- 解析 HTML，提取結構化數據
- 返回 JSON / Dict 格式

**關鍵方法**:
```python
def fetch_racecard(date_str, racecourse, race_no) -> dict:
    """爬取排位表，返回馬匹列表"""
    
def fetch_horse_history(horse_name, max_races=6) -> dict:
    """爬取馬匹往績"""
    
def fetch_draw_statistics() -> dict:
    """爬取檔位統計"""
```

**注意事項**:
- 實施 User-Agent + 請求頭，避免被馬會反爬
- 添加 timeout 和 retry 邏輯
- 返回前驗證數據完整性

---

### 分析模塊 (Analyzer Modules)

**位置**: `analyzers/runstyle_predictor.py`, `pace_predictor.py` 等

**職責**:
- 接收爬蟲數據 (dict / DataFrame)
- 執行分析算法
- 返回預測 / 評分結果

**關鍵方法**:
```python
def predict_runstyle(horse_data: dict) -> str:
    """輸入: 馬匹往績，輸出: FRONT/MID/BACK"""
    
def analyze_pace(race_data: dict) -> dict:
    """輸入: 賽次數據，輸出: 5 級配速"""
```

**數據流**:
```
爬蟲數據 (raw dict)
    ↓
分析模塊處理
    ├─ 數據清洗
    ├─ 特徵工程
    └─ 模型推理
    ↓
結構化結果 (預測 / 評分)
```

---

### UI 層 (Page Modules)

**位置**: `pages/page_*.py`

**職責**:
- 收集用戶輸入 (日期、賽場、賽次等)
- 調用分析模塊
- 展示結果 (表格、圖表、文字)

**標準流程**:
```python
# 1. 界面設置
st.set_page_config(page_title="排位表分析", layout="wide")

# 2. 側邊欄輸入
with st.sidebar:
    date = st.date_input("選擇日期")
    racecourse = st.selectbox("選擇賽場", ["沙田", "跑馬地"])
    race_no = st.number_input("賽次", min_value=1, max_value=14)

# 3. 調用分析
if st.button("分析"):
    analyzer = RaceCardAnalyzer()
    result = analyzer.fetch_racecard(date, racecourse, race_no)
    
# 4. 顯示結果
st.dataframe(result['horses'])
```

---

### 數據庫層 (Database Manager)

**位置**: `analyzers/db_manager.py`

**職責**:
- 管理 SQLite 連接
- 保存 / 查詢數據
- 緩存管理

**核心方法**:
```python
def save_racecard(race_id, horses_data) -> bool:
    """保存排位表"""
    
def query_horse_history(horse_name) -> list:
    """查詢馬匹歷史"""
    
def get_draw_statistics(draw_num) -> dict:
    """查詢檔位統計"""
```

**表結構**:
```sql
-- races 表
CREATE TABLE races (
    race_id TEXT PRIMARY KEY,
    date TEXT,
    racecourse TEXT,
    race_no INT,
    created_at TIMESTAMP
);

-- horses 表
CREATE TABLE horses (
    horse_id TEXT PRIMARY KEY,
    horse_name TEXT,
    race_id TEXT,
    draw INT,
    weight INT,
    jockey TEXT,
    ... (20+ 欄位)
    FOREIGN KEY (race_id) REFERENCES races(race_id)
);

-- predictions 表
CREATE TABLE predictions (
    pred_id TEXT PRIMARY KEY,
    horse_id TEXT,
    runstyle TEXT,    # FRONT/MID/BACK
    pace_level TEXT,  # A-E
    leg_fitness FLOAT,
    created_at TIMESTAMP
);
```

---

## ⚙ 常用工作流

### 場景 1: 分析某個賽次

```python
# 1. 爬蟲
analyzer = RaceCardAnalyzer()
racecard = analyzer.fetch_racecard("2026-01-15", "沙田", 1)

# 2. 預測
runstyle_pred = RunstylePredictor().predict_runstyle(racecard['horses'])
pace_pred = PacePredictor().analyze_pace(racecard)

# 3. 存儲
db = DBManager()
db.save_racecard(racecard['race_id'], racecard['horses'])
db.save_predictions(racecard['race_id'], runstyle_pred, pace_pred)

# 4. 展示（在 UI 層）
# st.dataframe(結果)
```

### 場景 2: 配腳評分計算

```python
# 1. 數據準備
prep = LegFitnessDataPrep()
prepared_data = prep.prepare(horse_data)

# 2. 計算評分
calc = LegFitnessCalculator()
scores = calc.calculate(prepared_data)

# 3. 識別標籤
identifier = LegFitnessTagIdentifier()
tags = identifier.identify(scores)

# 4. 實時評分
scorer = LegFitnessScorerRealtime()
final_score = scorer.score(scores, tags)
```

---

## 📊 版本歷史

| 版本 | 日期 | 重點改動 |
|------|------|---------|
| v16.0 | 2026-01-12 | 完整 Analyzers 層詳解 + 配腳評分系統 |
| v14.0 | 2025-12-20 | 7 個 Tab 導航整合 |
| v12.0 | 2025-12-10 | 完整模塊化重構 |
| v10.0 | 2025-11-15 | 跑法預測 v3.1 + 排位表 v2.0 |
| v1.0 | 2025-10-01 | 初始版本 |

---

## 🔧 常見修改點

### 修改排位表爬蟲邏輯
📁 修改位置: `analyzers/racecard_analyzer.py`  
⚠️ 風險等級: 🔴 高  
✅ 測試方式: `python integration_test.py`

### 修改跑法預測算法
📁 修改位置: `analyzers/runstyle_predictor.py`  
⚠️ 風險等級: 🟡 中  
✅ 測試方式: 在 `page_pace_prediction_integrated.py` 手動測試

### 新增 UI 頁面
📁 修改位置: `pages/page_*.py`  
⚠️ 風險等級: 🟢 低  
✅ 修改步驟:
1. 在 `pages/` 新增 `page_newfeature.py`
2. 在 `app.py` 的 Tab 區塊添加新 tab
3. 導入新頁面的 render 函數

### 新增數據庫表
📁 修改位置: `analyzers/db_manager.py`  
⚠️ 風險等級: 🟡 中  
✅ 修改步驟:
1. 在 `CREATE TABLE` 區塊添加新表
2. 實現 `save_*()` 和 `query_*()` 方法
3. 在其他模塊調用新方法

---

## 📞 聯繫方式 / 文檔資源

- **GitHub**: https://github.com/wongwong123w-sys/hkjc-racing-analysis
- **開發指引**: `HKJC-Sai-Ma-Fen-Xi-Xi-Tong-Kai-Fa-Zhi-Yin-Wen-Dang.md`
- **快速參考**: `QUICK_REFERENCE.md`
- **Pace 分析**: `PACE_ANALYSIS_GUIDE.md`

---

**最後更新**: 2026-01-15  
**AI 友好**: ✅ 本文檔專為 Perplexity / Claude 設計，包含完整上下文。
