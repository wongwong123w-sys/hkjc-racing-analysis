# -*- coding: utf-8 -*-

"""
HKJC 爬蟲錯誤處理和進度追蹤

Error Handler and Progress Tracking for HKJC Crawler

✨ 功能:
- 爬蟲進度追蹤
- 錯誤分類 + 詳細報告
- 成功/失敗統計
- 詳細日誌記錄
- 實時進度顯示

作者: AI Assistant
日期: 2026-01-09
版本: 1.0
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """錯誤類型分類"""
    NETWORK_ERROR = "網絡錯誤"
    TIMEOUT_ERROR = "超時錯誤"
    PARSE_ERROR = "解析錯誤"
    DATABASE_ERROR = "數據庫錯誤"
    VALIDATION_ERROR = "驗證錯誤"
    UNKNOWN_ERROR = "未知錯誤"


class ErrorHandler:
    """爬蟲錯誤處理器"""

    @staticmethod
    def classify_error(exception: Exception) -> str:
        """
        分類錯誤類型

        Args:
            exception: 異常對象

        Returns:
            str: 錯誤類型名稱

        Example:
            error_type = ErrorHandler.classify_error(timeout_error)
            print(f"錯誤類型: {error_type}")
        """
        exception_name = type(exception).__name__

        if 'Timeout' in exception_name or 'ConnectTimeout' in exception_name:
            return ErrorType.TIMEOUT_ERROR.value

        elif 'ConnectionError' in exception_name or 'URLError' in exception_name:
            return ErrorType.NETWORK_ERROR.value

        elif 'ParseError' in exception_name or 'AttributeError' in exception_name:
            return ErrorType.PARSE_ERROR.value

        elif 'DatabaseError' in exception_name or 'sqlite3' in exception_name:
            return ErrorType.DATABASE_ERROR.value

        elif 'ValidationError' in exception_name or 'ValueError' in exception_name:
            return ErrorType.VALIDATION_ERROR.value

        else:
            return ErrorType.UNKNOWN_ERROR.value

    @staticmethod
    def format_error_report(operation: str, exception: Exception,
                          retry_count: int = 0, context: str = None) -> str:
        """
        生成詳細的錯誤報告

        Args:
            operation: 操作名稱
            exception: 異常對象
            retry_count: 重試次數
            context: 額外上下文信息

        Returns:
            str: 格式化的錯誤報告

        Example:
            report = ErrorHandler.format_error_report(
                '爬取排位表',
                timeout_error,
                retry_count=3
            )
            logger.error(report)
        """
        error_type = ErrorHandler.classify_error(exception)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        report = f"""
╔═══════════════════════════════════════════════════════════╗
║                  爬蟲錯誤報告
╚═══════════════════════════════════════════════════════════╝

⏰ 時間: {timestamp}
📋 操作: {operation}
🔴 錯誤類型: {error_type}
💥 異常: {type(exception).__name__}
📝 信息: {str(exception)}
🔄 重試次數: {retry_count}
{'📌 上下文: ' + context if context else ''}

異常詳情:
{repr(exception)}
        """
        return report.strip()

    @staticmethod
    def should_retry(exception: Exception) -> bool:
        """
        判斷是否應該重試

        Args:
            exception: 異常對象

        Returns:
            bool: True 表示應該重試

        Example:
            if ErrorHandler.should_retry(exception):
                # 進行重試
                pass
        """
        error_type = ErrorHandler.classify_error(exception)

        # 可重試的錯誤類型
        retryable = [
            ErrorType.NETWORK_ERROR.value,
            ErrorType.TIMEOUT_ERROR.value,
        ]

        return error_type in retryable


class CrawlerProgressTracker:
    """爬蟲進度追蹤器"""

    def __init__(self, task_name: str, total_items: int):
        """
        初始化進度追蹤器

        Args:
            task_name: 任務名稱
            total_items: 總項目數

        Example:
            tracker = CrawlerProgressTracker('爬取馬匹往績', 12)
        """
        self.task_name = task_name
        self.total_items = total_items
        self.completed = 0
        self.successful = 0
        self.failed = 0
        self.failed_items = []
        self.start_time = datetime.now()

    def success(self, item_name: str, details: str = None) -> None:
        """
        記錄成功項目

        Args:
            item_name: 項目名稱
            details: 詳細信息

        Example:
            tracker.success('馬匹A', '爬取 6 筆往績')
        """
        self.completed += 1
        self.successful += 1
        progress = (self.completed / self.total_items) * 100
        print(f"✅ [{self.completed}/{self.total_items}] {item_name} {details or ''}")
        logger.info(f"✅ {item_name} 成功 - {details or ''}")

    def failure(self, item_name: str, error_msg: str = None) -> None:
        """
        記錄失敗項目

        Args:
            item_name: 項目名稱
            error_msg: 錯誤信息

        Example:
            tracker.failure('馬匹B', '無 horse_id')
        """
        self.completed += 1
        self.failed += 1
        self.failed_items.append({'name': item_name, 'error': error_msg})
        progress = (self.completed / self.total_items) * 100
        print(f"❌ [{self.completed}/{self.total_items}] {item_name} - {error_msg or '未知錯誤'}")
        logger.warning(f"❌ {item_name} 失敗 - {error_msg or '未知錯誤'}")

    def summary(self) -> str:
        """
        生成進度總結

        Returns:
            str: 格式化的總結報告

        Example:
            print(tracker.summary())
        """
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        success_rate = (self.successful / self.total_items * 100) if self.total_items > 0 else 0

        summary = f"""
