# 香港賽馬步速分析 - 快速參考

## 📦 新增檔案清單

| 檔案 | 大小 | 說明 |
|------|------|------|
| `standard_times_lookup.py` | ~15 KB | 標準時間查詢模組 + 香港賽馬會數據庫 |
| `pace_analysis.py` | ~12 KB | 步速分析引擎 + Streamlit 集成 |
| `PACE_ANALYSIS_GUIDE.md` | ~10 KB | 完整集成指南 |

**存放位置**: `C:\hkjc_app\`

---

## 🎯 主要功能

### ✅ 完成時間與標準時間比較
```
實際完成時間 vs 標準時間 → 差異(秒) → 步速分型
例: 1:09.50 vs 1:09.35 → +0.15秒 → 普通步速
```

### ✅ 分段時間與標準分段比較  
```
實際分段總和 vs 標準分段總和 → 差異(秒) → 步速分型
例: 69.90 vs 69.35 → +0.55秒 → 慢步速
```

### ✅ 步速分類
```
差異 ≤ -0.5秒    → 快步速 (FAST)
-0.5秒 < 差異 < +0.5秒 → 普通步速 (NORMAL)
差異 ≥ +0.5秒    → 慢步速 (SLOW)
```

---

## 🚀 最小化集成代碼

### app.py 中新增（複製貼上）：

```python
# ========== 在 import 區域新增 ==========
from pace_analysis import render_pace_analysis_section

# ========== 在側邊欄 radio 選項新增 ==========
query_mode = st.sidebar.radio(
    "選擇查詢模式",
    ["📊 全日分析", "🏇 單場詳細", "🏆 賽事步速分析"]  # ← 新增最後一項
)

# ========== 在主程式新增（elif 分支） ==========
elif query_mode == "🏆 賽事步速分析":
    st.subheader("🏆 賽事步速分析")
    
    if st.sidebar.button("取得分析數據"):
        try:
            df_all, num_races, metadata_dict = load_day_races(race_date, max_race_no)
            if not df_all.empty:
                render_pace_analysis_section(st, df_all, racecourse="Sha Tin")
            else:
                st.warning("無可用資料")
        except Exception as e:
            st.error(f"分析失敗: {e}")
```

---

## 📚 核心 API 速查表

### 時間轉換
```python
from standard_times_lookup import time_str_to_seconds, seconds_to_time_str

time_str_to_seconds("1:09.90")  # → 69.90
seconds_to_time_str(69.90)       # → "1:09.90"
```

### 標準時間查詢
```python
from standard_times_lookup import get_standard_time, get_standard_section_sum

# 查詢標準完成時間
get_standard_time("Happy Valley", 1200, "第四班")  # → 69.90

# 查詢標準分段總和
get_standard_section_sum("Sha Tin", 1200, "第四班")  # → 69.35
```

### 步速分類
```python
from standard_times_lookup import classify_speed

result = classify_speed(-1.0)   # 比標準快1秒
# → SpeedClassification(value='FAST', label_cn='快步速', ...)

result = classify_speed(1.5)    # 比標準慢1.5秒
# → SpeedClassification(value='SLOW', label_cn='慢步速', ...)
```

### 批量分析
```python
from pace_analysis import RacePaceAnalyzer

analyzer = RacePaceAnalyzer(races_df)
analyzer.set_racecourse("Sha Tin")

# 完成時間分析
finish_df = analyzer.analyze_finishing_times()

