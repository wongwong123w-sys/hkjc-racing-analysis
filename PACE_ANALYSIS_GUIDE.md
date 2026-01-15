# 香港賽馬步速分析模組 - 整合指南

## 📋 概述

本指南說明如何在 `app.py` 中集成「完成時間與標準時間比較」和「步速分析」功能。

---

## 🗂️ 新增檔案

在 `C:\hkjc_app` 目錄中新增以下 3 個檔案：

1. **`standard_times_lookup.py`** - 標準時間查詢模組
   - 包含香港賽馬會官方的標準時間資料庫
   - 提供時間轉換、查詢、分類等工具函數

2. **`pace_analysis.py`** - 步速分析模組
   - 建立 `RacePaceAnalyzer` 類
   - 分析完成時間與分段時間
   - 提供 Streamlit 集成函數

3. **`INTEGRATION_GUIDE.md`** - 本文件

---

## 🚀 快速開始

### 步驟 1：在 app.py 頂部匯入

```python
import streamlit as st
import pandas as pd
from hkjc_sectional import load_day_races
from pace_analysis import render_pace_analysis_section
```

### 步驟 2：新增側邊欄選項

```python
query_mode = st.sidebar.radio(
    "選擇查詢模式",
    [
        "📊 全日分析",
        "🏇 單場詳細",
        "🏆 賽事步速分析"  # ← 新增此選項
    ]
)
```

### 步驟 3：新增分析邏輯

```python
if query_mode == "🏆 賽事步速分析":
    st.subheader("🏆 賽事步速分析")
    
    # 加載資料
    try:
        df_all, num_races, metadata_dict = load_day_races(race_date, max_race_no)
        
        if not df_all.empty:
            # 呼叫步速分析函數
            render_pace_analysis_section(st, df_all, racecourse="Sha Tin")
        else:
            st.warning("無可用資料")
    
    except Exception as e:
        st.error(f"分析失敗: {e}")
```

---

## 📊 數據要求

確保你的 DataFrame 包含以下欄位：

### 必需欄位：
- `班次` (class): 例如 "第四班"、"分級賽"
- `途程` (distance_m): 例如 1200, 1400, 1800 (米)

### 完成時間分析需要：
- `頭馬完成時間` (finishing_time): 格式 "1:09.15" 或 "M:SS.SS"

### 分段時間分析需要：
- `起點-800` (起點-800段): 分段時間 (秒)
- `800-400` (800-400段): 分段時間 (秒)
- `400-終點` (終點段): 分段時間 (秒)
- 或其他分段欄位，根據途程決定

### 可選欄位（用於顯示）：
- `場次` (race_number): 賽事場次
- `賽事名稱` (race_name): 賽事名稱
- `賽事日期` (race_date): 日期

---

## 🔍 核心函數說明

### 1. 標準時間查詢 (`standard_times_lookup.py`)

#### 基本查詢：

```python
from standard_times_lookup import get_standard_time

# 查詢跑馬地第四班1200米的標準時間
std_time = get_standard_time(
    racecourse="Happy Valley",  # 或中文 "跑馬地"
    distance_m=1200,
    class_name="第四班"
)
# 回傳：69.90 (秒)
```

#### 分段查詢：

```python
from standard_times_lookup import get_standard_section_sum

# 查詢標準分段總和
std_section = get_standard_section_sum(
    racecourse="Happy Valley",
    distance_m=1200,
    class_name="第四班"
)
# 回傳：69.90 秒 (23.65 + 22.70 + 23.55)
```

#### 時間轉換：

```python
from standard_times_lookup import time_str_to_seconds, seconds_to_time_str

# 字串轉秒
seconds = time_str_to_seconds("1:09.90")  # → 69.90

# 秒轉字串
time_str = seconds_to_time_str(69.90)  # → "1:09.90"
```

#### 步速分類：

```python
from standard_times_lookup import classify_speed

# 根據差異判定步速
classification = classify_speed(-1.0)  # 比標準快1秒
# 回傳：SpeedClassification(value='FAST', label_cn='快步速', ...)

classification = classify_speed(1.5)   # 比標準慢1.5秒
# 回傳：SpeedClassification(value='SLOW', label_cn='慢步速', ...)
```

### 2. 批量分析 (`pace_analysis.py`)

#### 初始化分析器：

```python
from pace_analysis import RacePaceAnalyzer

analyzer = RacePaceAnalyzer(races_df)
analyzer.set_racecourse("Sha Tin")  # 或 "Happy Valley"、"Sha Tin AW"
```

#### 分析完成時間：

```python
# 生成完成時間分析表
finish_analysis_df = analyzer.analyze_finishing_times()

# 結果包含欄位：
# - 場次、班次、途程、賽事名稱
# - 頭馬完成時間(原始)、頭馬完成時間(秒)
# - 標準時間(秒)、差異(秒)、步速分型
```

#### 分析分段時間：

```python
# 生成分段時間分析表
section_analysis_df = analyzer.analyze_sectional_times()

# 結果包含欄位：
# - 場次、班次、途程、賽事名稱
# - 頭馬實際分段總和(秒)、標準分段總和(秒)
# - 分段差異(秒)、步速分型
```

### 3. 格式化與統計 (`pace_analysis.py`)

