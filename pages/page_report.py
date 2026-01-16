
# -*- coding: utf-8 -*-
"""
完整分析報告頁面
Complete Analysis Report Page
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
import os
from analyzers.report_analyzer import RaceSegmentAnalyzer, _classify_finishing_pace
from hkjc_sectional import load_race_from_csv



def _classify_pace_type_v2(diff_sec: float, avg_diff: float = None) -> str:
    """步速類型分類（新版5級分類）"""
    if avg_diff is not None:
        threshold_very_fast = avg_diff - 0.5
        threshold_fast = avg_diff - 0.3
        threshold_slow = avg_diff + 0.3
        threshold_very_slow = avg_diff + 0.5

        if diff_sec <= threshold_very_fast:
            return "🟢 快"
        elif diff_sec <= threshold_fast:
            return "🟢 偏快"
        elif diff_sec < threshold_slow:
            return "🟡 中等"
        elif diff_sec < threshold_very_slow:
            return "🔴 偏慢"
        else:
            return "🔴 慢"
    else:
        if diff_sec <= -0.5:
            return "快步速"
        elif diff_sec < 0.5:
            return "普通步速"
        else:
            return "慢步速"

def render_report_page(standard_times_data):
    """
    渲染完整分析報告頁面
    
    參數:
        standard_times_data: 標準時間數據字典
    """
    
    st.sidebar.header("📋 完整分析報告選項")
    report_race_date = st.sidebar.text_input("賽事日期 (dd/mm/yyyy)", "26/11/2025", key="report_date")
    report_num_races = st.sidebar.slider("要分析的場次", min_value=1, max_value=13, value=10, key="report_races")

    if st.sidebar.button("🔍 生成報告", key="report_button"):
        render_complete_analysis_section(report_race_date, report_num_races, standard_times_data)


def render_complete_analysis_section(race_date: str, num_races: int, standard_times_data):
    """
    完整分析報告渲染函數 - 修復版本
    
    參數：
    - race_date: 格式 'dd/mm/yyyy'
    - num_races: 要分析的場次數
    - standard_times_data: 標準時間數據字典
    """
    try:
        st.header("📊 完整分析報告")

        # 日期轉換
        date_parts = race_date.split('/')
        if len(date_parts) == 3:
            day, month, year = date_parts
            date_key = f"{year}{month}{day}"
        else:
            st.error("❌ 日期格式錯誤")
            return

        # 尋找 CSV 檔案
        current_dir = os.getcwd()
        csv_files = []
        for f in os.listdir(current_dir):
            if re.match(r'sectional_\d{8}_\d+\.csv', f):
                if date_key in f:
                    csv_files.append(f)

        if not csv_files:
            st.error(f"❌ 找不到 {race_date} 的 CSV 檔案")
            return

        # 修復 2: 按場次編號數字順序排序（不是字典順序）
        def extract_race_number(filename):
            match = re.search(r'_(\d+)\.csv$', filename)
            return int(match.group(1)) if match else 0

        csv_files = sorted(csv_files, key=extract_race_number)

        st.info(f"📄 找到 {len(csv_files)} 個檔案，分析前 {min(num_races, len(csv_files))} 場")

        # 分析所有場次
        all_results = []
        for csv_file in csv_files[:num_races]:
            csv_file_path = os.path.join(current_dir, csv_file)
            try:
                with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
                    csv_content = f.read()

                analyzer = RaceSegmentAnalyzer(csv_content)
                result = analyzer.analyze(standard_times_data)
                result['csv_file'] = csv_file

                # ✨ 改進 1: 提取頭馬走位 (修復版 - 缺失場次容錯)
                try:
                    race_no = extract_race_number(csv_file)
                    race_data = load_race_from_csv(race_date, race_no)
                    df = race_data['df']
                    first_place = df[(df['名次'] == '1') | (df['名次'] == 1)]

                    # 檢查欄位存在性和值有效性
                    if len(first_place) > 0 and '沿途走位' in df.columns:
                        val = first_place['沿途走位'].values[0]
                        # 檢查值是否為 NaN 或空字符串
                        horse_position = str(val).strip() if pd.notna(val) and str(val).strip() else '-'
                    else:
                        horse_position = '-'

                    result['horse_position'] = horse_position
                except:
                    result['horse_position'] = '-'

                all_results.append(result)

            except Exception as e:
                st.warning(f"⚠️ 檔案 {csv_file} 讀取失敗：{e}")
                continue

        if not all_results:
            st.error("❌ 無法分析任何場次")
            return

        st.success(f"✅ 成功讀取 {len(all_results)} 場賽事")

        # 計算平均分段差異（新版步速分類需要）
        valid_segment_diffs = [r['segment_sum_diff'] for r in all_results 
                               if r['segment_sum_diff'] is not None]
        avg_segment_diff = sum(valid_segment_diffs) / len(valid_segment_diffs) if valid_segment_diffs else None

        # 建立標籤頁
        tab1, tab2, tab3 = st.tabs(["一、完成時間分析", "二、步速分析", "三、詳細數據"])

        with tab1:
            st.header("一、完成時間與標準時間比較")
            finish_time_data = []

            for result in sorted(all_results, key=lambda x: extract_race_number(x.get('csv_file', ''))):
                if result['actual_finish_time'] and result['standard_time']:
                    m_actual = int(result['actual_finish_time'] // 60)
                    s_actual = result['actual_finish_time'] % 60
                    m_standard = int(result['standard_time'] // 60)
                    s_standard = result['standard_time'] % 60

                    finish_time_data.append({
                        '場次': extract_race_number(result.get('csv_file', '')),
                        '跑道': result['metadata'].get('track_type', '-'),
                        '途程(米)': result['metadata'].get('distance', '-'),
                        '班次': result['metadata'].get('class', '-'),
                        '標準時間': f"{m_standard}:{s_standard:05.2f}",
                        '實際完成時間': f"{m_actual}:{s_actual:05.2f}",
                        '差異(秒)': f"{result['finishing_time_diff']:+.2f}",
                        '差異幅度': _classify_finishing_pace(result['finishing_time_diff']),
                        '頭馬走位': result.get('horse_position', '-'),
                    })

            if finish_time_data:
                df_finish = pd.DataFrame(finish_time_data)
                st.dataframe(df_finish, use_container_width=True, height=400)
            else:
                st.warning("⚠️ 無完成時間數據")

        with tab2:
            st.header("二、步速分析")
            st.markdown("""
