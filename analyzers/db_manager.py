
# -*- coding: utf-8 -*-

"""
HKJC 賽馬數據庫管理器 - SQLite 數據持久化

DatabaseManager for HKJC Race Analysis - SQLite Data Persistence

✨ 功能:
- 排位表數據存儲
- 馬匹往績數據存儲
- 檔位統計數據存儲 ⭐ 完整支持
- 數據查詢接口
- 自動表初始化
- 錯誤恢復機制
- CSV 導出功能

作者: AI Assistant
日期: 2026-01-11
版本: 2.0 (完整修復版)
"""

import sqlite3
import json
import logging
import csv
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DatabaseManager:
    """HKJC 賽馬數據庫管理器"""

    def __init__(self, db_path: str = 'hkjc_data.db'):
        """
        初始化數據庫管理器

        Args:
            db_path: 數據庫文件路徑 (默認: hkjc_data.db)

        Example:
            db = DatabaseManager('hkjc_data.db')
        """
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        
        try:
            self._init_connection()
            self._create_tables()
            logger.info(f"✅ 數據庫已初始化: {db_path}")
        except Exception as e:
            logger.error(f"❌ 數據庫初始化失敗: {e}")
            raise

    def _init_connection(self):
        """初始化數據庫連接"""
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=10.0
            )
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            logger.info(f"✅ 數據庫連接已建立")
        except sqlite3.Error as e:
            logger.error(f"❌ 連接失敗: {e}")
            raise

    def _create_tables(self):
        """創建必要的表"""
        try:
            # 表 1: 排位表數據
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS racecards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    race_id TEXT UNIQUE NOT NULL,
                    date TEXT NOT NULL,
                    racecourse TEXT NOT NULL,
                    race_no INTEGER NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 表 2: 馬匹往績數據
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS horse_histories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    horse_id TEXT NOT NULL,
                    horse_name TEXT NOT NULL,
                    race_id TEXT NOT NULL,
                    history_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(horse_id, race_id)
                )
            ''')

            # 表 3: 爬蟲日誌
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS crawler_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 表 4: 檔位統計 ⭐ 完整版本
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS draw_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    race_num INTEGER NOT NULL,
                    distance INTEGER NOT NULL,
                    going TEXT NOT NULL,
                    track TEXT NOT NULL,
                    draw INTEGER NOT NULL,
                    races_run INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    places INTEGER DEFAULT 0,
                    thirds INTEGER DEFAULT 0,
                    fourths INTEGER DEFAULT 0,
                    win_rate REAL DEFAULT 0,
                    place_rate REAL DEFAULT 0,
                    top3_rate REAL DEFAULT 0,
                    top4_rate REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, race_num, draw)
                )
            ''')

            # 創建索引以提高查詢效率
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_draw_date 
                ON draw_statistics(date)
            ''')
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_draw_race 
                ON draw_statistics(date, race_num)
            ''')

            self.connection.commit()
            logger.info("✅ 數據庫表已創建/驗證")
        except sqlite3.Error as e:
            logger.error(f"❌ 創建表失敗: {e}")
            raise

    # ========================================================================
    # 排位表相關方法
    # ========================================================================

    def save_racecard(self, race_id: str, date_str: str, racecourse: str,
                     race_no: int, horses_data: List[Dict]) -> bool:
        """
        保存排位表數據

        Args:
            race_id: 賽次 ID (如 'HV_20260107_1')
            date_str: 日期字符串 (如 '2026/01/07')
            racecourse: 場次 (HV 或 ST)
            race_no: 賽次號碼
            horses_data: 馬匹數據列表

        Returns:
            bool: 保存成功返回 True，失敗返回 False
        """
        try:
            data_json = json.dumps(horses_data, ensure_ascii=False, indent=2)
            self.cursor.execute('''
                INSERT OR REPLACE INTO racecards
                (race_id, date, racecourse, race_no, data_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (race_id, date_str, racecourse, race_no, data_json, datetime.now().isoformat()))
            self.connection.commit()
            logger.info(f"✅ 排位表已保存: {race_id} ({len(horses_data)} 匹馬)")
            return True
        except sqlite3.Error as e:
            logger.error(f"❌ 保存排位表失敗: {e}")
            return False

    def get_racecard(self, race_id: str) -> Optional[List[Dict]]:
        """查詢排位表數據"""
        try:
            self.cursor.execute(
                'SELECT data_json FROM racecards WHERE race_id = ?',
                (race_id,)
            )
            row = self.cursor.fetchone()
            if row:
                return json.loads(row['data_json'])
            return None
        except Exception as e:
            logger.error(f"❌ 查詢排位表失敗: {e}")
            return None

    def get_all_racecards(self, limit: int = 100) -> List[Dict]:
        """查詢所有排位表"""
        try:
            self.cursor.execute(
                'SELECT race_id, date, racecourse, race_no, created_at FROM racecards ORDER BY created_at DESC LIMIT ?',
                (limit,)
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ 查詢所有排位表失敗: {e}")
            return []

    def delete_racecard(self, race_id: str) -> bool:
        """刪除排位表數據"""
        try:
            self.cursor.execute('DELETE FROM racecards WHERE race_id = ?', (race_id,))
            self.connection.commit()
            logger.info(f"✅ 排位表已刪除: {race_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"❌ 刪除排位表失敗: {e}")
            return False

    # ========================================================================
    # 馬匹往績相關方法
    # ========================================================================

    def save_horse_history(self, horse_id: str, horse_name: str, race_id: str,
                          history_data: List[Dict]) -> bool:
        """保存馬匹往績數據"""
        try:
            history_json = json.dumps(history_data, ensure_ascii=False, indent=2)
            self.cursor.execute('''
                INSERT OR REPLACE INTO horse_histories
                (horse_id, horse_name, race_id, history_json)
                VALUES (?, ?, ?, ?)
            ''', (horse_id, horse_name, race_id, history_json))
            self.connection.commit()
            logger.info(f"✅ 馬匹往績已保存: {horse_name} ({len(history_data)} 筆)")
            return True
        except sqlite3.Error as e:
            logger.error(f"❌ 保存馬匹往績失敗: {e}")
            return False

    def get_horse_history(self, horse_id: str, race_id: str) -> Optional[List[Dict]]:
        """查詢馬匹往績數據"""
        try:
            self.cursor.execute(
                'SELECT history_json FROM horse_histories WHERE horse_id = ? AND race_id = ?',
                (horse_id, race_id)
            )
            row = self.cursor.fetchone()
            if row:
                return json.loads(row['history_json'])
            return None
        except Exception as e:
            logger.error(f"❌ 查詢馬匹往績失敗: {e}")
            return None

    # ========================================================================
    # 檔位統計相關方法 ⭐ 完整實現
    # ========================================================================

    def save_all_races(self, date: str, races: List[Dict]) -> bool:
        """
        保存所有場次的檔位統計數據
        
        Args:
            date: 日期 (格式: YYYY-MM-DD)
            races: 場次列表，每場包含統計數據
            
        Returns:
            bool: 成功返回 True
        """
        try:
            # 先清除該日期的舊數據
            self.cursor.execute('DELETE FROM draw_statistics WHERE date = ?', (date,))
            logger.info(f"🗑️ 已清除 {date} 的舊數據")
            
            total_records = 0
            
            # 插入新數據
            for race in races:
                race_num = race.get('race_num')
                distance = race.get('distance', 1200)
                going = race.get('going', 'C')
                track = race.get('track', '草地')
                
                for stat in race.get('statistics', []):
                    self.cursor.execute('''
                        INSERT INTO draw_statistics
                        (date, race_num, distance, going, track, draw,
                         races_run, wins, places, thirds, fourths,
                         win_rate, place_rate, top3_rate, top4_rate, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        date,
                        race_num,
                        distance,
                        going,
                        track,
                        stat['draw'],
                        stat.get('races_run', 0),
                        stat.get('wins', 0),
                        stat.get('places', 0),
                        stat.get('thirds', 0),
                        stat.get('fourths', 0),
                        stat.get('win_rate', 0.0),
                        stat.get('place_rate', 0.0),
                        stat.get('top3_rate', 0.0),
                        stat.get('top4_rate', 0.0)
                    ))
                    total_records += 1
            
            self.connection.commit()
            logger.info(f"✅ 已保存 {len(races)} 場賽事，共 {total_records} 筆檔位數據")
            
            # 記錄操作日誌
            self.log_operation(
                'save_draw_statistics', 
                'success', 
                f'{date}: {len(races)} 場, {total_records} 筆'
            )
            
            return True
        
        except Exception as e:
            logger.error(f"❌ 保存檔位統計失敗: {e}", exc_info=True)
            self.connection.rollback()
            self.log_operation('save_draw_statistics', 'error', str(e))
            return False

    def get_all_races_for_date(self, date: str) -> Dict[int, Dict]:
        """
        查詢某日期的所有場次檔位統計
        
        Args:
            date: 日期 (格式: YYYY-MM-DD)
            
        Returns:
            Dict: 按場次號碼分組的數據
            {
                1: {race_num: 1, distance: 1200, statistics: [...]},
                2: {...},
                ...
            }
        """
        try:
            self.cursor.execute('''
                SELECT * FROM draw_statistics
                WHERE date = ?
                ORDER BY race_num, draw
            ''', (date,))
            
            cols = [desc[0] for desc in self.cursor.description]
            rows = [dict(zip(cols, row)) for row in self.cursor.fetchall()]
            
            if not rows:
                logger.warning(f"⚠️ 未找到日期 {date} 的數據")
                return {}
            
            # 按場次分組
            races = {}
            for row in rows:
                race_num = row['race_num']
                if race_num not in races:
                    races[race_num] = {
                        'race_num': race_num,
                        'distance': row['distance'],
                        'going': row['going'],
                        'track': row['track'],
                        'statistics': []
                    }
                
                # 添加檔位統計
                races[race_num]['statistics'].append({
                    'draw': row['draw'],
                    'races_run': row['races_run'],
                    'wins': row['wins'],
                    'places': row['places'],
                    'thirds': row['thirds'],
                    'fourths': row['fourths'],
                    'win_rate': row['win_rate'],
                    'place_rate': row['place_rate'],
                    'top3_rate': row['top3_rate'],
                    'top4_rate': row['top4_rate']
                })
            
            logger.info(f"✅ 已查詢 {date}: {len(races)} 場賽事")
            return races
        
        except Exception as e:
            logger.error(f"❌ 查詢檔位統計失敗: {e}")
            return {}

    def get_race_statistics(self, date: str, race_num: int) -> Optional[Dict]:
        """
        查詢特定場次的檔位統計
        
        Args:
            date: 日期
            race_num: 場次號碼
            
        Returns:
            Dict: 場次數據，包含 statistics 列表
        """
        try:
            self.cursor.execute('''
                SELECT * FROM draw_statistics
                WHERE date = ? AND race_num = ?
                ORDER BY draw
            ''', (date, race_num))
            
            cols = [desc[0] for desc in self.cursor.description]
            rows = [dict(zip(cols, row)) for row in self.cursor.fetchall()]
            
            if not rows:
                return None
            
            # 構建結果
            result = {
                'race_num': race_num,
                'distance': rows[0]['distance'],
                'going': rows[0]['going'],
                'track': rows[0]['track'],
                'statistics': []
            }
            
            for row in rows:
                result['statistics'].append({
                    'draw': row['draw'],
                    'races_run': row['races_run'],
                    'wins': row['wins'],
                    'places': row['places'],
                    'thirds': row['thirds'],
                    'fourths': row['fourths'],
                    'win_rate': row['win_rate'],
                    'place_rate': row['place_rate'],
                    'top3_rate': row['top3_rate'],
                    'top4_rate': row['top4_rate']
                })
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 查詢場次統計失敗: {e}")
            return None

    def get_latest_date(self) -> Optional[str]:
        """獲取數據庫中最新的檔位統計日期"""
        try:
            self.cursor.execute(
                'SELECT DISTINCT date FROM draw_statistics ORDER BY date DESC LIMIT 1'
            )
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception:
            return None

    def get_all_dates(self) -> List[str]:
        """獲取所有有數據的日期"""
        try:
            self.cursor.execute(
                'SELECT DISTINCT date FROM draw_statistics ORDER BY date DESC'
            )
            return [row[0] for row in self.cursor.fetchall()]
        except Exception:
            return []

    def delete_draw_statistics(self, date: str) -> bool:
        """刪除指定日期的檔位統計數據"""
        try:
            self.cursor.execute('DELETE FROM draw_statistics WHERE date = ?', (date,))
            deleted = self.cursor.rowcount
            self.connection.commit()
            logger.info(f"✅ 已刪除 {date} 的 {deleted} 筆數據")
            return True
        except sqlite3.Error as e:
            logger.error(f"❌ 刪除失敗: {e}")
            return False

    # ========================================================================
    # 導出功能
    # ========================================================================

    def export_racecard_csv(self, race_id: str, filename: str) -> bool:
        """匯出排位表為 CSV"""
        try:
            horses = self.get_racecard(race_id)
            if not horses:
                logger.warning(f"⚠️ 未找到排位表: {race_id}")
                return False
            
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                if horses:
                    fieldnames = list(horses[0].keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(horses)
            
            logger.info(f"✅ 排位表已匯出: {filename}")
            return True
        except Exception as e:
            logger.error(f"❌ 匯出失敗: {e}")
            return False

    def export_draw_statistics_csv(self, date: str, filename: str) -> bool:
        """
        匯出檔位統計為 CSV
        
        Args:
            date: 日期
            filename: 文件名
            
        Returns:
            bool: 成功返回 True
        """
        try:
            races = self.get_all_races_for_date(date)
            if not races:
                logger.warning(f"⚠️ 未找到日期 {date} 的數據")
                return False
            
            # 準備 CSV 數據
            rows = []
            for race_num, race_data in sorted(races.items()):
                for stat in race_data['statistics']:
                    rows.append({
                        '日期': date,
                        '場次': race_num,
                        '距離': race_data['distance'],
                        '跑道': race_data['track'],
                        '地況': race_data['going'],
                        '檔位': stat['draw'],
                        '出賽': stat['races_run'],
                        '冠': stat['wins'],
                        '亞': stat['places'],
                        '季': stat['thirds'],
                        '殿': stat['fourths'],
                        '勝率%': f"{stat['win_rate']:.2f}",
                        '入Q%': f"{stat['place_rate']:.2f}",
                        '上名%': f"{stat['top3_rate']:.2f}",
                        '前四%': f"{stat['top4_rate']:.2f}"
                    })
            
            # 寫入 CSV
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                fieldnames = list(rows[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            logger.info(f"✅ 檔位統計已匯出: {filename} ({len(rows)} 筆)")
            return True
        
        except Exception as e:
            logger.error(f"❌ 匯出失敗: {e}")
            return False

    # ========================================================================
    # 日誌相關方法
    # ========================================================================

    def log_operation(self, operation: str, status: str, message: str = None) -> bool:
        """記錄爬蟲操作日誌"""
        try:
            self.cursor.execute(
                'INSERT INTO crawler_logs (operation, status, message) VALUES (?, ?, ?)',
                (operation, status, message)
            )
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"❌ 記錄日誌失敗: {e}")
            return False

    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """獲取最近的操作日誌"""
        try:
            self.cursor.execute(
                'SELECT * FROM crawler_logs ORDER BY created_at DESC LIMIT ?',
                (limit,)
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ 查詢日誌失敗: {e}")
            return []

    # ========================================================================
    # 統計功能
    # ========================================================================

    def get_statistics(self) -> Dict:
        """獲取數據庫統計信息"""
        try:
            stats = {}
            
            # 排位表統計
            self.cursor.execute('SELECT COUNT(*) as count FROM racecards')
            stats['racecard_count'] = self.cursor.fetchone()['count']
            
            # 馬匹往績統計
            self.cursor.execute('SELECT COUNT(*) as count FROM horse_histories')
            stats['horse_history_count'] = self.cursor.fetchone()['count']
            
            # 檔位統計
            self.cursor.execute('SELECT COUNT(*) as count FROM draw_statistics')
            stats['draw_statistics_count'] = self.cursor.fetchone()['count']
            
            # 檔位統計日期數
            self.cursor.execute('SELECT COUNT(DISTINCT date) as count FROM draw_statistics')
            stats['draw_dates_count'] = self.cursor.fetchone()['count']
            
            # 日誌統計
            self.cursor.execute('SELECT COUNT(*) as count FROM crawler_logs')
            stats['log_count'] = self.cursor.fetchone()['count']
            
            # 最近爬蟲狀態
            self.cursor.execute(
                'SELECT status, COUNT(*) as count FROM crawler_logs GROUP BY status'
            )
            stats['log_status'] = {row['status']: row['count'] for row in self.cursor.fetchall()}
            
            # 最新數據日期
            stats['latest_draw_date'] = self.get_latest_date()
            
            return stats
        except Exception as e:
            logger.error(f"❌ 獲取統計信息失敗: {e}")
            return {}

    # ========================================================================
    # 連接管理
    # ========================================================================

    def close(self):
        """關閉數據庫連接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("✅ 數據庫連接已關閉")
        except Exception as e:
            logger.error(f"❌ 關閉數據庫失敗: {e}")

    def __del__(self):
        """析構函數 - 自動關閉"""
        self.close()

    def __enter__(self):
        """支持 with 語句"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持 with 語句"""
        self.close()


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("測試: DatabaseManager v2.0")
    print("=" * 60)
    
    # 使用 with 語句自動管理連接
    with DatabaseManager('test_hkjc.db') as db:
        
        # 測試 1: 保存檔位統計
        print("\n📝 測試 1: 保存檔位統計")
        test_races = [
            {
                'race_num': 1,
                'distance': 1200,
                'going': 'C+3',
                'track': '草地',
                'statistics': [
                    {'draw': 1, 'races_run': 100, 'wins': 10, 'places': 12, 'thirds': 11, 'fourths': 9,
                     'win_rate': 10.0, 'place_rate': 22.0, 'top3_rate': 33.0, 'top4_rate': 42.0},
                    {'draw': 2, 'races_run': 105, 'wins': 12, 'places': 14, 'thirds': 13, 'fourths': 11,
                     'win_rate': 11.43, 'place_rate': 24.76, 'top3_rate': 37.14, 'top4_rate': 47.62},
                ]
            }
        ]
        
        success = db.save_all_races('2026-01-11', test_races)
        print(f"保存結果: {'✅ 成功' if success else '❌ 失敗'}")
        
        # 測試 2: 查詢檔位統計
        print("\n📊 測試 2: 查詢檔位統計")
        races = db.get_all_races_for_date('2026-01-11')
        if races:
            for race_num, race_data in races.items():
                print(f"\n第 {race_num} 場 | {race_data['distance']}米")
                for stat in race_data['statistics']:
                    print(f"  檔位 {stat['draw']}: 出賽 {stat['races_run']}, "
                          f"冠 {stat['wins']}, 勝率 {stat['win_rate']:.1f}%")
        
        # 測試 3: 匯出 CSV
        print("\n💾 測試 3: 匯出 CSV")
        csv_success = db.export_draw_statistics_csv('2026-01-11', 'test_draw_stats.csv')
        print(f"匯出結果: {'✅ 成功' if csv_success else '❌ 失敗'}")
        
        # 測試 4: 統計信息
        print("\n📈 測試 4: 數據庫統計")
        stats = db.get_statistics()
        print(f"排位表: {stats.get('racecard_count', 0)} 筆")
        print(f"檔位統計: {stats.get('draw_statistics_count', 0)} 筆")
        print(f"統計日期數: {stats.get('draw_dates_count', 0)} 天")
        print(f"最新日期: {stats.get('latest_draw_date', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("✅ 測試完成")
    print("=" * 60)
