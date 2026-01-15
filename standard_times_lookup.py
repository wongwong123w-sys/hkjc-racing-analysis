"""
香港賽馬標準時間與分段時間查詢模組
HKJC Standard Times and Sectional Times Lookup Module

用於完成時間與標準時間比較，以及步速分析
For race pace analysis and sectional comparison

資料來源：香港賽馬會 2024-2025年度
Data Source: HKJC 2024-2025 Season
"""

import pandas as pd
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

# ============================================================================
# 第一部分：標準時間數據庫定義
# PART 1: STANDARD TIMES DATABASE
# ============================================================================

STANDARD_TIMES_DB = {
    # 沙田草地 (Sha Tin Turf)
    "Sha Tin": {
        1000: {
            "分級賽": {"std_time": 55.90, "segments": {"起點-800": 13.05, "800-400": 20.60, "400-終點": 22.25}},
            "第二班": {"std_time": 56.05, "segments": {"起點-800": 13.10, "800-400": 20.60, "400-終點": 22.35}},
            "第三班": {"std_time": 56.45, "segments": {"起點-800": 13.05, "800-400": 20.65, "400-終點": 22.75}},
            "第四班": {"std_time": 56.65, "segments": {"起點-800": 13.00, "800-400": 20.75, "400-終點": 22.90}},
            "第五班": {"std_time": 57.00, "segments": {"起點-800": 13.15, "800-400": 20.95, "400-終點": 22.90}},
            "新馬賽": {"std_time": 56.65, "segments": {"起點-800": 13.25, "800-400": 20.80, "400-終點": 22.60}},
        },
        1200: {
            "分級賽": {"std_time": 68.15, "segments": {"起點-800": 23.55, "800-400": 22.20, "400-終點": 22.40}},
            "第一班": {"std_time": 68.45, "segments": {"起點-800": 23.60, "800-400": 22.25, "400-終點": 22.60}},
            "第二班": {"std_time": 68.65, "segments": {"起點-800": 23.75, "800-400": 22.25, "400-終點": 22.65}},
            "第三班": {"std_time": 69.00, "segments": {"起點-800": 23.70, "800-400": 22.35, "400-終點": 22.95}},
            "第四班": {"std_time": 69.35, "segments": {"起點-800": 23.75, "800-400": 22.45, "400-終點": 23.15}},
            "第五班": {"std_time": 69.55, "segments": {"起點-800": 23.85, "800-400": 22.40, "400-終點": 23.30}},
            "新馬賽": {"std_time": 69.90, "segments": {"起點-800": 23.95, "800-400": 22.95, "400-終點": 23.00}},
        },
        1400: {
            "分級賽": {"std_time": 81.10, "segments": {"起點-1200": 13.50, "1200-800": 22.35, "800-400": 22.85, "400-終點": 22.40}},
            "第一班": {"std_time": 81.25, "segments": {"起點-1200": 13.65, "1200-800": 22.00, "800-400": 22.90, "400-終點": 22.70}},
            "第二班": {"std_time": 81.45, "segments": {"起點-1200": 13.45, "1200-800": 21.90, "800-400": 23.10, "400-終點": 23.00}},
            "第三班": {"std_time": 81.65, "segments": {"起點-1200": 13.45, "1200-800": 21.80, "800-400": 23.15, "400-終點": 23.25}},
            "第四班": {"std_time": 82.00, "segments": {"起點-1200": 13.45, "1200-800": 21.75, "800-400": 23.40, "400-終點": 23.40}},
            "第五班": {"std_time": 82.30, "segments": {"起點-1200": 13.40, "1200-800": 21.90, "800-400": 23.35, "400-終點": 23.65}},
        },
        1600: {
            "分級賽": {"std_time": 93.90, "segments": {"起點-1200": 24.85, "1200-800": 23.05, "800-400": 23.25, "400-終點": 22.75}},
            "第一班": {"std_time": 94.05, "segments": {"起點-1200": 24.75, "1200-800": 23.15, "800-400": 23.15, "400-終點": 23.00}},
            "第二班": {"std_time": 94.25, "segments": {"起點-1200": 24.55, "1200-800": 23.15, "800-400": 23.45, "400-終點": 23.10}},
            "第三班": {"std_time": 94.70, "segments": {"起點-1200": 24.50, "1200-800": 22.90, "800-400": 23.80, "400-終點": 23.50}},
            "第四班": {"std_time": 94.90, "segments": {"起點-1200": 24.50, "1200-800": 22.90, "800-400": 23.80, "400-終點": 23.70}},
            "第五班": {"std_time": 95.45, "segments": {"起點-1200": 24.55, "1200-800": 23.15, "800-400": 23.85, "400-終點": 23.90}},
        },
        1800: {
            "分級賽": {"std_time": 107.10, "segments": {"起點-1600": 14.05, "1600-1200": 22.80, "1200-800": 24.00, "800-400": 23.50, "400-終點": 22.75}},
            "第二班": {"std_time": 107.30, "segments": {"起點-1600": 14.00, "1600-1200": 22.60, "1200-800": 23.95, "800-400": 23.35, "400-終點": 23.40}},
            "第三班": {"std_time": 107.50, "segments": {"起點-1600": 13.85, "1600-1200": 22.30, "1200-800": 23.80, "800-400": 24.00, "400-終點": 23.55}},
            "第四班": {"std_time": 107.85, "segments": {"起點-1600": 13.85, "1600-1200": 22.20, "1200-800": 23.85, "800-400": 24.20, "400-終點": 23.75}},
            "第五班": {"std_time": 108.45, "segments": {"起點-1600": 13.95, "1600-1200": 22.25, "1200-800": 23.85, "800-400": 24.20, "400-終點": 24.20}},
        },
        2000: {
            "分級賽": {"std_time": 120.50, "segments": {"起點-1600": 25.95, "1600-1200": 23.90, "1200-800": 23.90, "800-400": 23.55, "400-終點": 23.20}},
            "第一班": {"std_time": 121.20, "segments": {"起點-1600": 26.10, "1600-1200": 24.35, "1200-800": 23.95, "800-400": 23.60, "400-終點": 23.20}},
            "第二班": {"std_time": 121.70, "segments": {"起點-1600": 26.05, "1600-1200": 24.65, "1200-800": 24.20, "800-400": 23.40, "400-終點": 23.40}},
            "第三班": {"std_time": 121.90, "segments": {"起點-1600": 26.05, "1600-1200": 24.70, "1200-800": 24.05, "800-400": 23.55, "400-終點": 23.55}},
            "第四班": {"std_time": 122.35, "segments": {"起點-1600": 25.85, "1600-1200": 24.40, "1200-800": 24.40, "800-400": 23.95, "400-終點": 23.75}},
            "第五班": {"std_time": 122.65, "segments": {"起點-1600": 25.75, "1600-1200": 24.40, "1200-800": 24.35, "800-400": 23.95, "400-終點": 24.20}},
        },
        2400: {
            "分級賽": {"std_time": 147.00, "segments": {"起點-2000": 25.60, "2000-1600": 24.50, "1600-1200": 25.35, "1200-800": 23.85, "800-400": 23.75, "400-終點": 23.95}},
        },
    },
    
    # 跑馬地草地 (Happy Valley)
    "Happy Valley": {
        1000: {
            "分級賽": {"std_time": 56.00, "segments": {"起點-800": 12.80, "800-400": 21.00, "400-終點": 22.20}},
            "第二班": {"std_time": 56.40, "segments": {"起點-800": 12.45, "800-400": 21.00, "400-終點": 22.95}},
            "第三班": {"std_time": 56.65, "segments": {"起點-800": 12.50, "800-400": 21.00, "400-終點": 23.15}},
            "第四班": {"std_time": 57.20, "segments": {"起點-800": 12.55, "800-400": 21.30, "400-終點": 23.35}},
            "第五班": {"std_time": 57.35, "segments": {"起點-800": 12.60, "800-400": 21.40, "400-終點": 23.35}},
        },
        1200: {
            "第一班": {"std_time": 69.10, "segments": {"起點-800": 23.55, "800-400": 22.30, "400-終點": 23.25}},
            "第二班": {"std_time": 69.30, "segments": {"起點-800": 23.45, "800-400": 22.35, "400-終點": 23.50}},
            "第三班": {"std_time": 69.60, "segments": {"起點-800": 23.50, "800-400": 22.55, "400-終點": 23.55}},
            "第四班": {"std_time": 69.90, "segments": {"起點-800": 23.65, "800-400": 22.70, "400-終點": 23.55}},
            "第五班": {"std_time": 70.10, "segments": {"起點-800": 23.70, "800-400": 22.75, "400-終點": 23.65}},
        },
        1650: {
            "第一班": {"std_time": 99.10, "segments": {"起點-1200": 28.45, "1200-800": 23.90, "800-400": 23.35, "400-終點": 23.40}},
            "第二班": {"std_time": 99.30, "segments": {"起點-1200": 28.00, "1200-800": 23.85, "800-400": 23.80, "400-終點": 23.65}},
            "第三班": {"std_time": 99.90, "segments": {"起點-1200": 27.95, "1200-800": 23.85, "800-400": 24.25, "400-終點": 23.85}},
            "第四班": {"std_time": 100.10, "segments": {"起點-1200": 28.00, "1200-800": 23.80, "800-400": 24.25, "400-終點": 24.05}},
            "第五班": {"std_time": 100.30, "segments": {"起點-1200": 27.95, "1200-800": 23.90, "800-400": 24.25, "400-終點": 24.20}},
        },
        1800: {
            "分級賽": {"std_time": 108.95, "segments": {"起點-1600": 13.65, "1600-1200": 22.90, "1200-800": 24.35, "800-400": 24.15, "400-終點": 23.90}},
            "第二班": {"std_time": 109.15, "segments": {"起點-1600": 13.65, "1600-1200": 22.80, "1200-800": 24.55, "800-400": 24.20, "400-終點": 23.95}},
            "第三班": {"std_time": 109.45, "segments": {"起點-1600": 13.75, "1600-1200": 23.00, "1200-800": 24.30, "800-400": 24.45, "400-終點": 23.95}},
            "第四班": {"std_time": 109.65, "segments": {"起點-1600": 13.75, "1600-1200": 22.90, "1200-800": 24.35, "800-400": 24.35, "400-終點": 24.30}},
            "第五班": {"std_time": 109.95, "segments": {"起點-1600": 13.70, "1600-1200": 22.80, "1200-800": 24.50, "800-400": 24.40, "400-終點": 24.55}},
        },
        2200: {
            "第三班": {"std_time": 136.60, "segments": {"起點-2000": 14.35, "2000-1600": 23.70, "1600-1200": 24.95, "1200-800": 24.85, "800-400": 24.45, "400-終點": 24.30}},
            "第四班": {"std_time": 137.05, "segments": {"起點-2000": 14.40, "2000-1600": 23.60, "1600-1200": 25.25, "1200-800": 25.15, "800-400": 24.30, "400-終點": 24.35}},
            "第五班": {"std_time": 137.35, "segments": {"起點-2000": 14.35, "2000-1600": 23.70, "1600-1200": 25.40, "1200-800": 25.15, "800-400": 24.15, "400-終點": 24.60}},
        },
    },
    
    # 沙田全天候 (Sha Tin All-Weather)
    "Sha Tin AW": {
        1200: {
            "第二班": {"std_time": 68.35, "segments": {"起點-800": 23.35, "800-400": 21.95, "400-終點": 23.05}},
            "第三班": {"std_time": 68.55, "segments": {"起點-800": 23.30, "800-400": 22.05, "400-終點": 23.20}},
            "第四班": {"std_time": 68.95, "segments": {"起點-800": 23.30, "800-400": 22.10, "400-終點": 23.55}},
            "第五班": {"std_time": 69.35, "segments": {"起點-800": 23.35, "800-400": 22.35, "400-終點": 23.65}},
        },
        1650: {
            "第一班": {"std_time": 97.80, "segments": {"起點-1200": 27.80, "1200-800": 22.85, "800-400": 23.25, "400-終點": 23.90}},
            "第二班": {"std_time": 98.40, "segments": {"起點-1200": 27.90, "1200-800": 23.55, "800-400": 23.05, "400-終點": 23.90}},
            "第三班": {"std_time": 98.60, "segments": {"起點-1200": 27.90, "1200-800": 23.00, "800-400": 23.75, "400-終點": 23.95}},
            "第四班": {"std_time": 99.05, "segments": {"起點-1200": 27.95, "1200-800": 23.15, "800-400": 23.80, "400-終點": 24.15}},
            "第五班": {"std_time": 99.45, "segments": {"起點-1200": 27.95, "1200-800": 23.20, "800-400": 24.00, "400-終點": 24.30}},
        },
        1800: {
            "第三班": {"std_time": 108.05, "segments": {"起點-1600": 13.75, "1600-1200": 22.80, "1200-800": 23.70, "800-400": 23.85, "400-終點": 23.95}},
            "第四班": {"std_time": 108.55, "segments": {"起點-1600": 13.60, "1600-1200": 23.10, "1200-800": 24.05, "800-400": 23.65, "400-終點": 24.15}},
            "第五班": {"std_time": 109.45, "segments": {"起點-1600": 13.75, "1600-1200": 23.20, "1200-800": 23.95, "800-400": 24.25, "400-終點": 24.30}},
        },
    },
}

