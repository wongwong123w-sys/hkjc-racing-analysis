# -*- coding: utf-8 -*-
"""
配腳評分計算器 - 4 維度評分計算
配腳評分系統 - 評分計算模塊

本模塊負責:
1. 計算 4 個維度的評分
2. 整合維度評分為總分
3. 轉換為評級等級 (A-E)
4. 生成診斷信息
"""

import logging
from typing import Dict, Optional

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LegFitnessCalculator:
    """配腳評分計算器 - 計算馬匹的配腳評分"""
    
    # 維度權重配置
    WEIGHTS = {
        'dimension_a': 0.30,  # 入位穩定性 (30%)
        'dimension_b': 0.25,  # 穩定性 (25%)
        'dimension_c': 0.25,  # 環境適應 (25%)
        'dimension_d': 0.20   # 近期狀態 (20%)
    }
    
    # 評級閾值
    GRADE_THRESHOLDS = {
        'A': 0.80,
        'B': 0.65,
        'C': 0.50,
        'D': 0.35,
        'E': 0.00
    }
    
    def __init__(self):
        """初始化計算器"""
        logger.info("✅ LegFitnessCalculator 已初始化")
    
    def calc_leg_fitness_score(self, 
                              horse_metrics: Dict,
                              draw_stats: Dict = None,
                              race_info: Dict = None) -> Dict:
        """
        計算配腳評分 (最高級函數)
        
        參數:
            horse_metrics (Dict): 馬匹指標 (來自 DataPreprocessor)
            draw_stats (Dict): 檔位統計 (可選)
            race_info (Dict): 賽事信息 (可選)
            
        返回:
            Dict: 包含以下結構:
                {
                    'total_score': float,        # 總分 (0.0-1.0)
                    'grade': str,               # 評級 (A-E)
                    'components': {             # 各維度分數
                        'dimension_a': float,
                        'dimension_b': float,
                        'dimension_c': float,
                        'dimension_d': float
                    },
                    'diagnostics': {            # 診斷信息
                        'a_placement_rate': float,
                        'b_win_place_ratio': float,
                        'c_draw_advantage': float,
                        'd_recent_trend': float
                    }
                }
        """
        try:
            logger.info("🔄 開始計算配腳評分...")
            
            # 計算 4 個維度
            dim_a = self.calc_dimension_a(horse_metrics)
            dim_b = self.calc_dimension_b(horse_metrics)
            dim_c = self.calc_dimension_c(horse_metrics, draw_stats, race_info)
            dim_d = self.calc_dimension_d(horse_metrics)
            
            logger.info(f"📊 維度分數: A={dim_a:.3f}, B={dim_b:.3f}, C={dim_c:.3f}, D={dim_d:.3f}")
            
            # 計算加權總分
            total_score = (
                dim_a * self.WEIGHTS['dimension_a'] +
                dim_b * self.WEIGHTS['dimension_b'] +
                dim_c * self.WEIGHTS['dimension_c'] +
                dim_d * self.WEIGHTS['dimension_d']
            )
            
            # 轉換為評級
            grade = self.convert_score_to_grade(total_score)
            
            logger.info(f"✅ 配腳評分計算完成: {grade} ({total_score:.3f})")
            
            return {
                'total_score': round(total_score, 3),
                'grade': grade,
                'components': {
                    'dimension_a': round(dim_a, 3),
                    'dimension_b': round(dim_b, 3),
                    'dimension_c': round(dim_c, 3),
                    'dimension_d': round(dim_d, 3)
                },
                'diagnostics': {
                    'a_placement_rate': horse_metrics.get('overall_placement_rate', 0),
                    'b_win_place_ratio': horse_metrics.get('win_place_ratio', 0),
                    'c_draw_advantage': draw_stats.get('win_rate', 1.0) if draw_stats else 1.0,
                    'd_recent_trend': round(
                        horse_metrics.get('recent_placement_rate', 0) / 
                        max(horse_metrics.get('overall_placement_rate', 0.35), 0.01), 3
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 評分計算失敗: {e}", exc_info=True)
            return self._get_default_score()
    
    def calc_dimension_a(self, horse_metrics: Dict) -> float:
        """
        A 維度: 入位穩定性 (30%)
        
        衡量馬匹的一致性入位能力
        
        公式: (全局 × 0.4) + (近期 × 0.4) + (同程 × 0.2)
        
        參數:
            horse_metrics (Dict): 馬匹指標
            
        返回:
            float: A 維度分數 (0.0-1.0)
        """
        overall = horse_metrics.get('overall_placement_rate', 0)
        recent = horse_metrics.get('recent_placement_rate', 0)
        
        # 同程入位率 (暫用全局)
        same_distance = overall
        
        # 加權平均
        score = (overall * 0.4 + recent * 0.4 + same_distance * 0.2)
        
        # 標準化到 0-1 範圍 (乘以 1.5 因為最大值通常 0.667)
        normalized = min(1.0, max(0.0, score * 1.5))
        
        logger.debug(f"維度 A 計算: overall={overall:.1%}, recent={recent:.1%} → {normalized:.3f}")
        
        return normalized
    
    def calc_dimension_b(self, horse_metrics: Dict) -> float:
        """
        B 維度: 穩定性 (25%)
        
        衡量馬匹的性能穩定性和前進性
        
        公式: (Win/Place Ratio × 0.7) + (馬位穩定性 × 0.3)
        
        參數:
            horse_metrics (Dict): 馬匹指標
            
        返回:
            float: B 維度分數 (0.0-1.0)
        """
        ratio = horse_metrics.get('win_place_ratio', 0)
        avg_distance = horse_metrics.get('avg_win_distance', 0)
        
        # Win/Place Ratio 正常值 0.3-0.5，越接近越穩定
        if ratio > 0:
            ratio_score = 1.0 - abs(ratio - 0.4) / 0.4
        else:
            ratio_score = 0.5
        
        # 馬位穩定性：輸距越小越穩定 (輸距 5 以上為完全失分)
        distance_score = max(0.0, 1.0 - avg_distance / 5.0)
        
        # 加權平均
        score = (ratio_score * 0.7 + distance_score * 0.3)
        normalized = min(1.0, max(0.0, score))
        
        logger.debug(f"維度 B 計算: ratio={ratio:.3f}, distance={avg_distance:.2f} → {normalized:.3f}")
        
        return normalized
    
    def calc_dimension_c(self, 
                        horse_metrics: Dict,
                        draw_stats: Dict = None,
                        race_info: Dict = None) -> float:
        """
        C 維度: 環境適應 (25%)
        
        衡量馬匹對不同環境的適應能力
        
        公式: (檔位利好 × 0.6) + (場地優勢 × 0.4)
        
        參數:
            horse_metrics (Dict): 馬匹指標
            draw_stats (Dict): 檔位統計 (可選)
            race_info (Dict): 賽事信息 (可選)
            
        返回:
            float: C 維度分數 (0.0-1.0)
        """
        # 檔位利好 (如果有檔位統計)
        draw_advantage = 1.0
        if draw_stats and 'win_rate' in draw_stats:
            avg_win_rate = 0.12  # 平均勝率
            if avg_win_rate > 0:
                draw_advantage = min(1.5, draw_stats['win_rate'] / avg_win_rate)
        
        # 場地優勢
        venue_stats = horse_metrics.get('venue_stats', {})
        overall_rate = horse_metrics.get('overall_placement_rate', 0.35)
        
        venue_advantage = 1.0
        if venue_stats and overall_rate > 0:
            best_venue_rate = max(venue_stats.values()) if venue_stats else overall_rate
            venue_advantage = min(1.5, best_venue_rate / overall_rate) if overall_rate > 0 else 1.0
        
        # 標準化到 0-1
        score = (min(draw_advantage, 1.5) * 0.6 + min(venue_advantage, 1.5) * 0.4) / 1.5
        normalized = min(1.0, max(0.0, score))
        
        logger.debug(f"維度 C 計算: draw={draw_advantage:.2f}, venue={venue_advantage:.2f} → {normalized:.3f}")
        
        return normalized
    
    def calc_dimension_d(self, horse_metrics: Dict) -> float:
        """
        D 維度: 近期狀態 (20%)
        
        衡量馬匹的最近狀態趨勢
        
        公式: 近期入位率 / 全局入位率
        
        參數:
            horse_metrics (Dict): 馬匹指標
            
        返回:
            float: D 維度分數 (0.0-1.0)
        """
        overall = horse_metrics.get('overall_placement_rate', 0.35)
        recent = horse_metrics.get('recent_placement_rate', 0.35)
        
        if overall <= 0:
            return 0.5  # 默認中等
        
        trend = recent / overall
        
        # 映射到 0-1 分數
        if trend >= 1.2:
            score = 0.9  # 上升趨勢
        elif trend >= 1.0:
            score = 0.8
        elif trend >= 0.8:
            score = 0.7  # 穩定
        elif trend >= 0.5:
            score = 0.5
        else:
            score = 0.2  # 下降趨勢
        
        logger.debug(f"維度 D 計算: trend={trend:.2f} → {score:.3f}")
        
        return score
    
    def convert_score_to_grade(self, score: float) -> str:
        """
        轉換分數為評級等級
        
        評級說明:
        - A: 0.80-1.00 (優秀配腳)
        - B: 0.65-0.79 (良好配腳)
        - C: 0.50-0.64 (中等配腳)
        - D: 0.35-0.49 (較差配腳)
        - E: 0.00-0.34 (很差配腳)
        
        參數:
            score (float): 評分 (0.0-1.0)
            
        返回:
            str: 評級 (A-E)
        """
        if score >= self.GRADE_THRESHOLDS['A']:
            return 'A'
        elif score >= self.GRADE_THRESHOLDS['B']:
            return 'B'
        elif score >= self.GRADE_THRESHOLDS['C']:
            return 'C'
        elif score >= self.GRADE_THRESHOLDS['D']:
            return 'D'
        else:
            return 'E'
    
    def _get_default_score(self) -> Dict:
        """返回默認分數 (發生錯誤時)"""
        return {
            'total_score': 0.5,
            'grade': 'C',
            'components': {
                'dimension_a': 0.5,
                'dimension_b': 0.5,
                'dimension_c': 0.5,
                'dimension_d': 0.5
            },
            'diagnostics': {}
        }


# ============= 使用示例 =============

if __name__ == '__main__':
    """
    使用示例:
    
    from analyzers.leg_fitness_calculator import LegFitnessCalculator
    
    # 初始化計算器
    calculator = LegFitnessCalculator()
    
    # 準備馬匹指標
    horse_metrics = {
        'overall_placement_rate': 0.45,
        'recent_placement_rate': 0.50,
        'win_place_ratio': 0.33,
        'avg_win_distance': 2.5,
        'venue_stats': {'沙田': 0.50, '跑馬地': 0.40}
    }
    
    # 計算評分
    result = calculator.calc_leg_fitness_score(horse_metrics)
    
    # 顯示結果
    print(f"評分: {result['total_score']:.3f}")
    print(f"評級: {result['grade']}")
    print(f"維度: A={result['components']['dimension_a']:.3f}, "
          f"B={result['components']['dimension_b']:.3f}, "
          f"C={result['components']['dimension_c']:.3f}, "
          f"D={result['components']['dimension_d']:.3f}")
    """
    print("✅ 評分計算模塊已準備好")
    print("📖 請查閱文件中的使用示例或文檔")
