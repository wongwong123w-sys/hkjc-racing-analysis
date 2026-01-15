
# -*- coding: utf-8 -*-

"""
档位统计爬虫 - 繁体修复版

修复：支持繁体中文（場、賽道等）
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import re
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DrawStatisticsParser:
    """档位统计爬虫 - Selenium版"""
    
    BASE_URL = "https://racing.hkjc.com/zh-hk/local/information/draw"
    
    def __init__(self):
        self.driver = None
        logger.info("✅ 爬虫已初始化")
    
    def _init_driver(self):
        """初始化 Selenium WebDriver"""
        try:
            logger.info("🔧 正在初始化浏览器驱动...")
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            chrome_options.add_argument('--lang=zh-HK')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            
            logger.info("✅ 浏览器驱动初始化成功")
            return True
        
        except Exception as e:
            logger.error(f"❌ 浏览器驱动初始化失败: {e}")
            return False
    
    def _close_driver(self):
        """关闭浏览器驱动"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🔒 浏览器已关闭")
            except:
                pass
    
    def fetch_all_races(self) -> Dict:
        """爬取所有场次的档位统计"""
        try:
            logger.info("=" * 60)
            logger.info("🔄 开始爬取档位统计...")
            logger.info(f"🌐 目标网址: {self.BASE_URL}")
            
            if not self._init_driver():
                return self._error_result('浏览器驱动初始化失败')
            
            logger.info("📡 正在加载页面...")
            self.driver.get(self.BASE_URL)
            
            logger.info("⏳ 等待页面渲染...")
            time.sleep(3)
            
            # 提取日期
            date_str = self._extract_date()
            logger.info(f"📅 赛事日期: {date_str}")
            
            # 解析所有场次
            races = self._parse_all_races()
            
            if not races:
                logger.warning("⚠️ 未找到场次数据")
                self._close_driver()
                return self._error_result('未找到场次数据', date_str)
            
            logger.info(f"✅ 成功解析 {len(races)} 场赛事")
            logger.info("=" * 60)
            
            self._close_driver()
            
            return {
                'status': 'success',
                'date': date_str,
                'races': races,
                'message': f'成功爬取 {len(races)} 场赛事'
            }
        
        except Exception as e:
            logger.error(f"❌ 爬虫错误: {e}", exc_info=True)
            self._close_driver()
            return self._error_result(f'爬虫错误: {str(e)}')
    
    def _error_result(self, message: str, date: str = None) -> Dict:
        """返回错误结果"""
        return {
            'status': 'error',
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'races': [],
            'message': message
        }
    
    def _extract_date(self) -> str:
        """提取日期"""
        try:
            try:
                date_element = self.driver.find_element(By.XPATH, "//div[@class='date_title']//a")
                date_text = date_element.text.strip()
            except:
                date_element = self.driver.find_element(By.XPATH, "//*[contains(text(), '月') and contains(text(), '日')]")
                date_text = date_element.text.strip()
            
            match = re.search(r'(\d{1,2})月(\d{1,2})日', date_text)
            if match:
                month, day = match.groups()
                year = datetime.now().year
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            return datetime.now().strftime('%Y-%m-%d')
        
        except Exception as e:
            logger.warning(f"⚠️ 日期提取失败: {e}")
            return datetime.now().strftime('%Y-%m-%d')
    
    def _parse_all_races(self) -> List[Dict]:
        """解析所有场次"""
        races = []
        
        try:
            # 查找所有赛事容器
            race_containers = self.driver.find_elements(By.CLASS_NAME, 'searchResult')
            logger.info(f"🔍 找到 {len(race_containers)} 个赛事容器")
            
            for idx, container in enumerate(race_containers):
                try:
                    # 直接在容器内查找标题行
                    try:
                        header_row = container.find_element(
                            By.XPATH, 
                            ".//tr[@class='bg_blue color_w font_wb f_tal f_fs16']"
                        )
                        header_td = header_row.find_element(By.TAG_NAME, 'td')
                        header_text = header_td.text.strip()
                        
                    except Exception as e:
                        logger.warning(f"  ⚠️ 容器 {idx+1} 无法找到标题行: {e}")
                        continue
                    
                    # 提取场次号码 - 支持繁体中文 "場"
                    race_match = re.search(r'第\s*(\d+)\s*[场場]', header_text)
                    if not race_match:
                        logger.warning(f"  ⚠️ 容器 {idx+1} 无法提取场次号")
                        continue
                    race_num = int(race_match.group(1))
                    
                    # 提取距离
                    distance_match = re.search(r'(\d{3,4})\s*米', header_text)
                    distance = int(distance_match.group(1)) if distance_match else 1200
                    
                    # 提取场地 - 支持繁体
                    if '草地' in header_text:
                        track = '草地'
                    elif '沙地' in header_text or '泥地' in header_text or '全天候' in header_text:
                        track = '沙地'
                    else:
                        track = '草地'
                    
                    # 提取地况
                    going_match = re.search(r'"([CGA][+\-]?\d*)"', header_text)
                    going = going_match.group(1) if going_match else 'C'
                    
                    logger.info(f"  🏇 第 {race_num} 场: {distance}米, {track}, {going}")
                    
                    # 查找该容器内的所有数据行
                    tbody = container.find_element(By.TAG_NAME, 'tbody')
                    all_rows = tbody.find_elements(By.TAG_NAME, 'tr')
                    
                    # 过滤掉标题行
                    data_rows = [row for row in all_rows if 'bg_blue' not in row.get_attribute('class')]
                    
                    logger.info(f"    找到 {len(data_rows)} 行数据")
                    
                    statistics = []
                    for row in data_rows:
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        
                        if len(cells) >= 6:
                            try:
                                # 第一列：档位
                                draw_text = cells[0].text.strip()
                                if not draw_text or not draw_text.isdigit():
                                    continue
                                
                                draw = int(draw_text)
                                if not (1 <= draw <= 14):
                                    continue
                                
                                # 统计数据
                                races_run = self._safe_int(cells[1].text.strip())
                                wins = self._safe_int(cells[2].text.strip())
                                places = self._safe_int(cells[3].text.strip())
                                thirds = self._safe_int(cells[4].text.strip())
                                fourths = self._safe_int(cells[5].text.strip())
                                
                                # 计算百分比
                                if races_run > 0:
                                    win_rate = round((wins / races_run) * 100, 2)
                                    place_rate = round(((wins + places) / races_run) * 100, 2)
                                    top3_rate = round(((wins + places + thirds) / races_run) * 100, 2)
                                    top4_rate = round(((wins + places + thirds + fourths) / races_run) * 100, 2)
                                else:
                                    win_rate = place_rate = top3_rate = top4_rate = 0
                                
                                statistics.append({
                                    'draw': draw,
                                    'races_run': races_run,
                                    'wins': wins,
                                    'places': places,
                                    'thirds': thirds,
                                    'fourths': fourths,
                                    'win_rate': win_rate,
                                    'place_rate': place_rate,
                                    'top3_rate': top3_rate,
                                    'top4_rate': top4_rate
                                })
                            
                            except (ValueError, IndexError) as e:
                                continue
                    
                    if statistics:
                        races.append({
                            'race_num': race_num,
                            'distance': distance,
                            'going': going,
                            'track': track,
                            'statistics': statistics
                        })
                        logger.info(f"    ✅ 成功解析 {len(statistics)} 个档位")
                    else:
                        logger.warning(f"    ⚠️ 第 {race_num} 场没有找到有效统计数据")
                
                except Exception as e:
                    logger.warning(f"  ⚠️ 解析容器 {idx+1} 失败: {e}")
                    import traceback
                    logger.warning(traceback.format_exc())
            
            return races
        
        except Exception as e:
            logger.error(f"❌ 解析场次失败: {e}", exc_info=True)
            return []
    
    def _safe_int(self, text: str, default: int = 0) -> int:
        """安全整数转换"""
        try:
            clean_text = re.sub(r'\D', '', text)
            return int(clean_text) if clean_text else default
        except:
            return default


