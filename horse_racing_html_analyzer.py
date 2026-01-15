# -*- coding: utf-8 -*-

"""
往績表格 HTML 結構診斷工具
Racing History HTML Structure Analyzer

用途: 分析實際的 HKJC 網頁結構，找出往績表格位置和欄位
"""

import requests
from bs4 import BeautifulSoup
import json

def diagnose_horse_page(horse_id: str = "HK_2023_J411"):
    """
    完整診斷馬匹資料頁的 HTML 結構
    """
    
    url = f"https://racing.hkjc.com/zh-hk/local/information/horse?horseid={horse_id}"
    
    print(f"🔍 診斷 {horse_id}")
    print(f"URL: {url}\n")
    
    # 爬取網頁
    response = requests.get(url, timeout=15)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # ============================================================
    # 1. 列出所有表格
    # ============================================================
    print("=" * 70)
    print("1️⃣ 所有表格統計")
    print("=" * 70)
    
    tables = soup.find_all('table')
    print(f"✓ 找到 {len(tables)} 個表格\n")
    
    for idx, table in enumerate(tables):
        rows = table.find_all('tr')
        cols = len(table.find_all('th')) + len(table.find_all('td'))
        table_class = table.get('class', [])
        table_id = table.get('id', '')
        
        print(f"表 {idx}:")
        print(f"  class: {table_class}")
        print(f"  id: {table_id}")
        print(f"  行數: {len(rows)}")
        print(f"  估計欄數: {cols}")
        
        # 提取表頭
        headers = table.find_all('th')
        if headers:
            header_texts = [h.get_text(strip=True)[:15] for h in headers[:10]]
            print(f"  表頭 (前 10 欄): {header_texts}")
        
        print()
    
    # ============================================================
    # 2. 詳細分析每個表格
    # ============================================================
    print("=" * 70)
    print("2️⃣ 詳細表格分析")
    print("=" * 70 + "\n")
    
    for idx, table in enumerate(tables):
        print(f"📊 表 {idx} 詳細信息:")
        print("-" * 70)
        
        # 表格屬性
        print(f"屬性:")
        print(f"  class: {table.get('class', [])}")
        print(f"  id: {table.get('id', '')}")
        print(f"  style: {table.get('style', '')[:80]}")
        
        # 表頭
        headers = table.find_all('th')
        print(f"\n表頭 ({len(headers)} 欄):")
        for h_idx, h in enumerate(headers[:20]):
            print(f"  {h_idx}: {h.get_text(strip=True)}")
        
        # 第一行數據
        rows = table.find_all('tr')
        if len(rows) > 1:
            first_row = rows[1]
            cells = first_row.find_all('td')
            print(f"\n第一行數據 ({len(cells)} 欄):")
            for c_idx, cell in enumerate(cells[:10]):
                cell_text = cell.get_text(strip=True)[:30]
                print(f"  {c_idx}: {cell_text}")
        
        # 判斷是否可能是往績表
        header_combined = ' '.join([h.get_text(strip=True) for h in headers]).lower()
        keywords = ['場次', '名次', '日期', '馬場', '距離', '評分', '往績', 'racing', 'history']
        keyword_matches = [k for k in keywords if k.lower() in header_combined]
        
        print(f"\n可能性:")
        print(f"  行數: {len(rows)} {'✓ (有數據)' if len(rows) > 1 else '✗ (無數據)'}")
        print(f"  欄數: {len(headers)} {'✓ (可能是往績)' if 10 <= len(headers) <= 20 else '✗'}")
        print(f"  關鍵詞匹配: {keyword_matches} {'✓' if len(keyword_matches) >= 2 else '✗'}")
        
        print()
    
    # ============================================================
    # 3. 查找關鍵元素
    # ============================================================
    print("=" * 70)
    print("3️⃣ 頁面結構分析")
    print("=" * 70 + "\n")
    
    # 查找包含「往績」的文本
    all_text = soup.get_text()
    if '往績' in all_text:
        print("✓ 頁面包含「往績」文本")
    else:
        print("✗ 頁面不包含「往績」文本")
    
    # 查找 div 容器
    divs_with_history = soup.find_all('div', string=lambda x: x and '往績' in x)
    print(f"✓ 包含「往績」文本的 div: {len(divs_with_history)}")
    
    # 查找所有含有數字和日期模式的 table
    print("\n📈 可能的往績表格 (根據內容推斷):")
    for idx, table in enumerate(tables):
        rows = table.find_all('tr')
        if len(rows) < 2:
            continue
        
        # 檢查第一行是否有日期格式
        first_row = rows[1]
        row_text = first_row.get_text()
        
        if any(pattern in row_text for pattern in ['/', '-', '年', '月', '日']):
            # 可能包含日期
            headers = table.find_all('th')
            print(f"  表 {idx}: {len(rows)} 行, {len(headers)} 欄 ← 可能是往績")
    
    # ============================================================
    # 4. 匯出原始 HTML (前 3000 字符)
    # ============================================================
    print("\n" + "=" * 70)
    print("4️⃣ 第一個表格的原始 HTML")
    print("=" * 70 + "\n")
    
    if tables:
        first_table_html = str(tables[0])[:2000]
        print(first_table_html)
        print("\n[HTML 已截斷...]")
    
    # ============================================================
    # 5. 導出 JSON 供分析
    # ============================================================
    print("\n" + "=" * 70)
    print("5️⃣ 匯出診斷數據")
    print("=" * 70 + "\n")
    
    diagnosis = {
        'horse_id': horse_id,
        'total_tables': len(tables),
        'tables': []
    }
    
    for idx, table in enumerate(tables):
        rows = table.find_all('tr')
        headers = table.find_all('th')
        
        table_info = {
            'index': idx,
            'class': table.get('class', []),
            'id': table.get('id', ''),
            'row_count': len(rows),
            'header_count': len(headers),
            'headers': [h.get_text(strip=True) for h in headers[:15]],
            'first_row': [cell.get_text(strip=True)[:30] for cell in rows[1].find_all('td')[:15]] if len(rows) > 1 else []
        }
        
        diagnosis['tables'].append(table_info)
    
    # 保存為 JSON
    json_str = json.dumps(diagnosis, ensure_ascii=False, indent=2)
    print("診斷數據已導出 (JSON):")
    print(json_str[:1000])
    print("\n[JSON 已截斷...]\n")
    
    return diagnosis


if __name__ == "__main__":
    # 執行診斷
    diagnosis = diagnose_horse_page("HK_2023_J411")
    
    print("\n" + "=" * 70)
    print("💡 建議")
    print("=" * 70)
    print("""
如果往績表格仍未被找到:

1. 檢查上方輸出，找出最可能的往績表格索引
2. 根據表頭和內容判斷哪個表格是往績
3. 更新爬蟲代碼，指定正確的表格或調整匹配邏輯

常見問題:
- 往績表格可能沒有 <th> 表頭 (只有 <td>)
- 往績可能在特定的 div > table 結構中
- 表格可能有多個層級或嵌套
- 日期格式可能與預期不同

下一步: 請將診斷輸出共享，我們會基於實際 HTML 結構調整爬蟲。
    """)