# 跑道別名對應
RACECOURSE_ALIASES = {
    "沙田": "Sha Tin",
    "Sha Tin": "Sha Tin",
    "沙田草地": "Sha Tin",
    "Sha Tin Turf": "Sha Tin",
    "跑馬地": "Happy Valley",
    "Happy Valley": "Happy Valley",
    "跑馬地草地": "Happy Valley",
    "Happy Valley Turf": "Happy Valley",
    "沙田全天候": "Sha Tin AW",
    "Sha Tin All-Weather": "Sha Tin AW",
    "沙田AW": "Sha Tin AW",
}

# 途程對應的分段數規則
DISTANCE_SEGMENT_RULES = {
    "3_segments": (1000, 1200),      # 3段：起點-800 + 800-400 + 400-終點
    "4_segments": (1400, 1650),      # 4段：起點-1200 + 1200-800 + 800-400 + 400-終點
    "5_segments": (1800, 2000),      # 5段：起點-1600 + 1600-1200 + 1200-800 + 800-400 + 400-終點
    "6_segments": (2200, 2400),      # 6段：起點-2000 + 2000-1600 + ... + 400-終點
}

# 分段欄位名稱對應
SEGMENT_FIELD_NAMES = {
    "3_segments": ["起點-800", "800-400", "400-終點"],
    "4_segments": ["起點-1200", "1200-800", "800-400", "400-終點"],
    "5_segments": ["起點-1600", "1600-1200", "1200-800", "800-400", "400-終點"],
    "6_segments": ["起點-2000", "2000-1600", "1600-1200", "1200-800", "800-400", "400-終點"],
}


