
# -*- coding: utf-8 -*-
"""
🏃 跑法預測頁面 (v5.7 - 完整版)

page_pace_prediction_integrated.py

版本: v5.7
- ✅ 同步表刷新：編輯後自動更新 Part 2 & Part 3
- ✅ 完善評論：詳細檔位分析
- ✅ 5 種配速：快/偏快/中等/偏慢/慢
- ✅ 動態期望分佈顯示
- ✅ 實際 vs 期望對比

日期: 2026-01-10
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from io import BytesIO
import sys
import os
import io

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

RunstylePredictor = None
PacePredictor = None


def load_analyzers():
    """動態載入分析器模組"""
    global RunstylePredictor, PacePredictor
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    sys.path.insert(0, current_dir)
    sys.path.insert(0, os.path.join(parent_dir, 'analyzers'))
    
    try:
        from analyzers.runstyle_predictor import RunstylePredictor as RP
        from analyzers.pace_predictor import PacePredictor as PP
        RunstylePredictor = RP
        PacePredictor = PP
        logger.info("✅ 已載入分析器 (v4.1 + v3.0)")
        return True
    except ImportError as e1:
        logger.debug(f"方式 1 失敗: {str(e1)}")
        
        try:
            from runstyle_predictor import RunstylePredictor as RP
            from pace_predictor import PacePredictor as PP
            RunstylePredictor = RP
            PacePredictor = PP
            logger.info("✅ 已直接匯入分析器")
            return True
        except ImportError as e2:
            logger.debug(f"方式 2 失敗: {str(e2)}")
            return False


def safe_int_convert(value, default=0):
    """安全的整數轉換"""
    if value is None:
        return default
    
    if isinstance(value, str):
        value = value.strip()
        if value == '':
            return default
    
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def render_pace_prediction_analysis(race_horses_data, total_runners=None):
    """渲染跑法預測分析頁面 (v5.7)"""
    
    current_race_id = st.session_state.get('race_id')
    
    if race_horses_data is not None and len(race_horses_data) > 0:
        st.session_state.pace_race_horses_data = race_horses_data
        st.session_state.pace_race_id = current_race_id
        if total_runners is not None:
            st.session_state.pace_total_runners = total_runners
        logger.info(f"✅ 已保存馬匹數據 (場次: {current_race_id})")
    
    if race_horses_data is None or len(race_horses_data) == 0:
        stored_race_id = st.session_state.get('pace_race_id')
        
        if stored_race_id == current_race_id and 'pace_race_horses_data' in st.session_state:
            race_horses_data = st.session_state.pace_race_horses_data
            logger.info(f"✅ 從 session_state 恢復")
        else:
            st.warning("⚠️ 無馬匹數據。請先爬取。")
            st.markdown("### 📋 使用步驟")
            st.markdown("1. 切換到 **Tab 4: 排位表分析**")
            st.markdown("2. 選擇日期、馬場、場次")
            st.markdown("3. 點擊「🔄 爬取排位表 + 往績」")
            return
    
    if total_runners is None:
        total_runners = st.session_state.get('pace_total_runners', len(race_horses_data))
    
    if 'pace_predictions' not in st.session_state:
        st.session_state.pace_predictions = []
    
    if 'pace_predictions_edited' not in st.session_state:
        st.session_state.pace_predictions_edited = None
    
    with st.expander("📋 數據驗證"):
        st.write(f"**場次**: {current_race_id}")
        st.write(f"**馬匹數**: {len(race_horses_data)}")
        
        if not load_analyzers():
            st.error("❌ 無法載入分析器")
            return
        else:
            st.success("✅ 分析器已載入")
    
    if race_horses_data and len(race_horses_data) > 0:
        with st.expander("🐴 首匹馬資訊"):
            first = race_horses_data[0]
            st.write(f"- 馬名: {first.get('horse_name', 'N/A')}")
            st.write(f"- 檔位: {first.get('barrier', 'N/A')}")
            hist = first.get('racing_history')
            st.write(f"- 往績數: {len(hist) if hist else 0}")
            if hist and len(hist) > 0:
                st.write(f"- going樣本: `{hist[0].get('going', '')}`")
    
    st.header("📊 Part 1: 跑法預測")
    st.info("ℹ️ 版本: RunstylePredictor v4.1 (Enhanced)")
    
    # 重置按鈕
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 重新預測", key="reset_pred"):
            st.session_state.pace_predictions = []
            st.session_state.pace_predictions_edited = None
            st.success("✅ 已清除，即將重新預測")
            st.rerun()
    
    if not st.session_state.pace_predictions:
        if not race_horses_data:
            st.error("❌ 無數據")
            return
        
        st.info("🔄 計算中...")
        
        # 創建日誌捕獲器
        log_capture = io.StringIO()
        log_handler = logging.StreamHandler(log_capture)
        log_handler.setLevel(logging.DEBUG)
        log_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        
        predictor_logger = logging.getLogger('analyzers.runstyle_predictor')
        if not predictor_logger.handlers:
            predictor_logger = logging.getLogger('runstyle_predictor')
        if not predictor_logger.handlers:
            predictor_logger = logging.getLogger('__main__')
        
        predictor_logger.addHandler(log_handler)
        predictor_logger.setLevel(logging.DEBUG)
        
        with st.spinner("分析中..."):
            try:
                total_runners = max(6, min(int(total_runners), 14))
                st.info(f"確認馬數: {total_runners}")
                
                if not RunstylePredictor:
                    st.error("❌ 分析器未載入")
                    return
                
                predictor = RunstylePredictor()
                predictions = []
                errors = []
                
                total_processed = 0
                with_history = 0
                with_valid_going = 0
                
                for idx, horse in enumerate(race_horses_data):
                    try:
                        total_processed += 1
                        
                        horse_num = safe_int_convert(horse.get('position') or horse.get('horse_number'), idx+1)
                        horse_name = horse.get('horse_name', '未知')
                        draw = safe_int_convert(horse.get('barrier') or horse.get('draw'), 0)
                        history = horse.get('racing_history') or horse.get('history') or []
                        
                        is_new = not history
                        
                        if is_new:
                            rating = safe_int_convert(horse.get('rating', 70), 70)
                            pred = predictor.predict_new_horse_running_style({
                                'horse_number': horse_num,
                                'horse_name': horse_name,
                                'draw': draw,
                                'rating': rating,
                                'history': []
                            }, total_runners)
                            if pred:
                                pred['is_new_horse'] = True
                        else:
                            with_history += 1
                            converted = []
                            valid_going = 0
                            
                            for rec in history:
                                try:
                                    dist = safe_int_convert(rec.get('distance'), 1800)
                                    going = str(rec.get('going', ''))
                                    
                                    if going and going != '' and going != '-':
                                        valid_going += 1
                                    
                                    converted.append({
                                        'distance': dist,
                                        'track': str(rec.get('track', '')),
                                        'venue': str(rec.get('venue', '')),
                                        'placing': safe_int_convert(rec.get('position'), 0),
                                        'barrier': safe_int_convert(rec.get('barrier'), 0),
                                        'running_path': going,
                                        'race_class': str(rec.get('race_class', '')),
                                        'date': str(rec.get('date', ''))
                                    })
                                except:
                                    continue
                            
                            if valid_going > 0:
                                with_valid_going += 1
                            
                            if not converted:
                                errors.append(f"馬{horse_num}: 無有效往績")
                                continue
                            
                            pred = predictor.predict_running_style({
                                'horse_number': horse_num,
                                'horse_name': horse_name,
                                'draw': draw,
                                'distance': safe_int_convert(converted[0].get('distance'), 1800),
                                'history': converted
                            }, total_runners)
                            if pred:
                                pred['is_new_horse'] = False
                        
                        if pred:
                            predictions.append(pred)
                        else:
                            errors.append(f"馬{horse_num}: 預測失敗")
                    
                    except Exception as e:
                        errors.append(f"馬{idx+1}: {str(e)}")
                        continue
                
                st.session_state.pace_predictions = predictions
                
                # 顯示日誌
                log_content = log_capture.getvalue()
                
                with st.expander("🔍 診斷 + 📋 詳細日誌", expanded=(len(predictions) == 0)):
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("處理", total_processed)
                    col2.metric("有往績", with_history)
                    col3.metric("有效going", with_valid_going)
                    col4.metric("成功", len(predictions))
                    
                    if errors:
                        st.error("**錯誤列表**:")
                        for e in errors[:10]:
                            st.text(f"  {e}")
                    
                    st.markdown("---")
                    st.markdown("### 📋 預測過程日誌")
                    if log_content:
                        st.text_area(
                            "日誌輸出（滾動查看）", 
                            log_content, 
                            height=400,
                            key="prediction_logs"
                        )
                    else:
                        st.info("ℹ️ 無日誌輸出")
                
                predictor_logger.removeHandler(log_handler)
            
            except Exception as e:
                st.error(f"❌ 錯誤: {str(e)}")
                
                log_content = log_capture.getvalue()
                if log_content:
                    with st.expander("📋 錯誤日誌", expanded=True):
                        st.text_area("日誌", log_content, height=300)
                
                import traceback
                st.error(traceback.format_exc())
                
                predictor_logger.removeHandler(log_handler)
                return
    
    st.write("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("✅ 成功", len(st.session_state.pace_predictions))
    col2.metric("❌ 失敗", len(race_horses_data) - len(st.session_state.pace_predictions))
    col3.metric("📊 總數", len(race_horses_data))
    
    # ========================================
    # ✅ Part 1: 預測結果表格（可編輯）
    # ========================================
    
    if st.session_state.pace_predictions:
        st.success(f"✅ 已生成 {len(st.session_state.pace_predictions)} 個預測")
        
        st.subheader("📈 預測結果")
        
        df = pd.DataFrame(st.session_state.pace_predictions)
        
        cols = ['horse_number', 'horse_name', 'baseline_position', 'adjusted_position', 
                'running_style', 'confidence', 'comment']
        display_cols = [c for c in cols if c in df.columns]
        
        if display_cols:
            edited_df = st.data_editor(
                df[display_cols],
                column_config={
                    "horse_number": "馬號",
                    "horse_name": "馬名",
                    "baseline_position": st.column_config.NumberColumn(
                        "基準位",
                        format="%.2f"
                    ),
                    "adjusted_position": st.column_config.NumberColumn(
                        "調整位",
                        format="%.2f"
                    ),
                    "running_style": st.column_config.SelectboxColumn(
                        "跑法", 
                        options=["FRONT", "MID", "BACK"],
                        required=True
                    ),
                    "confidence": st.column_config.NumberColumn(
                        "信心度", 
                        min_value=0, 
                        max_value=100,
                        format="%.1f%%"
                    ),
                    "comment": st.column_config.TextColumn(
                        "評論",
                        width="large"
                    )
                },
                hide_index=True,
                num_rows="fixed",
                key=f"editor_{current_race_id}"
            )
            
            # ========================================
            # ✅ 關鍵：同步編輯結果回 session_state
            # ========================================
            
            # 檢查是否有編輯
            original_df = df[display_cols].copy()
            
            # 比較並同步
            if not edited_df.equals(original_df):
                st.info("🔄 檢測到編輯，正在同步數據...")
                
                # 逐行更新
                for idx in range(len(edited_df)):
                    for col in display_cols:
                        if col in edited_df.columns:
                            st.session_state.pace_predictions[idx][col] = edited_df.iloc[idx][col]
                
                st.success("✅ 數據已同步！Part 2 和 Part 3 將使用最新數據")
                
                # 重新渲染（可選）
                # st.rerun()  # 如果需要立即刷新下方圖表，取消註釋這行
    else:
        st.warning("⚠️ 無預測結果，請查看上方診斷日誌")
    
    # ========================================
    # Part 2: 跑法分佈（使用最新數據）
    # ========================================
    
    st.write("---")
    st.header("📊 Part 2: 跑法分佈")
    
    if st.session_state.pace_predictions and PacePredictor:
        try:
            predictor = PacePredictor()
            
            # ✅ 使用最新的 session_state 數據
            dist = predictor.get_runstyle_distribution(st.session_state.pace_predictions)
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🏃 FRONT", dist['FRONT'])
            col2.metric("🚴 MID", dist['MID'])
            col3.metric("🐢 BACK", dist['BACK'])
            col4.metric("📊 合計", dist['total'])
            
            # 圖表
            chart_data = pd.DataFrame({
                '跑法': ['領放', '中置', '留後'],
                '馬匹數': [dist['FRONT'], dist['MID'], dist['BACK']]
            })
            st.bar_chart(chart_data.set_index('跑法'))
            
        except Exception as e:
            st.warning(f"分析失敗: {e}")
    
    # ========================================
    # Part 3: 配速診斷（使用最新數據）
    # ========================================
    
    st.write("---")
    st.header("📊 Part 3: 配速診斷")
    st.info("ℹ️ 版本: PacePredictor v3.0 (Five-Level) - 自動按比例調整")
    
    if st.session_state.pace_predictions and PacePredictor:
        try:
            predictor = PacePredictor()
            
            # 獲取當前馬匹數量
            current_total = len(st.session_state.pace_predictions)
            
            # ✅ 使用最新的 session_state 數據
            diag = predictor.predict_pace_diagnostic(st.session_state.pace_predictions)
            
            # ========================================
            # 顯示當前場次信息
            # ========================================
            st.info(f"📊 當前場次: {current_total} 匹馬 | 期望分佈已自動調整")
            
            st.subheader("🏁 配速診斷")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("配速類型", diag.get('pace_name', 'N/A'))
            col2.metric("信心度", f"{diag.get('confidence', 0):.1f}%")
            
            # 信心度顏色指示
            confidence = diag.get('confidence', 0)
            if confidence >= 70:
                confidence_color = "🟢 高"
            elif confidence >= 40:
                confidence_color = "🟡 中"
            else:
                confidence_color = "🔴 低"
            col3.metric("信心指示", confidence_color)
            
            st.markdown(f"**📝 特徵**: {diag.get('characteristics', 'N/A')}")
            st.markdown(f"**💡 建議**: {diag.get('suggestion', 'N/A')}")
            
            # ========================================
            # 📊 實際 vs 期望分佈對比
            # ========================================
            
            st.markdown("---")
            st.subheader("📊 實際 vs 期望分佈")
            
            # 獲取實際分佈
            actual_dist = predictor.get_runstyle_distribution(st.session_state.pace_predictions)
            
            # 獲取當前配速的期望分佈
            expected_dist = predictor.get_expected_distribution(
                diag.get('pace_type', 'NORMAL'), 
                current_total
            )
            
            # 創建對比表格
            comparison_data = {
                '跑法': ['前置 (FRONT)', '中置 (MID)', '後置 (BACK)'],
                '實際': [
                    actual_dist['FRONT'],
                    actual_dist['MID'],
                    actual_dist['BACK']
                ],
                '期望': [
                    expected_dist['FRONT'],
                    expected_dist['MID'],
                    expected_dist['BACK']
                ],
                '差距': [
                    actual_dist['FRONT'] - expected_dist['FRONT'],
                    actual_dist['MID'] - expected_dist['MID'],
                    actual_dist['BACK'] - expected_dist['BACK']
                ]
            }
            
            comparison_df = pd.DataFrame(comparison_data)
            
            st.dataframe(
                comparison_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    '跑法': st.column_config.TextColumn('跑法', width='medium'),
                    '實際': st.column_config.NumberColumn('實際', format='%d 匹'),
                    '期望': st.column_config.NumberColumn(
                        f'期望 ({diag.get("pace_name", "N/A")})', 
                        format='%d 匹'
                    ),
                    '差距': st.column_config.NumberColumn(
                        '差距', 
                        format='%+d',
                        help='正數=多於期望，負數=少於期望'
                    )
                }
            )
            
            # 視覺化對比
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 實際分佈")
                actual_chart = pd.DataFrame({
                    '跑法': ['前置', '中置', '後置'],
                    '馬匹數': [
                        actual_dist['FRONT'],
                        actual_dist['MID'],
                        actual_dist['BACK']
                    ]
                })
                st.bar_chart(actual_chart.set_index('跑法'))
            
            with col2:
                st.markdown(f"#### 期望分佈 ({diag.get('pace_name', 'N/A')})")
                expected_chart = pd.DataFrame({
                    '跑法': ['前置', '中置', '後置'],
                    '馬匹數': [
                        expected_dist['FRONT'],
                        expected_dist['MID'],
                        expected_dist['BACK']
                    ]
                })
                st.bar_chart(expected_chart.set_index('跑法'))
            
            # ========================================
            # 📊 距離矩陣（詳細分析）
            # ========================================
            
            with st.expander("📊 距離矩陣（5 種配速）", expanded=False):
                distances = diag.get('distances', {})
                
                if distances:
                    # 配速名稱映射
                    pace_names = {
                        'FAST': '快步速',
                        'MODERATELY_FAST': '偏快步速',
                        'NORMAL': '中等步速',
                        'MODERATELY_SLOW': '偏慢步速',
                        'SLOW': '慢步速'
                    }
                    
                    # 創建表格
                    distance_data = []
                    for pace_key, distance in distances.items():
                        # 獲取該配速的期望分佈
                        pace_expected = predictor.get_expected_distribution(pace_key, current_total)
                        
                        distance_data.append({
                            '配速': pace_names.get(pace_key, pace_key),
                            '期望分佈': f"前{pace_expected['FRONT']} / 中{pace_expected['MID']} / 後{pace_expected['BACK']}",
                            '距離': f"{distance:.3f}",
                            '匹配度': f"{max(0, 100 - distance*20):.1f}%"
                        })
                    
                    distance_df = pd.DataFrame(distance_data)
                    
                    # 按距離排序
                    distance_df['距離_數值'] = distance_df['距離'].astype(float)
                    distance_df = distance_df.sort_values('距離_數值').drop('距離_數值', axis=1)
                    
                    st.dataframe(
                        distance_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    st.markdown("📖 **解釋**: 距離越小，該配速的可能性越高")
                    st.markdown(f"📊 **當前場次**: {current_total} 匹馬，期望分佈已自動調整")
                else:
                    st.info("ℹ️ 無距離數據")
            
            # ========================================
            # 📚 五步速期望分佈（當前場次）
            # ========================================
            
            with st.expander(f"📚 五步速期望分佈（{current_total} 匹馬）", expanded=False):
                st.markdown(f"**當前場次期望馬群配置（{current_total} 匹馬）:**")
                
                pace_list = [
                    ('FAST', '快步速'),
                    ('MODERATELY_FAST', '偏快步速'),
                    ('NORMAL', '中等步速'),
                    ('MODERATELY_SLOW', '偏慢步速'),
                    ('SLOW', '慢步速')
                ]
                
                expected_data = []
                for pace_key, pace_name in pace_list:
                    expected = predictor.get_expected_distribution(pace_key, current_total)
                    expected_data.append({
                        '配速': pace_name,
                        '前置 (FRONT)': expected['FRONT'],
                        '中置 (MID)': expected['MID'],
                        '後置 (BACK)': expected['BACK'],
                        '合計': expected['FRONT'] + expected['MID'] + expected['BACK']
                    })
                
                expected_df = pd.DataFrame(expected_data)
                st.dataframe(
                    expected_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                st.markdown("---")
                st.markdown("**📖 算法說明:**")
                st.markdown(f"- 標準模板基於 12 匹馬")
                st.markdown(f"- 當前場次 {current_total} 匹馬，縮放比例: {current_total/12:.2f}x")
                st.markdown(f"- 實際分佈會標準化到 12 匹馬後再與模板比較")
                st.markdown(f"- 因此**無論多少匹馬，診斷邏輯保持一致**")
            
            # ========================================
            # 🔧 配速校正（帶距離影響）
            # ========================================
            
            st.markdown("---")
            st.subheader("🔧 配速校正")
            
            if hasattr(predictor, 'predict_pace'):
                # ✅ 使用最新數據
                pace = predictor.predict_pace(
                    st.session_state.pace_predictions, 
                    race_distance=1800
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 基礎配速")
                    st.metric("基礎值", f"{pace.get('base_pace', 0):.2f}")
                    st.metric("距離係數", f"{pace.get('distance_factor', 0):.2f}")
                    st.metric("賽程", f"{pace.get('race_distance', 0)} 米")
                
                with col2:
                    st.markdown("#### 調整後配速")
                    st.metric("早段", f"{pace.get('early_pace', 0):.2f}")
                    st.metric("中段", f"{pace.get('mid_pace', 0):.2f}")
                    st.metric("晚段", f"{pace.get('late_pace', 0):.2f}")
                
                # 距離影響說明
                distance = pace.get('race_distance', 1800)
                if distance <= 1200:
                    distance_note = "🏃 短途賽事，節奏加快 15%"
                elif distance >= 2000:
                    distance_note = "🐢 長途賽事，節奏放慢 15%"
                else:
                    distance_note = "⚖️ 標準中距離，節奏正常"
                
                if pace.get('adjustment_applied'):
                    st.success(f"✅ {distance_note}")
                else:
                    st.info(f"ℹ️ {distance_note}")
        
        except Exception as e:
            st.warning(f"配速分析失敗: {e}")
            import traceback
            st.error(traceback.format_exc())
    
    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: #888; font-size: 11px;'>"
        f"v5.7 Dynamic Scale - {current_race_id} | 2026-01-10"
        f"</div>",
        unsafe_allow_html=True
    )


if __name__ == '__main__':
    sample = [{
        'position': 1,
        'horse_name': '測試馬',
        'barrier': 12,
        'racing_history': [
            {'distance': 1200, 'going': '1 1 5', 'date': '2026-01-05'},
            {'distance': 1200, 'going': '2 2 6', 'date': '2025-12-20'}
        ]
    }]
    
    st.session_state.race_id = "TEST_R1"
    render_pace_prediction_analysis(sample, 12)
