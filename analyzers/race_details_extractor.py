# -*- coding: utf-8 -*-

"""
HKJC 排位表分析器 v2.1 - 集成賽次詳細信息提取
Racecard Analyzer v2.1 - With Race Details Extraction

新增功能:
- 提取賽次詳細信息 (日期、馬場、跑道、場地、途程、班次等)
- 篩選顯示欄位
- 返回完整結構化數據
"""

import re
import logging
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RaceDetailsExtractor:
    """賽次詳細信息提取"""
    
    BASE_URL = "https://racing.hkjc.com/zh-hk/local/information/racecard"
    
    def __init__(self, timeout=15):
        self.timeout = timeout
        self.session = requests.Session()
    
    def extract_race_details(self, race_date: str, racecourse: str, race_no: int) -> Dict:
        """
        完整的賽次詳細信息提取
        
        Args:
            race_date: "2026/01/07"
            racecourse: "HV" 或 "ST"
            race_no: 1-9
        
        Returns:
            {
                'status': 'success',
                'race_details': {
                    'race_number': '1',
                    'race_name': '美利讓賽',
                    'date': '2026年1月7日',
                    'day_of_week': '星期三',
                    'venue': '跑馬地',
                    'time': '18:40',
                    'track_type': '草地',
                    'track_rating': 'A',
                    'distance': '1800',
                    'going': '好地',
                    'prize_money': '875000',
                    'rating_range': '40-0',
                    'class': '第五班'
                }
            }
        """
        
        try:
            url = f"{self.BASE_URL}?racedate={race_date}&Racecourse={racecourse}&RaceNo={race_no}"
            logger.info(f"🔍 提取賽次詳細信息: {url}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            race_details = self._extract_details(soup)
            
            return {
                'status': 'success',
                'url': url,
                'race_details': race_details
            }
        
        except Exception as e:
            logger.error(f"❌ 提取失敗: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _extract_details(self, soup: BeautifulSoup) -> Dict:
        """從 HTML 中提取所有詳細信息"""
        
        details = {}
        all_text = soup.get_text(separator=' ')
        
        # ====================================================================
        # 賽次標題 (第 1 場 - 美利讓賽)
        # ====================================================================
        match = re.search(r'第\s*(\d+)\s*場\s*[－-]?\s*(.+?)(?=\d{4}年|\n|$)', all_text)
        if match:
            details['race_number'] = match.group(1).strip()
            details['race_name'] = match.group(2).strip()
        
        # ====================================================================
        # 日期和時間
        # ====================================================================
        
        # 日期 (2026年1月7日)
        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', all_text)
        if match:
            details['date'] = f"{match.group(1)}年{match.group(2)}月{match.group(3)}日"
        
        # 星期幾
        match = re.search(r'(星期[一二三四五六日])', all_text)
        if match:
            details['day_of_week'] = match.group(1)
        
        # 馬場 (跑馬地|沙田)
        if '跑馬地' in all_text:
            details['venue'] = '跑馬地'
        elif '沙田' in all_text:
            details['venue'] = '沙田'
        
        # 時間 (18:40)
        match = re.search(r'(\d{2}):(\d{2})', all_text)
        if match:
            details['time'] = f"{match.group(1)}:{match.group(2)}"
        
        # ====================================================================
        # 賽道資料
        # ====================================================================
        
        # 賽道類型 (草地|全天候)
        if re.search(r'草地(?!賽)', all_text):
            details['track_type'] = '草地'
        elif '全天候' in all_text:
            details['track_type'] = '全天候'
        
        # 賽道等級 ("A", "B", "C+3" 等)
        match = re.search(r'["\"]([A-Z]+(?:\+\d+)?)["\"]', all_text)
        if match:
            details['track_rating'] = match.group(1)
        
        # 距離 (1800米)
        match = re.search(r'(\d{4})米', all_text)
        if match:
            details['distance'] = match.group(1)
        
        # 場地狀況 (好地|好/快 等)
        match = re.search(r'(好地|好/快|快地|濡地|爛地)', all_text)
        if match:
            details['going'] = match.group(1)
        
        # ====================================================================
        # 賽事資料
        # ====================================================================
        
        # 獎金 ($875,000)
        match = re.search(r'\$\s*([\d,]+)', all_text)
        if match:
            details['prize_money'] = match.group(1).replace(',', '')
        
        # 評分範圍 (40-0)
        match = re.search(r'評分:\s*(\d+)[～-](\d+)', all_text)
        if match:
            details['rating_range'] = f"{match.group(1)}-{match.group(2)}"
        
        # 班次 (第五班)
        match = re.search(r'(第[一二三四五六]班|\d班)', all_text)
        if match:
            details['class'] = match.group(1)
        
        return details
    
    def get_display_fields(self, race_details: Dict) -> Dict:
        """
        篩選並返回顯示需要的欄位
        
        顯示欄位:
        - 場次: race_number
        - 日期: date
        - 馬場: venue
        - 跑道: track_type + track_rating (合併)
        - 場地: going
        - 途程: distance
        - 班次: class
        """
        
        # 合併跑道信息
        track_info = ""
        if 'track_type' in race_details and 'track_rating' in race_details:
            track_info = f"{race_details['track_type']} \"{race_details['track_rating']}\" 賽道"
        elif 'track_type' in race_details:
            track_info = race_details['track_type']
        
        display_fields = {
            'race_number': race_details.get('race_number', ''),
            'date': race_details.get('date', ''),
            'venue': race_details.get('venue', ''),
            'track_info': track_info,
            'track_type': race_details.get('track_type', ''),
            'track_rating': race_details.get('track_rating', ''),
            'going': race_details.get('going', ''),
            'distance': race_details.get('distance', ''),
            'class': race_details.get('class', '')
        }
        
        return display_fields


if __name__ == "__main__":
    extractor = RaceDetailsExtractor(timeout=15)
    
    result = extractor.extract_race_details("2026/01/07", "HV", 1)
    
    print("\n" + "="*80)
    print("📋 提取結果 - 全部信息")
    print("="*80)
    
    if result['status'] == 'success':
        print("\n✅ 提取成功！\n")
        for key, value in sorted(result['race_details'].items()):
            print(f"  {key:20s}: {value}")
        
        # 顯示篩選後的欄位
        print("\n" + "="*80)
        print("📊 顯示欄位 (篩選)")
        print("="*80 + "\n")
        
        display_fields = extractor.get_display_fields(result['race_details'])
        print("  場次            :", display_fields['race_number'])
        print("  日期            :", display_fields['date'])
        print("  馬場            :", display_fields['venue'])
        print("  跑道            :", display_fields['track_info'])
        print("  場地            :", display_fields['going'])
        print("  途程            :", display_fields['distance'] + "米")
        print("  班次            :", display_fields['class'])
    
    else:
        print(f"\n❌ 提取失敗: {result['error']}")
