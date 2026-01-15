# -*- coding: utf-8 -*-

"""
HKJC 應用 - 數據庫監控 + 爬蟲進度面板

Database Monitoring & Crawler Progress Dashboard for HKJC

✨ 新增視覺化功能:
- 數據庫統計信息面板
- 爬蟲進度實時顯示
- 數據查詢和導出
- 日誌視圖

作者: AI Assistant
日期: 2026-01-09
版本: 1.0
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional


class DatabaseDashboard:
    """數據庫監控面板"""

    @staticmethod
    def render():
        """渲染數據庫監控面板"""
        st.markdown("### 📊 數據庫統計信息")

        db_manager = st.session_state.db_manager

        # 獲取統計信息
        stats = db_manager.get_statistics()

        # 顯示統計卡片
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="📋 排位表記錄",
                value=stats.get('racecard_count', 0),
                delta="筆"
            )

        with col2:
            st.metric(
                label="🐴 馬匹往績",
                value=stats.get('horse_history_count', 0),
                delta="筆"
            )

        with col3:
            st.metric(
                label="📝 爬蟲日誌",
                value=stats.get('log_count', 0),
                delta="筆"
            )

        # 日誌狀態分佈
        st.markdown("#### 爬蟲日誌狀態")

        log_status = stats.get('log_status', {})

        if log_status:
            status_df = pd.DataFrame([
                {
                    '狀態': status,
                    '數量': count,
                }
                for status, count in log_status.items()
            ])

            # 顯示狀態表格
            col1, col2 = st.columns(2)

            with col1:
                st.dataframe(status_df, use_container_width=True)

            with col2:
                # 狀態圖表
                st.bar_chart(status_df.set_index('狀態'), use_container_width=True)

        # 最近的排位表
        st.markdown("#### 最近爬取的排位表")

        recent_racecards = db_manager.get_all_racecards(limit=10)

        if recent_racecards:
            df = pd.DataFrame([
                {
                    '賽次 ID': rc['race_id'],
                    '日期': rc['date'],
                    '場次': rc['racecourse'],
                    '賽次': rc['race_no'],
                    '時間': rc['created_at'][:10] if rc['created_at'] else '-',
                }
                for rc in recent_racecards
            ])

            st.dataframe(df, use_container_width=True)

            # 選擇排位表查詢
            st.markdown("#### 查詢排位表詳情")

            selected_race_id = st.selectbox(
                "選擇賽次:",
                [rc['race_id'] for rc in recent_racecards],
                key="racecard_query"
            )

            if selected_race_id:
                horses = db_manager.get_racecard(selected_race_id)

                if horses:
                    st.success(f"✅ 找到 {len(horses)} 匹馬")

                    # 馬匹列表
                    horses_df = pd.DataFrame([
                        {
                            '編號': h.get('position', '-'),
                            '馬名': h.get('horse_name', '-'),
                            '騎師': h.get('jockey', '-'),
                            '評分': h.get('rating', '-'),
                            '檔位': h.get('barrier', '-'),
                        }
                        for h in horses[:20]  # 最多顯示 20 匹
                    ])

                    st.dataframe(horses_df, use_container_width=True)

                    # 導出選項
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("📥 導出為 CSV", key=f"export_{selected_race_id}"):
                            csv_file = db_manager.export_racecard_csv(
                                selected_race_id,
                                f"racecard_{selected_race_id}.csv"
                            )
                            if csv_file:
                                st.success(f"✅ 已導出: {csv_file}")

                    with col2:
                        if st.button("🗑️ 刪除此記錄", key=f"delete_{selected_race_id}"):
                            db_manager.delete_racecard(selected_race_id)
                            st.success("✅ 已刪除")
                            st.rerun()

        else:
            st.info("📭 暫無排位表數據")


class CrawlerProgressPanel:
    """爬蟲進度面板"""

    @staticmethod
    def render():
        """渲染爬蟲進度面板"""
        st.markdown("### 🔄 爬蟲進度監控")

        # 進度追蹤狀態
        if 'crawler_progress' not in st.session_state:
            st.session_state.crawler_progress = {
                'task_name': '',
                'total_items': 0,
                'completed': 0,
                'successful': 0,
                'failed': 0,
                'status': 'idle'  # idle, running, completed
            }

        progress_data = st.session_state.crawler_progress

        # 顯示進度信息
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="📋 任務",
                value=progress_data['task_name'] or "無",
                delta=""
            )

        with col2:
            st.metric(
                label="✅ 成功",
                value=progress_data['successful'],
                delta=f"/{progress_data['total_items']}"
            )

        with col3:
            st.metric(
                label="❌ 失敗",
                value=progress_data['failed'],
                delta=f"/{progress_data['total_items']}"
            )

        with col4:
            if progress_data['total_items'] > 0:
                success_rate = (progress_data['successful'] / progress_data['total_items'] * 100)
            else:
                success_rate = 0
            st.metric(
                label="📈 成功率",
                value=f"{success_rate:.1f}%",
                delta=""
            )

        # 進度條
        if progress_data['total_items'] > 0:
            progress_percent = progress_data['completed'] / progress_data['total_items']
        else:
            progress_percent = 0

        st.progress(progress_percent)

        # 狀態指示器
        st.markdown("#### 爬蟲狀態")

        col1, col2, col3 = st.columns(3)

        with col1:
            if progress_data['status'] == 'idle':
                st.info("🔵 待機中")
            elif progress_data['status'] == 'running':
                st.warning("🟡 運行中")
            elif progress_data['status'] == 'completed':
                st.success("🟢 已完成")

        with col2:
            st.metric(
                label="⏱️ 已完成",
                value=progress_data['completed'],
                delta=f"{progress_percent*100:.0f}%"
            )

        with col3:
            st.metric(
                label="⏳ 剩餘",
                value=progress_data['total_items'] - progress_data['completed'],
                delta=f"{(1-progress_percent)*100:.0f}%"
            )

        # 詳細日誌
        st.markdown("#### 📝 爬蟲日誌")

        db_manager = st.session_state.db_manager

        # 查詢最近的日誌
        cursor = db_manager.cursor
        cursor.execute(
            'SELECT operation, status, message, created_at FROM crawler_logs ORDER BY created_at DESC LIMIT 20'
        )
        logs = cursor.fetchall()

        if logs:
            logs_df = pd.DataFrame([
                {
                    '操作': log['operation'],
                    '狀態': log['status'],
                    '信息': log['message'][:50] if log['message'] else '-',
                    '時間': log['created_at'][:10] if log['created_at'] else '-',
                }
                for log in logs
            ])

            # 狀態顏色映射
            def color_status(status):
                if status == 'success':
                    return '✅ 成功'
                elif status == 'failure':
                    return '❌ 失敗'
                else:
                    return '⚠️ 警告'

            logs_df['狀態'] = logs_df['狀態'].apply(color_status)

            st.dataframe(logs_df, use_container_width=True, height=400)

        else:
            st.info("📭 暫無日誌記錄")


class SystemMonitor:
    """系統監控面板"""

    @staticmethod
    def render():
        """渲染系統監控面板"""
        st.markdown("### 🖥️ 系統狀態監控")

        db_manager = st.session_state.db_manager

        # 數據庫連接狀態
        col1, col2, col3 = st.columns(3)

        with col1:
            if db_manager.connection:
                st.success("✅ 數據庫已連接")
            else:
                st.error("❌ 數據庫未連接")

        with col2:
            st.metric(
                label="💾 數據庫",
                value="hkjc_data.db",
                delta=""
            )

        with col3:
            import os
            db_size = os.path.getsize(db_manager.db_path) / 1024  # KB
            st.metric(
                label="📊 文件大小",
                value=f"{db_size:.1f}",
                delta="KB"
            )

        # 系統時間
        st.markdown("#### 系統信息")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                label="⏰ 當前時間",
                value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                delta=""
            )

        with col2:
            st.metric(
                label="🔌 應用版本",
                value="v12.1",
                delta=""
            )

        # 健康檢查
        st.markdown("#### 🏥 健康檢查")

        checks = {
            '數據庫連接': db_manager.connection is not None,
            '排位表表': False,
            '馬匹往績表': False,
            '日誌表': False,
        }

        try:
            db_manager.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in db_manager.cursor.fetchall()]
            checks['排位表表'] = 'racecards' in tables
            checks['馬匹往績表'] = 'horse_histories' in tables
            checks['日誌表'] = 'crawler_logs' in tables
        except:
            pass

        col1, col2 = st.columns(2)

        for i, (check_name, status) in enumerate(checks.items()):
            if i % 2 == 0:
                col = col1
            else:
                col = col2

            with col:
                if status:
                    st.success(f"✅ {check_name}: 正常")
                else:
                    st.error(f"❌ {check_name}: 異常")


def render_database_page():
    """渲染數據庫監控完整頁面"""
    st.title("💾 數據庫監控中心")

    # 頁籤
    tab1, tab2, tab3 = st.tabs([
        "📊 數據庫面板",
        "🔄 爬蟲進度",
        "🖥️ 系統監控"
    ])

    with tab1:
        DatabaseDashboard.render()

    with tab2:
        CrawlerProgressPanel.render()

    with tab3:
        SystemMonitor.render()


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 初始化 Streamlit session state
    if 'db_manager' not in st.session_state:
        from analyzers.db_manager import DatabaseManager
        st.session_state.db_manager = DatabaseManager('hkjc_data.db')

    # 渲染頁面
    render_database_page()
