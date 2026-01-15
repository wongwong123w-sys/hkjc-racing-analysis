# -*- coding: utf-8 -*-
"""
賽馬資料爬取器 v2 - 動態賽馬場偵測版本
HKJC Race Crawler v2 - Dynamic Racecourse Detection

✅ 自動從網頁偵測賽馬場 (沙田/跑馬地)
✅ 動態產生報告頭 (不寫死馬場名稱)
✅ 支持全天候跑道和草地跑道
✅ 自動檢測新馬賽/班次
"""

import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import os
from typing import Optional, Dict, List, Tuple

def first_float_clean(txt: str) -> str:
    """從文字中提取第一個浮點數，若過長只取前5字元（保留兩位小數的秒數格式）"""
    nums = re.findall(r"\d+\.\d+(?:\d+)?", txt)
    if not nums:
        return ""
    raw = nums[0]
    if len(raw) > 5:
        raw = raw[:5]
    return raw

def extract_racecourse(soup: BeautifulSoup) -> str:
    """
    從網頁內容中動態偵測賽馬場
    
    Returns:
        str: 賽馬場名稱 ("沙田", "跑馬地", 或 "未知")
    """
    # 方法1: 查找頁面標題或主要文字
    page_text = soup.get_text()
    
    if '跑馬地' in page_text or 'Happy Valley' in page_text:
        return '跑馬地'
    elif '沙田' in page_text or 'Sha Tin' in page_text:
        return '沙田'
    
    # 方法2: 查找 URL 中的線索
    # (如果需要可以在這裡檢查 request URL)
    
    return '未知'

def extract_track_type(soup: BeautifulSoup) -> str:
    """
    從網頁內容中偵測跑道類型
    
    Returns:
        str: "草地" 或 "全天候"
    """
    page_text = soup.get_text()
    
    if '全天候' in page_text or 'All-Weather' in page_text:
        return '全天候'
    
    return '草地'

