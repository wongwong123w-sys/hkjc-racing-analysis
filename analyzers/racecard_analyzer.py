# -*- coding: utf-8 -*-

"""
HKJC 排位表分析器 - 完整版本 (v2.1 - 含數據庫 + 錯誤處理)

✨ v2.1 新增功能:
- SQLite 數據持久化
- 改進的爬蟲錯誤處理
- 進度追蹤
- 詳細的日誌記錄

- 完整提取全部 27 欄 (內部數據庫，不錯位)
- 只顯示指定的 17 欄
- 單一文件，開箱即用
- 支持 timeout 和 retry 參數
- 馬匹往績爬蟲集成

作者: AI Assistant
日期: 2026-01-09
版本: 2.1 (新增: 數據庫 + 改進錯誤處理)
"""

import re
import logging
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from typing import List, Dict, Optional
import time

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 導入往績爬蟲
from .horse_racing_history_parser import HorseRacingHistoryParser

# ✨ 新增: 導入數據庫和錯誤處理模塊
from .db_manager import DatabaseManager
from .error_handler import CrawlerProgressTracker, ErrorHandler, CrawlerLogger

# ===== 完整欄位定義 (內部: 全部 27 欄) =====

COMPLETE_FIELD_MAP = {
    0: 'position',              # 馬匹編號
    1: 'recent_runs',           # 6次近績
    2: 'color_image',           # 綵衣 (圖片)
    3: 'horse_name',            # 馬名
    4: 'horse_code',            # 烙號
    5: 'weight',                # 負磅
    6: 'jockey',                # 騎師
    7: 'possible_overweight',   # 可能超磅
    8: 'barrier',               # 檔位
    9: 'trainer',               # 練馬師
    10: 'intl_rating',          # 國際評分
    11: 'rating',               # 評分
    12: 'rating_change',        # 評分+/-
    13: 'stable_weight',        # 排位體重
    14: 'weight_change',        # 排位體重+/-
    15: 'best_time',            # 最佳時間
    16: 'age',                  # 馬齡
    17: 'age_allowance',        # 分齡讓磅
    18: 'sex',                  # 性別
    19: 'season_prize',         # 今季獎金
    20: 'priority_order',       # 優先參賽次序
    21: 'days_since_race',      # 上賽距今日數
    22: 'remarks',              # 配備
    23: 'owner',                # 馬主
    24: 'sire',                 # 父系
    25: 'dam',                  # 母系
    26: 'import_type',          # 進口類別
}

# ===== 顯示欄位 (只這 17 欄) =====

DISPLAY_FIELDS = [
    'position',         # 馬匹編號
    'recent_runs',      # 6次近績
    'horse_name',       # 馬名
    'horse_code',       # 烙號
    'weight',           # 負磅
    'jockey',           # 騎師
    'barrier',          # 檔位
    'trainer',          # 練馬師
    'rating',           # 評分
    'rating_change',    # 評分+/-
    'stable_weight',    # 排位體重
    'weight_change',    # 排位體重+/-
    'best_time',        # 最佳時間
    'priority_order',   # 優先參賽次序
    'remarks',          # 配備
    'sire',             # 父系
    'age',              # 馬齡
]


