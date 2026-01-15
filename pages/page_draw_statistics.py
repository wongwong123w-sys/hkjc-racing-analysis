
# -*- coding: utf-8 -*-

"""
檔位統計頁面 - 正式版

Draw Statistics Page - Production Version

✨ 功能:
- 從馬會網站爬取檔位統計
- 完整的數據展示（1-14檔）
- CSV 導出功能
- 圖表分析
"""

import streamlit as st
from analyzers.draw_statistics_parser import DrawStatisticsParser
from analyzers.db_manager import DatabaseManager
import pandas as pd
from datetime import datetime
import time


def render_draw_statistics_page():
    """檔位統計頁面"""
    
    st.header("📊 檔位統計")
    st.write("從香港賽馬會獲取當日所有場次的檔位統計數據 (1-14檔)")
    
    # 初始化數據庫
    try:
        db = DatabaseManager()
    except Exception as e:
        st.error(f"❌ 數據庫初始化失敗: {e}")
        return
    
    # ========== 控制條 ==========
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col2:
        if st.button("🔄 更新數據", use_container_width=True, type="primary"):
            with st.spinner("🔄 正在從馬會網站爬取數據..."):
                try:
                    parser = DrawStatisticsParser()
                    result = parser.fetch_all_races()
                    
                    if result['status'] == 'success':
                        success = db.save_all_races(result['date'], result['races'])
                        
                        if success:
                            st.success(f"✅ 成功更新 {len(result['races'])} 場賽事 - {datetime.now().strftime('%H:%M:%S')}")
                            st.balloons()
                            st.info("💡 頁面將在 2 秒後刷新...")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("❌ 數據保存失敗")
                            st.info("💡 請檢查數據庫連接")
                    else:
                        st.error(f"❌ 爬取失敗")
                        st.warning(result.get('message', '未知錯誤'))
                        
                        # 提供調試信息
                        with st.expander("🔍 調試信息", expanded=False):
                            st.write(f"**錯誤訊息:** {result.get('message')}")
                            st.write(f"**日期:** {result.get('date')}")
                            st.write(f"**場次數:** {len(result.get('races', []))}")
                            st.info("💡 請查看 debug_draw_page.html 文件以診斷問題")
                
                except Exception as e:
                    st.error(f"❌ 更新錯誤: {e}")
                    st.code(str(e))
    
    with col3:
        latest_date = db.get_latest_date()
        if latest_date:
            st.info(f"📅 {latest_date}")
        else:
            st.warning("⚠️ 無數據")
    
    with col4:
        if st.button("🗑️ 清空", use_container_width=True):
            latest_date = db.get_latest_date()
            if latest_date:
                if st.session_state.get('confirm_delete'):
                    if db.delete_draw_statistics(latest_date):
                        st.success("✅ 已清空")
                        st.session_state.confirm_delete = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ 清空失敗")
                else:
                    st.session_state.confirm_delete = True
                    st.warning("⚠️ 再點一次確認刪除")
            else:
                st.warning("⚠️ 無數據")
    
    st.divider()
    
    # ========== 顯示所有場次 ==========
    latest_date = db.get_latest_date()
    
    if latest_date:
        races = db.get_all_races_for_date(latest_date)
        
        if races:
            # 頂部信息欄
            col_date, col_count, col_export = st.columns([3, 1, 1])
            
            with col_date:
                st.markdown(f"### 📅 {latest_date}")
            
            with col_count:
                st.metric("總場次", len(races))
            
            with col_export:
                if st.button("📥 匯出CSV", use_container_width=True):
                    try:
                        filename = f"draw_statistics_{latest_date}.csv"
                        if db.export_draw_statistics_csv(latest_date, filename):
                            st.success(f"✅ 已匯出")
                            st.info(f"📁 {filename}")
                        else:
                            st.error("❌ 匯出失敗")
                    except Exception as e:
                        st.error(f"❌ 匯出錯誤: {e}")
            
            st.divider()
            
            # 逐個顯示每場賽事
            for race_num in sorted(races.keys()):
                race = races[race_num]
                
                # 場次標題卡片
                st.markdown(f"""
                <div style="background: linear-gradient(90deg, #FF6B35 0%, #F7931E 100%); 
                            padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <h3 style="color: white; margin: 0;">
                        🏇 第 {race['race_num']} 場
                    </h3>
                    <p style="color: white; margin: 5px 0 0 0; font-size: 14px;">
                        📏 {race['distance']}米 · 🌿 {race['track']} · 🌤️ {race['going']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # 轉為 DataFrame
                df = pd.DataFrame(race['statistics'])
                
                if df.empty:
                    st.warning(f"⚠️ 第 {race_num} 場無數據")
                    continue
                
                # 準備顯示數據
                display_cols = ['draw', 'races_run', 'wins', 'places', 'thirds', 'fourths',
                               'win_rate', 'place_rate', 'top3_rate', 'top4_rate']
                available_cols = [col for col in display_cols if col in df.columns]
                
                # 重命名列
                rename_cols = {
                    'draw': '檔位',
                    'races_run': '出賽',
                    'wins': '冠',
                    'places': '亞',
                    'thirds': '季',
                    'fourths': '殿',
                    'win_rate': '勝率%',
                    'place_rate': '入Q%',
                    'top3_rate': '上名%',
                    'top4_rate': '前4%'
                }
                
                df_display = df[available_cols].copy().rename(columns=rename_cols)
                
                # 格式化百分比
                for col in ['勝率%', '入Q%', '上名%', '前4%']:
                    if col in df_display.columns:
                        df_display[col] = df_display[col].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
                
                # 格式化整數
                for col in ['出賽', '冠', '亞', '季', '殿']:
                    if col in df_display.columns:
                        df_display[col] = df_display[col].fillna(0).astype(int)
                
                # 顯示表格
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        '檔位': st.column_config.NumberColumn('檔位', width='small', format='%d'),
                        '出賽': st.column_config.NumberColumn('出賽', width='small'),
                        '冠': st.column_config.NumberColumn('冠', width='small'),
                        '亞': st.column_config.NumberColumn('亞', width='small'),
                        '季': st.column_config.NumberColumn('季', width='small'),
                        '殿': st.column_config.NumberColumn('殿', width='small'),
                        '勝率%': st.column_config.TextColumn('勝率%', width='small'),
                        '入Q%': st.column_config.TextColumn('入Q%', width='small'),
                        '上名%': st.column_config.TextColumn('上名%', width='small'),
                        '前4%': st.column_config.TextColumn('前4%', width='small'),
                    }
                )
                
                # 統計指標卡片
                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                
                with col_s1:
                    total_runs = int(df['races_run'].sum()) if 'races_run' in df.columns else 0
                    st.metric("總出賽", f"{total_runs:,}")
                
                with col_s2:
                    total_wins = int(df['wins'].sum()) if 'wins' in df.columns else 0
                    st.metric("總冠軍", f"{total_wins}")
                
                with col_s3:
                    avg_win_rate = df['win_rate'].mean() if 'win_rate' in df.columns else 0
                    st.metric("平均勝率", f"{avg_win_rate:.1f}%")
                
                with col_s4:
                    best_draw = df.loc[df['win_rate'].idxmax(), 'draw'] if 'win_rate' in df.columns and not df.empty else '-'
                    st.metric("最佳檔位", f"{int(best_draw)}" if isinstance(best_draw, (int, float)) else best_draw)
                
                # 圖表分析
                with st.expander(f"📊 第 {race_num} 場 · 圖表分析", expanded=False):
                    if 'win_rate' in df.columns and 'draw' in df.columns:
                        tab1, tab2, tab3 = st.tabs(["📈 勝率分布", "📊 出賽統計", "🏆 冠軍次數"])
                        
                        with tab1:
                            chart_df = df[['draw', 'win_rate']].set_index('draw')
                            st.bar_chart(chart_df, height=250, use_container_width=True)
                        
                        with tab2:
                            if 'races_run' in df.columns:
                                chart_df2 = df[['draw', 'races_run']].set_index('draw')
                                st.bar_chart(chart_df2, height=250, use_container_width=True)
                        
                        with tab3:
                            if 'wins' in df.columns:
                                chart_df3 = df[['draw', 'wins']].set_index('draw')
                                st.bar_chart(chart_df3, height=250, use_container_width=True)
                    else:
                        st.info("數據不足，無法顯示圖表")
                
                st.divider()
            
            # 整體統計摘要
            with st.expander("📈 整體統計摘要", expanded=False):
                total_races = len(races)
                total_draws = sum(len(race['statistics']) for race in races.values())
                total_all_runs = sum(
                    sum(s.get('races_run', 0) for s in race['statistics']) 
                    for race in races.values()
                )
                total_all_wins = sum(
                    sum(s.get('wins', 0) for s in race['statistics']) 
                    for race in races.values()
                )
                
                col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
                
                with col_sum1:
                    st.metric("總場次", total_races)
                
                with col_sum2:
                    st.metric("總檔位數", total_draws)
                
                with col_sum3:
                    st.metric("總出賽次數", f"{total_all_runs:,}")
                
                with col_sum4:
                    overall_win_rate = (total_all_wins / total_all_runs * 100) if total_all_runs > 0 else 0
                    st.metric("整體勝率", f"{overall_win_rate:.2f}%")
        
        else:
            st.info("📌 該日期暫無數據")
    
    else:
        # 無數據時的引導頁面
        st.info("📌 暫無數據，請點擊「🔄 更新數據」從馬會網站爬取")
        
        st.markdown("""
        ### 🔄 使用說明
        
        1. **點擊「更新數據」** - 從馬會網站爬取最新的檔位統計
        2. **檢查日期** - 確認爬取的是正確日期的數據
        3. **查看統計** - 瀏覽所有場次的1-14檔統計數據
        4. **匯出CSV** - 將數據導出為CSV文件進行進一步分析
        
        ### ⚠️ 注意事項
        
        - 檔位統計通常在**賽事前幾天**才會公布
        - 如果顯示「未找到數據」，可能是還沒到公布時間
        - 確保網絡連接正常
        """)
        
        # 數據庫狀態
        with st.expander("💾 數據庫狀態", expanded=False):
            stats = db.get_statistics()
            
            col_db1, col_db2, col_db3, col_db4 = st.columns(4)
            
            with col_db1:
                st.metric("排位表", stats.get('racecard_count', 0))
            
            with col_db2:
                st.metric("檔位統計", stats.get('draw_statistics_count', 0))
            
            with col_db3:
                st.metric("統計日期數", stats.get('draw_dates_count', 0))
            
            with col_db4:
                st.metric("操作日誌", stats.get('log_count', 0))
            
            # 顯示所有可用日期
            all_dates = db.get_all_dates()
            if all_dates:
                st.write("**歷史數據日期:**")
                for date in all_dates[:10]:
                    st.text(f"  📅 {date}")


if __name__ == "__main__":
    render_draw_statistics_page()
