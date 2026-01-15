
# -*- coding: utf-8 -*-

"""
分析器模組 - 初始化檔案 (v2.1)

Analyzers Module - Init File

包含:
- 賽事分析模塊 (報告分析、賽卡分析、往績爬蟲)
- 配腳評分系統模塊 (數據預處理、配腳計算、標籤識別、評分系統)
"""

# 賽事分析相關類
from .report_analyzer import RaceSegmentAnalyzer, _classify_finishing_pace, _classify_pace_type
from .racecard_analyzer import RaceCardAnalyzer
from .horse_racing_history_parser import HorseRacingHistoryParser

# 配腳評分系統相關類
from .leg_fitness_data_prep import DataPreprocessor
from .leg_fitness_calculator import LegFitnessCalculator
from .leg_fitness_tag_identifier import TagIdentifier
from .leg_fitness_scorer_realtime import RealtimeLegFitnessScorer as LegFitnessScorer

__all__ = [
    # 賽事分析
    'RaceSegmentAnalyzer',
    'RaceCardAnalyzer',
    'HorseRacingHistoryParser',
    '_classify_finishing_pace',
    '_classify_pace_type',
    # 配腳評分系統
    'DataPreprocessor',
    'LegFitnessCalculator',
    'TagIdentifier',
    'LegFitnessScorer'
]

__version__ = '2.1.0'
__author__ = 'HKJC Analysis Team'
__description__ = '綜合分析系統 - 賽事分析與配腳評分'
