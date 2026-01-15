
# -*- coding: utf-8 -*-
"""
分段時間分析頁面
Segment Time Analysis Page
"""

import streamlit as st
import re
from hkjc_sectional import load_race_from_csv, load_day_races


def render_segment_page():
    """渲染分段時間分析頁面"""
    
    st.sidebar.header("📋 查詢條件")
    race_date = st.sidebar.text_input("賽事日期 (dd/mm/yyyy)", "26/11/2025")
    max_race_no = st.sidebar.number_input("當日場次數", min_value=1, max_value=13, value=9, step=1)

    query_mode = st.sidebar.radio(
        "選擇查詢模式",
        ["📊 全日分析", "🏇 單場詳細"]
    )

    if query_mode == "📊 全日分析":
        st.subheader(f"全日分析 - {race_date}")

        if st.sidebar.button("取得全日數據", key="day_button"):
            try:
                df_all, num_races, metadata_dict = load_day_races(race_date, max_race_no)
                st.success(f"✓ 已加載 {num_races} 場賽事資料")

                st.markdown("### 📈 全日統計概覽")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("總場次", num_races)

                with col2:
                    st.metric("馬匹總數", len(df_all))

                with col3:
                    if "完成時間" in df_all.columns:
                        try:
                            avg_time = df_all["完成時間"].apply(
                                lambda x: float(str(x).replace(":", ".")) if isinstance(x, str) else None
                            ).dropna().mean()
                            st.metric("平均完成時間", f"{avg_time:.2f}")
                        except:
                            st.metric("平均完成時間", "N/A")
                    else:
                        st.metric("平均完成時間", "N/A")

                with col4:
                    if "馬名" in df_all.columns:
                        st.metric("參賽馬匹數", df_all["馬名"].nunique())
                    else:
                        st.metric("參賽馬匹數", "N/A")

                st.markdown("---")
                st.markdown("### 🏁 各場次馬匹成績")

                for race_no in sorted(df_all["場次"].unique()):
                    with st.expander(f"第 {int(race_no)} 場", expanded=False):
                        if int(race_no) in metadata_dict:
                            meta_lines = metadata_dict[int(race_no)]
                            st.text("\n".join(meta_lines))

                        st.markdown("---")
                        df_race = df_all[df_all["場次"] == race_no].copy()

                        if "名次" in df_race.columns:
                            df_race = df_race.sort_values("名次", ascending=True)

                        def extract_segment_number(name):
                            try:
                                m = re.match(r"第(\d+)段時間", name)
                                if m:
                                    return int(m.group(1))
                            except:
                                pass
                            return 999

                        main_cols = ["名次", "馬號", "馬名"]
                        seg_cols = sorted(
                            [c for c in df_race.columns if c.startswith("第") and c.endswith("時間")],
                            key=extract_segment_number
                        )
                        final_cols = ["完成時間", "沿途走位"]
                        col_order = main_cols + seg_cols + final_cols
                        cols_to_show = [c for c in col_order if c in df_race.columns]

                        st.dataframe(df_race[cols_to_show], use_container_width=True, height=400)

                st.markdown("---")
                csv_data = df_all.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="📥 下載全日數據 CSV",
                    data=csv_data,
                    file_name=f"races_{race_date.replace('/', '')}_all.csv",
                    mime="text/csv"
                )

            except Exception as e:
                st.error(f"❌ 取得數據失敗：{e}")

    else:
        st.subheader(f"單場詳細分析 - {race_date}")
        selected_race_no = st.sidebar.number_input("場次", min_value=1, max_value=13, value=1, step=1)

        if st.sidebar.button("取得單場數據", key="race_button"):
            try:
                data = load_race_from_csv(race_date, int(selected_race_no))
                st.success(f"✓ 已加載第 {int(selected_race_no)} 場")

                st.markdown("### 📋 賽事資料")
                meta_lines = data["metadata_lines"]
                st.text("\n".join(meta_lines))

                st.markdown("---")
                st.markdown(f"### 🐴 第 {int(selected_race_no)} 場 - 馬匹分段與位置")

                df_m = data["df"].copy()
                if "名次" in df_m.columns:
                    df_m = df_m.sort_values("名次", ascending=True)

                def extract_segment_number(name):
                    try:
                        m = re.match(r"第(\d+)段時間", name)
                        if m:
                            return int(m.group(1))
                    except:
                        pass
                    return 999

                main_cols = ["名次", "馬號", "馬名"]
                seg_cols = sorted(
                    [c for c in df_m.columns if c.startswith("第") and c.endswith("時間")],
                    key=extract_segment_number
                )
                final_cols = ["完成時間", "沿途走位"]
                col_order = main_cols + seg_cols + final_cols
                cols_to_show = [c for c in col_order if c in df_m.columns]

                st.dataframe(df_m[cols_to_show], use_container_width=True, height=600)

                st.markdown("---")
                csv_bytes = df_m[cols_to_show].to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label=f"📥 下載第 {int(selected_race_no)} 場 CSV",
                    data=csv_bytes,
                    file_name=f"race_{race_date.replace('/', '')}_{int(selected_race_no)}.csv",
                    mime="text/csv"
                )

            except FileNotFoundError as e:
                st.error(f"❌ 找不到 CSV 檔案：{e}")
            except Exception as e:
                st.error(f"❌ 取得數據失敗：{e}")