# ============================================================================
# 测试代码
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🏇 档位统计爬虫 - 繁体修复版")
    print("=" * 70)
    
    parser = DrawStatisticsParser()
    result = parser.fetch_all_races()
    
    print("\n" + "=" * 70)
    print("📊 爬取结果:")
    print("=" * 70)
    print(f"状态: {result['status']}")
    print(f"日期: {result['date']}")
    print(f"场次数: {len(result['races'])}")
    print(f"讯息: {result['message']}")
    
    if result['status'] == 'success' and result['races']:
        print("\n" + "-" * 70)
        for race in result['races']:
            print(f"\n🏇 第 {race['race_num']} 场:")
            print(f"  📏 距离: {race['distance']}米")
            print(f"  🌿 跑道: {race['track']}")
            print(f"  🌤️  地况: {race['going']}")
            print(f"  🎯 档位数: {len(race['statistics'])} 个")
            
            if race['statistics']:
                print(f"  📊 样本数据 (前3个档位):")
                for stat in race['statistics'][:3]:
                    print(f"    档位 {stat['draw']}: 出赛 {stat['races_run']}, "
                          f"冠 {stat['wins']}, 胜率 {stat['win_rate']:.1f}%")
        
        # 总结统计
        print("\n" + "=" * 70)
        print("📈 总结统计:")
        print("=" * 70)
        total_draws = sum(len(r['statistics']) for r in result['races'])
        total_races_run = sum(sum(s['races_run'] for s in r['statistics']) for r in result['races'])
        total_wins = sum(sum(s['wins'] for s in r['statistics']) for r in result['races'])
        print(f"  总场次: {len(result['races'])} 场")
        print(f"  总档位: {total_draws} 个")
        print(f"  总出赛: {total_races_run} 次")
        print(f"  总冠军: {total_wins} 次")
    
    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70)