# ============================================================================
# 第二部分：工具函數
# PART 2: UTILITY FUNCTIONS
# ============================================================================

def time_str_to_seconds(time_str: str) -> float:
    """
    將時間字串轉換為秒數
    Convert time string to seconds
    
    例子 / Examples:
        "1:09.15" → 69.15 秒
        "0:56.40" → 56.40 秒
        "2:01.70" → 121.70 秒
    
    Args:
        time_str: 時間字串格式 "M:SS.SS" 或 "MM:SS.SS"
    
    Returns:
        float: 轉換後的秒數，四捨五入到2位小數點
    
    Raises:
        ValueError: 如果格式不正確
    """
    try:
        parts = time_str.split(':')
        if len(parts) != 2:
            raise ValueError(f"Invalid time format: {time_str}. Expected 'M:SS.SS'")
        
        minutes = int(parts[0])
        seconds = float(parts[1])
        total_seconds = minutes * 60 + seconds
        
        return round(total_seconds, 2)
    except (ValueError, IndexError) as e:
        raise ValueError(f"Failed to convert time '{time_str}': {str(e)}")


def seconds_to_time_str(seconds: float) -> str:
    """
    將秒數轉換回時間字串
    Convert seconds back to time string format
    
    Args:
        seconds: 秒數
    
    Returns:
        str: 格式為 "M:SS.SS" 的時間字串
    """
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:05.2f}"


