# -*- coding: utf-8 -*-

"""
頁面模組 - 初始化檔案

Pages Module - Init File
"""

from .page_segment import render_segment_page
from .page_pace import render_pace_page
from .page_report import render_report_page
from .page_racecard import render as render_racecard_page

__all__ = [
    'render_segment_page',
    'render_pace_page',
    'render_report_page',
    'render_racecard_page'
]
