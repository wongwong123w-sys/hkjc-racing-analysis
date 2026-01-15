
# -*- coding: utf-8 -*-
"""
基礎分析器 - 共用標準時間查詢函數
Base Analyzer - Standard Time Lookup Functions
"""

from typing import Optional, Dict


def get_standard_time(racecourse: str, distance: int, class_name: str, standard_times_data: Dict) -> Optional[float]:
    """
    查詢標準完成時間
    
    參數:
        racecourse: 馬場名稱 (如 'Sha Tin', 'Happy Valley', 'Sha Tin AW')
        distance: 途程 (米)
        class_name: 班次 (如 '第一班', '分級賽')
        standard_times_data: 標準時間數據字典
    
    返回:
        標準完成時間 (秒)，若無數據則返回 None
    """
    try:
        if racecourse in standard_times_data:
            if distance in standard_times_data[racecourse]:
                if class_name in standard_times_data[racecourse][distance]:
                    return standard_times_data[racecourse][distance][class_name][0]
    except:
        pass
    return None


def get_standard_segments(racecourse: str, distance: int, class_name: str, standard_times_data: Dict) -> Optional[Dict]:
    """
    查詢標準分段時間
    
    參數:
        racecourse: 馬場名稱
        distance: 途程 (米)
        class_name: 班次
        standard_times_data: 標準時間數據字典
    
    返回:
        標準分段時間字典，若無數據則返回 None
    """
    try:
        if racecourse in standard_times_data:
            if distance in standard_times_data[racecourse]:
                if class_name in standard_times_data[racecourse][distance]:
                    return standard_times_data[racecourse][distance][class_name][1]
    except:
        pass
    return None


def get_standard_segment_sum(racecourse: str, distance: int, class_name: str, standard_times_data: Dict) -> Optional[float]:
    """
    根據距離範圍只加總相應分段
    
    規則:
    - 短途（≤1200米）：首兩段總和
    - 中距離（1400-1650米）：首三段總和
    - 長途（≥1800米）：首四段總和
    
    參數:
        racecourse: 馬場名稱
        distance: 途程 (米)
        class_name: 班次
        standard_times_data: 標準時間數據字典
    
    返回:
        標準分段總和 (秒)，若無數據則返回 None
    """
    segs = get_standard_segments(racecourse, distance, class_name, standard_times_data)
    if not segs:
        return None
    
    # 根據距離判定段數
    if distance <= 1200:
        segment_count = 2  # 短途：首兩段 ✅
    elif distance <= 1650:
        segment_count = 3  # 中距離：首三段 ✅
    else:
        segment_count = 4  # 長途：首四段 ✅
    
    # 只加總前 segment_count 段
    total = 0
    for i in range(min(segment_count, len(list(segs.values())))):
        total += list(segs.values())[i]
    
    return total if total > 0 else None
