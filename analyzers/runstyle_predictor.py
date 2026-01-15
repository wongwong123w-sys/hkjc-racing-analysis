
# -*- coding: utf-8 -*-
"""
馬匹跑法預測器 v4.2 - 簡潔評論版（修正）

RunstylePredictor - Concise Comment Version (Fixed)

改進：
- ✅ 改進 1: 近績權重（最近 3 場權重更高）
- ✅ 改進 2: 距離相似度過濾（±200米優先）
- ✅ 改進 3: 簡潔評論（精簡風格）
- ✅ 修復：支持空格分隔的 running_path（'1 1 5'）
- ✅ 修復：draw_factor → draw_adjustment

日期: 2026-01-10
"""

import numpy as np
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class RunstylePredictor:
    """
    馬匹跑法預測器 v4.2
    
    改進：
    - ✅ 改進 1: 近績權重（最近 3 場權重更高）
    - ✅ 改進 2: 距離相似度過濾（±200米優先）
    - ✅ 改進 3: 簡潔評論（精簡風格）
    - ✅ 修復：支持空格分隔的 running_path（'1 1 5'）
    - ✅ 修復：draw_factor → draw_adjustment
    """
    
    def __init__(self):
        """初始化預測器"""
        logger.info("✅ RunstylePredictor v4.2 (Concise-Fixed) 已初始化")
    
    def _filter_history_by_distance(
        self, 
        history: List[Dict], 
        target_distance: int, 
        tolerance: int = 200,
        min_records: int = 3
    ) -> List[Dict]:
        """距離相似度過濾"""
        if not history or not target_distance:
            return history
        
        logger.debug(f"🔍 距離過濾: 目標={target_distance}米, 往績數={len(history)}")
        
        # ±200 米
        filtered_200 = [
            r for r in history 
            if r.get('distance') and abs(r['distance'] - target_distance) <= 200
        ]
        
        if len(filtered_200) >= min_records:
            logger.debug(f"✅ 使用 ±200 米: {len(filtered_200)} 場")
            return filtered_200
        
        # ±400 米
        filtered_400 = [
            r for r in history 
            if r.get('distance') and abs(r['distance'] - target_distance) <= 400
        ]
        
        if len(filtered_400) >= min_records:
            logger.debug(f"✅ 使用 ±400 米: {len(filtered_400)} 場")
            return filtered_400
        
        logger.debug(f"⚠️ 使用全部 {len(history)} 場")
        return history
    
    def _get_draw_analysis(self, draw: int, total_runners: int) -> tuple:
        """
        檔位分析（返回修正值和簡潔描述）
        
        Returns:
            tuple: (adjustment, description)
        """
        midpoint = (total_runners + 1) / 2.0
        
        if draw <= midpoint - 2:
            return (-0.3, f"內檔{draw}有利跑前")
        elif draw >= midpoint + 2:
            return (+0.5, f"外檔{draw}可能被迫靠後")
        elif draw >= midpoint - 1 and draw <= midpoint + 1:
            return (0.0, f"中檔{draw}無特殊影響")
        elif draw > midpoint + 1:
            return (+0.3, f"外檔{draw}稍不利")
        else:
            return (-0.1, f"內檔{draw}稍有利")
    
    def predict_running_style(
        self, 
        horse_data: Dict, 
        total_runners: Optional[int] = None
    ) -> Optional[Dict]:
        """預測馬匹跑法（簡潔版）"""
        try:
            horse_num = horse_data.get('horse_number', 0)
            horse_name = horse_data.get('horse_name', '未知')
            draw = horse_data.get('barrier') or horse_data.get('draw', 0)
            target_distance = horse_data.get('distance', 1200)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"🐴 預測: 馬{horse_num} {horse_name} (檔位={draw}, {target_distance}米)")
            
            history = horse_data.get('history', [])
            
            if not history:
                logger.warning(f"❌ 無往績")
                return None
            
            logger.info(f"  原始往績: {len(history)} 場")
            
            # 距離過濾
            filtered_history = self._filter_history_by_distance(
                history, target_distance, tolerance=200, min_records=3
            )
            
            if not filtered_history:
                logger.warning(f"❌ 過濾後無往績")
                return None
            
            logger.info(f"  過濾後: {len(filtered_history)} 場")
            
            # 提取早段位置
            valid_records = []
            early_positions = []
            
            for idx, record in enumerate(filtered_history):
                running_path = record.get('running_path', '')
                
                logger.debug(f"    往績{idx+1}: '{running_path}', {record.get('distance')}米")
                
                if not running_path or running_path == '-' or running_path == '--':
                    logger.debug(f"      ⚠️ 跳過: 無效")
                    continue
                
                # 支持空格、逗號、破折號分隔
                positions = (
                    running_path
                    .replace(' ', '-')
                    .replace(',', '-')
                    .split('-')
                )
                
                positions = [p.strip() for p in positions if p.strip()]
                
                if not positions:
                    logger.debug(f"      ⚠️ 跳過: 解析後為空")
                    continue
                
                try:
                    early_pos = int(positions[0])
                    early_positions.append(early_pos)
                    valid_records.append(record)
                    logger.debug(f"      ✅ 早段位置: {early_pos}")
                except (ValueError, IndexError) as e:
                    logger.debug(f"      ❌ 解析失敗: {e}")
                    continue
            
            if not early_positions:
                logger.warning(f"❌ 無有效早段位置")
                return None
            
            logger.info(f"  有效早段位置: {early_positions}")
            
            # 近績權重
            has_dates = all('date' in r for r in valid_records)
            if has_dates:
                valid_records_with_pos = list(zip(valid_records, early_positions))
                valid_records_with_pos.sort(
                    key=lambda x: x[0].get('date', ''), 
                    reverse=True
                )
                valid_records = [r for r, _ in valid_records_with_pos]
                early_positions = [p for _, p in valid_records_with_pos]
            
            # 計算權重
            recency_weights = [
                max(0.5, 1.0 - 0.1 * idx) 
                for idx in range(len(early_positions))
            ]
            
            # 加權平均
            baseline_pos = np.average(early_positions, weights=recency_weights)
            
            # 計算穩定性
            std_dev = np.std(early_positions) if len(early_positions) > 1 else 0
            
            logger.info(f"  加權基準位: {baseline_pos:.2f} (標準差: {std_dev:.2f})")
            
            # 檔位修正
            if total_runners is None:
                total_runners = 12
            
            draw_adjustment, draw_desc = self._get_draw_analysis(draw, total_runners)
            adjusted_pos = baseline_pos + draw_adjustment
            
            logger.info(f"  檔位分析: {draw_desc}")
            logger.info(f"  修正: {draw_adjustment:+.1f} → 調整位: {adjusted_pos:.2f}")
            
            # 動態分類
            front_threshold = total_runners * 0.3
            back_threshold = total_runners * 0.7
            
            if adjusted_pos <= front_threshold:
                running_style = "FRONT"
                style_desc = "領放/跟放" if baseline_pos > 3 else "領放"
            elif adjusted_pos > back_threshold:
                running_style = "BACK"
                style_desc = "留後/後上"
            else:
                running_style = "MID"
                style_desc = "中置/跟前"
            
            # 信心度
            confidence = self._calculate_confidence(
                valid_records, early_positions, len(filtered_history)
            )
            
            logger.info(f"  跑法: {running_style} ({style_desc}), 信心度: {confidence}%")
            
            # ========================================
            # ✅ 簡潔評論（風格統一）
            # ========================================
            
            # 跑法描述
            base_desc = f"{horse_name} 習慣{style_desc}"
            
            # 往績描述
            if len(early_positions) >= 8:
                reliability = "往績充分"
            elif len(early_positions) >= 5:
                reliability = "往績尚可"
            else:
                reliability = "往績較少"
            
            # 穩定性描述
            if std_dev <= 2:
                consistency = "跑法穩定"
            elif std_dev <= 4:
                consistency = "跑法一般"
            else:
                consistency = "跑法不穩"
            
            # 組合評論
            comment = f"{base_desc}。{draw_desc}。{reliability}，{consistency}，預測位置 {adjusted_pos:.1f}"
            
            logger.info(f"✅ 預測成功")
            logger.info(f"{'='*60}\n")
            
            return {
                'horse_number': horse_num,
                'horse_name': horse_name,
                'baseline_position': round(baseline_pos, 2),
                'adjusted_position': round(adjusted_pos, 2),
                'running_style': running_style,
                'confidence': round(confidence, 2),
                'comment': comment,
                'is_new_horse': False,
                'early_positions': early_positions,
                'std_dev': round(std_dev, 2)
            }
        
        except Exception as e:
            logger.error(f"❌ 預測失敗: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _calculate_confidence(
        self, 
        records: List[Dict], 
        positions: List[int],
        filtered_count: int
    ) -> float:
        """計算信心度"""
        if filtered_count >= 6:
            base_confidence = 85
        elif filtered_count >= 4:
            base_confidence = 75
        elif filtered_count >= 3:
            base_confidence = 65
        else:
            base_confidence = 50
        
        if len(positions) > 1:
            std_dev = np.std(positions)
            
            if std_dev > 3.0:
                stability_penalty = -15
            elif std_dev > 2.0:
                stability_penalty = -10
            elif std_dev > 1.5:
                stability_penalty = -5
            else:
                stability_penalty = 0
        else:
            stability_penalty = -10
        
        confidence = base_confidence + stability_penalty
        
        return max(0, min(100, confidence))
    
    def predict_new_horse_running_style(
        self, 
        horse_data: Dict, 
        total_runners: Optional[int] = None
    ) -> Optional[Dict]:
        """預測無往績馬（簡潔版）"""
        try:
            horse_num = horse_data.get('horse_number', 0)
            horse_name = horse_data.get('horse_name', '未知')
            draw = horse_data.get('barrier') or horse_data.get('draw', 0)
            rating = horse_data.get('rating', 70)
            
            logger.info(f"🆕 新馬: 馬{horse_num} {horse_name}, 評分={rating}, 檔={draw}")
            
            if total_runners is None:
                total_runners = 12
            
            # 基準位置（中點）
            midpoint = (total_runners + 1) / 2.0
            baseline_pos = midpoint
            
            # 評分修正
            rating_factor = (rating - 70) / 20.0
            rating_adjustment = rating_factor * 2
            
            # 檔位修正
            draw_adjustment, draw_desc = self._get_draw_analysis(draw, total_runners)
            
            # ✅ 修正：使用 draw_adjustment 而非 draw_factor
            adjusted_pos = baseline_pos + draw_adjustment + rating_adjustment
            adjusted_pos = max(1.0, min(adjusted_pos, float(total_runners)))
            
            # 分類
            front_threshold = total_runners * 0.3
            back_threshold = total_runners * 0.7
            
            if adjusted_pos <= front_threshold:
                running_style = "FRONT"
                if rating >= 85:
                    style_desc = "評分優異，傾向領放或跟放"
                else:
                    style_desc = "預期跑法以領放為主"
            elif adjusted_pos > back_threshold:
                running_style = "BACK"
                if rating <= 65:
                    style_desc = "評分偏低，傾向留後"
                else:
                    style_desc = "預期跑法以後上為主"
            else:
                running_style = "MID"
                style_desc = "綜合評估為中置馬"
            
            # 信心度
            base_confidence = 50
            if rating >= 80:
                confidence_bonus = 10
            elif rating >= 70:
                confidence_bonus = 5
            else:
                confidence_bonus = 0
            confidence = min(60, base_confidence + confidence_bonus)
            
            # ========================================
            # ✅ 簡潔評論（新馬風格）
            # ========================================
            
            # 評分描述
            if rating >= 85:
                rating_desc = f"，評分{rating}屬高水平"
            elif rating <= 65:
                rating_desc = f"，評分{rating}較低需磨練"
            else:
                rating_desc = f"，評分{rating}接近平均"
            
            # 組合評論
            comment = f"{horse_name} {style_desc}。{draw_desc}{rating_desc}。無往績馬預測信心度較低，僅供參考，預測位置 {adjusted_pos:.1f}"
            
            logger.info(f"✅ 新馬預測: {running_style}, 位置: {adjusted_pos:.1f}")
            
            return {
                'horse_number': horse_num,
                'horse_name': horse_name,
                'baseline_position': round(baseline_pos, 2),
                'adjusted_position': round(adjusted_pos, 2),
                'running_style': running_style,
                'confidence': confidence,
                'comment': comment,
                'is_new_horse': True
            }
        
        except Exception as e:
            logger.error(f"❌ 新馬預測失敗: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    
    print("\n" + "="*60)
    print("測試 1: 有往績馬")
    print("="*60)
    
    test_horse = {
        'horse_number': 1,
        'horse_name': '凌風傲雪',
        'draw': 3,
        'distance': 1200,
        'history': [
            {'distance': 1200, 'running_path': '1 1 5', 'date': '2026-01-05'},
            {'distance': 1200, 'running_path': '2 2 6', 'date': '2025-12-20'},
            {'distance': 1200, 'running_path': '1 1 2', 'date': '2025-12-10'},
            {'distance': 1200, 'running_path': '3 3 7', 'date': '2025-11-25'},
        ]
    }
    
    predictor = RunstylePredictor()
    result = predictor.predict_running_style(test_horse, total_runners=12)
    
    if result:
        print(f"\n✅ 預測結果:")
        print(f"  跑法: {result['running_style']}")
        print(f"  信心度: {result['confidence']}%")
        print(f"  評論: {result['comment']}")
    
    print("\n" + "="*60)
    print("測試 2: 無往績馬")
    print("="*60)
    
    test_new_horse = {
        'horse_number': 2,
        'horse_name': '新星馬',
        'draw': 4,
        'rating': 85
    }
    
    result2 = predictor.predict_new_horse_running_style(test_new_horse, total_runners=12)
    
    if result2:
        print(f"\n✅ 預測結果:")
        print(f"  跑法: {result2['running_style']}")
        print(f"  信心度: {result2['confidence']}%")
        print(f"  評論: {result2['comment']}")
