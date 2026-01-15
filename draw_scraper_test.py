#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
draw_statistics_scraper_test.py - v1.0 測試爬蟲

功能: 測試是否能爬取香港馬會檔位統計數據

使用: python draw_statistics_scraper_test.py
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import logging

# ===== 日誌配置 =====
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DrawStatisticsScraperTest:
    """香港馬會檔位統計爬蟲 - 測試版"""
    
    def __init__(self):
        self.base_url = "https://racing.hkjc.com/zh-hk/local/information/draw"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-HK,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'https://racing.hkjc.com/'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def test_connection(self):
        """測試 1: 檢查連接"""
        logger.info("="*60)
        logger.info("測試 1: 連接測試")
        logger.info("="*60)
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            logger.info(f"✅ URL 可訪問")
            logger.info(f"📊 HTTP 狀態碼: {response.status_code}")
            logger.info(f"📋 Content-Type: {response.headers.get('Content-Type')}")
            logger.info(f"📏 頁面大小: {len(response.content)} 字節")
            
            if response.status_code == 200:
                logger.info("✅ 連接成功!")
                return True
            else:
                logger.warning(f"⚠️ 狀態碼非 200: {response.status_code}")
                return False
        
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ 連接失敗: {str(e)}")
            return False
        except requests.exceptions.Timeout:
            logger.error("❌ 連接超時")
            return False
        except Exception as e:
            logger.error(f"❌ 未知錯誤: {str(e)}")
            return False
    
    def test_html_structure(self):
        """測試 2: 分析 HTML 結構"""
        logger.info("\n" + "="*60)
        logger.info("測試 2: HTML 結構分析")
        logger.info("="*60)
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            logger.info(f"✅ HTML 解析成功")
            
            # 查找表格
            tables = soup.find_all('table')
            logger.info(f"📊 找到 {len(tables)} 個表格")
            
            if len(tables) == 0:
                logger.warning("⚠️ 沒有找到 HTML 表格")
                logger.info("💡 可能原因: 數據由 JavaScript 動態加載")
                return False
            
            # 分析第一個表格
            if len(tables) > 0:
                first_table = tables[0]
                rows = first_table.find_all('tr')
                logger.info(f"📈 第一個表格: {len(rows)} 行")
                
                if len(rows) > 0:
                    cells = rows[0].find_all(['th', 'td'])
                    logger.info(f"📋 第一行: {len(cells)} 列")
            
            logger.info("✅ HTML 結構分析完成")
            return True
        
        except Exception as e:
            logger.error(f"❌ 分析失敗: {str(e)}")
            return False
    
    def test_data_extraction(self):
        """測試 3: 數據提取"""
        logger.info("\n" + "="*60)
        logger.info("測試 3: 數據提取測試")
        logger.info("="*60)
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找表格
            tables = soup.find_all('table')
            
            if len(tables) == 0:
                logger.warning("❌ 沒有找到表格")
                return None
            
            # 嘗試提取數據
            extracted_data = {
                'timestamp': datetime.now().isoformat(),
                'url': self.base_url,
                'tables_found': len(tables),
                'samples': []
            }
            
            # 從前 3 個表格提取樣本數據
            for idx, table in enumerate(tables[:3]):
                rows = table.find_all('tr')
                table_data = {
                    'table_index': idx,
                    'rows': len(rows),
                    'sample_rows': []
                }
                
                # 提取前 3 行
                for row_idx, row in enumerate(rows[:3]):
                    cells = row.find_all(['th', 'td'])
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    table_data['sample_rows'].append({
                        'row_index': row_idx,
                        'cells': len(cells),
                        'content': cell_texts[:5]  # 只保留前 5 列
                    })
                
                extracted_data['samples'].append(table_data)
            
            logger.info(f"✅ 成功提取 {len(extracted_data['samples'])} 個表格的樣本")
            
            # 打印樣本數據
            logger.info("\n📊 提取的樣本數據:")
            logger.info(json.dumps(extracted_data, indent=2, ensure_ascii=False))
            
            return extracted_data
        
        except Exception as e:
            logger.error(f"❌ 提取失敗: {str(e)}")
            return None
    
    def test_javascript_detection(self):
        """測試 4: JavaScript 動態加載檢測"""
        logger.info("\n" + "="*60)
        logger.info("測試 4: JavaScript 動態加載檢測")
        logger.info("="*60)
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找一些常見的 JavaScript 框架跡象
            react_check = soup.find(id='__react')
            vue_check = soup.find(id='app')
            angular_check = soup.find('ng-app') or soup.find('[ng-app]')
            
            indicators = {
                'React': bool(react_check),
                'Vue': bool(vue_check),
                'Angular': bool(angular_check),
                'Script tags': len(soup.find_all('script'))
            }
            
            logger.info("🔍 框架檢測:")
            for framework, found in indicators.items():
                status = "✅ 發現" if found else "❌ 未發現"
                logger.info(f"  {status}: {framework}")
            
            # 查找數據容器
            tables = soup.find_all('table')
            
            if len(tables) > 0:
                logger.info("✅ 靜態表格存在 - 可直接爬取")
                return {'javascript_required': False, 'reason': 'Static HTML tables found'}
            else:
                logger.warning("⚠️ 未找到靜態表格")
                logger.info("💡 可能需要 JavaScript 渲染")
                return {'javascript_required': True, 'reason': 'No static tables found'}
        
        except Exception as e:
            logger.error(f"❌ 檢測失敗: {str(e)}")
            return None
    
    def run_all_tests(self):
        """運行所有測試"""
        logger.info("\n\n" + "🚀 "*30)
        logger.info("香港馬會檔位統計爬蟲 - 完整測試")
        logger.info("🚀 "*30 + "\n")
        
        results = {}
        
        # 測試 1
        results['connection'] = self.test_connection()
        
        if not results['connection']:
            logger.error("\n❌ 連接失敗，無法繼續測試")
            return results
        
        # 測試 2
        results['html_structure'] = self.test_html_structure()
        
        # 測試 3
        results['data_extraction'] = self.test_data_extraction()
        
        # 測試 4
        results['javascript_detection'] = self.test_javascript_detection()
        
        # 生成報告
        self.generate_report(results)
        
        return results
    
    def generate_report(self, results):
        """生成測試報告"""
        logger.info("\n\n" + "="*60)
        logger.info("📋 測試報告總結")
        logger.info("="*60)
        
        logger.info("\n✅ 測試結果:")
        logger.info(f"  1️⃣  連接測試: {'✅ 通過' if results['connection'] else '❌ 失敗'}")
        logger.info(f"  2️⃣  HTML 結構: {'✅ 通過' if results['html_structure'] else '❌ 失敗'}")
        logger.info(f"  3️⃣  數據提取: {'✅ 通過' if results['data_extraction'] else '❌ 失敗'}")
        
        # 建議
        logger.info("\n💡 建議:")
        
        if results['connection'] and results['html_structure']:
            logger.info("  ✅ 可以使用簡單爬蟲 (BeautifulSoup)")
            logger.info("  ✅ 預計開發時間: 2-3 小時")
            logger.info("  ✅ 推薦方案: 方案 A (簡單爬蟲)")
        else:
            logger.info("  ⚠️ 可能需要使用高級爬蟲 (Selenium)")
            logger.info("  ⚠️ 預計開發時間: 4-6 小時")
            logger.info("  ⚠️ 備用方案: 方案 B (Selenium)")
        
        logger.info("\n📝 後續步驟:")
        logger.info("  1. 確認爬蟲可行性")
        logger.info("  2. 編寫完整爬蟲模塊")
        logger.info("  3. 實現配腳評分功能")
        logger.info("  4. 集成到主應用")
        
        logger.info("\n" + "="*60)


# ===== 主函數 =====
if __name__ == "__main__":
    logger.info("🐴 香港馬會檔位統計爬蟲 - 測試版 v1.0\n")
    
    scraper = DrawStatisticsScraperTest()
    results = scraper.run_all_tests()
    
    logger.info("\n\n✅ 所有測試完成!")
    logger.info("📊 詳細結果已上方顯示")
    logger.info("\n💬 下一步: 根據測試結果決定爬蟲方案")
