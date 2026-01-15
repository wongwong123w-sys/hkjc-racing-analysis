
# -*- coding: utf-8 -*-
"""
配速預測器 v3.0 - 5 種配速完整版

PacePredictor - Five-Level Pace System

恢復功能：
- ✅ 5 種配速：快/偏快/中等/偏慢/慢
- ✅ 距離矩陣算法
- ✅ 詳細期望分佈
- ✅ 高精度配速診斷
- ✅ 自動按馬匹數量比例調整

日期: 2026-01-10
"""

import numpy as np
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PacePredictor:
    """
    配速預測器 v3.0 - 5 種配速系統
    
    配速類型：
    1. FAST (快步速) - 前置馬 6-7 匹
    2. MODERATELY_FAST (偏快) - 前置馬 4-5 匹
    3. NORMAL (中等) - 前置馬 3-4 匹
    4. MODERATELY_SLOW (偏慢) - 前置馬 2-3 匹
    5. SLOW (慢步速) - 前置馬 1-2 匹
    """
    
    def __init__(self):
        """初始化配速預測器"""
        logger.info("✅ PacePredictor v3.0 (Five-Level) 已初始化")
        
        # ========================================
        # 五步速期望分佈（12 匹馬標準）
        # ========================================
        self.pace_templates = {
            'FAST': {
                'FRONT': 6.5,   # 6-7 匹前置
                'MID': 3.5,     # 3-4 匹中置
                'BACK': 1.5,    # 1-2 匹後置
                'name': '快步速',
                'characteristics': '大量前置馬搶位，早段競爭激烈，節奏快',
                'suggestion': '後置馬有利，前置馬需保持體力'
            },
            'MODERATELY_FAST': {
                'FRONT': 4.5,   # 4-5 匹前置
                'MID': 4.5,     # 4-5 匹中置
                'BACK': 2.5,    # 2-3 匹後置
                'name': '偏快步速',
                'characteristics': '前置馬較多，早段有一定壓力',
                'suggestion': '中後置馬有一定機會，需把握時機'
            },
            'NORMAL': {
                'FRONT': 3.5,   # 3-4 匹前置
                'MID': 5.5,     # 5-6 匹中置
                'BACK': 2.5,    # 2-3 匹後置
                'name': '中等步速',
                'characteristics': '馬群分佈均衡，節奏穩定',
                'suggestion': '各種跑法都有機會，視乎馬匹狀態'
            },
            'MODERATELY_SLOW': {
                'FRONT': 2.5,   # 2-3 匹前置
                'MID': 4.5,     # 4-5 匹中置
                'BACK': 4.5,    # 4-5 匹後置
                'name': '偏慢步速',
                'characteristics': '後置馬較多，早段壓力小',
                'suggestion': '前置馬佔優，可控制節奏'
            },
            'SLOW': {
                'FRONT': 1.5,   # 1-2 匹前置
                'MID': 3.5,     # 3-4 匹中置
                'BACK': 6.5,    # 6-7 匹後置
                'name': '慢步速',
                'characteristics': '大量後置馬留後，早段節奏慢',
                'suggestion': '前置馬大優，可輕鬆控制局面'
            }
        }
    
    def get_runstyle_distribution(self, predictions: List[Dict]) -> Dict:
        """
        計算跑法分佈
        
        Args:
            predictions: 跑法預測結果列表
        
        Returns:
            Dict: {'FRONT': count, 'MID': count, 'BACK': count, 'total': count}
        """
        if not predictions:
            return {'FRONT': 0, 'MID': 0, 'BACK': 0, 'total': 0}
        
        distribution = {'FRONT': 0, 'MID': 0, 'BACK': 0}
        
        for pred in predictions:
            style = pred.get('running_style', 'MID')
            if style in distribution:
                distribution[style] += 1
        
        distribution['total'] = sum(distribution.values())
        
        logger.info(f"跑法分佈: FRONT={distribution['FRONT']}, MID={distribution['MID']}, BACK={distribution['BACK']}")
        
        return distribution
    
    def calculate_distance_to_template(
        self, 
        actual_dist: Dict, 
        template: Dict
    ) -> float:
        """
        計算實際分佈與模板的歐氏距離
        
        Args:
            actual_dist: 實際分佈 {'FRONT': n, 'MID': m, 'BACK': k}
            template: 模板分佈 {'FRONT': x, 'MID': y, 'BACK': z}
        
        Returns:
            float: 歐氏距離（越小越接近）
        """
        total = actual_dist.get('total', 12)
        
        # 標準化到 12 匹馬
        scale = 12 / total if total > 0 else 1
        
        actual_front = actual_dist['FRONT'] * scale
        actual_mid = actual_dist['MID'] * scale
        actual_back = actual_dist['BACK'] * scale
        
        # 計算歐氏距離
        distance = np.sqrt(
            (actual_front - template['FRONT']) ** 2 +
            (actual_mid - template['MID']) ** 2 +
            (actual_back - template['BACK']) ** 2
        )
        
        return distance
    
    def predict_pace_diagnostic(self, predictions: List[Dict]) -> Dict:
        """
        配速診斷（5 種配速）
        
        Args:
            predictions: 跑法預測結果
        
        Returns:
            Dict: {
                'pace_type': str,          # 配速類型（英文鍵）
                'pace_name': str,          # 配速名稱（中文）
                'confidence': float,       # 信心度 0-100
                'characteristics': str,    # 特徵描述
                'suggestion': str,         # 建議
                'distances': Dict          # 各配速的距離
            }
        """
        try:
            # 計算實際分佈
            distribution = self.get_runstyle_distribution(predictions)
            
            if distribution['total'] == 0:
                logger.warning("無有效預測數據")
                return {
                    'pace_type': 'NORMAL',
                    'pace_name': '未知',
                    'confidence': 0,
                    'characteristics': '無數據',
                    'suggestion': '需要更多數據',
                    'distances': {}
                }
            
            # ========================================
            # 計算與各模板的距離
            # ========================================
            distances = {}
            
            for pace_key, template in self.pace_templates.items():
                dist = self.calculate_distance_to_template(distribution, template)
                distances[pace_key] = dist
            
            # 找出最接近的配速
            best_pace = min(distances, key=distances.get)
            min_distance = distances[best_pace]
            
            # ========================================
            # 計算信心度
            # ========================================
            # 基於距離：距離越小，信心度越高
            # 距離 0 = 100%, 距離 3 = 50%, 距離 6+ = 0%
            confidence = max(0, min(100, 100 - (min_distance / 6) * 100))
            
            # 調整：如果次優距離接近，降低信心度
            sorted_distances = sorted(distances.values())
            if len(sorted_distances) >= 2:
                second_distance = sorted_distances[1]
                if second_distance - min_distance < 0.5:
                    confidence *= 0.8  # 降低 20%
            
            logger.info(f"配速診斷: {best_pace} ({self.pace_templates[best_pace]['name']}), 信心度: {confidence:.1f}%")
            logger.info(f"距離矩陣: {distances}")
            
            return {
                'pace_type': best_pace,
                'pace_name': self.pace_templates[best_pace]['name'],
                'confidence': round(confidence, 1),
                'characteristics': self.pace_templates[best_pace]['characteristics'],
                'suggestion': self.pace_templates[best_pace]['suggestion'],
                'distances': {k: round(v, 3) for k, v in distances.items()}
            }
        
        except Exception as e:
            logger.error(f"配速診斷錯誤: {str(e)}")
            return {
                'pace_type': 'NORMAL',
                'pace_name': '錯誤',
                'confidence': 0,
                'characteristics': f'錯誤: {str(e)}',
                'suggestion': '請檢查數據',
                'distances': {}
            }
    
    def get_expected_distribution(self, pace_type: str, total_horses: int = 12) -> Dict:
        """
        獲取期望分佈
        
        Args:
            pace_type: 配速類型（'FAST', 'MODERATELY_FAST', etc.）
            total_horses: 總馬數
        
        Returns:
            Dict: {'FRONT': n, 'MID': m, 'BACK': k}
        """
        if pace_type not in self.pace_templates:
            pace_type = 'NORMAL'
        
        template = self.pace_templates[pace_type]
        scale = total_horses / 12
        
        return {
            'FRONT': round(template['FRONT'] * scale),
            'MID': round(template['MID'] * scale),
            'BACK': round(template['BACK'] * scale)
        }
    
    def predict_pace(
        self, 
        predictions: List[Dict], 
        race_distance: int = 1800
    ) -> Dict:
        """
        配速預測（帶距離校正）
        
        Args:
            predictions: 跑法預測結果
            race_distance: 賽事距離（米）
        
        Returns:
            Dict: 配速預測結果
        """
        try:
            # 基礎配速診斷
            diagnostic = self.predict_pace_diagnostic(predictions)
            
            # 距離校正係數
            # 短途 (≤1200m): 節奏更快
            # 中距離 (1400-1800m): 標準
            # 長途 (≥2000m): 節奏較慢
            distance_factor = 1.0
            
            if race_distance <= 1200:
                distance_factor = 1.15  # 短途加快 15%
            elif race_distance >= 2000:
                distance_factor = 0.85  # 長途減慢 15%
            
            # 基礎配速值（假設標準為 1.0）
            pace_values = {
                'FAST': 1.2,
                'MODERATELY_FAST': 1.1,
                'NORMAL': 1.0,
                'MODERATELY_SLOW': 0.9,
                'SLOW': 0.8
            }
            
            base_pace = pace_values.get(diagnostic['pace_type'], 1.0)
            adjusted_pace = base_pace * distance_factor
            
            # 早中晚段配速
            early_pace = adjusted_pace
            mid_pace = adjusted_pace * 0.95
            late_pace = adjusted_pace * 0.9
            
            return {
                **diagnostic,
                'race_distance': race_distance,
                'distance_factor': distance_factor,
                'base_pace': base_pace,
                'adjusted_pace': adjusted_pace,
                'early_pace': early_pace,
                'mid_pace': mid_pace,
                'late_pace': late_pace,
                'adjustment_applied': distance_factor != 1.0
            }
        
        except Exception as e:
            logger.error(f"配速預測錯誤: {str(e)}")
            return {
                'pace_type': 'NORMAL',
                'pace_name': '錯誤',
                'confidence': 0,
                'error': str(e)
            }


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    
    # 測試：快步速場景
    test_predictions_fast = [
        {'horse_number': 1, 'running_style': 'FRONT'},
        {'horse_number': 2, 'running_style': 'FRONT'},
        {'horse_number': 3, 'running_style': 'FRONT'},
        {'horse_number': 4, 'running_style': 'FRONT'},
        {'horse_number': 5, 'running_style': 'FRONT'},
        {'horse_number': 6, 'running_style': 'FRONT'},
        {'horse_number': 7, 'running_style': 'FRONT'},
        {'horse_number': 8, 'running_style': 'MID'},
        {'horse_number': 9, 'running_style': 'MID'},
        {'horse_number': 10, 'running_style': 'MID'},
        {'horse_number': 11, 'running_style': 'BACK'},
        {'horse_number': 12, 'running_style': 'BACK'},
    ]
    
    # 測試：慢步速場景
    test_predictions_slow = [
        {'horse_number': 1, 'running_style': 'FRONT'},
        {'horse_number': 2, 'running_style': 'MID'},
        {'horse_number': 3, 'running_style': 'MID'},
        {'horse_number': 4, 'running_style': 'MID'},
        {'horse_number': 5, 'running_style': 'BACK'},
        {'horse_number': 6, 'running_style': 'BACK'},
        {'horse_number': 7, 'running_style': 'BACK'},
        {'horse_number': 8, 'running_style': 'BACK'},
        {'horse_number': 9, 'running_style': 'BACK'},
        {'horse_number': 10, 'running_style': 'BACK'},
        {'horse_number': 11, 'running_style': 'BACK'},
        {'horse_number': 12, 'running_style': 'BACK'},
    ]
    
    predictor = PacePredictor()
    
    print("\n" + "="*60)
    print("測試 1: 快步速場景（7 FRONT + 3 MID + 2 BACK）")
    print("="*60)
    result1 = predictor.predict_pace_diagnostic(test_predictions_fast)
    print(f"配速: {result1['pace_name']}")
    print(f"信心度: {result1['confidence']}%")
    print(f"特徵: {result1['characteristics']}")
    print(f"距離矩陣: {result1['distances']}")
    
    print("\n" + "="*60)
    print("測試 2: 慢步速場景（1 FRONT + 3 MID + 8 BACK）")
    print("="*60)
    result2 = predictor.predict_pace_diagnostic(test_predictions_slow)
    print(f"配速: {result2['pace_name']}")
    print(f"信心度: {result2['confidence']}%")
    print(f"特徵: {result2['characteristics']}")
    print(f"距離矩陣: {result2['distances']}")
    
    print("\n" + "="*60)
    print("測試 3: 期望分佈")
    print("="*60)
    for pace_key in ['FAST', 'MODERATELY_FAST', 'NORMAL', 'MODERATELY_SLOW', 'SLOW']:
        expected = predictor.get_expected_distribution(pace_key, 12)
        pace_name = predictor.pace_templates[pace_key]['name']
        print(f"{pace_name}: 前{expected['FRONT']} / 中{expected['MID']} / 後{expected['BACK']}")