```python
from pace_analysis import format_analysis_for_display, create_summary_chart_data

# 格式化用於顯示
display_df, stats = format_analysis_for_display(finish_analysis_df, "finishing")

# 統計摘要包含：
# {
#     "指標": "完成時間",
#     "總場次": 10,
#     "平均差異(秒)": 0.35,
#     "最快(秒)": -1.20,
#     "最慢(秒)": 2.15,
#     "快步速": 2,
#     "普通步速": 5,
#     "慢步速": 3
# }

# 生成圖表資料
chart_data = create_summary_chart_data(finish_analysis_df)
```

---

## 📈 Streamlit 集成完整示例

```python
import streamlit as st
import pandas as pd
from hkjc_sectional import load_day_races
from pace_analysis import render_pace_analysis_section

st.set_page_config(page_title="HKJC 賽馬分析", layout="wide")
st.title("🐴 HKJC 賽馬分析工具")

# 側邊欄
race_date = st.sidebar.text_input("賽事日期 (dd/mm/yyyy)", "30/11/2025")
max_race_no = st.sidebar.number_input("場次數量", min_value=1, max_value=12, value=9)

query_mode = st.sidebar.radio(
    "選擇查詢模式",
    [
        "📊 全日分析",
        "🏇 單場詳細",
        "🏆 賽事步速分析"
    ]
)

# ===== 新增步速分析頁面 =====
if query_mode == "🏆 賽事步速分析":
    st.subheader("🏆 賽事步速分析")
    
    if st.sidebar.button("取得分析數據"):
        try:
            with st.spinner("正在分析..."):
                df_all, num_races, metadata_dict = load_day_races(race_date, max_race_no)
                
                if not df_all.empty:
                    render_pace_analysis_section(st, df_all, racecourse="Sha Tin")
                    
                    # 提供下載整個結果
                    if st.button("📥 下載完整分析結果"):
                        csv = df_all.to_csv(index=False)
                        st.download_button(
                            "下載 CSV",
                            csv,
                            file_name=f"pace_analysis_{race_date.replace('/', '')}.csv"
                        )
                else:
                    st.warning("找不到賽事資料")
        
        except Exception as e:
            st.error(f"分析失敗: {e}")

# ===== 其他既有頁面保持不變 =====
elif query_mode == "📊 全日分析":
    # ... 既有的全日分析邏輯
    pass

elif query_mode == "🏇 單場詳細":
    # ... 既有的單場詳細邏輯
    pass
```

---

## 🎯 支持的跑道與途程

### 支持的跑道：

1. **沙田草地** (Sha Tin / 沙田)
   - 途程：1000, 1200, 1400, 1600, 1800, 2000, 2400 米

2. **跑馬地草地** (Happy Valley / 跑馬地)
   - 途程：1000, 1200, 1650, 1800, 2200 米

3. **沙田全天候** (Sha Tin AW / 沙田全天候)
   - 途程：1200, 1650, 1800 米

### 支持的班次：

- 分級賽 / 第一班 / 第二班 / 第三班 / 第四班 / 第五班
- 新馬賽 (限部分途程)

---

## 🔧 自訂與擴展

### 新增自訂標準時間：

```python
from standard_times_lookup import STANDARD_TIMES_DB

# 新增沙田1050米的標準時間
STANDARD_TIMES_DB["Sha Tin"][1050] = {
    "第四班": {
        "std_time": 62.50,
        "segments": {
            "起點-800": 15.50,
            "800-400": 21.00,
            "400-終點": 26.00
        }
    }
}
```

### 新增自訂分類規則：

修改 `pace_analysis.py` 中的 `classify_speed` 函數來改變分類閾值。

---

## ⚠️ 常見問題

### Q1: 報錯 "找不到 app.py 檔案"

**A:** 確保：
- `standard_times_lookup.py` 和 `pace_analysis.py` 在 `C:\hkjc_app` 目錄
- 已執行 `pip install pandas streamlit`

### Q2: 分析結果為空

**A:** 檢查：
- DataFrame 中是否有 "班次" 和 "途程" 欄位
- CSV 中的班次是否與標準表相符（例如 "第四班" vs "Class 4"）

### Q3: 時間轉換錯誤

**A:** 確保時間格式正確：
- 正確：`"1:09.90"`, `"0:56.40"`, `"2:01.70"`
- 錯誤：`"1:9.9"`, `"69.90"`

### Q4: 分段時間欄位找不到

**A:** 確認 CSV 中的分段欄位名稱：
- 1200m 應該有：`起點-800`, `800-400`, `400-終點`
- 1400m 應該有：`起點-1200`, `1200-800`, `800-400`, `400-終點`

---

## 📚 相關資源

- 香港賽馬會官網：https://racing.hkjc.com
- 標準時間表：`standard_times_lookup.py` 中的 `STANDARD_TIMES_DB`
- 完整 API 文件：見各模組的 docstrings

---

## ✅ 檢查清單

在使用前，確認：

- [ ] 已下載 `standard_times_lookup.py`
- [ ] 已下載 `pace_analysis.py`
- [ ] 已在 `app.py` 中匯入模組
- [ ] 已新增 "賽事步速分析" 選項到側邊欄
- [ ] DataFrame 包含必需欄位（班次、途程、時間等）
- [ ] 時間格式正確 ("M:SS.SS")
- [ ] 班次名稱與標準表相符

---

## 🎉 完成！

現在你可以：
1. 執行 `python C:\hkjc_app\app_gui.py`
2. 在 Streamlit 選擇 "🏆 賽事步速分析"
3. 查看完成時間與分段時間的詳細分析！

---

**最後更新**: 2025-12-01  
**版本**: 1.0
