# -*- coding: utf-8 -*-

"""
HKJC 排位表詳細賽次信息提取器 v2.0 (HTML 結構分析版)
Race Details Extractor v2.0 - HTML Structure Analysis

改進:
1. 直接解析完整 HTML
2. 查找所有可能的容器 (div, section, span 等)
3. 提取屬性信息 (class, id, data-* 等)
4. 詳細日誌輸出 HTML 結構
5. 多策略提取
"""

import re
import logging
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class RaceDetailsExtractorV2:
    """賽次詳細信息提取 v2.0 - HTML 結構分析"""
    
    BASE_URL = "https://racing.hkjc.com/zh-hk/local/information/racecard"
    
    def __init__(self, timeout=15):
        self.timeout = timeout
        self.session = requests.Session()
    
    def extract_race_details(self, race_date: str, racecourse: str, race_no: int) -> Dict:
        """完整的賽次詳細信息提取"""
        
        try:
            url = f"{self.BASE_URL}?racedate={race_date}&Racecourse={racecourse}&RaceNo={race_no}"
            logger.info(f"\n{'='*80}")
            logger.info(f"🔍 提取賽次詳細信息")
            logger.info(f"URL: {url}")
            logger.info(f"{'='*80}\n")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 1. 分析頁面結構
            logger.info("\n📊 頁面結構分析...")
            self._analyze_page_structure(soup)
            
            # 2. 嘗試多種提取策略
            logger.info("\n🎯 嘗試提取策略...")
            race_details = self._extract_via_multiple_strategies(soup)
            
            return {
                'status': 'success',
                'url': url,
                'race_details': race_details
            }
        
        except Exception as e:
            logger.error(f"❌ 提取失敗: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _analyze_page_structure(self, soup: BeautifulSoup):
        """分析頁面結構，打印所有主要容器"""
        
        # 找出所有主要容器
        logger.info("📌 主要容器掃描:")
        
        # 查找 heading
        for tag_name in ['h1', 'h2', 'h3', 'h4', 'strong']:
            elements = soup.find_all(tag_name)
            if elements:
                logger.info(f"\n  <{tag_name}> ({len(elements)} 個):")
                for elem in elements[:3]:  # 最多顯示 3 個
                    text = elem.get_text(strip=True)[:60]
                    logger.info(f"    - {text}")
        
        # 查找 divs with id or class
        logger.info(f"\n  <div> with id/class ({len(soup.find_all('div'))} 個 div):")
        for div in soup.find_all('div')[:20]:  # 掃描前 20 個
            div_id = div.get('id', '')
            div_class = div.get('class', [])
            div_data = {k: v for k, v in div.attrs.items() if k.startswith('data-')}
            
            if div_id or div_class or div_data:
                text_preview = div.get_text(strip=True)[:40]
                logger.debug(f"    - id='{div_id}', class={div_class}, text='{text_preview}'")
        
        # 查找 spans
        logger.info(f"\n  <span> ({len(soup.find_all('span'))} 個):")
        for span in soup.find_all('span')[:10]:
            span_class = span.get('class', [])
            text = span.get_text(strip=True)[:50]
            if span_class or len(text) > 5:
                logger.debug(f"    - class={span_class}, text='{text}'")
    
    def _extract_via_multiple_strategies(self, soup: BeautifulSoup) -> Dict:
        """使用多種策略提取賽次信息"""
        
        details = {}
        all_text = soup.get_text(separator=' ')
        
        logger.info("\n🎯 提取策略 1: 正則表達式")
        self._strategy_regex(all_text, details)
        
        logger.info("\n🎯 提取策略 2: HTML 標籤掃描")
        self._strategy_html_scanning(soup, details)
        
        logger.info("\n🎯 提取策略 3: 容器分析")
        self._strategy_container_analysis(soup, details)
        
        return details
    
    def _strategy_regex(self, text: str, details: Dict):
        """策略 1: 使用正則表達式從文本中提取"""
        
        # 賽次標題 (第 1 場 - 美利讓賽)
        match = re.search(r'第\s*(\d+)\s*場\s*[－-]?\s*(.+?)(?=\d{4}年|\n|$)', text)
        if match:
            details['race_number'] = match.group(1).strip()
            details['race_name'] = match.group(2).strip()
            logger.info(f"  ✓ 賽次: {match.group(0)}")
        
        # 日期 (2026年1月7日)
        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
        if match:
            details['date'] = f"{match.group(1)}年{match.group(2)}月{match.group(3)}日"
            logger.info(f"  ✓ 日期: {details['date']}")
        
        # 星期幾
        match = re.search(r'(星期[一二三四五六日])', text)
        if match:
            details['day_of_week'] = match.group(1)
            logger.info(f"  ✓ 星期: {details['day_of_week']}")
        
        # 馬場 (跑馬地|沙田)
        if '跑馬地' in text:
            details['venue'] = '跑馬地'
        elif '沙田' in text:
            details['venue'] = '沙田'
        if 'venue' in details:
            logger.info(f"  ✓ 馬場: {details['venue']}")
        
        # 時間 (18:40)
        match = re.search(r'(\d{2}):(\d{2})', text)
        if match:
            details['time'] = f"{match.group(1)}:{match.group(2)}"
            logger.info(f"  ✓ 時間: {details['time']}")
        
        # 賽道類型 (草地|全天候)
        if re.search(r'草地(?!賽)', text):
            details['track_type'] = '草地'
            logger.info(f"  ✓ 賽道類型: 草地")
        elif '全天候' in text:
            details['track_type'] = '全天候'
            logger.info(f"  ✓ 賽道類型: 全天候")
        
        # 賽道等級 ("A", "B", "C+3" 等)
        match = re.search(r'["\"]([A-Z]+(?:\+\d+)?)["\"]', text)
        if match:
            details['track_rating'] = match.group(1)
            logger.info(f"  ✓ 賽道等級: {details['track_rating']}")
        
        # 距離 (1800米)
        match = re.search(r'(\d{4})米', text)
        if match:
            details['distance'] = match.group(1)
            logger.info(f"  ✓ 距離: {details['distance']}米")
        
        # 場地狀況 (好地|好/快 等)
        match = re.search(r'(好地|好/快|快地|濡地|爛地)', text)
        if match:
            details['going'] = match.group(1)
            logger.info(f"  ✓ 場地: {details['going']}")
        
        # 獎金 ($875,000)
        match = re.search(r'\$\s*([\d,]+)', text)
        if match:
            details['prize_money'] = match.group(1).replace(',', '')
            logger.info(f"  ✓ 獎金: ${details['prize_money']}")
        
        # 評分範圍 (40-0)
        match = re.search(r'評分:\s*(\d+)[～-](\d+)', text)
        if match:
            details['rating_range'] = f"{match.group(1)}-{match.group(2)}"
            logger.info(f"  ✓ 評分: {details['rating_range']}")
        
        # 班次 (第五班)
        match = re.search(r'(第[一二三四五六]班|\d班)', text)
        if match:
            details['class'] = match.group(1)
            logger.info(f"  ✓ 班次: {details['class']}")
    
    def _strategy_html_scanning(self, soup: BeautifulSoup, details: Dict):
        """策略 2: 掃描 HTML 標籤中的內容"""
        
        # 掃描所有 heading 標籤
        for heading in soup.find_all(['h1', 'h2', 'h3', 'strong']):
            text = heading.get_text(strip=True)
            
            # 檢查是否包含賽次信息
            if re.search(r'第\s*\d+\s*場', text):
                logger.info(f"  ✓ 在 <{heading.name}> 中找到賽次: {text}")
                match = re.search(r'第\s*(\d+)\s*場\s*[－-]?\s*(.+)', text)
                if match and 'race_number' not in details:
                    details['race_number'] = match.group(1).strip()
                    details['race_name'] = match.group(2).strip()
    
    def _strategy_container_analysis(self, soup: BeautifulSoup, details: Dict):
        """策略 3: 分析特定容器 (如 class='raceInfo', 'raceDetails' 等)"""
        
        # 尋找可能包含賽次信息的容器
        containers_keywords = ['race', 'info', 'detail', 'condition', 'track']
        
        for container in soup.find_all(['div', 'section']):
            container_class = ' '.join(container.get('class', []))
            container_id = container.get('id', '')
            
            # 檢查是否匹配關鍵詞
            if any(kw in container_class.lower() or kw in container_id.lower() for kw in containers_keywords):
                text = container.get_text(strip=True)
                if len(text) > 20:  # 避免空容器
                    logger.debug(f"  - 找到相關容器: id='{container_id}', class='{container_class}'")
                    logger.debug(f"    內容: {text[:100]}")


if __name__ == "__main__":
    extractor = RaceDetailsExtractorV2(timeout=15)
    
    result = extractor.extract_race_details("2026/01/07", "HV", 1)
    
    print("\n" + "="*80)
    print("📋 提取結果")
    print("="*80)
    
    if result['status'] == 'success':
        print("\n✅ 提取成功！\n")
        for key, value in result['race_details'].items():
            print(f"  {key:20s}: {value}")
    else:
        print(f"\n❌ 提取失敗: {result['error']}")
