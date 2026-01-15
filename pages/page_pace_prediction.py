"""
🖥️ 馬匹跑法預測 UI 頁面
page_pace_prediction.py (410 行)

功能: Streamlit UI 應用，整合 Part 1-2-3 的完整預測系統
使用: Part 1 (跑法預測) + Part 2 (馬群分析) + Part 3 (步速預測)

頁面結構:
  • 側邊欄: 日期/馬場/場次選擇 + 爬取按鈕
  • Part 1: 馬匹跑法預測表格 + 手動修改 + CSV 導出
  • Part 2: 馬群分析 + 柱狀圖 + 特徵說明
  • Part 3: 步速預測 + 距離矩陣 + 信心分數

作者: HKJC AI System
版本: 1.0
日期: 2026-01-08
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from io import BytesIO
import sys
import os

# 導入自定義模塊
try:
    from analyzers.runstyle_predictor import RunstylePredictor
    from analyzers.pace_predictor import PacePredictor
    from analyzers.racecard_analyzer import RaceCardAnalyzer
except ImportError:
    st.error("❌ 無法導入分析模塊。請確保 analyzers 目錄中有必要的文件。")
    st.stop()

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def render_pace_prediction_page():
    """
    主頁面渲染函數
    
    頁面布局:
      1. 標題和說明
      2. 側邊欄: 參數選擇
      3. Part 1: 馬匹跑法預測
      4. Part 2: 馬群分析
      5. Part 3: 步速預測
    """
    
    # 頁面配置
    st.set_page_config(page_title="🏃 跑法預測", layout="wide")
    st.title("🏃 馬匹跑法與步速預測系統")
    st.markdown("---")
    
    # 初始化會話狀態
    if 'predictions' not in st.session_state:
        st.session_state.predictions = []
    if 'racecard_data' not in st.session_state:
        st.session_state.racecard_data = None
    if 'modified_predictions' not in st.session_state:
        st.session_state.modified_predictions = None
    
    # ==================== 側邊欄 ====================
    with st.sidebar:
        st.header("⚙️ 參數設置")
        
        # 日期選擇
        today = datetime.now()
        race_date = st.date_input(
            "📅 選擇賽日",
            value=today,
            min_value=today - timedelta(days=30),
            max_value=today + timedelta(days=7)
        )
        
        # 馬場選擇
        venue = st.selectbox(
            "🏟️ 選擇馬場",
            options=['跑馬地', '沙田'],
            index=0
        )
        
        # 場次選擇
        race_number = st.selectbox(
            "🎯 選擇場次",
            options=list(range(1, 11)),
            index=0
        )
        
        # 爬取按鈕
        if st.button("🔄 爬取排位表 + 往績", key="fetch_button"):
            with st.spinner("🔄 正在爬取數據..."):
                try:
                    # 初始化分析器
                    racecard_analyzer = RaceCardAnalyzer()
                    runstyle_predictor = RunstylePredictor()
                    
                    # 爬取數據
                    racecard_result = racecard_analyzer.fetch_racecard(
                        date=race_date,
                        venue=venue,
                        race_number=race_number
                    )
                    
                    if racecard_result['status'] == 'success':
                        # 保存排位表數據
                        st.session_state.racecard_data = racecard_result['data']
                        
                        # 進行跑法預測
                        predictions = []
                        for horse in racecard_result['data']:
                            try:
                                # 準備預測數據
                                horse_data = {
                                    'horse_number': horse.get('horse_number'),
                                    'horse_name': horse.get('horse_name', ''),
                                    'draw': horse.get('draw', 0),
                                    'distance': horse.get('distance', 1800),
                                    'history': horse.get('history', [])
                                }
                                
                                # 預測跑法
                                prediction = runstyle_predictor.predict_running_style(horse_data)
                                predictions.append(prediction)
                            except Exception as e:
                                logger.error(f"預測錯誤 (馬 {horse.get('horse_number')}): {e}")
                                continue
                        
                        st.session_state.predictions = predictions
                        st.session_state.modified_predictions = None
                        st.success(f"✅ 成功爬取 {venue} 第 {race_number} 場，{len(predictions)} 隻馬")
                    else:
                        st.error(f"❌ 爬取失敗: {racecard_result.get('error', '未知錯誤')}")
                
                except Exception as e:
                    st.error(f"❌ 發生錯誤: {str(e)}")
    
    # ==================== 主要內容 ====================
    if not st.session_state.predictions:
        st.info("👈 請在左側選擇賽事並點擊「爬取」按鈕開始分析")
        return
    
    # Part 1: 馬匹跑法預測
    st.header("📊 Part 1: 馬匹跑法預測")
    st.markdown("根據往績數據預測每隻馬的跑法 (前置/中置/後置)")
    
    # 創建預測表格
    predictions_df = pd.DataFrame(st.session_state.predictions)
    
    # 顯示表格
    col1, col2 = st.columns([4, 1])
    with col1:
        st.dataframe(
            predictions_df[[
                'horse_number', 'horse_name', 'baseline_position',
                'adjusted_position', 'running_style', 'confidence', 'comment'
            ]],
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        # CSV 導出
        if st.button("💾 導出 CSV", key="export_csv"):
            csv_buffer = BytesIO()
            predictions_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_buffer.seek(0)
            
            st.download_button(
                label="下載 CSV",
                data=csv_buffer.getvalue(),
                file_name=f"predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    # 手動修改預測
    with st.expander("✏️ 手動修改預測跑法"):
        st.markdown("選擇馬匹並修改其預測的跑法:")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            horse_to_modify = st.selectbox(
                "選擇馬匹",
                options=[f"{p['horse_number']} - {p['horse_name']}" for p in st.session_state.predictions],
                key="horse_selector"
            )
        
        if horse_to_modify:
            horse_num = int(horse_to_modify.split(' ')[0])
            
            with col2:
                new_style = st.selectbox(
                    "新的跑法",
                    options=['FRONT', 'MID', 'BACK'],
                    key="style_selector"
                )
            
            with col3:
                if st.button("✅ 保存修改", key="save_modification"):
                    # 修改預測
                    modified_predictions = st.session_state.predictions.copy()
                    for pred in modified_predictions:
                        if pred['horse_number'] == horse_num:
                            pred['running_style'] = new_style
                            break
                    
                    st.session_state.modified_predictions = modified_predictions
                    st.success(f"✅ 已修改馬 {horse_num} 的跑法為 {new_style}")
    
    st.markdown("---")
    
    # Part 2: 馬群分析
    st.header("📈 Part 2: 馬群配置分析")
    st.markdown("分析馬群中前置/中置/後置馬的分佈情況")
    
    # 使用修改後的預測 (如果有) 或原始預測
    current_predictions = st.session_state.modified_predictions or st.session_state.predictions
    
    pace_predictor = PacePredictor()
    distribution = pace_predictor.get_runstyle_distribution(current_predictions)
    
    # 分佈統計表
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏃 前置馬", f"{distribution['FRONT']}")
    with col2:
        st.metric("🚴 中置馬", f"{distribution['MID']}")
    with col3:
        st.metric("🐢 後置馬", f"{distribution['BACK']}")
    with col4:
        st.metric("📊 總數", f"{distribution['total']}")
    
    # 柱狀圖
    dist_data = {
        '前置馬': distribution['FRONT'],
        '中置馬': distribution['MID'],
        '後置馬': distribution['BACK']
    }
    
    st.bar_chart(dist_data)
    
    # 馬群特徵說明
    front_pct = distribution['FRONT'] / distribution['total'] * 100 if distribution['total'] > 0 else 0
    mid_pct = distribution['MID'] / distribution['total'] * 100 if distribution['total'] > 0 else 0
    back_pct = distribution['BACK'] / distribution['total'] * 100 if distribution['total'] > 0 else 0
    
    feature_text = ""
    if front_pct > 35:
        feature_text += "🔴 **前置馬佔多** - 競爭激烈，節奏快\n"
    if mid_pct > 45:
        feature_text += "🟡 **中置馬佔多** - 節奏穩定，均衡分佈\n"
    if back_pct > 40:
        feature_text += "🟢 **後置馬佔多** - 節奏偏慢，外檔機會多\n"
    
    if feature_text:
        st.markdown(feature_text)
    
    st.markdown("---")
    
    # Part 3: 步速預測
    st.header("⚡ Part 3: 整場步速預測")
    st.markdown("根據馬群配置預測整場賽事的預期步速")
    
    # 步速預測
    pace_result = pace_predictor.predict_pace_diagnostic(current_predictions)
    
    # 顯示預測結果
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("預測步速", pace_result['pace_name'])
    with col2:
        st.metric("信心度", f"{pace_result['confidence']}%")
    with col3:
        # 信心度指示
        confidence_color = "🟢" if pace_result['confidence'] >= 70 else (
            "🟡" if pace_result['confidence'] >= 40 else "🔴"
        )
        st.metric("", confidence_color)
    
    # 步速特徵說明
    st.markdown(f"**📝 特徵:** {pace_result['characteristics']}")
    st.markdown(f"**💡 建議:** {pace_result['suggestion']}")
    
    # 距離矩陣
    with st.expander("📊 距離矩陣 (詳細分析)"):
        distances = pace_result['distances']
        
        # 創建距離表格
        distance_data = {
            '步速': list(distances.keys()),
            '距離': list(distances.values())
        }
        distance_df = pd.DataFrame(distance_data)
        distance_df['步速'] = distance_df['步速'].map({
            'FAST': '快',
            'MODERATELY_FAST': '偏快',
            'NORMAL': '中等',
            'MODERATELY_SLOW': '偏慢',
            'SLOW': '慢'
        })
        distance_df['距離'] = distance_df['距離'].apply(lambda x: f"{x:.3f}")
        
        st.dataframe(distance_df, use_container_width=True, hide_index=True)
        
        st.markdown("📖 解釋: 距離越小，該步速的可能性越大")
    
    # 五步速參考分佈
    with st.expander("📚 五步速參考分佈"):
        st.markdown("**12 隻馬的期望馬群配置:**")
        
        pace_names = {
            'FAST': '快',
            'MODERATELY_FAST': '偏快',
            'NORMAL': '中等',
            'MODERATELY_SLOW': '偏慢',
            'SLOW': '慢'
        }
        
        for pace_key, pace_name in pace_names.items():
            expected = pace_predictor.get_expected_distribution(pace_key, 12)
            st.markdown(
                f"**{pace_name}**: 前{expected['FRONT']} / 中{expected['MID']} / 後{expected['BACK']}"
            )
    
    st.markdown("---")
    
    # 頁腳
    st.markdown(
        """
        <div style='text-align: center; color: #888; font-size: 12px; margin-top: 30px;'>
            🏇 馬匹跑法與步速預測系統 v1.0 | 最後更新: 2026-01-08
        </div>
        """,
        unsafe_allow_html=True
    )


# 主程序入口
if __name__ == '__main__':
    render_pace_prediction_page()
