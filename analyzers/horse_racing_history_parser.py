# -*- coding: utf-8 -*-

"""
馬匹往績爬蟲模塊 (v3.0 - 終極修復版)
Horse Racing History Parser - Ultimate Fix

針對 HKJC 實際 HTML 結構進行的精確適配
"""

import re
import logging
from typing import Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HorseRacingHistoryParser:
    """馬匹往績爬蟲 (v3.0)"""
    
    # 往績表格欄位對應 (19 欄 - 根據實際網頁結構)
    RACING_HISTORY_FIELDS = {
        0: 'race_no',           # 場次 (e.g., 230)
        1: 'position',          # 名次 (e.g., 12)
        2: 'date',              # 日期 (e.g., 03/12/25)
        3: 'venue',             # 馬場/跑道/賽道 (e.g., 跑馬地草地"C+3")
        4: 'distance',          # 途程 (e.g., 1200)
        5: 'condition',         # 場地狀況 (e.g., 好)
        6: 'race_class',        # 賽事班次 (e.g., 4)
        7: 'barrier',           # 檔位 (e.g., 5)
        8: 'rating',            # 評分 (e.g., 44)
        9: 'trainer',           # 練馬師 (e.g., 葉楚航)
        10: 'jockey',           # 騎師 (e.g., 鍾易禮)
        11: 'winning_distance', # 頭馬距離 (e.g., 15)
        12: 'win_odds',         # 獨贏賠率 (e.g., 126)
        13: 'actual_weight',    # 實際負磅 (e.g., 119)
        14: 'going',            # 沿途走位 (e.g., 11 12 12)
        15: 'finishing_time',   # 完成時間 (e.g., 1.12.16)
        16: 'stable_weight',    # 排位體重 (e.g., 1177)
        17: 'gear',             # 配備 (e.g., B2)
        18: 'video_replay'      # 賽事重播
    }
    
    BASE_URL = "https://racing.hkjc.com/zh-hk/local/information/horse"
    
    def __init__(self, timeout=15, retry=5):
        self.timeout = timeout
        self.retry = retry
        self.session = self._create_session()
    
    def _create_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=self.retry,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def fetch_horse_racing_history(self, horse_id: str, max_races: Optional[int] = None) -> Dict:
        try:
            url = f"{self.BASE_URL}?horseid={horse_id}"
            logger.info(f"爬取馬匹往績: {horse_id}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取往績 (v3.0 邏輯)
            racing_history = self._extract_history_v3(soup)
            
            if max_races:
                racing_history = racing_history[:max_races]
            
            return {
                'horse_id': horse_id,
                'status': 'success',
                'racing_history': racing_history,
                'total_races': len(racing_history)
            }
        
        except Exception as e:
            logger.error(f"爬取 {horse_id} 失敗: {str(e)}")
            return {
                'horse_id': horse_id,
                'status': 'error',
                'racing_history': [],
                'error': str(e)
            }
    
    def _extract_history_v3(self, soup: BeautifulSoup) -> List[Dict]:
        """
        v3.0 提取邏輯 - 針對 class="bigborder" 表格
        """
        racing_history = []
        
        # 根據你的診斷，表 9 (class="bigborder") 是最可能的往績表
        # 特徵: 有多行，第一行包含 "25/26馬季"
        
        tables = soup.find_all('table', {'class': 'bigborder'})
        logger.info(f"找到 {len(tables)} 個 bigborder 表格")
        
        target_table = None
        
        # 1. 優先嘗試 class="bigborder"
        if tables:
            target_table = tables[0]
            logger.info("使用第一個 bigborder 表格")
        else:
            # 2. 備選方案: 尋找包含大量行的表格
            all_tables = soup.find_all('table')
            for t in all_tables:
                rows = t.find_all('tr')
                # 往績表通常行數較多且包含日期
                if len(rows) > 5 and self._has_date_in_rows(rows):
                    target_table = t
                    logger.info("使用行數匹配的備選表格")
                    break
        
        if not target_table:
            logger.warning("未找到合適的往績表格")
            return []
            
        # 解析表格行
        rows = target_table.find_all('tr')
        logger.info(f"表格共有 {len(rows)} 行")
        
        for row in rows:
            cells = row.find_all('td')
            
            # 跳過空行或分隔行 (如 "25/26馬季")
            if len(cells) < 10:  # 往績行至少有 10+ 欄
                continue
                
            # 解析數據
            race_data = {}
            valid_row = True
            
            for col_idx, field_name in self.RACING_HISTORY_FIELDS.items():
                if col_idx < len(cells):
                    cell_text = cells[col_idx].get_text(strip=True)
                    
                    # 特殊處理: 日期標準化
                    if field_name == 'date':
                        cell_text = self._normalize_date(cell_text)
                    
                    race_data[field_name] = cell_text
                else:
                    race_data[field_name] = ''
            
            # 驗證關鍵欄位 (場次、名次、日期)
            if race_data.get('race_no') and race_data.get('position') and race_data.get('date'):
                # 過濾非數字的名次 (如 "WV", "WX" 等退賽馬)
                # if not race_data['position'].isdigit():
                #     continue
                
                racing_history.append(race_data)
                logger.debug(f"✓ 提取: {race_data['date']} 第 {race_data['position']} 名")
        
        logger.info(f"成功提取 {len(racing_history)} 筆往績")
        return racing_history

    def _has_date_in_rows(self, rows) -> bool:
        """檢查行中是否包含日期格式"""
        for row in rows[:5]:  # 檢查前 5 行
            text = row.get_text()
            if re.search(r'\d{2}/\d{2}/\d{2}', text):
                return True
        return False
    
    def _normalize_date(self, date_str: str) -> str:
        """標準化日期格式"""
        # 移除非日期字符
        clean_date = re.sub(r'[^\d/]', '', date_str)
        return clean_date
    
    def close(self):
        if self.session:
            self.session.close()


if __name__ == "__main__":
    parser = HorseRacingHistoryParser(timeout=15, retry=5)
    horse_id = "HK_2023_J411"
    result = parser.fetch_horse_racing_history(horse_id, max_races=6)
    
    if result['status'] == 'success':
        print(f"✅ 成功爬取 {horse_id}")
        print(f"往績數: {result['total_races']}")
        for race in result['racing_history'][:3]:
            print(f"  - {race['date']}: 第 {race['position']} 位 ({race['venue']})")
    else:
        print(f"❌ 失敗: {result['error']}")
    
    parser.close()