def normalize_racecourse_name(racecourse: str) -> str:
    """
    將跑道名稱標準化為英文標準名稱
    Normalize racecourse name to standard English name
    
    支援中文與英文別名 / Supports Chinese and English aliases
    
    Args:
        racecourse: 跑道名稱（中文或英文）
    
    Returns:
        str: 標準化後的跑道名稱
    
    Raises:
        ValueError: 如果找不到該跑道
    """
    normalized = RACECOURSE_ALIASES.get(racecourse.strip())
    if not normalized:
        available = list(set(RACECOURSE_ALIASES.values()))
        raise ValueError(f"Unknown racecourse: {racecourse}. Available: {available}")
    return normalized


def get_segment_type(distance_m: int) -> str:
    """
    根據途程判斷該用幾段分段時間
    Determine segment type based on distance
    
    Args:
        distance_m: 途程（米）
    
    Returns:
        str: 分段類型 ("3_segments", "4_segments", "5_segments", "6_segments")
    
    Raises:
        ValueError: 如果途程不被支持
    """
    for segment_type, (min_dist, max_dist) in DISTANCE_SEGMENT_RULES.items():
        if min_dist <= distance_m <= max_dist:
            return segment_type
    
    raise ValueError(f"Unsupported distance: {distance_m}m. Supported: 1000-2400m")