def make_report(race_date: str, race_no: int, save_csv: bool = False, print_report: bool = True):
    """
    爬取單場賽事資料，並存成CSV（可選）。
    
    Args:
        race_date: 賽事日期 (格式: "30/10/2025")
        race_no: 場次編號 (1-9)
        save_csv: 是否儲存為 CSV
        print_report: 是否印出報告
    
    Returns:
        dict: 包含爬取結果的字典
    """
    
    # 1. 爬取網頁
    url = (
        "https://racing.hkjc.com/racing/information/Chinese/Racing/DisplaySectionalTime.aspx"
        f"?RaceDate={race_date}&RaceNo={race_no}"
    )
    
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")
    
    wrapper = soup.find("div", class_="dispalySectionalTime")
    if wrapper is None:
        print(f"第{race_no}場：找不到dispalySectionalTime區塊")
        return None
    
    # ✨ 新增：動態偵測賽馬場
    racecourse = extract_racecourse(soup)
    track_type = extract_track_type(soup)
    
    # 2. 賽事基本資料
    info_block = wrapper.find("div", class_="Race")
    if info_block:
        info_text = info_block.get_text("\n", strip=True)
        m_classline = re.search(r"第五班.*|第四班.*|第三班.*|第二班.*|第一班.*|新馬.*|一級賽.*|二級賽.*|三級賽.*", info_text)
        race_info_line = m_classline.group() if m_classline else info_text.split("\n")[0]
    else:
        race_info_line = "賽事資料未找到"
    
    race_name = ""
    if info_block:
        for ln in info_block.get_text("\n", strip=True).split("\n"):
            if "讓賽" in ln or "盃" in ln or "杯" in ln:
                race_name = ln.strip()
                break
    
    if not race_name:
        race_name = "（賽事名稱未能自動辨識）"
    
    # 3. 分段時間小表（Table 2）
    tables = wrapper.find_all("table")
    if len(tables) < 3:
        print(f"第{race_no}場：找不到分段時間小表")
        return None
    
    time_table = tables[2]
    time_rows = time_table.find_all("tr")
    head_times = [c.get_text(strip=True) for c in time_rows[0].find_all("td")]
    seg_times = [c.get_text(strip=True) for c in time_rows[1].find_all("td")]
    
    time_marks = head_times[1:]
    section_times = [first_float_clean(s) for s in seg_times[1:]]
    section_count = len(section_times)
    
    t_fin_mark = time_marks[-1]
    t_fin_value = t_fin_mark.strip("()")
    
    # 4. 各馬匹分段（Table 3）
    if len(tables) < 4:
        print(f"第{race_no}場：找不到馬匹分段主表")
        return None
    
    section_table = tables[3]
    rows = section_table.find_all("tr")
    seg_header_cells = rows[2].find_all(["th", "td"])
    segment_count = len(seg_header_cells)
    horse_rows = rows[3:]
    
    def parse_section_td(td):
        ps = td.find_all("p")
        pos = ""
        main_time = ""
        if ps:
            first_text = ps[0].get_text(" ", strip=True)
            if first_text:
                pos = first_text.split()[0]
            text_all = " ".join(p.get_text(" ", strip=True) for p in ps[1:])
            mt = first_float_clean(text_all)
            if mt:
                main_time = mt
        else:
            txt = td.get_text(" ", strip=True)
            if txt:
                pos = txt.split()[0]
            mt = first_float_clean(txt)
            if mt:
                main_time = mt
        return pos, main_time
    
    horses = []
    for row in horse_rows:
        tds = row.find_all("td")
        if not tds:
            continue
        
        rank = tds[0].get_text(strip=True)
        horse_no = tds[1].get_text(strip=True)
        horse_name = tds[2].get_text(strip=True).replace("\xa0", " ")
        finish_time = tds[-1].get_text(strip=True)
        
        seg_tds = tds[3:3 + segment_count]
        seg_positions = []
        seg_times_clean = []
        
        for seg_td in seg_tds:
            pos, tval = parse_section_td(seg_td)
            seg_positions.append(pos)
            seg_times_clean.append(tval)
        
        trip = "-".join(seg_positions).replace(" ", "")
        
        horse_data = {
            "名次": rank,
            "馬號": horse_no,
            "馬名": horse_name,
            "完成時間": finish_time,
            "沿途走位": trip,
        }
        
        for i, tval in enumerate(seg_times_clean, start=1):
            horse_data[f"第{i}段時間"] = tval
        
        horses.append(horse_data)
    
    # 5. 儲存資料成 CSV
    if save_csv and horses:
        d, m, y = race_date.split("/")
        date_key = f"{y}{m}{d}"
        csv_filename = f"sectional_{date_key}_{race_no}.csv"
        
        # ✨ 改進：產生文字內容包括一、二、三要素，賽馬場動態取得
        lines = []
        
        # 📌 第一行：動態使用偵測到的賽馬場名稱
        lines.append(f"{racecourse} {race_date} 第{race_no}場完整數據整理報告\n")
        
        lines.append("一、賽事基本資料")
        lines.append(race_info_line)
        lines.append(f"跑道類型：{track_type}")
        lines.append(f"賽事名稱：{race_name}\n")
        
        lines.append("二、賽事分段時間總覽表")
        lines.append("時間標示\t對應時間\t時間說明")
        
        if section_count >= 1:
            lines.append(f"{time_marks[0]}\t{section_times[0]}秒\t第一段")
        
        if section_count >= 2:
            try:
                total_2 = float(section_times[0]) + float(section_times[1])
                lines.append(f"{time_marks[1]}\t{total_2:.2f}秒\t前兩段合計")
            except:
                lines.append(f"{time_marks[1]}\t{section_times[0]}+{section_times[1]}秒\t前兩段合計")
        
        lines.append(f"{t_fin_mark}\t{t_fin_value}\t頭馬完成時間\n")
        
        lines.append("分段時間\t時間\t時間說明")
        for i, v in enumerate(section_times, start=1):
            lines.append(f"第{i}段\t{v}\t分段{i}")
        
        # 3. 馬匹分段與位置數據
        lines.append("\n三、各馬匹分段與位置數據")
        header = ["名次", "馬號", "馬名"]
        for i in range(1, segment_count + 1):
            header.append(f"第{i}段時間")
        header.extend(["完成時間", "沿途走位"])
        
        lines.append("\t".join(header))
        
        for h in horses:
            row = [
                h["名次"],
                h["馬號"],
                h["馬名"],
            ]
            for i in range(1, segment_count + 1):
                row.append(h.get(f"第{i}段時間", ""))
            row.append(h["完成時間"])
            row.append(h["沿途走位"])
            lines.append("\t".join(row))
        
        # 寫入文件
        with open(csv_filename, "w", encoding="utf-8-sig") as f:
            f.write("\n".join(lines))
        
        print(f"✓ 已儲存：{csv_filename}")
    
    # 6. ✨ 改進：印出報告，賽馬場動態取得（不寫死）
    if print_report:
        print(f"\n{racecourse} {race_date} 第{race_no}場完整數據整理報告\n")
        
        print("一、賽事基本資料")
        print(race_info_line)
        print(f"跑道類型：{track_type}")
        print(f"賽事名稱：{race_name}\n")
        
        print("二、賽事分段時間總覽表")
        print("時間標示\t對應時間\t時間說明")
        
        if section_count >= 1:
            print(f"{time_marks[0]}\t{section_times[0]}秒\t第一段")
        
        if section_count >= 2:
            try:
                total_2 = float(section_times[0]) + float(section_times[1])
                print(f"{time_marks[1]}\t{total_2:.2f}秒\t前兩段合計")
            except:
                print(f"{time_marks[1]}\t{section_times[0]}+{section_times[1]}秒\t前兩段合計")
        
        print(f"{t_fin_mark}\t{t_fin_value}\t頭馬完成時間\n")
        
        print("分段時間\t時間\t時間說明")
        for i, v in enumerate(section_times, start=1):
            print(f"第{i}段\t{v}\t分段{i}")
        
        print("\n三、各馬匹分段與位置數據")
        header = ["名次", "馬號", "馬名"]
        for i in range(1, segment_count + 1):
            header.append(f"第{i}段時間")
        header.extend(["完成時間", "沿途走位"])
        
        print("\t".join(header))
        
        for h in horses:
            row = [
                h["名次"],
                h["馬號"],
                h["馬名"],
            ]
            for i in range(1, segment_count + 1):
                row.append(h.get(f"第{i}段時間", ""))
            row.append(h["完成時間"])
            row.append(h["沿途走位"])
            print("\t".join(row))
        
        print()
    
    return {
        "csv_filename": f"sectional_{date_key}_{race_no}.csv" if save_csv else None,
        "racecourse": racecourse,
        "track_type": track_type,
        "horse_data": horses,
        "section_times": section_times,
        "race_info": race_info_line,
        "race_name": race_name,
    }

def make_day_reports(race_date: str, max_race_no: int = 9, save_csv: bool = True, print_report: bool = True):
    """
    一次批次爬取某日全部賽事（1~max_race_no），存檔並印報告
    
    Args:
        race_date: 賽事日期 (格式: "30/10/2025")
        max_race_no: 最大場次編號 (通常是 9)
        save_csv: 是否儲存為 CSV
        print_report: 是否印出報告
    """
    results = []
    print(f"🏇 開始爬取 {race_date} 全日賽事...\n")
    
    for rn in range(1, max_race_no + 1):
        try:
            result = make_report(race_date, rn, save_csv=save_csv, print_report=print_report)
            if result:
                results.append(result)
        except Exception as e:
            print(f"❌ 第{rn}場出錯：{e}\n")
    
    print(f"\n✅ 完成！共爬取 {len(results)} 場賽事")
    return results

# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 單場爬取
    # make_report("30/10/2025", 1, save_csv=True, print_report=True)
    
    # 全日爬取
    # make_day_reports("30/10/2025", max_race_no=9, save_csv=True, print_report=True)
    pass