╔═══════════════════════════════════════════════════════════╗
║                 📊 任務進度總結
╚═══════════════════════════════════════════════════════════╝

📋 任務: {self.task_name}
✅ 成功: {self.successful}/{self.total_items} 項
❌ 失敗: {self.failed}/{self.total_items} 項
📈 成功率: {success_rate:.1f}%
⏱️  耗時: {elapsed_time:.1f} 秒
"""

        if self.failed_items:
            summary += "\n❌ 失敗項目詳情:\n"
            for item in self.failed_items:
                summary += f"  - {item['name']}: {item['error'] or '未知錯誤'}\n"

        summary += "═" * 61 + "\n"
        return summary


class CrawlerLogger:
    """爬蟲詳細日誌記錄器"""

    def __init__(self, logger_name: str = 'Crawler'):
        """
        初始化日誌記錄器

        Args:
            logger_name: 日誌記錄器名稱

        Example:
            logger = CrawlerLogger('RaceCardAnalyzer')
        """
        self.logger_name = logger_name
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)

        # 設置日誌格式
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_success(self, operation: str, target: str, details: str = None) -> None:
        """
        記錄成功日誌

        Args:
            operation: 操作名稱
            target: 目標對象
            details: 詳細信息

        Example:
            logger.log_success('爬取排位表', 'HV_20260107_1', '12 匹馬')
        """
        message = f"✅ [{operation}] {target}" + (f" - {details}" if details else "")
        self.logger.info(message)

    def log_warning(self, operation: str, message: str) -> None:
        """
        記錄警告日誌

        Args:
            operation: 操作名稱
            message: 警告信息

        Example:
            logger.log_warning('爬取往績', '馬匹 A 無 horse_id')
        """
        full_message = f"⚠️  [{operation}] {message}"
        self.logger.warning(full_message)

    def log_error(self, operation: str, error_msg: str, exception: Exception = None) -> None:
        """
        記錄錯誤日誌

        Args:
            operation: 操作名稱
            error_msg: 錯誤信息
            exception: 異常對象（可選）

        Example:
            logger.log_error('爬取排位表', '表格未找到', exception)
        """
        full_message = f"❌ [{operation}] {error_msg}"
        if exception:
            full_message += f" ({type(exception).__name__})"
        self.logger.error(full_message)

    def log_progress(self, current: int, total: int, item: str) -> None:
        """
        記錄進度日誌

        Args:
            current: 當前項
            total: 總項
            item: 項目名稱

        Example:
            logger.log_progress(1, 12, '馬匹 A')
        """
        progress = (current / total * 100) if total > 0 else 0
        message = f"📊 [{current}/{total}] {item} ({progress:.0f}%)"
        self.logger.info(message)

    def log_debug(self, operation: str, debug_info: str) -> None:
        """
        記錄調試日誌

        Args:
            operation: 操作名稱
            debug_info: 調試信息

        Example:
            logger.log_debug('解析排位表', 'HTML 結構確認')
        """
        message = f"🔍 [{operation}] {debug_info}"
        self.logger.debug(message)


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 示例 1: 錯誤分類
    print("=" * 60)
    print("【示例 1】錯誤分類")
    print("=" * 60)

    test_errors = [
        TimeoutError("請求超時"),
        ConnectionError("網絡連接失敗"),
        ValueError("數據驗證失敗"),
    ]

    for error in test_errors:
        error_type = ErrorHandler.classify_error(error)
        print(f"❌ {type(error).__name__} -> {error_type}")

    # 示例 2: 錯誤報告
    print("\n" + "=" * 60)
    print("【示例 2】詳細錯誤報告")
    print("=" * 60)

    try:
        raise TimeoutError("連接超時 (30 秒)")
    except Exception as e:
        report = ErrorHandler.format_error_report(
            '爬取排位表',
            e,
            retry_count=3,
            context='URL: https://racing.hkjc.com/racing/...'
        )
        print(report)

    # 示例 3: 進度追蹤
    print("\n" + "=" * 60)
    print("【示例 3】進度追蹤")
    print("=" * 60)

    tracker = CrawlerProgressTracker('爬取馬匹往績', 5)

    tracker.success('馬匹 A', '6 筆往績')
    tracker.success('馬匹 B', '5 筆往績')
    tracker.failure('馬匹 C', '無 horse_id')
    tracker.success('馬匹 D', '7 筆往績')
    tracker.failure('馬匹 E', '爬蟲超時')

    print(tracker.summary())

    # 示例 4: 詳細日誌記錄
    print("=" * 60)
    print("【示例 4】詳細日誌記錄")
    print("=" * 60)

    logger_instance = CrawlerLogger('RaceCardAnalyzer')

    logger_instance.log_success('爬取排位表', 'HV_20260107_1', '12 匹馬')
    logger_instance.log_warning('爬取往績', '馬匹 A 無 horse_id')
    logger_instance.log_progress(5, 12, '馬匹 B')

    try:
        raise ConnectionError("無法連接到伺服器")
    except Exception as e:
        logger_instance.log_error('爬取排位表', '網絡連接失敗', e)