def get_segment_field_names(distance_m: int) -> List[str]:
    """
    根據途程取得應該用哪些分段欄位名稱
    Get segment field names based on distance
    
    Args:
        distance_m: 途程（米）
    
    Returns:
        List[str]: 分段欄位名稱列表
    """
    segment_type = get_segment_type(distance_m)
    return SEGMENT_FIELD_NAMES[segment_type]


# ============================================================================
# 第三部分：查詢函數 - 單場賽事
# PART 3: LOOKUP FUNCTIONS - SINGLE RACE
# ============================================================================

def get_standard_time(racecourse: str, distance_m: int, class_name: str) -> Optional[float]:
    """
    查詢標準完成時間
    Lookup standard finishing time
    
    Args:
        racecourse: 跑道名稱（中文或英文）
        distance_m: 途程（米）
        class_name: 班次（例如"第三班"、"新馬賽"、"分級賽"）
    
    Returns:
        float: 標準時間（秒），或 None 如果找不到
    
    例子 / Example:
        >>> get_standard_time("跑馬地", 1200, "第四班")
        69.90
    """
    try:
        racecourse_en = normalize_racecourse_name(racecourse)
        data = STANDARD_TIMES_DB[racecourse_en][distance_m][class_name]
        return data["std_time"]
    except (KeyError, ValueError):
        return None


def get_standard_segments(racecourse: str, distance_m: int, class_name: str) -> Optional[Dict[str, float]]:
    """
    查詢標準分段時間字典
    Lookup standard segment times dictionary
    
    Args:
        racecourse: 跑道名稱
        distance_m: 途程（米）
        class_name: 班次
    
    Returns:
        Dict[str, float]: 分段名稱→時間，或 None 如果找不到
    
    例子 / Example:
        >>> get_standard_segments("Happy Valley", 1200, "第四班")
        {"起點-800": 23.65, "800-400": 22.70, "400-終點": 23.55}
    """
    try:
        racecourse_en = normalize_racecourse_name(racecourse)
        data = STANDARD_TIMES_DB[racecourse_en][distance_m][class_name]
        return data["segments"]
    except (KeyError, ValueError):
        return None


def get_standard_section_sum(racecourse: str, distance_m: int, class_name: str) -> Optional[float]:
    """
    查詢標準分段總和（根據途程組合適當的段數）
    Get sum of standard segments (combines appropriate number of segments based on distance)
    
    例如：1200米用3段，加總起點-800 + 800-400 + 400-終點
    For example: 1200m uses 3 segments, sums up 起點-800 + 800-400 + 400-終點
    
    Args:
        racecourse: 跑道名稱
        distance_m: 途程（米）
        class_name: 班次
    
    Returns:
        float: 標準分段總和（秒），或 None 如果找不到
    
    例子 / Example:
        >>> get_standard_section_sum("Happy Valley", 1200, "第四班")
        69.90  # 23.65 + 22.70 + 23.55
    """
    segments = get_standard_segments(racecourse, distance_m, class_name)
    if not segments:
        return None
    
    # 根據途程決定要加總的段數
    segment_fields = get_segment_field_names(distance_m)
    
    # 加總前 N 段（N 由途程決定）
    total = sum(segments.get(field, 0) for field in segment_fields)
    return round(total, 2)


# ============================================================================
# 第四部分：步速判定函數
# PART 4: PACE CLASSIFICATION FUNCTIONS
# ============================================================================