class RaceCardAnalyzer:
    """HKJC 排位表分析器 (v2.1 - 含數據庫 + 錯誤處理)"""

    def __init__(self, timeout: int = 10, retry: int = 3, enable_db: bool = True):
        """
        初始化分析器

        Args:
            timeout: 請求超時秒數 (默認: 10)
            retry: 重試次數 (默認: 3)
            enable_db: 是否啟用數據庫 (默認: True)

        Example:
            analyzer = RaceCardAnalyzer(timeout=15, retry=5, enable_db=True)
        """
        self.data = {}  # 內部存儲完整 27 欄數據
        self.timeout = timeout
        self.retry = retry

        # ✨ 新增: 初始化往績爬蟲
        self.history_parser = HorseRacingHistoryParser(timeout=timeout, retry=retry)

        # ✨ 新增: 初始化數據庫
        self.db_manager = DatabaseManager('hkjc_data.db') if enable_db else None

        # ✨ 新增: 初始化日誌記錄器
        self.logger = CrawlerLogger('RaceCardAnalyzer')

        print(f"🏇 HKJC 排位表分析器已啟動 (超時: {timeout}s, 重試: {retry}次)")
        print(f"📊 往績爬蟲已就緒 (17 欄往績數據)")
        if self.db_manager:
            print(f"💾 數據庫已啟用")

    def fetch_racecard(self, date_str: str, racecourse: str, race_no: int,
                      fetch_history: bool = True, max_races: int = 6) -> Dict:
        """
        從 HKJC 爬取排位表並可選爬取馬匹往績

        Args:
            date_str: 日期字符串，格式 '2026/01/07'
            racecourse: 場次，'HV'(跑馬地) 或 'ST'(沙田)
            race_no: 賽次，1, 2, 3...
            fetch_history: 是否爬取馬匹往績 (預設 True)
            max_races: 每匹馬最多爬取的往績數 (預設 6)

        Returns:
            dict: {
                'status': 'success',
                'race_id': 'HV_20260107_1',
                'horses': [...],
                'total_horses': 12
            } 或 {'error': 'error message'}

        Example:
            result = analyzer.fetch_racecard('2026/01/07', 'HV', 1, fetch_history=True, max_races=6)
            if 'error' not in result:
                print(f"✅ {result['race_id']}: {result['total_horses']} 匹馬")
        """
        url = "https://racing.hkjc.com/racing/information/Chinese/racing/RaceCard.aspx"
        params = {
            'RaceDate': date_str,
            'Racecourse': racecourse,
            'RaceNo': race_no
        }

        # 帶重試機制的爬取
        for attempt in range(self.retry):
            try:
                response = requests.get(url, params=params, timeout=self.timeout)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.content, 'html.parser')
                table = soup.find('table', {'class': 'starter'})

                if not table:
                    return {'error': 'Table not found'}

                # 完整提取全部 27 欄
                all_horses = self._parse_complete(table)

                # 生成 race_id
                race_id = f"{racecourse}_{date_str.replace('/', '')}_{race_no}"

                # 存到內部數據庫
                self.data[race_id] = {
                    'horses_all': all_horses,
                    'date': date_str,
                    'racecourse': racecourse,
                    'race_no': race_no,
                    'total': len(all_horses),
                    'fetched_at': datetime.now().isoformat()
                }

                # ✨ 新增: 保存到 SQLite 數據庫
                if self.db_manager:
                    self.db_manager.save_racecard(race_id, date_str, racecourse, race_no, all_horses)

                self.logger.log_success('爬取排位表', race_id, f'{len(all_horses)} 匹馬')

                # ✨ 新增: 如果需要，爬取馬匹往績
                if fetch_history:
                    print(f"🔍 開始爬取 {len(all_horses)} 匹馬的往績...")
                    all_horses = self._enrich_horses_with_history(all_horses, race_id, max_races)
                    self.data[race_id]['horses_all'] = all_horses

                return {
                    'status': 'success',
                    'race_id': race_id,
                    'horses': all_horses,
                    'total_horses': len(all_horses)
                }

            except requests.Timeout as e:
                self.logger.log_warning('爬取排位表', f"超時 (第 {attempt + 1}/{self.retry} 次)")
                if attempt == self.retry - 1:
                    error_report = ErrorHandler.format_error_report(
                        f'爬取排位表 {race_id}',
                        e,
                        retry_count=attempt
                    )
                    logger.error(error_report)
                    return {'error': f'Request timeout after {self.retry} retries'}
                continue

            except Exception as e:
                error_type = ErrorHandler.classify_error(e)
                self.logger.log_warning('爬取排位表', f"{error_type} (第 {attempt + 1}/{self.retry} 次)")
                if attempt == self.retry - 1:
                    error_report = ErrorHandler.format_error_report(
                        f'爬取排位表 {race_id}',
                        e,
                        retry_count=attempt
                    )
                    logger.error(error_report)
                    return {'error': str(e)}
                continue

        return {'error': 'Failed after retries'}

    def _enrich_horses_with_history(self, horses: list, race_id: str, max_races: int = 6) -> list:
        """
        為馬匹數據添加往績紀錄

        Args:
            horses: 馬匹數據列表
            race_id: 排位表 ID
            max_races: 每匹馬最多爬取的往績數

        Returns:
            包含往績數據的馬匹列表
        """
        # ✨ 新增: 進度追蹤
        progress_tracker = CrawlerProgressTracker('爬取馬匹往績', len(horses))

        for idx, horse in enumerate(horses):
            # 檢查是否有 horse_id
            if not horse.get('horse_id'):
                self.logger.log_warning('爬取往績', f"{horse.get('horse_name')} 無 horse_id")
                horse['racing_history'] = []
                continue

            self.logger.log_progress(idx + 1, len(horses), horse['horse_name'])

            history_result = self.history_parser.fetch_horse_racing_history(
                horse['horse_id'],
                max_races=max_races
            )

            if history_result['status'] == 'success':
                horse['racing_history'] = history_result['racing_history']
                # ✨ 新增: 保存馬匹往績到數據庫
                if self.db_manager:
                    self.db_manager.save_horse_history(
                        horse['horse_id'],
                        horse['horse_name'],
                        race_id,
                        history_result['racing_history']
                    )
                progress_tracker.success(horse['horse_name'], f"{history_result['total_races']} 筆往績")
            else:
                horse['racing_history'] = []
                error_msg = history_result.get('error', '未知錯誤')
                progress_tracker.failure(horse['horse_name'], error_msg)

            time.sleep(0.3)

        # ✨ 新增: 輸出進度總結
        print(progress_tracker.summary())

        return horses

    def _parse_complete(self, table) -> List[Dict]:
        """
        內部方法：完整提取全部 27 欄

        Args:
            table: BeautifulSoup 的 table 對象

        Returns:
            list: 包含所有馬匹數據的列表 (每匹馬包含完整 27 欄)
        """
        horses = []

        for row in table.find_all('tr')[1:]:  # 跳過表頭
            cells = row.find_all('td')
            horse = {}

            for col_idx, field_name in COMPLETE_FIELD_MAP.items():
                if col_idx < len(cells):
                    cell = cells[col_idx]

                    # ===== 特殊欄位處理 =====

                    if field_name == 'color_image':
                        # 綵衣: 提取圖片 URL
                        img = cell.find('img')
                        horse[field_name] = {'src': img.get('src')} if img else None

                    elif field_name == 'horse_name':
                        # 馬名: 提取名稱和馬ID
                        link = cell.find('a')
                        if link:
                            horse[field_name] = link.get_text(strip=True)
                            href = link.get('href', '')
                            horse['horse_id'] = href.split('horseid=')[-1] if 'horseid=' in href else None
                        else:
                            horse[field_name] = cell.get_text(strip=True)
                            horse['horse_id'] = None

                    elif field_name == 'jockey':
                        # 騎師: 分離名稱和附加資訊
                        text = cell.get_text(strip=True)
                        match = re.match(r'(.+?)(\(.+?\))?$', text)
                        if match:
                            horse[field_name] = match.group(1)
                            horse['jockey_info'] = match.group(2)
                        else:
                            horse[field_name] = text
                            horse['jockey_info'] = None

                    else:
                        # 其他欄位: 直接提取文本
                        horse[field_name] = cell.get_text(strip=True)

            horses.append(horse)

        return horses

    def get_racecard(self, race_id: str) -> Optional[List[Dict]]:
        """
        獲取排位表 (自動只顯示指定的 17 欄)

        Args:
            race_id: 賽次 ID，如 'HV_20260107_1'

        Returns:
            list: 馬匹列表 (每匹馬只含 17 欄)，如果未找到返回 None

        Example:
            racecard = analyzer.get_racecard('HV_20260107_1')
            if racecard:
                for horse in racecard:
                    print(f"{horse['position']} {horse['horse_name']}")
        """
        if race_id not in self.data:
            print(f"⚠️ 未找到賽次: {race_id}")
            return None

        all_horses = self.data[race_id]['horses_all']

        # 只保留 17 欄顯示欄位
        return [
            {k: v for k, v in horse.items() if k in DISPLAY_FIELDS or k == 'horse_id' or k == 'racing_history'}
            for horse in all_horses
        ]

    def export_csv(self, race_id: str, filename: Optional[str] = None) -> Optional[str]:
        """
        匯出排位表為 CSV

        Args:
            race_id: 賽次 ID
            filename: 輸出檔名 (預設: racecard_{race_id}.csv)

        Returns:
            str: 輸出檔名，如果失敗返回 None

        Example:
            csv_file = analyzer.export_csv('HV_20260107_1')
        """
        import csv

        racecard = self.get_racecard(race_id)
        if not racecard:
            print(f"❌ 無法匯出: {race_id} 未找到")
            return None

        if not filename:
            filename = f"racecard_{race_id}.csv"

        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                if racecard:
                    fieldnames = [k for k in racecard[0].keys() if k not in ['racing_history']]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for horse in racecard:
                        writer.writerow({k: v for k, v in horse.items() if k in fieldnames})

            print(f"✅ 已匯出: {filename}")
            return filename

        except Exception as e:
            print(f"❌ 匯出失敗: {e}")
            return None

    def close(self):
        """關閉分析器、往績爬蟲和數據庫"""
        if hasattr(self, 'history_parser') and self.history_parser:
            self.history_parser.close()
        # ✨ 新增: 關閉數據庫
        if hasattr(self, 'db_manager') and self.db_manager:
            self.db_manager.close()
        print("🏇 分析器已關閉")

    def __del__(self):
        """析構函數 - 自動關閉"""
        self.close()


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 創建分析器
    analyzer = RaceCardAnalyzer(timeout=15, retry=5, enable_db=True)

    # 爬取排位表 + 往績
    result = analyzer.fetch_racecard('2026/01/07', 'HV', 1, fetch_history=True, max_races=6)

    if 'error' not in result:
        race_id = result['race_id']
        horses = result['horses']

        print(f"\n✅ 成功: {race_id} ({result['total_horses']} 匹馬)")

        # 獲取排位表
        racecard = analyzer.get_racecard(race_id)

        if racecard:
            # 顯示前 3 匹馬
            for horse in racecard[:3]:
                print(f"\n{horse['position']}. {horse['horse_name']}")
                print(f" 騎師: {horse['jockey']}, 評分: {horse['rating']}")

                if horse.get('racing_history'):
                    print(f" 往績: {len(horse['racing_history'])} 筆")
                    for race in horse['racing_history'][:2]:
                        print(f" - {race['date']}: 第 {race['position']} 位 ({race['venue']})")

        # 匯出 CSV
        csv_file = analyzer.export_csv(race_id)

    else:
        print(f"❌ 失敗: {result['error']}")

    # 關閉
    analyzer.close()
