
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

    def predict_pace_by_epp(self, predictions: List[Dict], total_horses: int = 12) -> Dict:
        """EPP (Expected Pace Profile) 方法預測配速 - 前段壓力指標版"""
        try:
            logger.info("=" * 60)
            logger.info("🔍 EPP 方法：前段壓力指標計算")
            logger.info("=" * 60)
            
            if not predictions or len(predictions) == 0:
                logger.warning("無預測數據，使用默認值")
                return {
                    "pace_type": "NORMAL",
                    "pace_value": 2.0,
                    "confidence": 0.0,
                    "reasoning": "無數據",
                    "details": {},
                }
            
            # ========================================
            # ✅ 第一步：計算前段壓力指標 (EPP)
            # ========================================
            front_threshold = total_horses / 3.0  # 前段定義：前 1/3 位置
            logger.info(f"前段門值: ≤ {front_threshold:.1f} 位")
            
            epp = 0.0  # EPP 指數（馬匹數）
            front_horses = []  # 前段馬匹明細
            
            for p in predictions:
                # ✅ 使用 adjusted_position 而非 running_style
                adj_pos = p.get('adjusted_position')
                draw = p.get('draw', 6)
                horse_name = p.get('horse_name', f"馬{p.get('horse_number', '?')}")
                
                if adj_pos is None:
                    logger.warning(f"⚠️ {horse_name} 缺少 adjusted_position，跳過")
                    continue
                
                # 判斷是否為前段馬
                if adj_pos <= front_threshold:
                    # ✅ 外檔加權（檔位 ≥ 9）
                    if draw >= 9:
                        weight = 1.5  # 外檔搶放加權（可優化至 1.8）
                        epp += weight
                        front_horses.append({
                            'name': horse_name,
                            'adjusted_position': adj_pos,
                            'draw': draw,
                            'weight': weight,
                            'note': '外檔搶放'
                        })
                        logger.debug(f"  ✅ {horse_name} (檔{draw}, 調整位{adj_pos:.2f}) +{weight} [外檔]")
                    else:
                        weight = 1.0
                        epp += weight
                        front_horses.append({
                            'name': horse_name,
                            'adjusted_position': adj_pos,
                            'draw': draw,
                            'weight': weight,
                            'note': '內/中檔'
                        })
                        logger.debug(f"  ✅ {horse_name} (檔{draw}, 調整位{adj_pos:.2f}) +{weight}")
            
            logger.info(f"前段壓力馬數: {len(front_horses)} 匹")
            logger.info(f"加權 EPP 指數: {epp:.2f}")
            
            # ========================================
            # ✅ 第二步：配速判定（符合附件標準）
            # ========================================
            # 基於 12 匹馬的標準，按比例調整
            epp_ratio = epp / total_horses  # 標準化比例
            
            # ✅ 附件標準的門值（12 匹馬基準）
            if epp <= 2.0:
                pace_type = "SLOW"
                pace_name = "慢步速"
                confidence = 75.0
            elif epp <= 3.2:
                pace_type = "MODERATELY_SLOW"
                pace_name = "偏慢步速"
                confidence = 75.0
            elif epp <= 4.5:
                pace_type = "NORMAL"
                pace_name = "中等步速"
                confidence = 80.0
            elif epp <= 5.8:
                pace_type = "MODERATELY_FAST"
                pace_name = "偏快步速"
                confidence = 75.0
            else:
                pace_type = "FAST"
                pace_name = "快步速"
                confidence = 70.0
            
            logger.info(f"配速判定: {pace_type} ({pace_name}), EPP={epp:.2f}")
            
            # ========================================
            # ✅ 第三步：推理文字
            # ========================================
            if epp_ratio >= 0.5:
                reasoning = f"大量前段壓力馬({len(front_horses)}匹, EPP={epp:.1f})，搶位激烈 → 預期快步速"
            elif epp_ratio >= 0.3:
                reasoning = f"適量前段壓力馬({len(front_horses)}匹, EPP={epp:.1f})，配速均衡 → 預期中等步速"
            else:
                reasoning = f"前段壓力較低({len(front_horses)}匹, EPP={epp:.1f})，節奏穩定 → 預期較慢步速"
            
            logger.info(f"推理: {reasoning}")
            
            # ========================================
            # ✅ 返回結果（與原格式相容）
            # ========================================
            result = {
                "pace_type": pace_type,
                "pace_value": round(epp, 2),  # ✅ 返回 EPP 指數本身
                "confidence": round(confidence, 1),
                "reasoning": reasoning,
                "details": {
                    "front_threshold": round(front_threshold, 2),
                    "front_horses_count": len(front_horses),
                    "front_horses": front_horses,  # 明細列表
                    "epp_index": round(epp, 2),
                    "epp_ratio": round(epp_ratio, 3),
                    "total_horses": total_horses
                },
            }
            
            logger.info(f"✓ EPP 方法完成: {pace_type} (EPP={epp:.2f}, 信心度: {confidence}%)")
            return result
            
        except Exception as e:
            logger.error(f"❌ EPP 方法出錯: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "pace_type": "NORMAL",
                "pace_value": 2.0,
                "confidence": 0.0,
                "reasoning": f"錯誤: {str(e)}",
                "details": {},
            }

    def _pace_type_to_value(self, pace_type: str) -> float:
        """將配速類型轉換為數值 (1.0–3.0)，用於融合計算。"""
        pace_mapping = {
            "SLOW": 1.0,
            "MODERATELY_SLOW": 1.5,
            "NORMAL": 2.0,
            "MODERATELY_FAST": 2.5,
            "FAST": 3.0,
        }
        value = pace_mapping.get(pace_type, 2.0)
        logger.debug(f"配速轉換: {pace_type} → {value}")
        return value

    def _value_to_pace_type(self, value: float) -> str:
        """將數值配速轉回類型（最近鄰）。"""
        if value <= 1.25:
            return "SLOW"
        elif value <= 1.75:
            return "MODERATELY_SLOW"
        elif value <= 2.25:
            return "NORMAL"
        elif value <= 2.75:
            return "MODERATELY_FAST"
        else:
            return "FAST"

    def _analyze_confidence_trend(self, conf_t: float, conf_e: float) -> str:
        """分析傳統方法 vs EPP 方法置信度誰更強。"""
        diff = conf_t - conf_e
        if diff > 10:
            trend = "傳統方法更有信心"
        elif diff < -10:
            trend = "EPP 方法更有信心"
        else:
            trend = "兩個方法置信度接近"

        logger.debug(f"置信度趨勢: {trend} (差異: {diff:.1f}%)")
        return trend

    def _get_timestamp(self) -> str:
        """回傳當前時間戳字串。"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    def predict_pace_hybrid_v1_confidence_weighted(
        self, predictions: List[Dict], total_horses: int = 12
    ) -> Dict:
        """融合預測方案 A：置信度加權融合。"""
        logger.info("=" * 60)
        logger.info("🔄 開始融合預測 (方案 A：置信度加權)")
        logger.info("=" * 60)
    
        try:
            # ===== 1. 檢查數據 =====
            logger.info("📊 [1/5] 檢查預測數據...")
            
            if not predictions or len(predictions) == 0:
                logger.warning("無預測數據，返回預設值")
                return {
                    'method': 'hybrid',
                    'status': 'no_data',
                    'pace_type': 'NORMAL',
                    'pace_name': '未知',
                    'confidence': 0,
                    'characteristics': '無數據',
                    'suggestion': '需要更多數據',
                    'distribution_result': {},
                    'pressure_result': {},
                    'distances': {}
                }
            
            # ===== 2. 傳統方法（馬群分佈分析） =====
            logger.info("📊 [2/5] 計算傳統步速預測...")
            pace_traditional = self.predict_pace_diagnostic(predictions)
            conf_traditional = pace_traditional.get("confidence", 50.0)
            pace_type_t = pace_traditional.get("pace_type", "NORMAL")
            pace_value_t = self._pace_type_to_value(pace_type_t)
            
            # ✨ 獲取馬群分佈數據
            distribution = self.get_runstyle_distribution(predictions)
            
            # ===== 3. EPP 方法（前段壓力分析） =====
            logger.info("📊 [3/5] 計算 EPP 步速預測...")
            pace_epp = self.predict_pace_by_epp(predictions, total_horses)
            conf_epp = pace_epp.get("confidence", 50.0)
            pace_type_e = pace_epp.get("pace_type", "NORMAL")
            pace_value_e = pace_epp.get("pace_value", 2.0)
            
            # ===== 4. 置信度加權融合 =====
            logger.info("📊 [4/5] 進行置信度加權融合...")
            
            # 計算權重（基於置信度）
            total_confidence = conf_traditional + conf_epp
            if total_confidence > 0:
                w_traditional = conf_traditional / total_confidence
                w_epp = conf_epp / total_confidence
            else:
                w_traditional = 0.5
                w_epp = 0.5
            
            logger.info(f"   傳統方法: 配速={pace_type_t}, 置信度={conf_traditional:.1f}%, 權重={w_traditional:.2f}")
            logger.info(f"   EPP 方法: 配速={pace_type_e}, 置信度={conf_epp:.1f}%, 權重={w_epp:.2f}")
            
            # 融合配速數值
            pace_value_fusion = w_traditional * pace_value_t + w_epp * pace_value_e
            pace_type_fusion = self._value_to_pace_type(pace_value_fusion)
            
            logger.info(f"   融合結果: 配速數值={pace_value_fusion:.2f} → 類型={pace_type_fusion}")
            
            # 計算融合後的置信度
            divergence = abs(pace_value_t - pace_value_e)
            
            if divergence < 0.5:
                consensus = "兩個方法高度一致"
                confidence_fusion = min(95, (conf_traditional + conf_epp) / 2 * 1.2)
            elif divergence < 1.0:
                consensus = "兩個方法基本一致"
                confidence_fusion = (conf_traditional + conf_epp) / 2
            else:
                consensus = "兩個方法存在分歧"
                confidence_fusion = (conf_traditional + conf_epp) / 2 * 0.8
            
            logger.info(f"   一致性: {consensus} (分歧度={divergence:.2f})")
            logger.info(f"   融合置信度: {confidence_fusion:.1f}%")
            
            # 生成建議
            if divergence >= 1.0:
                if conf_traditional > conf_epp + 15:
                    recommendation = "建議偏向傳統方法（馬群分佈分析）"
                elif conf_epp > conf_traditional + 15:
                    recommendation = "建議偏向 EPP 方法（前段壓力分析）"
                else:
                    recommendation = "兩個方法分歧較大，建議結合賽事實況判斷"
                warning = "⚠️ 注意：兩個方法的預測存在明顯差異"
            else:
                recommendation = "兩個方法預測一致，可信度較高"
                warning = None
            
            # ===== 5. 構建頁面兼容的返回格式 =====
            logger.info("🔍 [5/5] 生成分析...")
            
            # 獲取融合後的配速模板
            fusion_template = self.pace_templates.get(pace_type_fusion, self.pace_templates['NORMAL'])
            
            result = {
                # ✅ 頂層必需欄位（頁面直接使用）
                'pace_type': pace_type_fusion,
                'pace_name': fusion_template['name'],
                'confidence': round(confidence_fusion, 1),
                'characteristics': fusion_template['characteristics'],
                'suggestion': fusion_template['suggestion'],
                'method': 'hybrid',
                
                # ✅ 馬群分佈分析結果（用於詳細展示）
                'distribution_result': {
                    'pace_type': pace_type_t,
                    'pace_name': pace_traditional.get('pace_name', '未知'),
                    'confidence': round(conf_traditional, 1),
                    'front_count': distribution['FRONT'],
                    'mid_count': distribution['MID'],
                    'back_count': distribution['BACK'],
                    'total': distribution['total']
                },
                
                # ✅ 前段壓力分析結果（用於詳細展示）
                'pressure_result': {
                    'pace_type': pace_type_e,
                    'pace_name': self.pace_templates.get(pace_type_e, {}).get('name', '未知'),
                    'confidence': round(conf_epp, 1),
                    'pressure_index': pace_epp.get('pace_value', 2.0),
                    'details': pace_epp.get('details', {})  # ✅ 完整傳遞 EPP 的 details
                },
                
                # ✅ 距離矩陣（用於診斷頁面）
                'distances': pace_traditional.get('distances', {}),
                
                # ✅ 距離調整因子（預設值，需要在頁面層處理實際距離）
                'distance_factor': 1.0,
                
                # 📊 原始詳細數據（用於進階分析）
                'traditional': {
                    'pace_type': pace_type_t,
                    'pace_value': round(pace_value_t, 2),
                    'confidence': round(conf_traditional, 1),
                    'reasoning': pace_traditional.get('characteristics', '')
                },
                'epp': {
                    'pace_type': pace_type_e,
                    'pace_value': round(pace_value_e, 2),
                    'confidence': round(conf_epp, 1),
                    'reasoning': pace_epp.get('reasoning', ''),
                    'details': pace_epp.get('details', {})
                },
                'fusion': {
                    'pace_type': pace_type_fusion,
                    'pace_value': round(pace_value_fusion, 2),
                    'confidence': round(confidence_fusion, 1),
                    'weights': {
                        'traditional': round(w_traditional, 3),
                        'epp': round(w_epp, 3)
                    },
                    'divergence': round(divergence, 2)
                },
                'analysis': {
                    'consensus': consensus,
                    'recommendation': recommendation,
                    'warning': warning,
                    'confidence_trend': self._analyze_confidence_trend(
                        conf_traditional, conf_epp
                    )
                },
                
                # 元數據
                'method_version': 'v1.0_confidence_weighted',
                'timestamp': self._get_timestamp(),
                'status': 'success'
            }
            
            logger.info("=" * 60)
            logger.info("✅ 融合預測完成！")
            logger.info("=" * 60)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 融合預測錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                'method': 'hybrid',
                'status': 'error',
                'pace_type': 'NORMAL',
                'pace_name': '錯誤',
                'confidence': 0,
                'characteristics': f'錯誤: {str(e)}',
                'suggestion': '請檢查數據',
                'distribution_result': {},
                'pressure_result': {},
                'distances': {},
                'error_message': str(e)
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
