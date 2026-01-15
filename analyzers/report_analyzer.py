
# -*- coding: utf-8 -*-
"""
報告分析器 - RaceSegmentAnalyzer 類
Report Analyzer - Race Segment Analysis Class
"""

import re
from typing import Optional, Dict
from .base_analyzer import get_standard_time, get_standard_segments, get_standard_segment_sum


def _classify_finishing_pace(diff_sec):
    """判定完成時間幅度"""
    if diff_sec is None:
        return "-"
    if abs(diff_sec) < 0.1:
        return "接近標準"
    elif diff_sec < -0.5:
        return "顯著優化"
    elif diff_sec < 0:
        return "優於標準"
    elif diff_sec < 0.5:
        return "接近標準"
    else:
        return "略遜標準"


def _classify_pace_type(diff_sec):
    """判定步速類型"""
    if diff_sec is None:
        return "-"
    if diff_sec < -0.5:
        return "快步速"
    elif diff_sec < 0.1:
        return "快步速"
    elif diff_sec < 0.5:
        return "普通步速"
    else:
        return "慢步速"


class RaceSegmentAnalyzer:
    """賽事分段分析器 - 支持全天候"""
    
    def __init__(self, csv_content: str):
        """從 CSV 內容初始化"""
        self.metadata = {}
        self.actual_segments = {}
        self.finish_time = None
        self._parse_csv(csv_content)

    def _parse_csv(self, csv_content: str):
        """解析 CSV 內容"""
        lines = csv_content.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            if '跑馬地' in first_line:
                self.metadata['location'] = '跑馬地'
                self.metadata['racecourse'] = 'Happy Valley'
            elif '沙田' in first_line:
                self.metadata['location'] = '沙田'
                self.metadata['racecourse'] = 'Sha Tin'

        if len(lines) > 3:
            line4 = lines[3].strip()
            # 修復 1: 識別 一級賽、二級賽、三級賽 並轉換為 分級賽
            class_match = re.search(r'([一二三])級賽|第(\S+?)班|新馬賽', line4)
            distance_match = re.search(r'(\d+)米', line4)
            aw_match = re.search(r'全天候|AW', line4)

            if class_match:
                full_match = class_match.group(0)
                # 級賽類型統一轉換為 分級賽
                if '級賽' in full_match:
                    self.metadata['class'] = '分級賽'
                else:
                    self.metadata['class'] = full_match

            if distance_match:
                self.metadata['distance'] = int(distance_match.group(1))

            if aw_match and self.metadata.get('racecourse') == 'Sha Tin':
                self.metadata['racecourse'] = 'Sha Tin AW'
                self.metadata['track_type'] = '全天候'
            else:
                self.metadata['track_type'] = '草地'

        in_segment_detail_section = False
        for i, line in enumerate(lines):
            if '分段時間' in line and '時間' in line and '時間說明' in line:
                in_segment_detail_section = True
                continue

            if in_segment_detail_section and ('三、' in line or '各馬匹' in line):
                in_segment_detail_section = False

            if in_segment_detail_section and '\t' in line and line.strip():
                parts = line.split('\t')
                if len(parts) >= 2:
                    segment_name = parts[0].strip()
                    time_str = parts[1].strip()
                    if '第' in segment_name and '段' in segment_name:
                        try:
                            time_sec = float(time_str)
                            self.actual_segments[segment_name] = time_sec
                        except:
                            pass

            if '頭馬完成時間' in line and '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    time_value = parts[1].strip()
                    try:
                        if ':' in time_value:
                            # 修復 3: 支援 MM:SS 或 M:SS 格式
                            time_parts = time_value.split(':')
                            minutes = int(time_parts[0])
                            seconds = float(time_parts[1])
                            self.finish_time = minutes * 60 + seconds
                        else:
                            # 支援純秒數格式（如 57.28）
                            self.finish_time = float(time_value)
                    except:
                        pass

    def _get_segment_count(self) -> int:
        """根據途程返回需要比較的分段數 - 修復版"""
        if 'distance' not in self.metadata:
            return 0

        distance = self.metadata['distance']
        if distance <= 1200:
            return 2  # 短途（≤1200米）：首兩段總和
        elif distance <= 1650:
            return 3  # 中距離（1400-1650米）：首三段總和
        else:
            return 4  # 長途（≥1800米）：首四段總和

    def _get_standard_time(self, standard_times_data: Dict) -> Optional[float]:
        """查詢標準完成時間"""
        if 'class' not in self.metadata or 'distance' not in self.metadata:
            return None

        class_name = self.metadata['class']
        distance = self.metadata['distance']
        racecourse = self.metadata.get('racecourse', 'Sha Tin')

        return get_standard_time(racecourse, int(distance), class_name, standard_times_data)

    def analyze(self, standard_times_data: Dict) -> Dict:
        """執行完整分析"""
        class_name = self.metadata.get('class')
        distance = self.metadata.get('distance')
        racecourse = self.metadata.get('racecourse', 'Sha Tin')
        segment_count = self._get_segment_count()

        result = {
            'metadata': self.metadata,
            'actual_finish_time': self.finish_time,
            'standard_time': self._get_standard_time(standard_times_data),
            'segment_count': segment_count,
            'actual_segment_sum': None,
            'standard_segment_sum': None,
            'finishing_time_diff': None,
            'segment_sum_diff': None,
        }

        # 計算完成時間差異
        if self.finish_time and result['standard_time']:
            result['finishing_time_diff'] = self.finish_time - result['standard_time']

        # 計算實際分段總和（來自 CSV）
        if segment_count > 0:
            actual_sum = 0
            for i in range(1, segment_count + 1):
                segment_key = f'第{i}段'
                if segment_key in self.actual_segments:
                    actual_sum += self.actual_segments[segment_key]
            if actual_sum > 0:
                result['actual_segment_sum'] = actual_sum

        # 查詢標準分段總和（來自 STANDARD_TIMES_DATA）
        if class_name and distance:
            try:
                std_sum = get_standard_segment_sum(racecourse, int(distance), class_name, standard_times_data)
                if std_sum:
                    result['standard_segment_sum'] = std_sum
            except:
                pass

        # 計算分段差異
        if result['actual_segment_sum'] and result['standard_segment_sum']:
            result['segment_sum_diff'] = result['actual_segment_sum'] - result['standard_segment_sum']

        return result
