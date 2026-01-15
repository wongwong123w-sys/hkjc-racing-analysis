# -*- coding: utf-8 -*-
"""
馬匹標籤識別器
配腳評分系統 - 標籤識別模塊

本模塊負責:
1. 識別「分盡馬」(難贏但穩定進位)
2. 識別「忠心馬」(非常穩定可靠)
3. 識別「場地得益」(場地優勢明顯)
"""

import logging
from typing import Dict, List

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TagIdentifier:
    """馬匹標籤識別器 - 識別馬匹的特殊特徵"""
    
    def __init__(self):
        """初始化識別器"""
        logger.info("✅ TagIdentifier 已初始化")
    
    def identify_all_tags(self, 
                         horse_metrics: Dict,
                         fitness_score: Dict = None) -> List[str]:
        """
        識別馬匹的所有適用標籤
        
        參數:
            horse_metrics (Dict): 馬匹指標
            fitness_score (Dict): 配腳評分結果 (可選)
            
        返回:
            List[str]: 標籤列表，範例: ['分盡馬', '忠心馬', '場地得益']
        """
        tags = []
        
        if self.identify_quitter(horse_metrics):
            tags.append('分盡馬')
        
        if self.identify_loyal(horse_metrics):
            tags.append('忠心馬')
        
        if self.identify_surface_specialist(horse_metrics):
            tags.append('場地得益')
        
        logger.info(f"✅ 識別出標籤: {tags if tags else '無'}")
        return tags
    
    def identify_quitter(self, horse_metrics: Dict) -> bool:
        """
        識別「分盡馬」
        
        特徵: 難贏但穩定進三甲的馬匹
        
        判定條件:
        1. Win/Place Ratio < 0.1 (冠軍比例低，難贏)
        2. 入位率 > 50% (但很穩定進位)
        3. 評分標準差 < 8 (性能非常穩定)
        
        參數:
            horse_metrics (Dict): 馬匹指標
            
        返回:
            bool: True 如果符合所有條件
        """
        ratio = horse_metrics.get('win_place_ratio', 0)
        placement_rate = horse_metrics.get('overall_placement_rate', 0)
        rating_std = horse_metrics.get('rating_std', 10)
        
        condition1 = ratio < 0.1
        condition2 = placement_rate > 0.5
        condition3 = rating_std < 8
        
        is_quitter = condition1 and condition2 and condition3
        
        if is_quitter:
            logger.info(f"✅ 識別為分盡馬")
            logger.info(f"   冠亞比={ratio:.3f} | 入位率={placement_rate:.1%} | 評分波動={rating_std:.1f}")
        
        return is_quitter
    
    def identify_loyal(self, horse_metrics: Dict) -> bool:
        """
        識別「忠心馬」
        
        特徵: 非常穩定且可靠的馬匹
        
        判定條件:
        1. 入位率 >= 50% (穩定進位)
        2. 評分標準差 < 6 (性能穩定度很高)
        
        參數:
            horse_metrics (Dict): 馬匹指標
            
        返回:
            bool: True 如果符合所有條件
        """
        placement_rate = horse_metrics.get('overall_placement_rate', 0)
        rating_std = horse_metrics.get('rating_std', 10)
        
        condition1 = placement_rate >= 0.5
        condition2 = rating_std < 6
        
        is_loyal = condition1 and condition2
        
        if is_loyal:
            logger.info(f"✅ 識別為忠心馬")
            logger.info(f"   入位率={placement_rate:.1%} | 評分波動={rating_std:.1f}")
        
        return is_loyal
    
    def identify_surface_specialist(self, horse_metrics: Dict) -> bool:
        """
        識別「場地得益」
        
        特徵: 在某個特定場地有明顯優勢的馬匹
        
        判定條件:
        1. 最好場地的入位率 - 全局入位率 >= 15%
        
        參數:
            horse_metrics (Dict): 馬匹指標
            
        返回:
            bool: True 如果符合條件
        """
        venue_stats = horse_metrics.get('venue_stats', {})
        overall_rate = horse_metrics.get('overall_placement_rate', 0)
        
        if not venue_stats or overall_rate <= 0:
            return False
        
        # 找到最好的場地入位率
        best_venue_rate = max(venue_stats.values()) if venue_stats else 0
        advantage = best_venue_rate - overall_rate
        
        is_specialist = advantage >= 0.15
        
        if is_specialist:
            logger.info(f"✅ 識別為場地得益馬")
            logger.info(f"   場地優勢={advantage:.1%} (最佳場地: {best_venue_rate:.1%} vs 全局: {overall_rate:.1%})")
        
        return is_specialist


# ============= 使用示例 =============

if __name__ == '__main__':
    """
    使用示例:
    
    from analyzers.leg_fitness_tag_identifier import TagIdentifier
    
    # 初始化識別器
    identifier = TagIdentifier()
    
    # 準備馬匹指標
    horse_metrics = {
        'overall_placement_rate': 0.52,
        'win_place_ratio': 0.08,
        'rating_std': 7.5,
        'venue_stats': {'沙田': 0.60, '跑馬地': 0.40}
    }
    
    # 識別標籤
    tags = identifier.identify_all_tags(horse_metrics)
    
    # 顯示結果
    print(f"標籤: {', '.join(tags)}")
    """
    print("✅ 標籤識別模塊已準備好")
    print("📖 請查閱文件中的使用示例或文檔")