# 分段時間分析
section_df = analyzer.analyze_sectional_times()
```

---

## 📊 支持的跑道 & 途程

| 跑道 | 代碼 | 支持途程 |
|------|------|---------|
| 沙田草地 | "Sha Tin" | 1000, 1200, 1400, 1600, 1800, 2000, 2400 |
| 跑馬地草地 | "Happy Valley" | 1000, 1200, 1650, 1800, 2200 |
| 沙田全天候 | "Sha Tin AW" | 1200, 1650, 1800 |

### 中文別名
```python
"沙田" / "沙田草地" / "Sha Tin Turf" → 正規化為 "Sha Tin"
"跑馬地" / "跑馬地草地" / "Happy Valley Turf" → "Happy Valley"
"沙田全天候" / "沙田AW" / "Sha Tin All-Weather" → "Sha Tin AW"
```

---

## ✅ 檢查清單

### 前置準備
- [ ] 下載 `standard_times_lookup.py`
- [ ] 下載 `pace_analysis.py`
- [ ] 放入 `C:\hkjc_app\` 資料夾

### 數據準備
- [ ] CSV 包含 `班次` 欄位
- [ ] CSV 包含 `途程` 欄位（數字）
- [ ] CSV 包含 `頭馬完成時間` 欄位（格式: M:SS.SS）
- [ ] CSV 包含分段時間欄位（如 `起點-800`, `800-400` 等）

### 代碼整合
- [ ] 在 app.py 頂部匯入模組
- [ ] 在側邊欄新增 "賽事步速分析" 選項
- [ ] 新增 elif 分支處理該選項
- [ ] 測試：`python app_gui.py` → 選擇新選項

### 測試運行
- [ ] 爬取賽事數據成功
- [ ] 步速分析頁面正常加載
- [ ] 完成時間表格顯示正常
- [ ] 分段時間表格顯示正常
- [ ] 統計摘要計算正確
- [ ] CSV 下載功能正常

---

## 🔧 常見故障排除

| 問題 | 解決方案 |
|------|---------|
| `ModuleNotFoundError: standard_times_lookup` | 確保 py 文件在正確目錄 & 執行 `cd C:\hkjc_app` |
| 時間轉換報錯 | 檢查格式：應為 `"1:09.90"`，不應為 `"69.90"` 或 `"1:9.9"` |
| "找不到班次" | 班次名稱應與表格相符：`"第四班"` 不是 `"Class 4"` |
| 分段欄位空白 | 確認 CSV 中確實有分段時間欄位（非 NaN） |
| DataFrame 為空 | 執行爬蟲取得數據後再執行分析 |

---

## 📈 輸出表格格式

### 完成時間分析表
```
場次 | 班次   | 途程 | 賽事名稱 | 頭馬完成時間(原始) | 完成時間(秒) | 標準時間 | 差異  | 步速分型
─────┼────────┼─────┼────────┼──────────────────┼─────────────┼────────┼──────┼────────
1   | 第四班 | 1200 | ...    | 1:09.50         | 69.50       | 69.35  | +0.15| 普通步速
2   | 第四班 | 1200 | ...    | 1:08.90         | 68.90       | 69.35  | -0.45| 快步速
```

### 分段時間分析表
```
場次 | 班次   | 途程 | 賽事名稱 | 實際分段總和 | 標準分段總和 | 分段差異 | 步速分型
─────┼────────┼─────┼────────┼─────────────┼─────────────┼────────┼────────
1   | 第四班 | 1200 | ...    | 69.90       | 69.35       | +0.55  | 慢步速
2   | 第四班 | 1200 | ...    | 68.95       | 69.35       | -0.40  | 快步速
```

---

## 💡 使用提示

### Tip 1: 批量分析效率
```python
# 一次分析整日的所有場次
analyzer = RacePaceAnalyzer(entire_day_df)
finish_analysis = analyzer.analyze_finishing_times()
section_analysis = analyzer.analyze_sectional_times()

# 統計摘要
stats = finish_analysis["步速分型"].value_counts()
print(f"快: {stats.get('快步速', 0)}, 普通: {stats.get('普通步速', 0)}, 慢: {stats.get('慢步速', 0)}")
```

### Tip 2: 自訂分類閾值
如需改變步速分類標準（例如 ±1秒而不是 ±0.5秒），編輯 `pace_analysis.py` 中的 `classify_speed()` 函數。

### Tip 3: 導出分析結果
```python
# 導出為 Excel（需 openpyxl）
analysis_df.to_excel("pace_analysis.xlsx", sheet_name="分析結果")

# 導出為 CSV
analysis_df.to_csv("pace_analysis.csv", index=False, encoding="utf-8-sig")
```

---

## 📞 支持

遇到問題或有改進建議？

1. 檢查 `PACE_ANALYSIS_GUIDE.md` 的詳細文檔
2. 查看各模組的 docstrings（Python 說明）
3. 執行模組自測：`python standard_times_lookup.py`

---

**版本**: 1.0  
**最後更新**: 2025-12-01  
**兼容**: Python 3.8+, Streamlit 1.0+, Pandas 1.0+