@dataclass
class SpeedClassification:
    """步速分類結果"""
    value: str          # "FAST" / "NORMAL" / "SLOW"
    label_cn: str       # 中文標籤
    label_en: str       # 英文標籤
    diff_sec: float     # 差異秒數


def classify_speed(diff_sec: float) -> SpeedClassification:
    """
    根據差異秒數判定步速類型
    Classify pace based on difference in seconds
    
    規則 / Rules:
        - ≤ -0.5 秒 → "快步速" (FAST)
        - -0.5 ~ +0.5 秒 → "普通步速" (NORMAL)
        - ≥ +0.5 秒 → "慢步速" (SLOW)
    
    Args:
        diff_sec: 實際 - 標準 的差異（秒）
                   正數表示較標準時間慢
                   Negative = faster, Positive = slower
    
    Returns:
        SpeedClassification: 包含分類、標籤和差異的物件
    
    例子 / Examples:
        >>> classify_speed(-1.0)  # 比標準快1秒
        SpeedClassification(value='FAST', label_cn='快步速', ...)
        
        >>> classify_speed(0.0)   # 等同標準時間
        SpeedClassification(value='NORMAL', label_cn='普通步速', ...)
        
        >>> classify_speed(1.5)   # 比標準慢1.5秒
        SpeedClassification(value='SLOW', label_cn='慢步速', ...)
    """
    diff_rounded = round(diff_sec, 2)
    
    if diff_rounded <= -0.5:
        return SpeedClassification(
            value="FAST",
            label_cn="快步速",
            label_en="Fast Pace",
            diff_sec=diff_rounded
        )
    elif diff_rounded < 0.5:  # -0.5 < diff < 0.5
        return SpeedClassification(
            value="NORMAL",
            label_cn="普通步速",
            label_en="Normal Pace",
            diff_sec=diff_rounded
        )
    else:  # >= 0.5
        return SpeedClassification(
            value="SLOW",
            label_cn="慢步速",
            label_en="Slow Pace",
            diff_sec=diff_rounded
        )


# ============================================================================
# 第五部分：綜合分析函數
# PART 5: COMPREHENSIVE ANALYSIS FUNCTIONS
# ============================================================================

@dataclass
class RacePaceAnalysis:
    """賽事步速分析結果"""
    # 完成時間分析
    actual_finishing_time_sec: float
    standard_finishing_time_sec: float
    finish_time_diff_sec: float
    finish_time_classification: SpeedClassification
    
    # 分段分析
    actual_section_sum_sec: float
    standard_section_sum_sec: float
    section_diff_sec: float
    section_classification: SpeedClassification
    
    # 元資訊
    racecourse: str
    distance_m: int
    class_name: str


def analyze_race_pace(
    racecourse: str,
    distance_m: int,
    class_name: str,
    actual_finishing_time_str: str,
    horse_sectional_times: Dict[str, float]
) -> Optional[RacePaceAnalysis]:
    """
    完整的賽事步速分析
    Comprehensive race pace analysis
    
    分析實際完成時間 vs 標準時間，以及分段時間 vs 標準分段
    
    Args:
        racecourse: 跑道名稱
        distance_m: 途程（米）
        class_name: 班次
        actual_finishing_time_str: 實際完成時間字串 (例如 "1:09.15")
        horse_sectional_times: 馬匹分段時間字典 (例如 {"起點-800": 23.65, "800-400": 22.70, "400-終點": 23.55})
    
    Returns:
        RacePaceAnalysis: 完整分析結果，或 None 如果查詢失敗
    
    例子 / Example:
        >>> analysis = analyze_race_pace(
        ...     racecourse="Happy Valley",
        ...     distance_m=1200,
        ...     class_name="第四班",
        ...     actual_finishing_time_str="1:09.50",
        ...     horse_sectional_times={"起點-800": 23.65, "800-400": 22.70, "400-終點": 23.55}
        ... )
    """
    try:
        # 查詢標準時間
        std_finish_time = get_standard_time(racecourse, distance_m, class_name)
        if std_finish_time is None:
            return None
        
        # 轉換實際完成時間
        actual_finish_time = time_str_to_seconds(actual_finishing_time_str)
        
        # 計算完成時間差異
        finish_time_diff = actual_finish_time - std_finish_time
        finish_classification = classify_speed(finish_time_diff)
        
        # 查詢標準分段
        std_segments = get_standard_segments(racecourse, distance_m, class_name)
        if std_segments is None:
            return None
        
        # 計算標準分段總和
        segment_fields = get_segment_field_names(distance_m)
        std_section_sum = sum(std_segments.get(field, 0) for field in segment_fields)
        
        # 計算實際分段總和
        actual_section_sum = sum(
            horse_sectional_times.get(field, 0) for field in segment_fields
        )
        
        # 計算分段差異
        section_diff = actual_section_sum - std_section_sum
        section_classification = classify_speed(section_diff)
        
        return RacePaceAnalysis(
            actual_finishing_time_sec=round(actual_finish_time, 2),
            standard_finishing_time_sec=std_finish_time,
            finish_time_diff_sec=round(finish_time_diff, 2),
            finish_time_classification=finish_classification,
            actual_section_sum_sec=round(actual_section_sum, 2),
            standard_section_sum_sec=round(std_section_sum, 2),
            section_diff_sec=round(section_diff, 2),
            section_classification=section_classification,
            racecourse=normalize_racecourse_name(racecourse),
            distance_m=distance_m,
            class_name=class_name
        )
    except Exception as e:
        print(f"Error in analyze_race_pace: {e}")
        return None


