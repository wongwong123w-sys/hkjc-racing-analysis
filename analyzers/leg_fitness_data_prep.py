# -*- coding: utf-8 -*-
"""
馬匹往績 CSV 預處理器
配腳評分系統 - 數據預處理模塊

本模塊負責:
1. 讀取和清理馬匹往績 CSV 文件
2. 計算馬匹性能指標
3. 轉換輸距格式
4. 統計場地和距離優勢
"""

import pandas as pd
import logging
from typing import Dict, List, Optional

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataPreprocessor:
    """CSV 數據預處理器 - 用於馬匹往績數據處理"""
    
    # 輸距轉換表 (馬位對應)
    DISTANCE_MAP = {
        '頭位': 0.08,
        '短頭': 0.04,
        '馬身': 1.00,
        '1-1/4': 1.25,
        '1-1/2': 1.50,
        '1-3/4': 1.75,
        '2': 2.0,
        '2-1/4': 2.25,
        '2-1/2': 2.50,
        '3-3/4': 3.75,
        '5': 5.0,
        '12-1/2': 12.50,
    }
    
    def __init__(self):
        """初始化預處理器"""
        logger.info("✅ DataPreprocessor 已初始化")
    
    def preprocess_race_history(self, horse_name: str, csv_path: str) -> Dict:
        """
        預處理馬匹往績 CSV 文件
        
        參數:
            horse_name (str): 馬名 (用於篩選)
            csv_path (str): CSV 文件路徑
            
        返回:
            Dict: 包含以下結構的字典:
                {
                    'horse_name': str,
                    'total_races': int,
                    'races': List[Dict],
                    'metrics': Dict,
                    'status': 'success' | 'warning' | 'error',
                    'error': str (如果有錯誤)
                }
        """
        try:
            # 步驟 1: 讀取 CSV 文件
            logger.info(f"📖 讀取 CSV 文件: {csv_path}")
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            
            # 步驟 2: 篩選指定馬匹的記錄
            horse_races = df[df['馬名'] == horse_name].copy()
            
            if horse_races.empty:
                logger.warning(f"⚠️ 未找到馬匹 {horse_name} 的記錄")
                return self._get_empty_result(horse_name)
            
            logger.info(f"✅ 找到 {len(horse_races)} 條記錄")
            
            # 步驟 3: 逐行轉換數據
            races = []
            for idx, row in horse_races.iterrows():
                try:
                    race = {
                        'date': str(row.get('日期', '')).strip(),
                        'distance': self._parse_int(row.get('途程', 1200)),
                        'venue': str(row.get('馬場', '沙田')).strip(),
                        'going': str(row.get('狀況', 'C')).strip(),
                        'draw': self._parse_int(row.get('檔位', 0)),
                        'finishing_position': self._parse_position(row.get('名次', '')),
                        'win_distance': self.transform_distance(
                            str(row.get('頭馬距離', '')).strip()
                        ),
                        'rating': self._parse_int(row.get('評分', 0)),
                        'weight': self._parse_int(row.get('重量', 0)),
                        'jockey': str(row.get('騎師', '')).strip(),
                    }
                    race['is_placed'] = self._is_placed(race['finishing_position'])
                    races.append(race)
                except Exception as e:
                    logger.warning(f"⚠️ 第 {idx+1} 行轉換失敗: {e}")
                    continue
            
            if not races:
                logger.warning(f"⚠️ 沒有有效的比賽記錄")
                return self._get_empty_result(horse_name)
            
            # 步驟 4: 計算馬匹指標
            metrics = self.calculate_horse_metrics(races)
            
            logger.info(f"✅ {horse_name} 預處理完成 ({len(races)} 條記錄)")
            
            return {
                'horse_name': horse_name,
                'total_races': len(races),
                'races': races,
                'metrics': metrics,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"❌ CSV 預處理失敗: {e}", exc_info=True)
            return self._get_error_result(horse_name, str(e))
    
    def calculate_horse_metrics(self, races: List[Dict]) -> Dict:
        """
        計算馬匹的所有性能指標
        
        參數:
            races (List[Dict]): 比賽記錄列表
            
        返回:
            Dict: 包含以下指標的字典:
                - overall_placement_rate: 全局入位率
                - recent_placement_rate: 近期入位率
                - win_place_ratio: 冠亞比
                - avg_rating: 平均評分
                - rating_std: 評分標準差
                - distance_stats: 距離統計
                - venue_stats: 場地統計
                - avg_win_distance: 平均輸距
        """
        if not races:
            logger.warning("❌ 輸入為空，返回默認指標")
            return self._get_empty_metrics()
        
        logger.info(f"📊 計算 {len(races)} 條記錄的指標...")
        
        # 基本統計
        placed_count = sum(1 for r in races if r['is_placed'])
        win_count = sum(1 for r in races if r['finishing_position'] == 1)
        place_count = sum(1 for r in races if r['finishing_position'] == 2)
        
        # 全局指標
        overall_placement_rate = placed_count / len(races) if races else 0
        overall_win_rate = win_count / len(races) if races else 0
        overall_place_rate = place_count / len(races) if races else 0
        
        # 近期指標 (最近 10 仗)
        recent_races = races[-10:] if len(races) >= 10 else races
        recent_placed = sum(1 for r in recent_races if r['is_placed'])
        recent_placement_rate = recent_placed / len(recent_races) if recent_races else 0
        
        # 評分分析
        ratings = [r['rating'] for r in races if r['rating'] > 0]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        rating_std = self._calculate_std(ratings) if ratings else 0
        
        # 距離統計
        distance_stats = self._calculate_distance_stats(races)
        
        # 場地統計
        venue_stats = self._calculate_venue_stats(races)
        
        # 馬位統計
        win_place_ratio = win_count / (win_count + place_count) if (win_count + place_count) > 0 else 0
        
        # 平均輸距
        placed_races = [r for r in races if r['is_placed']]
        avg_win_distance = sum(r['win_distance'] for r in placed_races) / len(placed_races) if placed_races else 0
        
        metrics = {
            'overall_placement_rate': round(overall_placement_rate, 3),
            'overall_win_rate': round(overall_win_rate, 3),
            'overall_place_rate': round(overall_place_rate, 3),
            'recent_placement_rate': round(recent_placement_rate, 3),
            'avg_rating': round(avg_rating, 1),
            'rating_std': round(rating_std, 1),
            'distance_stats': distance_stats,
            'venue_stats': venue_stats,
            'win_place_ratio': round(win_place_ratio, 3),
            'avg_win_distance': round(avg_win_distance, 2),
            'total_wins': win_count,
            'total_places': place_count,
            'total_shows': placed_count
        }
        
        logger.info(f"✅ 指標計算完成")
        logger.info(f"   入位率: {overall_placement_rate:.1%} | "
                   f"勝率: {overall_win_rate:.1%} | "
                   f"評分: {avg_rating:.1f}±{rating_std:.1f}")
        
        return metrics
    
    def transform_distance(self, distance_str: str) -> float:
        """
        輸距轉換: 將馬匹輸距字符串轉換為馬位數值
        
        範例:
            "1-1/4" → 1.25
            "頭位" → 0.08
            "3-3/4" → 3.75
        
        參數:
            distance_str (str): 輸距字符串
            
        返回:
            float: 馬位 (0.00-12.50)
        """
        distance_str = str(distance_str).strip()
        
        # 直接查表
        if distance_str in self.DISTANCE_MAP:
            return self.DISTANCE_MAP[distance_str]
        
        # 嘗試轉換純數字
        try:
            return float(distance_str)
        except:
            logger.debug(f"⚠️ 輸距轉換失敗: '{distance_str}' → 返回 0.0")
            return 0.0
    
    # ========== 私有方法 ==========
    
    def _parse_int(self, value) -> int:
        """安全解析整數"""
        try:
            return int(float(value))
        except:
            return 0
    
    def _parse_position(self, position_str: str) -> int:
        """
        解析馬匹名次
        
        範例: "1" → 1, "05" → 5, "" → 0
        """
        try:
            pos = str(position_str).strip()
            if not pos:
                return 0
            return int(pos)
        except:
            return 0
    
    def _is_placed(self, finishing_position: int) -> bool:
        """
        判定馬匹是否進入前三名 (入位)
        
        參數:
            finishing_position (int): 名次 (1-14)
            
        返回:
            bool: True 如果進三甲 (1-3), False 否則
        """
        return 1 <= finishing_position <= 3
    
    def _calculate_std(self, values: List[float]) -> float:
        """
        計算標準差 (样本標準差)
        
        參數:
            values (List[float]): 數值列表
            
        返回:
            float: 標準差
        """
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _calculate_distance_stats(self, races: List[Dict]) -> Dict:
        """
        計算每個距離的入位統計
        
        返回: {
            '1400': 0.500,  # 1400 途程的入位率
            '1600': 0.333,
            ...
        }
        """
        distance_data = {}
        for race in races:
            dist = race['distance']
            if dist not in distance_data:
                distance_data[dist] = {'races': 0, 'placed': 0}
            distance_data[dist]['races'] += 1
            if race['is_placed']:
                distance_data[dist]['placed'] += 1
        
        # 轉換為入位率
        stats = {}
        for dist, data in distance_data.items():
            rate = data['placed'] / data['races'] if data['races'] > 0 else 0
            stats[str(dist)] = round(rate, 3)
        
        return stats
    
    def _calculate_venue_stats(self, races: List[Dict]) -> Dict:
        """
        計算每個場地的入位統計
        
        返回: {
            '沙田': 0.400,   # 沙田場地的入位率
            '跑馬地': 0.333,
            ...
        }
        """
        venue_data = {}
        for race in races:
            venue = race['venue']
            if venue not in venue_data:
                venue_data[venue] = {'races': 0, 'placed': 0}
            venue_data[venue]['races'] += 1
            if race['is_placed']:
                venue_data[venue]['placed'] += 1
        
        # 轉換為入位率
        stats = {}
        for venue, data in venue_data.items():
            rate = data['placed'] / data['races'] if data['races'] > 0 else 0
            stats[venue] = round(rate, 3)
        
        return stats
    
    def _get_empty_result(self, horse_name: str) -> Dict:
        """返回空結果 (無數據)"""
        return {
            'horse_name': horse_name,
            'total_races': 0,
            'races': [],
            'metrics': self._get_empty_metrics(),
            'status': 'warning'
        }
    
    def _get_empty_metrics(self) -> Dict:
        """返回空指標 (所有值為 0)"""
        return {
            'overall_placement_rate': 0.0,
            'overall_win_rate': 0.0,
            'overall_place_rate': 0.0,
            'recent_placement_rate': 0.0,
            'avg_rating': 0.0,
            'rating_std': 0.0,
            'distance_stats': {},
            'venue_stats': {},
            'win_place_ratio': 0.0,
            'avg_win_distance': 0.0,
            'total_wins': 0,
            'total_places': 0,
            'total_shows': 0
        }
    
    def _get_error_result(self, horse_name: str, error: str) -> Dict:
        """返回錯誤結果"""
        return {
            'horse_name': horse_name,
            'total_races': 0,
            'races': [],
            'metrics': self._get_empty_metrics(),
            'status': 'error',
            'error': error
        }


# ============= 使用示例 =============

if __name__ == '__main__':
    """
    使用示例:
    
    from analyzers.leg_fitness_data_prep import DataPreprocessor
    
    # 初始化預處理器
    preprocessor = DataPreprocessor()
    
    # 預處理馬匹數據
    result = preprocessor.preprocess_race_history(
        horse_name='添喜運',
        csv_path='./data/horses.csv'
    )
    
    # 檢查結果
    if result['status'] == 'success':
        print(f"馬名: {result['horse_name']}")
        print(f"比賽次數: {result['total_races']}")
        print(f"入位率: {result['metrics']['overall_placement_rate']:.1%}")
        print(f"評分: {result['metrics']['avg_rating']:.1f}")
    """
    print("✅ 數據預處理模塊已準備好")
    print("📖 請查閱文件中的使用示例或文檔")