### 分段步速判定規則（修復版）

- **短途（≤1200米）**：首兩段總和
- **中距離（1400-1650米）**：首三段總和
- **長途（≥1800米）**：首四段總和
            """)

            pace_data = []
            for result in sorted(all_results, key=lambda x: extract_race_number(x.get('csv_file', ''))):
                if result['actual_segment_sum'] and result['standard_segment_sum']:
                    pace_data.append({
                        '場次': extract_race_number(result.get('csv_file', '')),
                        '跑道': result['metadata'].get('track_type', '-'),
                        '途程(米)': result['metadata'].get('distance', '-'),
                        '班次': result['metadata'].get('class', '-'),
                        '實際分段總和': f"{result['actual_segment_sum']:.2f}秒",
                        '標準分段總和': f"{result['standard_segment_sum']:.2f}秒",
                        '差異(秒)': f"{result['segment_sum_diff']:+.2f}",
                        '步速類型': _classify_pace_type_v2(result['segment_sum_diff'], avg_segment_diff),
                    })

            if pace_data:
                df_pace = pd.DataFrame(pace_data)
                st.dataframe(df_pace, use_container_width=True, height=400)
            else:
                st.warning("⚠️ 無分段時間數據")

        with tab3:
            st.header("三、詳細數據")

            # ✨ 改進 2: 平均差異統計 Metric 卡片
            # 計算平均完成時間差異
            valid_times = [r['finishing_time_diff'] for r in all_results
                           if r['finishing_time_diff'] is not None]
            avg_time_diff = np.mean(valid_times) if valid_times else 0

            # 計算平均分段差異
            valid_segments = [r['segment_sum_diff'] for r in all_results
                              if r['segment_sum_diff'] is not None]
            avg_segment_diff = np.mean(valid_segments) if valid_segments else 0

            # 顯示 Metric 卡片
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label="平均完成時間差異",
                    value=f"{avg_time_diff:+.2f}",
                    delta=f"{avg_time_diff:+.2f} sec"
                )
            with col2:
                st.metric(
                    label="平均分段差異",
                    value=f"{avg_segment_diff:+.2f}",
                    delta=f"{avg_segment_diff:+.2f} sec"
                )

            st.divider()

            summary_data = []
            for result in sorted(all_results, key=lambda x: extract_race_number(x.get('csv_file', ''))):
                summary_data.append({
                    '場次': extract_race_number(result.get('csv_file', '')),
                    '跑道': result['metadata'].get('track_type', '-'),
                    '途程': result['metadata'].get('distance', '-'),
                    '班次': result['metadata'].get('class', '-'),
                    '完成時間': f"{int(result['actual_finish_time']//60)}:{result['actual_finish_time']%60:05.2f}" if result['actual_finish_time'] else '-',
                    '標準時間': f"{int(result['standard_time']//60)}:{result['standard_time']%60:05.2f}" if result['standard_time'] else '-',
                    '差異(秒)': f"{result['finishing_time_diff']:+.2f}" if result['finishing_time_diff'] is not None else '-',
                    '實際分段總和': f"{result['actual_segment_sum']:.2f}" if result['actual_segment_sum'] else '-',
                    '標準分段總和': f"{result['standard_segment_sum']:.2f}" if result['standard_segment_sum'] else '-',
                    '分段差異': f"{result['segment_sum_diff']:+.2f}" if result['segment_sum_diff'] is not None else '-',
                })

            df_download = pd.DataFrame(summary_data)
            csv_data = df_download.to_csv(index=False, encoding='utf-8-sig')

            date_key = date_parts[2] + date_parts[1] + date_parts[0]
            st.download_button(
                label="📥 下載全日匯總 (CSV)",
                data=csv_data,
                file_name=f"day_summary_{date_key}.csv",
                mime="text/csv"
            )

            st.dataframe(df_download, use_container_width=True, height=400)

        st.success("✅ 報告生成完成！")

    except Exception as e:
        st.error(f"❌ 分析錯誤：{e}")
        import traceback
        with st.expander("詳細錯誤堆棧"):
            st.code(traceback.format_exc())