# ============================================================================
# 第六部分：批量分析函數 (用於 DataFrame)
# PART 6: BATCH ANALYSIS FUNCTIONS (for DataFrame)
# ============================================================================

def create_race_time_comparison_df(
    races_data: List[Dict]
) -> pd.DataFrame:
    """
    建立「完成時間與標準時間比較表」
    Create "Race Time Comparison" dataframe
    
    Args:
        races_data: 包含以下欄位的字典列表：
            - racecourse: 跑道
            - distance_m: 途程
            - class_name: 班次
            - race_name: 賽事名稱（可選）
            - race_date: 賽事日期（可選）
            - race_number: 場次（可選）
            - actual_finishing_time: 頭馬完成時間字串
    
    Returns:
        pd.DataFrame: 包含以下欄位的表格
            - 賽事日期、場次、班次、途程、賽事名稱
            - 頭馬完成時間（原始）、頭馬完成時間（秒）
            - 標準時間（秒）、差異（秒）、步速分型
    """
    results = []
    
    for race in races_data:
        try:
            std_time = get_standard_time(
                race["racecourse"],
                race["distance_m"],
                race["class_name"]
            )
            
            if std_time is None:
                continue
            
            actual_time_sec = time_str_to_seconds(race["actual_finishing_time"])
            diff_sec = actual_time_sec - std_time
            speed_class = classify_speed(diff_sec)
            
            results.append({
                "賽事日期": race.get("race_date", ""),
                "場次": race.get("race_number", ""),
                "班次": race["class_name"],
                "途程(米)": race["distance_m"],
                "賽事名稱": race.get("race_name", ""),
                "頭馬完成時間(原始)": race["actual_finishing_time"],
                "頭馬完成時間(秒)": actual_time_sec,
                "標準時間(秒)": std_time,
                "差異(秒)": round(diff_sec, 2),
                "步速分型": speed_class.label_cn,
            })
        except Exception as e:
            print(f"Error processing race {race}: {e}")
            continue
    
    return pd.DataFrame(results)


def create_pace_analysis_df(
    races_with_sections: List[Dict]
) -> pd.DataFrame:
    """
    建立「步速分析表」（實際分段 vs 標準分段）
    Create "Pace Analysis" dataframe
    
    Args:
        races_with_sections: 包含以下欄位的字典列表：
            - racecourse: 跑道
            - distance_m: 途程
            - class_name: 班次
            - race_name: 賽事名稱（可選）
            - race_date: 賽事日期（可選）
            - race_number: 場次（可選）
            - sectional_times: 分段時間字典
    
    Returns:
        pd.DataFrame: 包含以下欄位的表格
            - 賽事日期、場次、班次、途程、賽事名稱
            - 頭馬實際分段總和(秒)、標準分段總和(秒)
            - 分段差異(秒)、步速分型
    """
    results = []
    
    for race in races_with_sections:
        try:
            std_section_sum = get_standard_section_sum(
                race["racecourse"],
                race["distance_m"],
                race["class_name"]
            )
            
            if std_section_sum is None:
                continue
            
            # 獲取應該用的分段欄位
            segment_fields = get_segment_field_names(race["distance_m"])
            
            # 計算實際分段總和
            actual_section_sum = sum(
                race["sectional_times"].get(field, 0) for field in segment_fields
            )
            
            diff_sec = actual_section_sum - std_section_sum
            speed_class = classify_speed(diff_sec)
            
            results.append({
                "賽事日期": race.get("race_date", ""),
                "場次": race.get("race_number", ""),
                "班次": race["class_name"],
                "途程(米)": race["distance_m"],
                "賽事名稱": race.get("race_name", ""),
                "頭馬實際分段總和(秒)": round(actual_section_sum, 2),
                "標準分段總和(秒)": std_section_sum,
                "分段差異(秒)": round(diff_sec, 2),
                "步速分型": speed_class.label_cn,
            })
        except Exception as e:
            print(f"Error processing sectional race {race}: {e}")
            continue
    
    return pd.DataFrame(results)


