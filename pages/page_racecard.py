
# -*- coding: utf-8 -*-

"""
頁面代碼 - v3.10 ✅ 配腳評分 + 檔位統計整合 + 防混淆驗證

Page Racecard - v3.10 Enhanced with Draw Statistics Integration & Anti-Confusion Validation

新增內容：
✅ 排位表爬蟲 (保留 v3.9.1)
✅ 往績爬蟲 (保留 v3.9.1)
✅ 賽次詳細信息 (保留 v3.9.1)
✅ 跑法預測分析 (保留 v3.9.1)
✅ 配腳評分分析 (保留 v3.9.1)
✅ 錯誤追蹤顯示 (保留 v3.9.1)

🆕 檔位統計加載 (v3.10 - 防混淆 Level 1)
🆕 防混淆驗證 (v3.10 - 防混淆 Level 2)
🆕 混合評分詳情 (v3.10 - 增強診斷)
🆕 檔位統計來源顯示 (v3.10 - 可選診斷)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from analyzers.racecard_analyzer import RaceCardAnalyzer
from analyzers.race_details_extractor import RaceDetailsExtractor
from pages.page_pace_prediction_integrated import render_pace_prediction_analysis
import logging
import traceback

logger = logging.getLogger(__name__)


def clear_predictions():
    """
    清除舊場次的預測數據
    ✅ 使用場次 ID 識別，而非全部清除
    """
    current_race_id = st.session_state.get('race_id')
    stored_race_id = st.session_state.get('pace_race_id')
    
    # 如果是不同場次，清除舊數據
    if current_race_id != stored_race_id:
        logger.info(f"🔄 檢測到場次變更: {stored_race_id} → {current_race_id}")
        st.session_state.pop('pace_predictions', None)
        st.session_state.pop('pace_predictions_edited', None)
        st.session_state.pop('pace_race_horses_data', None)
        st.session_state.pop('pace_total_runners', None)
        st.session_state['pace_race_id'] = current_race_id
        logger.info("✅ 已清除舊場次數據")
    else:
        logger.info(f"ℹ️ 同一場次 ({current_race_id})，保留現有數據")


def render_leg_fitness_scoring(horses, race_details):
    """
    🆕 配腳評分分析 (v3.10 檔位統計整合版)
    
    流程：
    1. 加載檔位統計 (防混淆 Level 1)
    2. 防混淆驗證 (防混淆 Level 2)
    3. 構建 race_info
    4. 初始化評分器
    5. 對每匹馬評分 (傳遞檔位統計) ← 新增參數
    6. 顯示排名結果
    7. 診斷模式 (混合評分詳情) ← 新增
    """
    st.subheader("📊 配腳評分分析 (v3.10)")
    
    try:
        # 檢查是否有馬匹數據
        if not horses:
            st.warning("❌ 沒有馬匹數據，無法進行配腳評分")
            return
        
        # 🔧 診斷按鈕
        col1, col2, col3 = st.columns(3)
        
        with col1:
            score_button = st.button("🚀 開始配腳評分", key="leg_fitness_score")
        
        with col2:
            debug_button = st.button("🔍 診斷往績數據", key="debug_racing_history")
        
        with col3:
            show_draw_stats_button = st.button("📊 檔位統計來源", key="show_draw_stats_source")
        
        # ============================================================
        # 🆕 診斷模式 1：顯示檔位統計來源
        # ============================================================
        
        if show_draw_stats_button:
            st.info("📊 顯示檔位統計數據來源...")
            
            selected_race_num = st.session_state.get('race_id', '').split('_')[-1].replace('R', '')
            
            try:
                selected_race_num = int(selected_race_num)
            except:
                st.error("❌ 無法解析場次號")
                return
            
            try:
                from db_manager import DatabaseManager
                
                db = DatabaseManager()
                latest_date = db.get_latest_date()
                
                if latest_date:
                    all_races = db.get_all_races_for_date(latest_date)
                    
                    if selected_race_num in all_races:
                        current_race_data = all_races[selected_race_num]
                        
                        st.success(f"✅ 找到第 {selected_race_num} 場的檔位統計")
                        
                        # 顯示元數據
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("場次", current_race_data.get('race_num', '未知'))
                        with col2:
                            st.metric("距離", f"{current_race_data.get('distance', '未知')} 米")
                        with col3:
                            st.metric("場地", current_race_data.get('going', '未知'))
                        with col4:
                            st.metric("日期", latest_date)
                        
                        # 驗證匹配
                        if current_race_data.get('race_num') == selected_race_num:
                            st.success("✅ 檔位統計場次匹配正確")
                        else:
                            st.error("❌ 警告：檔位統計場次不匹配！")
                        
                        # 顯示統計表
                        if st.checkbox("顯示完整檔位統計", key="show_full_draw_stats"):
                            stats_list = []
                            for stat in current_race_data.get('statistics', []):
                                stats_list.append({
                                    '檔位': stat.get('draw'),
                                    '樣本數': stat.get('races_run', 0),
                                    '冠軍次數': stat.get('wins', 0),
                                    '入位次數': stat.get('places', 0),
                                    '勝率%': stat.get('win_rate', 0),
                                    '入位率%': stat.get('place_rate', 0),
                                    '上名率%': stat.get('top3_rate', 0)
                                })
                            
                            st.dataframe(stats_list, use_container_width=True)
                    else:
                        st.warning(f"⚠️ 找不到第 {selected_race_num} 場的檔位統計")
                else:
                    st.warning("⚠️ 數據庫中無最新日期")
            
            except Exception as e:
                st.error(f"❌ 取得檔位統計時出錯: {str(e)}")
                logger.error(f"取得檔位統計錯誤: {e}", exc_info=True)
            
            return
        
        # ============================================================
        # 🆕 診斷模式 2：顯示前 3 匹馬的完整往績
        # ============================================================
        
        if debug_button:
            st.info("📊 顯示前 3 匹馬的完整往績結構...")
            
            for idx, horse in enumerate(horses[:3]):  # 只顯示前 3 匹
                horse_name = horse.get('horse_name', 'Unknown')
                barrier = horse.get('barrier', '?')
                racing_history = horse.get('racing_history', [])
                
                with st.expander(f"🐴 {horse_name} (檔位: {barrier}) - {len(racing_history)} 場往績", expanded=True):
                    
                    # 基本信息
                    st.write(f"**馬名:** {horse_name}")
                    st.write(f"**當前檔位:** {barrier} (類型: {type(barrier).__name__})")
                    st.write(f"**往績數量:** {len(racing_history)}")
                    
                    st.markdown("---")
                    
                    # 顯示前 5 場往績的完整內容
                    if racing_history:
                        st.write("**前 5 場往績詳情:**")
                        
                        for i, record in enumerate(racing_history[:5]):
                            st.write(f"**第 {i+1} 場:**")
                            
                            # 關鍵字段檢查
                            st.json({
                                'position': f"{record.get('position')} (type: {type(record.get('position')).__name__})",
                                'barrier': f"{record.get('barrier')} (type: {type(record.get('barrier')).__name__})",
                                'distance': f"{record.get('distance')} (type: {type(record.get('distance')).__name__})",
                                'condition': f"{record.get('condition')} (type: {type(record.get('condition')).__name__})",
                                'going': f"{record.get('going')} (type: {type(record.get('going')).__name__})",
                                'venue': record.get('venue'),
                                'date': record.get('date'),
                                'winning_distance': record.get('winning_distance'),
                            })
                            
                            st.markdown("---")
                        
                        # 統計分析
                        st.write("**📊 統計分析:**")
                        
                        # 檔位分布
                        barriers_in_history = [r.get('barrier') for r in racing_history if r.get('barrier')]
                        st.write(f"- 歷史檔位: {barriers_in_history[:10]}")
                        
                        # 距離分布
                        distances_in_history = [r.get('distance') for r in racing_history if r.get('distance')]
                        st.write(f"- 歷史距離: {distances_in_history[:10]}")
                        
                        # 場地分布
                        conditions_in_history = [r.get('condition') for r in racing_history if r.get('condition')]
                        goings_in_history = [r.get('going') for r in racing_history if r.get('going')]
                        st.write(f"- condition 字段: {conditions_in_history[:10]}")
                        st.write(f"- going 字段: {goings_in_history[:10]}")
                        
                    else:
                        st.error("❌ 無往績數據")
            
            st.success("✅ 診斷完成！")
            return
        
        # ============================================================
        # 🆕 評分按鈕：主流程
        # ============================================================
        
        if score_button:
            st.info("⏳ 正在計算配腳評分...")
            
            # ========================================================
            # 📍 Step 1: 檔位統計加載 (防混淆 Level 1)
            # ========================================================
            
            selected_race_num = st.session_state.get('race_id', '').split('_')[-1].replace('R', '')
            
            try:
                selected_race_num = int(selected_race_num)
            except:
                st.error("❌ 無法解析場次號")
                return
            
            draw_stats_dict = None
            current_race_data = None
            
            try:
                from db_manager import DatabaseManager
                
                db = DatabaseManager()
                latest_date = db.get_latest_date()
                
                if latest_date:
                    try:
                        # 獲取檔位統計
                        all_races = db.get_all_races_for_date(latest_date)
                        
                        if selected_race_num in all_races:
                            current_race_data = all_races[selected_race_num]
                            
                            # ========================================================
                            # 🆕 防混淆驗證 (防混淆 Level 2)
                            # ========================================================
                            
                            if current_race_data.get('race_num') == selected_race_num:
                                # 通過驗證 → 使用統計
                                draw_stats_dict = {
                                    stat['draw']: stat
                                    for stat in current_race_data.get('statistics', [])
                                }
                                
                                # 加入元數據（防混淆）
                                draw_stats_dict['_race_num'] = selected_race_num
                                draw_stats_dict['_distance'] = current_race_data.get('distance')
                                draw_stats_dict['_going'] = current_race_data.get('going')
                                draw_stats_dict['_date'] = latest_date
                                
                                st.success(
                                    f"✅ 已加載第 {selected_race_num} 場檔位統計 ({len(draw_stats_dict) - 4} 個檔位)"
                                )
                                logger.info(f"✅ 已加載第 {selected_race_num} 場檔位統計")
                            
                            else:
                                # 驗證失敗 → 報錯
                                st.error(
                                    f"❌ 數據不匹配！"
                                    f"預期第 {selected_race_num} 場，"
                                    f"實際第 {current_race_data.get('race_num')} 場"
                                )
                                logger.error(f"❌ 防混淆驗證失敗: 場次不符")
                                draw_stats_dict = None
                        
                        else:
                            st.warning(f"⚠️ 找不到第 {selected_race_num} 場的檔位統計")
                            logger.warning(f"⚠️ 找不到第 {selected_race_num} 場的檔位統計")
                    
                    except Exception as e:
                        st.error(f"❌ 取得檔位統計時出錯: {str(e)}")
                        logger.error(f"取得檔位統計錯誤: {e}", exc_info=True)
            
            except Exception as e:
                st.error(f"❌ 初始化數據庫時出錯: {str(e)}")
                logger.error(f"初始化數據庫錯誤: {e}", exc_info=True)
            
            # ========================================================
            # Step 2: 準備賽事信息
            # ========================================================
            
            race_info = {
                'distance': race_details.get('distance', '1400'),
                'venue': race_details.get('venue', '沙田'),
                'going': race_details.get('going', 'Good'),
                'track': race_details.get('track_type', '草地')
            }
            
            # 清理距離（移除"米"）
            if isinstance(race_info['distance'], str):
                import re
                match = re.search(r'(\d+)', race_info['distance'])
                race_info['distance'] = int(match.group(1)) if match else 1400
            else:
                race_info['distance'] = int(race_info['distance']) if race_info['distance'] else 1400
            
            logger.info(f"📊 賽事信息: {race_info}")
            logger.info(f"🐴 馬匹數: {len(horses)}")
            
            # ========================================================
            # Step 3: 調用配腳評分系統
            # ========================================================
            
            try:
                from analyzers.leg_fitness_scorer_realtime import RealtimeLegFitnessScorer
                
                scorer = RealtimeLegFitnessScorer()
                
                # ========================================================
                # 📍 Step 4: 對每匹馬評分 (傳遞檔位統計)
                # ========================================================
                
                scored_horses = []
                errors = []
                
                for idx, horse in enumerate(horses):
                    try:
                        # 構建賽事信息
                        horse_race_info = {
                            'race_num': selected_race_num,
                            'barrier': horse.get('barrier'),
                            'distance': race_info['distance'],
                            'going': race_info['going'],
                            'venue': race_info['venue'],
                            'track': race_info['track']
                        }
                        
                        # ⭐ 傳入檔位統計（關鍵改動）
                        scores = scorer.calculate_scores(
                            racing_history=horse.get('racing_history', []),
                            race_info=horse_race_info,
                            draw_statistics=draw_stats_dict  # ← 新增參數！
                        )
                        
                        # 存儲評分結果
                        horse['scores'] = scores
                        scored_horses.append(horse)
                    
                    except ValueError as ve:
                        # 捕獲防混淆驗證錯誤
                        st.error(f"❌ 馬匹 #{idx+1} ({horse.get('horse_name')}) 評分失敗: {str(ve)}")
                        logger.error(f"評分驗證錯誤: {ve}")
                        errors.append({
                            'horse': horse.get('horse_name'),
                            'error': str(ve)
                        })
                        continue
                    
                    except Exception as e:
                        # 其他錯誤
                        st.error(f"❌ 馬匹 #{idx+1} ({horse.get('horse_name')}) 評分失敗: {str(e)}")
                        logger.error(f"評分錯誤: {e}", exc_info=True)
                        errors.append({
                            'horse': horse.get('horse_name'),
                            'error': str(e)
                        })
                        continue
                
                # ========================================================
                # Step 5: 顯示評分結果
                # ========================================================
                
                if scored_horses:
                    # 按總分排序
                    scored_horses.sort(key=lambda x: x['scores'].get('total_score', 0), reverse=True)
                    
                    st.success(f"✅ 評分完成！共評分 {len(scored_horses)}/{len(horses)} 匹馬")
                    logger.info(f"✅ 評分完成：{len(scored_horses)}/{len(horses)}")
                    
                    # ========================================================
                    # 📊 評分排名表
                    # ========================================================
                    
                    st.subheader("🏆 評分排名表")
                    
                    ranking_data = []
                    for rank, horse in enumerate(scored_horses, 1):
                        scores = horse['scores']
                        ranking_data.append({
                            '排名': rank,
                            '馬名': horse.get('horse_name', '未知'),
                            '檔位': horse.get('barrier'),
                            '總分': f"{scores.get('total_score', 0):.3f}",
                            '評級': scores.get('grade', 'N/A'),
                            '檔位適應': f"{scores.get('barrier', {}).get('score', 0):.3f}",
                            '距離適應': f"{scores.get('distance', {}).get('score', 0):.3f}",
                            '場地適應': f"{scores.get('going', {}).get('score', 0):.3f}",
                            '穩定性': f"{scores.get('stability', {}).get('score', 0):.3f}",
                            '狀態趨勢': f"{scores.get('trend', {}).get('score', 0):.3f}",
                            '一致性': f"{scores.get('consistency', {}).get('score', 0):.3f}"
                        })
                    
                    ranking_df = pd.DataFrame(ranking_data)
                    st.dataframe(ranking_df, use_container_width=True)
                    
                    # ========================================================
                    # 📍 Step 6: 診斷模式 (混合評分詳情)
                    # ========================================================
                    
                    st.subheader("🔬 詳細分析")
                    
                    for horse_idx, horse in enumerate(scored_horses):
                        horse_name = horse.get('horse_name', 'Unknown')
                        barrier = horse.get('barrier')
                        
                        with st.expander(f"🐴 {horse_name} (檔位: {barrier})", expanded=False):
                            
                            if 'scores' in horse:
                                scores = horse['scores']
                                
                                # ========== 檔位適應詳情 (混合評分) ==========
                                if 'barrier' in scores:
                                    st.write("### 1️⃣ 檔位適應 (混合評分)")
                                    barrier_info = scores['barrier'].get('details', {})
                                    
                                    # 判斷情境（A/B/C）
                                    n = barrier_info.get('barrier_races', 0)
                                    pw = barrier_info.get('personal_weight', 0)
                                    
                                    if n >= 8:
                                        strategy = f"✅ 情境 A: 樣本充足（個人 {pw:.0%}，統計 {(1-pw):.0%}）"
                                        strategy_color = "green"
                                    elif n >= 3:
                                        strategy = f"⚠️ 情境 C: 樣本中等（個人 {pw:.0%}，統計 {(1-pw):.0%}）"
                                        strategy_color = "orange"
                                    else:
                                        strategy = "⚠️ 情境 B: 樣本不足（統計主導 100%）"
                                        strategy_color = "red"
                                    
                                    st.markdown(f":{strategy_color}[{strategy}]")
                                    
                                    # 三欄展示
                                    col1, col2, col3 = st.columns(3)
                                    
                                    # 個人表現
                                    with col1:
                                        st.write("**👤 個人表現:**")
                                        st.metric("樣本數", f"{n} 場")
                                        if barrier_info.get('personal_score'):
                                            st.metric("入位率", f"{barrier_info.get('personal_place_rate', 0):.1%}")
                                            st.metric("個人評分", f"{barrier_info.get('personal_score', 0):.3f}")
                                            st.metric("權重", f"{pw:.0%}")
                                        else:
                                            st.write("_無足夠樣本_")
                                    
                                    # 群體統計
                                    with col2:
                                        st.write("**📊 群體統計:**")
                                        st.metric("統計樣本", f"{barrier_info.get('stat_races_run', 0)} 場")
                                        st.metric("統計入位率", f"{barrier_info.get('stat_place_rate', 0):.1%}")
                                        st.metric("統計評分", f"{barrier_info.get('stat_score', 0):.3f}")
                                        st.metric("權重", f"{(1-pw):.0%}")
                                    
                                    # 最終結果
                                    with col3:
                                        st.write("**🎯 最終結果:**")
                                        st.metric("最終評分", f"{barrier_info.get('final_score', 0):.3f}")
                                        st.metric("評分來源", barrier_info.get('score_source', 'N/A'))
                                    
                                    # 計算公式
                                    if barrier_info.get('personal_score'):
                                        ps = barrier_info.get('personal_score', 0)
                                        ss = barrier_info.get('stat_score', 0)
                                        fs = barrier_info.get('final_score', 0)
                                        formula = f"{fs:.3f} = {ps:.3f} × {pw:.2f} + {ss:.3f} × {(1-pw):.2f}"
                                        st.code(formula, language="python")
                                    
                                    if barrier_info.get('warning'):
                                        st.warning(barrier_info['warning'])
                                    if barrier_info.get('stat_warning'):
                                        st.warning(barrier_info['stat_warning'])
                                
                                # ========== 其他維度詳情 ==========
                                st.write("### 2️⃣ 距離適應")
                                distance_info = scores.get('distance', {}).get('details', {})
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("相近距離場數", distance_info.get('distance_races', 0))
                                with col2:
                                    st.metric("入位率", f"{distance_info.get('place_rate', 0):.1%}")
                                
                                st.write("### 3️⃣ 場地適應")
                                going_info = scores.get('going', {}).get('details', {})
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("相同場地場數", going_info.get('going_races', 0))
                                with col2:
                                    st.metric("入位率", f"{going_info.get('place_rate', 0):.1%}")
                                
                                st.write("### 4️⃣ 穩定性 (Win/Place Ratio)")
                                stability_info = scores.get('stability', {}).get('details', {})
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("冠軍次數", stability_info.get('wins', 0))
                                with col2:
                                    st.metric("入位次數", stability_info.get('places', 0))
                                with col3:
                                    st.metric("Win/Place Ratio", f"{stability_info.get('win_place_ratio', 0):.3f}")
                                
                                st.info(f"馬型: {stability_info.get('pattern', '未知')}")
                                
                                st.write("### 5️⃣ 狀態趨勢")
                                trend_info = scores.get('trend', {}).get('details', {})
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("全局入位率", f"{trend_info.get('overall_place_rate', 0):.1%}")
                                with col2:
                                    st.metric("近期入位率", f"{trend_info.get('recent_place_rate', 0):.1%}")
                                with col3:
                                    st.metric("趨勢比例", f"{trend_info.get('trend_ratio', 0):.2f}")
                                
                                st.info(f"趨勢: {trend_info.get('trend', '未知')}")
                                
                                st.write("### 6️⃣ 一致性")
                                consistency_info = scores.get('consistency', {}).get('details', {})
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("排位標準差", f"{consistency_info.get('stddev', 0):.2f}")
                                with col2:
                                    st.metric("平均排位", f"{consistency_info.get('mean_position', 0):.1f}")
                                
                                st.info(f"評級: {consistency_info.get('rating', '未知')}")
                    
                    # 保存結果到 session
                    st.session_state.leg_fitness_results = scored_horses
                
                else:
                    st.error(f"❌ 沒有成功評分的馬匹")
                    logger.error("❌ 沒有成功評分的馬匹")
                
                # 顯示錯誤摘要
                if errors:
                    with st.expander(f"⚠️ {len(errors)} 匹馬評分失敗", expanded=False):
                        for err in errors:
                            st.error(f"**{err['horse']}**: {err['error']}")
            
            except Exception as e:
                st.error(f"❌ 評分系統錯誤: {str(e)}")
                logger.error(f"評分系統錯誤: {e}", exc_info=True)
                with st.expander("🔍 錯誤詳情"):
                    st.code(traceback.format_exc())
    
    except Exception as e:
        st.error(f"❌ 配腳評分模塊出錯: {str(e)}")
        logger.error(f"模塊錯誤: {e}", exc_info=True)
        with st.expander("🔍 錯誤詳情"):
            st.code(traceback.format_exc())


def _display_scoring_results(scoring_results):
    """
    顯示配腳評分結果 (從 render_leg_fitness_scoring 抽離)
    ⚠️ 注意：這個函數已經被整合到 render_leg_fitness_scoring 中
    保留作為向後兼容
    """
    pass


def render_racecard_page():
    """渲染排位表分析頁面 v3.10 - 檔位統計整合 + 防混淆"""
    
    st.header("🏇 排位表分析")
    st.markdown("---")
    
    # ============================================================================
    # 側邊欄: 參數選擇
    # ============================================================================
    
    with st.sidebar:
        st.subheader("⚙️ 參數設置")
        
        # 日期選擇
        race_date = st.date_input(
            "📅 選擇賽事日期",
            value=datetime.now(),
            help="選擇馬會賽事日期"
        )
        
        # 馬場選擇
        racecourse = st.radio(
            "🏟️ 選擇馬場",
            options=[("跑馬地 (Happy Valley)", "HV"), ("沙田 (Sha Tin)", "ST")],
            format_func=lambda x: x[0],
            help="選擇賽事馬場"
        )
        
        racecourse = racecourse[1] if isinstance(racecourse, tuple) else racecourse
        
        # 場次選擇
        race_no = st.selectbox(
            "🎯 選擇場次",
            options=range(1, 14),
            format_func=lambda x: f"第 {x} 場",
            help="選擇賽事場次"
        )
        
        # 往績數量選擇
        max_races = st.slider(
            "📊 每匹馬最多往績數",
            min_value=3,
            max_value=30,
            value=6,
            step=1,
            help="每匹馬最多爬取的往績記錄數"
        )
        
        # 爬取按鈕
        fetch_button = st.button("🔄 爬取排位表 + 往績", use_container_width=True)
        
        # 診斷開關
        show_debug = st.checkbox("🔍 顯示詳細診斷信息", value=False, help="顯示完整的數據流診斷")
    
    # ============================================================================
    # 主區域: 數據爬取和展示
    # ============================================================================
    
    if fetch_button:
        date_str = race_date.strftime("%Y/%m/%d")
        
        # ✅ 生成場次 ID（提前生成）
        date_id = race_date.strftime("%Y%m%d")
        race_id_temp = f"{racecourse}_{date_id}_R{race_no}"
        
        st.session_state.race_id = race_id_temp  # 提前設置
        
        # ✅ 清除舊場次數據（如果場次變更）
        clear_predictions()
        
        with st.spinner("🔍 正在爬取排位表、賽次信息和馬匹往績..."):
            analyzer = RaceCardAnalyzer(timeout=15, retry=5)
            details_extractor = RaceDetailsExtractor(timeout=15)
            
            try:
                # 爬取排位表
                result = analyzer.fetch_racecard(
                    date_str,
                    racecourse,
                    race_no,
                    fetch_history=True,
                    max_races=max_races
                )
                
                if 'error' in result:
                    st.error(f"❌ 爬蟲錯誤: {result['error']}")
                    st.stop()
                
                race_id = result.get('race_id')
                horses = result.get('horses', [])
                
                # 提取賽次詳細信息
                details_result = details_extractor.extract_race_details(
                    date_str,
                    racecourse,
                    race_no
                )
                
                race_details = details_result.get('race_details', {}) if details_result['status'] == 'success' else {}
                
                # 統計往績爬取情況
                with_history = sum(1 for h in horses if h.get('racing_history'))
                
                st.success(f"✅ 成功爬取: {race_id} ({len(horses)} 隻馬, {with_history} 隻含往績)")
                
                # ============================================================================
                # 🔍 診斷第 1 層：排位表爬蟲數據
                # ============================================================================
                
                if show_debug:
                    st.markdown("---")
                    st.subheader("🔍 診斷第 1 層：排位表爬蟲數據")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("📊 接收馬數", len(horses))
                    with col2:
                        st.metric("📋 含往績馬數", with_history)
                    with col3:
                        st.metric("📊 缺往績馬數", len(horses) - with_history)
                    
                    # 詳細馬匹信息
                    with st.expander("📋 馬匹詳細信息表"):
                        horses_info = []
                        for h in horses:
                            history = h.get('racing_history', [])
                            horses_info.append({
                                '編號': h.get('position'),
                                '馬名': h.get('horse_name'),
                                '往績數': len(history),
                                '有効': '✅' if len(history) > 0 else '❌'
                            })
                        
                        info_df = pd.DataFrame(horses_info)
                        st.dataframe(info_df, use_container_width=True, hide_index=True)
                    
                    # 第一隻馬的往績樣本
                    if horses and len(horses) > 0:
                        first_horse = horses[0]
                        first_history = first_horse.get('racing_history', [])
                        
                        with st.expander(f"🐴 {first_horse.get('horse_name')} 往績樣本（前3條）"):
                            if first_history:
                                for idx, record in enumerate(first_history[:3]):
                                    st.write(f"**往績 {idx+1}:**")
                                    st.json(record)
                            else:
                                st.warning("無往績數據")
                
                # 保存到 session state
                st.session_state.race_id = race_id
                st.session_state.horses = horses
                st.session_state.analyzer = analyzer
                st.session_state.race_details = race_details
                
            except Exception as e:
                st.error(f"❌ 發生錯誤: {str(e)}")
                st.error(f"詳細信息:\n{traceback.format_exc()}")
                st.stop()
    
    # ============================================================================
    # ✅ 修復：無論是否爬取，都顯示已有數據
    # ============================================================================
    
    if 'race_id' in st.session_state and 'horses' in st.session_state:
        race_id = st.session_state.race_id
        horses = st.session_state.horses
        race_details = st.session_state.get('race_details', {})
        
        # ====================================================================
        # 🆕 賽次詳細信息卡片
        # ====================================================================
        
        st.subheader("📋 賽次詳細信息")
        
        if race_details:
            # 建立欄位顯示
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🎯 場次", race_details.get('race_number', ''))
                st.metric("📅 日期", race_details.get('date', ''))
                st.metric("🏟️ 馬場", race_details.get('venue', ''))
            
            with col2:
                st.metric("🏃 跑道", race_details.get('track_type', ''))
                st.metric("📏 途程", f"{race_details.get('distance', '')}米")
                st.metric("🌧️ 場地", race_details.get('going', ''))
            
            with col3:
                st.metric("📊 賽道等級", f"\"{race_details.get('track_rating', '')}\"")
                st.metric("📋 班次", race_details.get('class', ''))
                if race_details.get('prize_money'):
                    st.metric("💰 獎金", f"${race_details.get('prize_money', '')}")
                else:
                    st.metric("💰 獎金", "")
            
            st.markdown("---")
        else:
            # 原始賽次信息卡片 (備用)
            st.subheader(f"📋 賽次信息: {race_id}")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📅 日期", race_id.split('_')[1] if '_' in race_id else "")
            with col2:
                st.metric("🏟️ 馬場", "跑馬地" if race_id.startswith('HV') else "沙田")
            with col3:
                st.metric("🎯 場次", f"第 {race_id.split('_')[-1].replace('R', '')} 場" if '_' in race_id else '')
            with col4:
                st.metric("🐴 參賽馬數", len(horses))
            
            st.markdown("---")
        
        # ====================================================================
        # ✅ 關鍵修復：渲染跑法預測分析（無論是否剛爬取）
        # ====================================================================
        
        st.subheader("🏃 馬匹跑法預測分析")
        
        # 檢查是否有馬匹數據
        if horses:
            # ✅ 始終渲染預測頁面（無論是否剛爬取）
            render_pace_prediction_analysis(
                race_horses_data=horses,
                total_runners=len(horses)
            )
        else:
            st.error("❌ 沒有馬匹數據可以預測")
        
        st.markdown("---")
        
        # ====================================================================
        # 🆕 新增：配腳評分分析 (v3.10)
        # ====================================================================
        
        render_leg_fitness_scoring(horses, race_details)
        
        st.markdown("---")
        
        # ====================================================================
        # 排位表 (17 欄)
        # ====================================================================
        
        st.subheader("📊 排位表 (17 欄)")
        
        df = pd.DataFrame(horses)
        
        # 顯示欄位映射
        display_columns = {
            'position': '編號',
            'recent_runs': '6次近績',
            'horse_name': '馬名',
            'horse_code': '烙號',
            'weight': '負磅',
            'jockey': '騎師',
            'barrier': '檔位',
            'trainer': '練馬師',
            'rating': '評分',
            'rating_change': '評分+/-',
            'stable_weight': '排位體重',
            'weight_change': '體重+/-',
            'best_time': '最佳時間',
            'priority_order': '優先參賽',
            'remarks': '配備',
            'sire': '父系',
            'age': '馬齡'
        }
        
        # 過濾並重命名
        cols_to_use = [c for c in display_columns.keys() if c in df.columns]
        df_display = df[cols_to_use].rename(columns=display_columns)
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=600
        )
        
        st.markdown("---")
        
        # ====================================================================
        # 馬匹往績 (展開式) - 適配爬蟲格式
        # ====================================================================
        
        st.subheader("📈 馬匹往績紀錄 (點擊展開)")
        
        # 爬蟲欄位映射
        history_column_mapping = {
            'race_no': '場次',
            'position': '名次',
            'date': '日期',
            'venue': '馬場/跑道',
            'distance': '途程',
            'condition': '場地',
            'race_class': '班次',
            'barrier': '檔位',
            'rating': '評分',
            'trainer': '練馬師',
            'jockey': '騎師',
            'winning_distance': '頭馬距離',
            'win_odds': '獨贏',
            'actual_weight': '實際負磅',
            'going': '沿途走位',
            'finishing_time': '完成時間',
            'stable_weight': '排位體重',
            'gear': '配備',
            'remarks': '配備'
        }
        
        # 遍歷每隻馬並展示往績
        for horse in horses:
            horse_name = horse.get('horse_name', 'N/A')
            racing_history = horse.get('racing_history', [])
            
            with st.expander(f"🐴 {horse_name} (往績 {len(racing_history)} 場)"):
                if racing_history:
                    # 轉換為 DataFrame
                    history_df = pd.DataFrame(racing_history)
                    
                    # 篩選可用欄位並重命名
                    available_cols = [c for c in history_column_mapping.keys() if c in history_df.columns]
                    
                    if available_cols:
                        history_df_display = history_df[available_cols].rename(columns=history_column_mapping)
                        
                        st.dataframe(
                            history_df_display,
                            use_container_width=True,
                            hide_index=True,
                            height=200
                        )
                    else:
                        st.write("無法找到對應的往績欄位")
                else:
                    st.write("暫無往績記錄")
        
        st.markdown("---")
        
        # ====================================================================
        # 下載區域
        # ====================================================================
        
        if not df_display.empty:
            csv = df_display.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                "📥 下載排位表 (CSV)",
                csv,
                f"racecard_{race_id}.csv",
                "text/csv"
            )


# 頁面入口
if __name__ == "__main__":
    render_racecard_page()

# ============================================================
# 🔗 向後兼容別名 (供 __init__.py 使用)
# ============================================================

# 為了兼容 __init__.py 中的 from .page_racecard import render
render = render_racecard_page


# ============================================================
# 🔧 輔助函數區 (Helper Functions)
# ============================================================

def export_scoring_results_to_csv(scored_horses, filename=None):
    """
    導出評分結果到 CSV
    
    Args:
        scored_horses: 評分後的馬匹列表
        filename: 文件名（可選，自動生成）
    
    Returns:
        tuple: (success: bool, message: str, csv_data: str)
    """
    try:
        if not filename:
            race_id = st.session_state.get('race_id', 'unknown')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"leg_fitness_results_{race_id}_{timestamp}.csv"
        
        export_data = []
        for rank, horse in enumerate(scored_horses, 1):
            scores = horse.get('scores', {})
            barrier_details = scores.get('barrier', {}).get('details', {})
            
            export_data.append({
                '排名': rank,
                '馬名': horse.get('horse_name', '未知'),
                '檔位': horse.get('barrier'),
                '騎師': horse.get('jockey', '未知'),
                '練馬師': horse.get('trainer', '未知'),
                '評分': horse.get('rating', 'N/A'),
                '總分': round(scores.get('total_score', 0), 3),
                '評級': scores.get('grade', 'N/A'),
                '檔位適應': round(scores.get('barrier', {}).get('score', 0), 3),
                '檔位樣本數': barrier_details.get('barrier_races', 0),
                '檔位個人評分': round(barrier_details.get('personal_score', 0), 3) if barrier_details.get('personal_score') else 0,
                '檔位統計評分': round(barrier_details.get('stat_score', 0), 3),
                '檔位權重來源': barrier_details.get('score_source', 'N/A'),
                '距離適應': round(scores.get('distance', {}).get('score', 0), 3),
                '場地適應': round(scores.get('going', {}).get('score', 0), 3),
                '穩定性': round(scores.get('stability', {}).get('score', 0), 3),
                '狀態趨勢': round(scores.get('trend', {}).get('score', 0), 3),
                '一致性': round(scores.get('consistency', {}).get('score', 0), 3)
            })
        
        df = pd.DataFrame(export_data)
        csv_data = df.to_csv(index=False, encoding='utf-8-sig')
        
        return True, f"✅ 已準備導出 {filename}", csv_data
    
    except Exception as e:
        logger.error(f"導出失敗: {e}", exc_info=True)
        return False, f"❌ 導出失敗: {str(e)}", None


def calculate_scoring_statistics(scored_horses):
    """
    計算評分統計信息
    
    Args:
        scored_horses: 評分後的馬匹列表
    
    Returns:
        dict: 統計信息字典
    """
    if not scored_horses:
        return None
    
    try:
        total_scores = [h['scores']['total_score'] for h in scored_horses]
        barrier_scores = [h['scores']['barrier']['score'] for h in scored_horses]
        distance_scores = [h['scores']['distance']['score'] for h in scored_horses]
        going_scores = [h['scores']['going']['score'] for h in scored_horses]
        
        stats = {
            'total_horses': len(scored_horses),
            'total_score_stats': {
                'mean': sum(total_scores) / len(total_scores),
                'max': max(total_scores),
                'min': min(total_scores),
                'std': pd.Series(total_scores).std()
            },
            'barrier_score_stats': {
                'mean': sum(barrier_scores) / len(barrier_scores),
                'max': max(barrier_scores),
                'min': min(barrier_scores)
            },
            'distance_score_stats': {
                'mean': sum(distance_scores) / len(distance_scores),
                'max': max(distance_scores),
                'min': min(distance_scores)
            },
            'going_score_stats': {
                'mean': sum(going_scores) / len(going_scores),
                'max': max(going_scores),
                'min': min(going_scores)
            }
        }
        
        return stats
    
    except Exception as e:
        logger.error(f"計算統計失敗: {e}", exc_info=True)
        return None


def render_scoring_statistics_panel(scored_horses):
    """
    渲染評分統計面板
    
    Args:
        scored_horses: 評分後的馬匹列表
    """
    stats = calculate_scoring_statistics(scored_horses)
    
    if not stats:
        st.warning("⚠️ 無法計算統計數據")
        return
    
    st.subheader("📈 評分統計摘要")
    
    # 總分統計
    st.write("### 🎯 總分統計")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("參賽馬數", stats['total_horses'])
    with col2:
        st.metric("平均總分", f"{stats['total_score_stats']['mean']:.3f}")
    with col3:
        st.metric("最高分", f"{stats['total_score_stats']['max']:.3f}")
    with col4:
        st.metric("最低分", f"{stats['total_score_stats']['min']:.3f}")
    
    # 各維度統計
    st.write("### 📊 各維度平均分")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("檔位適應", f"{stats['barrier_score_stats']['mean']:.3f}")
    with col2:
        st.metric("距離適應", f"{stats['distance_score_stats']['mean']:.3f}")
    with col3:
        st.metric("場地適應", f"{stats['going_score_stats']['mean']:.3f}")


def generate_horse_recommendation_tags(horse_scores):
    """
    根據評分生成智能推薦標籤
    
    Args:
        horse_scores: 單匹馬的評分字典
    
    Returns:
        list: 標籤列表
    """
    tags = []
    
    try:
        # 總分標籤
        total_score = horse_scores.get('total_score', 0)
        if total_score >= 0.75:
            tags.append("⭐ 強力推薦")
        elif total_score >= 0.65:
            tags.append("👍 值得考慮")
        elif total_score >= 0.55:
            tags.append("🤔 觀察")
        else:
            tags.append("⚠️ 謹慎")
        
        # 檔位標籤
        barrier_score = horse_scores.get('barrier', {}).get('score', 0)
        barrier_details = horse_scores.get('barrier', {}).get('details', {})
        
        if barrier_score >= 0.8:
            tags.append("🎯 檔位優勢")
        elif barrier_score <= 0.3:
            tags.append("⚠️ 檔位不利")
        
        # 檔位來源標籤
        score_source = barrier_details.get('score_source', '')
        if score_source == '混合':
            tags.append("🔀 混合評分")
        elif score_source == '統計主導':
            tags.append("📊 依賴統計")
        elif score_source == '個人主導':
            tags.append("👤 個人表現")
        
        # 穩定性標籤
        stability_details = horse_scores.get('stability', {}).get('details', {})
        pattern = stability_details.get('pattern', '')
        if pattern:
            tags.append(pattern)
        
        # 趨勢標籤
        trend_details = horse_scores.get('trend', {}).get('details', {})
        trend = trend_details.get('trend', '')
        if trend == '📈 狀態上升':
            tags.append("📈 近況佳")
        elif trend == '📉 狀態下降':
            tags.append("📉 近況差")
        
        # 一致性標籤
        consistency_details = horse_scores.get('consistency', {}).get('details', {})
        rating = consistency_details.get('rating', '')
        if rating == '⭐ 表現穩定':
            tags.append("✅ 穩定")
        elif rating == '⚠️ 波動較大':
            tags.append("⚠️ 不穩")
        
        return tags
    
    except Exception as e:
        logger.error(f"生成標籤失敗: {e}", exc_info=True)
        return []


def render_enhanced_ranking_table(scored_horses):
    """
    渲染增強版排名表（帶標籤）
    
    Args:
        scored_horses: 評分後的馬匹列表
    """
    st.subheader("🏆 評分排名表（增強版）")
    
    ranking_data = []
    for rank, horse in enumerate(scored_horses, 1):
        scores = horse['scores']
        tags = generate_horse_recommendation_tags(scores)
        
        ranking_data.append({
            '排名': rank,
            '馬名': horse.get('horse_name', '未知'),
            '檔位': horse.get('barrier'),
            '總分': f"{scores.get('total_score', 0):.3f}",
            '評級': scores.get('grade', 'N/A'),
            '推薦標籤': ' | '.join(tags),
            '檔位': f"{scores.get('barrier', {}).get('score', 0):.3f}",
            '距離': f"{scores.get('distance', {}).get('score', 0):.3f}",
            '場地': f"{scores.get('going', {}).get('score', 0):.3f}",
            '穩定性': f"{scores.get('stability', {}).get('score', 0):.3f}",
            '趨勢': f"{scores.get('trend', {}).get('score', 0):.3f}",
            '一致性': f"{scores.get('consistency', {}).get('score', 0):.3f}"
        })
    
    ranking_df = pd.DataFrame(ranking_data)
    
    # 使用顏色標記高分
    def highlight_top_scores(val):
        try:
            if isinstance(val, str) and val.replace('.', '').isdigit():
                score = float(val)
                if score >= 0.75:
                    return 'background-color: #d4edda'  # 綠色
                elif score >= 0.65:
                    return 'background-color: #fff3cd'  # 黃色
                elif score <= 0.40:
                    return 'background-color: #f8d7da'  # 紅色
        except:
            pass
        return ''
    
    styled_df = ranking_df.style.applymap(
        highlight_top_scores,
        subset=['總分', '檔位', '距離', '場地', '穩定性', '趨勢', '一致性']
    )
    
    st.dataframe(styled_df, use_container_width=True)


def compare_horses(horse1_scores, horse2_scores, horse1_name, horse2_name):
    """
    比較兩匹馬的評分
    
    Args:
        horse1_scores: 第一匹馬的評分
        horse2_scores: 第二匹馬的評分
        horse1_name: 第一匹馬名
        horse2_name: 第二匹馬名
    
    Returns:
        dict: 比較結果
    """
    comparison = {
        'horse1_name': horse1_name,
        'horse2_name': horse2_name,
        'total_score': {
            'horse1': horse1_scores.get('total_score', 0),
            'horse2': horse2_scores.get('total_score', 0),
            'winner': horse1_name if horse1_scores.get('total_score', 0) > horse2_scores.get('total_score', 0) else horse2_name
        },
        'barrier': {
            'horse1': horse1_scores.get('barrier', {}).get('score', 0),
            'horse2': horse2_scores.get('barrier', {}).get('score', 0),
            'winner': horse1_name if horse1_scores.get('barrier', {}).get('score', 0) > horse2_scores.get('barrier', {}).get('score', 0) else horse2_name
        },
        'distance': {
            'horse1': horse1_scores.get('distance', {}).get('score', 0),
            'horse2': horse2_scores.get('distance', {}).get('score', 0),
            'winner': horse1_name if horse1_scores.get('distance', {}).get('score', 0) > horse2_scores.get('distance', {}).get('score', 0) else horse2_name
        },
        'going': {
            'horse1': horse1_scores.get('going', {}).get('score', 0),
            'horse2': horse2_scores.get('going', {}).get('score', 0),
            'winner': horse1_name if horse1_scores.get('going', {}).get('score', 0) > horse2_scores.get('going', {}).get('score', 0) else horse2_name
        }
    }
    
    return comparison


def render_horse_comparison_tool(scored_horses):
    """
    渲染馬匹比較工具
    
    Args:
        scored_horses: 評分後的馬匹列表
    """
    st.subheader("⚖️ 馬匹對比工具")
    
    if len(scored_horses) < 2:
        st.warning("⚠️ 至少需要 2 匹馬才能比較")
        return
    
    horse_names = [h.get('horse_name', f"馬 {i+1}") for i, h in enumerate(scored_horses)]
    
    col1, col2 = st.columns(2)
    
    with col1:
        horse1_name = st.selectbox("選擇第一匹馬", horse_names, key="compare_horse1")
    
    with col2:
        horse2_name = st.selectbox("選擇第二匹馬", horse_names, key="compare_horse2", index=1 if len(horse_names) > 1 else 0)
    
    if horse1_name == horse2_name:
        st.warning("⚠️ 請選擇不同的馬匹")
        return
    
    # 找到對應的馬匹
    horse1 = next((h for h in scored_horses if h.get('horse_name') == horse1_name), None)
    horse2 = next((h for h in scored_horses if h.get('horse_name') == horse2_name), None)
    
    if not horse1 or not horse2:
        st.error("❌ 找不到馬匹數據")
        return
    
    comparison = compare_horses(
        horse1['scores'],
        horse2['scores'],
        horse1_name,
        horse2_name
    )
    
    # 顯示比較結果
    st.write("### 📊 對比結果")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "總分",
            f"{comparison['total_score']['horse1']:.3f}",
            delta=f"{comparison['total_score']['horse1'] - comparison['total_score']['horse2']:.3f}",
            help=horse1_name
        )
    
    with col2:
        st.write("**VS**")
    
    with col3:
        st.metric(
            "總分",
            f"{comparison['total_score']['horse2']:.3f}",
            help=horse2_name
        )
    
    st.write(f"**總分優勝:** {comparison['total_score']['winner']}")
    
    # 各維度對比
    st.write("### 📏 各維度對比")
    
    dimensions = ['檔位適應', '距離適應', '場地適應']
    keys = ['barrier', 'distance', 'going']
    
    for dim, key in zip(dimensions, keys):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(dim, f"{comparison[key]['horse1']:.3f}", help=horse1_name)
        
        with col2:
            st.write("**VS**")
        
        with col3:
            st.metric(dim, f"{comparison[key]['horse2']:.3f}", help=horse2_name)
        
        st.write(f"**{dim}優勝:** {comparison[key]['winner']}")
        st.markdown("---")


# ============================================================
# 🧪 測試和調試工具 (Development Only)
# ============================================================

def test_draw_statistics_integration():
    """
    測試檔位統計整合功能
    """
    st.subheader("🧪 檔位統計整合測試")
    
    try:
        from db_manager import DatabaseManager
        
        db = DatabaseManager()
        latest_date = db.get_latest_date()
        
        if latest_date:
            all_races = db.get_all_races_for_date(latest_date)
            
            st.write(f"**測試日期:** {latest_date}")
            st.write(f"**場次數:** {len(all_races)}")
            
            # 測試每場的場次號匹配
            test_results = []
            for race_num, race_data in all_races.items():
                actual_race_num = race_data.get('race_num')
                match = race_num == actual_race_num
                
                test_results.append({
                    '字典 Key': race_num,
                    '實際 race_num': actual_race_num,
                    '匹配狀態': '✅ 通過' if match else '❌ 失敗',
                    '統計數': len(race_data.get('statistics', []))
                })
            
            test_df = pd.DataFrame(test_results)
            st.dataframe(test_df, use_container_width=True)
            
            # 統計
            pass_count = sum(1 for r in test_results if '✅' in r['匹配狀態'])
            
            if pass_count == len(test_results):
                st.success(f"✅ 全部 {pass_count} 場測試通過！")
            else:
                st.error(f"❌ {len(test_results) - pass_count} 場測試失敗")
        
        else:
            st.warning("⚠️ 數據庫無數據")
    
    except Exception as e:
        st.error(f"❌ 測試失敗: {str(e)}")
        logger.error(f"測試失敗: {e}", exc_info=True)


# ============================================================
# 🔒 版本信息和日誌
# ============================================================

__version__ = "3.10.0"
__author__ = "Racing Analysis Team"
__update_date__ = "2026-01-12"
__features__ = [
    "排位表爬蟲",
    "往績爬蟲",
    "賽次詳細信息",
    "跑法預測分析",
    "配腳評分分析 (v3.10)",
    "檔位統計整合 (v3.10)",
    "防混淆驗證 (v3.10)",
    "混合評分詳情 (v3.10)",
    "智能推薦標籤",
    "馬匹對比工具",
    "評分統計面板",
    "CSV 導出功能"
]

logger.info(f"✅ page_racecard.py v{__version__} 已加載")
logger.info(f"✅ 功能列表: {', '.join(__features__)}")
