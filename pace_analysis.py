# -*- coding: utf-8 -*-
"""
香港賽馬 - 步速分析模組（超級增強版 v2）
HKJC Race Pace Analysis Module - SUPER ENHANCED v2

【超級改進】針對實際 CSV 格式優化
✅ 智能解析 metadata（班次、途程）
✅ 支持多種 metadata 格式
✅ 自動從第一行提取跑馬地、日期等
✅ 完全自動化，無需手動配置
"""

import pandas as pd
import numpy as np
import re
from typing import Optional, Dict, List, Tuple
from standard_times_lookup import (
    get_standard_time,
    get_standard_section_sum,
    classify_speed,
    normalize_racecourse_name,
)


class RacePaceAnalyzer:
    """賽事步速分析器 - 超級增強版 v2"""
    
    def __init__(self, races_df: pd.DataFrame, metadata_dict: Dict = None):
        """初始化分析器"""
        self.races_df = races_df.copy()
        self.metadata_dict = metadata_dict or {}
        self.racecourse = "Sha Tin"
        self.extraction_log = []
        self.global_metadata = {}  # 全局 metadata（來自第一行）
        
    def set_racecourse(self, racecourse: str):
        """設定賽馬場"""
        try:
            self.racecourse = normalize_racecourse_name(racecourse)
        except:
            self.racecourse = "Sha Tin"
    
    def _parse_first_line_metadata(self, first_line: str):
        """從第一行提取全局 metadata（跑馬地、日期等）"""
        # 例如："跑馬地 26/11/2025 第1場完整數據整理報告"
        parts = first_line.split()
        if len(parts) >= 2:
            self.global_metadata['location'] = parts[0]
            self.global_metadata['date'] = parts[1]
    
    def _extract_race_info_from_metadata(self, race_no: int) -> Dict:
        """從 metadata 行提取班次、途程等信息"""
        result = {
            'class': None,
            'distance': None,
            'race_name': None,
        }
        
        if race_no not in self.metadata_dict:
            return result
        
        metadata_lines = self.metadata_dict[race_no]
        
        for line in metadata_lines:
            # 提取班次和途程（例如："第五班 - 1200米"）
            if '班' in line and '米' in line:
                # 提取班次：第X班 → 班次
                match_class = re.search(r'第(\S+?)班', line)
                if match_class:
                    class_name = match_class.group(1)
                    # 轉換為標準格式
                    if '五' in class_name or '5' in class_name:
                        result['class'] = 'Class 5'
                    elif '四' in class_name or '4' in class_name:
                        result['class'] = 'Class 4'
                    elif '三' in class_name or '3' in class_name:
                        result['class'] = 'Class 3'
                    elif '二' in class_name or '2' in class_name:
                        result['class'] = 'Class 2'
                    elif '一' in class_name or '1' in class_name:
                        result['class'] = 'Class 1'
                    else:
                        result['class'] = class_name
                
                # 提取途程
                match_dist = re.search(r'(\d+)\s*米', line)
                if match_dist:
                    result['distance'] = int(match_dist.group(1))
            
            # 提取賽事名稱（例如："賽事名稱：福斯公路橋讓賽"）
            if '賽事名稱' in line:
                parts = line.split('：')
                if len(parts) > 1:
                    result['race_name'] = parts[1].strip()
        
        return result
    
    def _find_column(self, patterns: List[str]) -> Optional[str]:
        """尋找匹配模式的欄位"""
        for pattern in patterns:
            for col in self.races_df.columns:
                if pattern.lower() in col.lower() or col.lower() in pattern.lower():
                    return col
        return None
    
    def _extract_time_value(self, value) -> Optional[float]:
        """提取時間值（秒數）"""
        try:
            if pd.isna(value) or value == "" or value is None:
                return None
            
            if isinstance(value, (int, float)):
                return float(value)
            
            value_str = str(value).strip()
            
            # "分:秒.百分秒" 格式
            if ':' in value_str:
                parts = value_str.split(':')
                if len(parts) == 2:
                    minutes = float(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
            
            # 直接數字（可能帶秒符號）
            value_str = re.sub(r'[^0-9\.]', '', value_str)
            if value_str:
                return float(value_str)
        except:
            pass
        return None
    
    def analyze_finishing_times(self) -> pd.DataFrame:
        """分析完成時間"""
        results = []
        
        # 查找欄位
        race_no_col = self._find_column(['場次', 'race', '馬號'])
        
        for idx, row in self.races_df.iterrows():
            try:
                # 提取場次（或使用索引）
                race_no = idx + 1 if race_no_col is None else row.get(race_no_col, idx + 1)
                
                # 從 metadata 提取班次、途程
                race_info = self._extract_race_info_from_metadata(int(race_no))
                class_name = race_info['class']
                distance = race_info['distance']
                race_name = race_info['race_name'] or ""
                
                if not class_name or not distance:
                    continue
                
                # 查詢標準時間
                std_time = get_standard_time(self.racecourse, int(distance), str(class_name))
                if std_time is None:
                    continue
                
                # 嘗試找完成時間欄位
                finish_time_col = self._find_column(['完成時間', 'finishing', '時間'])
                finish_time_sec = None
                
                if finish_time_col and finish_time_col in row.index:
                    finish_time_sec = self._extract_time_value(row[finish_time_col])
                
                # 如果沒有完成時間，計算為分段時間總和
                if finish_time_sec is None:
                    segment_cols = [c for c in self.races_df.columns 
                                   if c.startswith('第') and c.endswith('時間')]
                    if segment_cols:
                        total = 0
                        for seg_col in segment_cols:
                            seg_val = self._extract_time_value(row[seg_col])
                            if seg_val is not None:
                                total += seg_val
                        if total > 0:
                            finish_time_sec = total
                
                if finish_time_sec is None or finish_time_sec == 0:
                    continue
                
                # 計算差異
                diff_sec = finish_time_sec - std_time
                speed_class = classify_speed(diff_sec)
                
                results.append({
                    "場次": str(race_no),
                    "班次": str(class_name),
                    "途程(米)": int(distance),
                    "賽事名稱": str(race_name),
                    "頭馬完成時間(秒)": round(finish_time_sec, 2),
                    "標準時間(秒)": std_time,
                    "差異(秒)": round(diff_sec, 2),
                    "步速分型": speed_class.label_cn,
                })
            except Exception as e:
                self.extraction_log.append(f"Row {idx} error: {e}")
                continue
        
        return pd.DataFrame(results)
    
    def analyze_sectional_times(self) -> pd.DataFrame:
        """分析分段時間"""
        results = []
        
        race_no_col = self._find_column(['場次', 'race', '馬號'])
        
        for idx, row in self.races_df.iterrows():
            try:
                race_no = idx + 1 if race_no_col is None else row.get(race_no_col, idx + 1)
                
                # 從 metadata 提取
                race_info = self._extract_race_info_from_metadata(int(race_no))
                class_name = race_info['class']
                distance = race_info['distance']
                race_name = race_info['race_name'] or ""
                
                if not class_name or not distance:
                    continue
                
                # 查詢標準分段總和
                std_section_sum = get_standard_section_sum(
                    self.racecourse, int(distance), str(class_name)
                )
                if std_section_sum is None:
                    continue
                
                # 累加所有分段時間
                actual_section_sum = 0
                segment_cols = [c for c in self.races_df.columns 
                               if c.startswith('第') and c.endswith('時間')]
                
                found_segments = False
                for seg_col in segment_cols:
                    seg_val = self._extract_time_value(row[seg_col])
                    if seg_val is not None:
                        actual_section_sum += seg_val
                        found_segments = True
                
                if not found_segments or actual_section_sum == 0:
                    continue
                
                # 計算差異
                diff_sec = actual_section_sum - std_section_sum
                speed_class = classify_speed(diff_sec)
                
                results.append({
                    "場次": str(race_no),
                    "班次": str(class_name),
                    "途程(米)": int(distance),
                    "賽事名稱": str(race_name),
                    "頭馬實際分段總和(秒)": round(actual_section_sum, 2),
                    "標準分段總和(秒)": std_section_sum,
                    "分段差異(秒)": round(diff_sec, 2),
                    "步速分型": speed_class.label_cn,
                })
            except Exception as e:
                self.extraction_log.append(f"Sectional row {idx} error: {e}")
                continue
        
        return pd.DataFrame(results)


def render_pace_analysis_section(
    app_state,
    df: pd.DataFrame,
    metadata_dict: Dict = None,
    racecourse: str = "Sha Tin"
):
    """在 Streamlit 應用中呈現步速分析結果"""
    try:
        analyzer = RacePaceAnalyzer(df, metadata_dict)
        analyzer.set_racecourse(racecourse)
        
        tab1, tab2, tab3 = app_state.tabs([
            "完成時間分析",
            "分段時間分析",
            "統計摘要"
        ])
        
        # ===== 完成時間分析 =====
        with tab1:
            app_state.subheader("頭馬完成時間 vs 標準時間")
            finish_df = analyzer.analyze_finishing_times()
            
            if not finish_df.empty:
                col1, col2, col3, col4 = app_state.columns(4)
                with col1:
                    app_state.metric("總場次", len(finish_df))
                with col2:
                    avg_diff = finish_df["差異(秒)"].mean()
                    app_state.metric("平均差異", f"{avg_diff:+.2f}s")
                with col3:
                    app_state.metric("最快", f"{finish_df['差異(秒)'].min():+.2f}s")
                with col4:
                    app_state.metric("最慢", f"{finish_df['差異(秒)'].max():+.2f}s")
                
                col1, col2, col3 = app_state.columns(3)
                speed_dist = finish_df["步速分型"].value_counts()
                with col1:
                    app_state.metric("快步速", speed_dist.get("快步速", 0))
                with col2:
                    app_state.metric("普通步速", speed_dist.get("普通步速", 0))
                with col3:
                    app_state.metric("慢步速", speed_dist.get("慢步速", 0))
                
                app_state.dataframe(finish_df, use_container_width=True)
                
                csv = finish_df.to_csv(index=False, encoding="utf-8-sig")
                app_state.download_button(
                    label="📥 下載完成時間分析 (CSV)",
                    data=csv,
                    file_name="race_finishing_time_analysis.csv",
                    mime="text/csv"
                )
            else:
                app_state.warning("⚠️ 無可用的完成時間數據\n可能原因：metadata 中缺少班次或途程信息")
        
        # ===== 分段時間分析 =====
        with tab2:
            app_state.subheader("頭馬分段時間 vs 標準分段")
            section_df = analyzer.analyze_sectional_times()
            
            if not section_df.empty:
                col1, col2, col3, col4 = app_state.columns(4)
                with col1:
                    app_state.metric("總場次", len(section_df))
                with col2:
                    avg_diff = section_df["分段差異(秒)"].mean()
                    app_state.metric("平均差異", f"{avg_diff:+.2f}s")
                with col3:
                    app_state.metric("最快", f"{section_df['分段差異(秒)'].min():+.2f}s")
                with col4:
                    app_state.metric("最慢", f"{section_df['分段差異(秒)'].max():+.2f}s")
                
                col1, col2, col3 = app_state.columns(3)
                speed_dist = section_df["步速分型"].value_counts()
                with col1:
                    app_state.metric("快步速", speed_dist.get("快步速", 0))
                with col2:
                    app_state.metric("普通步速", speed_dist.get("普通步速", 0))
                with col3:
                    app_state.metric("慢步速", speed_dist.get("慢步速", 0))
                
                app_state.dataframe(section_df, use_container_width=True)
                
                csv = section_df.to_csv(index=False, encoding="utf-8-sig")
                app_state.download_button(
                    label="📥 下載分段時間分析 (CSV)",
                    data=csv,
                    file_name="race_sectional_time_analysis.csv",
                    mime="text/csv"
                )
            else:
                app_state.warning("⚠️ 無可用的分段時間數據\n可能原因：缺少分段時間欄位")
        
        # ===== 統計摘要 =====
        with tab3:
            app_state.subheader("分析統計摘要")
            
            finish_df = analyzer.analyze_finishing_times()
            section_df = analyzer.analyze_sectional_times()
            
            if not finish_df.empty or not section_df.empty:
                col1, col2 = app_state.columns(2)
                
                with col1:
                    if not finish_df.empty:
                        app_state.write("#### ✅ 完成時間分析")
                        stats = {
                            "場次": len(finish_df),
                            "平均差異": f"{finish_df['差異(秒)'].mean():+.2f}s",
                            "最快": f"{finish_df['差異(秒)'].min():+.2f}s",
                            "最慢": f"{finish_df['差異(秒)'].max():+.2f}s",
                        }
                        for key, val in stats.items():
                            app_state.write(f"• **{key}**: {val}")
                    else:
                        app_state.info("完成時間數據不可用")
                
                with col2:
                    if not section_df.empty:
                        app_state.write("#### ✅ 分段時間分析")
                        stats = {
                            "場次": len(section_df),
                            "平均差異": f"{section_df['分段差異(秒)'].mean():+.2f}s",
                            "最快": f"{section_df['分段差異(秒)'].min():+.2f}s",
                            "最慢": f"{section_df['分段差異(秒)'].max():+.2f}s",
                        }
                        for key, val in stats.items():
                            app_state.write(f"• **{key}**: {val}")
                    else:
                        app_state.info("分段時間數據不可用")
            else:
                app_state.error("❌ 無可用數據，無法進行分析")
    
    except Exception as e:
        app_state.error(f"❌ 分析錯誤：{e}")
        import traceback
        app_state.error(traceback.format_exc())