# ============================================================================
# 第七部分：快速參考函數
# PART 7: QUICK REFERENCE FUNCTIONS
# ============================================================================

def list_available_racecourses() -> List[str]:
    """列出所有可用的跑道"""
    return list(set(RACECOURSE_ALIASES.values()))


def list_available_distances(racecourse: str) -> List[int]:
    """列出指定跑道的所有可用途程"""
    try:
        racecourse_en = normalize_racecourse_name(racecourse)
        return sorted(STANDARD_TIMES_DB[racecourse_en].keys())
    except ValueError:
        return []


def list_available_classes(racecourse: str, distance_m: int) -> List[str]:
    """列出指定跑道途程的所有可用班次"""
    try:
        racecourse_en = normalize_racecourse_name(racecourse)
        return sorted(STANDARD_TIMES_DB[racecourse_en][distance_m].keys())
    except (KeyError, ValueError):
        return []


# ============================================================================
# 測試 / TESTING
# ============================================================================

if __name__ == "__main__":
    # 基本測試
    print("=" * 60)
    print("標準時間查詢模組 - 功能演示")
    print("=" * 60)
    
    # 測試1：時間轉換
    print("\n【測試1】時間轉換")
    print(f"'1:09.90' → {time_str_to_seconds('1:09.90')} 秒")
    print(f"'0:56.40' → {time_str_to_seconds('0:56.40')} 秒")
    print(f"'2:01.70' → {time_str_to_seconds('2:01.70')} 秒")
    
    # 測試2：標準時間查詢
    print("\n【測試2】標準時間查詢")
    std_time = get_standard_time("Happy Valley", 1200, "第四班")
    print(f"跑馬地 1200米 第四班 標準時間: {std_time} 秒 ({seconds_to_time_str(std_time)})")
    
    # 測試3：標準分段查詢
    print("\n【測試3】標準分段查詢")
    segs = get_standard_segments("Happy Valley", 1200, "第四班")
    print(f"跑馬地 1200米 第四班 標準分段: {segs}")
    
    # 測試4：標準分段總和
    print("\n【測試4】標準分段總和")
    seg_sum = get_standard_section_sum("Happy Valley", 1200, "第四班")
    print(f"跑馬地 1200米 第四班 標準分段總和: {seg_sum} 秒")
    
    # 測試5：步速分類
    print("\n【測試5】步速分類")
    for diff in [-1.0, -0.3, 0.0, 0.3, 1.5]:
        classification = classify_speed(diff)
        print(f"差異 {diff:+.1f} 秒 → {classification.label_cn} ({classification.value})")
    
    # 測試6：完整分析
    print("\n【測試6】完整賽事分析")
    analysis = analyze_race_pace(
        racecourse="Happy Valley",
        distance_m=1200,
        class_name="第四班",
        actual_finishing_time_str="1:09.50",
        horse_sectional_times={"起點-800": 23.65, "800-400": 22.70, "400-終點": 23.55}
    )
    if analysis:
        print(f"完成時間差異: {analysis.finish_time_diff_sec:+.2f} 秒 ({analysis.finish_time_classification.label_cn})")
        print(f"分段差異: {analysis.section_diff_sec:+.2f} 秒 ({analysis.section_classification.label_cn})")
    
    print("\n✅ 模組功能正常！")
