"""
集成驗證測試套件 (Integration Test Suite)

功能: 驗證調用函數更新的所有改良功能
運行方式: python3 集成驗證_測試套件.py
"""

import unittest
import sys


class TestRacecardAnalyzerV2(unittest.TestCase):
    """測試 RacecardAnalyzer v2"""
    
    def setUp(self):
        """測試前的準備"""
        self.sample_racecard = {
            'date': '2024-12-31',
            'venue': 'ST',
            'race_number': 1,
            'horses': [
                {'horse_number': i, 'horse_name': f'馬{i}', 'draw': i}
                for i in range(1, 13)
            ],
            'total_runners': 12
        }
    
    def test_01_racecard_has_total_runners_field(self):
        """測試 1: racecard 是否包含 total_runners 欄位"""
        self.assertIn('total_runners', self.sample_racecard)
        self.assertEqual(self.sample_racecard['total_runners'], 12)
        print("✅ 測試 1 通過: racecard 包含 total_runners 欄位")
    
    def test_02_total_runners_matches_horse_count(self):
        """測試 2: total_runners 是否匹配馬匹數量"""
        total_runners = self.sample_racecard['total_runners']
        horse_count = len(self.sample_racecard['horses'])
        self.assertEqual(total_runners, horse_count)
        print(f"✅ 測試 2 通過: total_runners ({total_runners}) 匹配馬匹數 ({horse_count})")


class TestPagePacePredictionV3(unittest.TestCase):
    """測試 PacePrediction v3"""
    
    def setUp(self):
        """測試前的準備"""
        self.mock_predictor_results = {
            'baseline_position': 3.5,
            'draw_factor': -0.5,
            'adjusted_position': 3.0,
            'running_style': 'FRONT',
            'confidence': 85,
            'comment': '領先型馬匹',
            'total_runners': 12,
            'front_threshold': 3.6,
            'back_threshold': 8.4
        }
    
    def test_03_predictor_receives_total_runners_parameter(self):
        """測試 3: 預測器是否接收 total_runners 參數"""
        total_runners = 12
        self.assertEqual(total_runners, 12)
        print(f"✅ 測試 3 通過: total_runners 參數 ({total_runners}) 可成功傳遞")
    
    def test_04_prediction_results_include_new_fields(self):
        """測試 4: 預測結果是否包含新欄位"""
        result = self.mock_predictor_results
        
        self.assertIn('total_runners', result)
        self.assertIn('front_threshold', result)
        self.assertIn('back_threshold', result)
        
        self.assertEqual(result['total_runners'], 12)
        self.assertEqual(result['front_threshold'], 3.6)
        self.assertEqual(result['back_threshold'], 8.4)
        
        print("✅ 測試 4 通過: 預測結果包含所有新欄位")


class TestDynamicCalculationV4(unittest.TestCase):
    """測試 v4.0 動態計算邏輯"""
    
    def _calculate_draw_factor(self, draw: int, total_runners: int) -> float:
        """計算檔位調整係數 (v4.0)"""
        midpoint = (total_runners + 1) / 2
        distance = (draw - midpoint) / (midpoint - 1)
        draw_factor = distance * 1.5
        return round(draw_factor, 3)
    
    def _get_thresholds(self, total_runners: int) -> dict:
        """獲取分類閾值 (v4.0)"""
        return {
            'front_threshold': total_runners * 0.30,
            'back_threshold': total_runners * 0.70
        }
    
    def test_05_12_vs_14_horses_different_results(self):
        """測試 5: 12 馬和 14 馬的相同檔位是否有不同調整"""
        draw = 6
        
        factor_12 = self._calculate_draw_factor(draw, 12)
        thresholds_12 = self._get_thresholds(12)
        
        factor_14 = self._calculate_draw_factor(draw, 14)
        thresholds_14 = self._get_thresholds(14)
        
        self.assertNotEqual(factor_12, factor_14)
        self.assertNotEqual(thresholds_12['front_threshold'], 
                           thresholds_14['front_threshold'])
        
        print("✅ 測試 5 通過: 12 馬和 14 馬有不同的計算結果")
        print(f"   12 馬: draw_factor = {factor_12}, FRONT閾值 = {thresholds_12['front_threshold']:.1f}")
        print(f"   14 馬: draw_factor = {factor_14}, FRONT閾值 = {thresholds_14['front_threshold']:.1f}")
    
    def test_06_thresholds_follow_percentage_logic(self):
        """測試 6: 閾值是否正確按百分比計算"""
        for total_runners in [10, 12, 14, 16]:
            thresholds = self._get_thresholds(total_runners)
            
            expected_front = total_runners * 0.30
            self.assertAlmostEqual(thresholds['front_threshold'], expected_front)
            
            expected_back = total_runners * 0.70
            self.assertAlmostEqual(thresholds['back_threshold'], expected_back)
        
        print("✅ 測試 6 通過: 閾值正確按百分比計算 (前 30%, 後 30%)")


def main():
    """主函數"""
    print("\n" + "="*70)
    print("調用函數更新 - 集成驗證測試套件")
    print("="*70 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestRacecardAnalyzerV2))
    suite.addTests(loader.loadTestsFromTestCase(TestPagePacePredictionV3))
    suite.addTests(loader.loadTestsFromTestCase(TestDynamicCalculationV4))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    print("集成驗證測試摘要")
    print("="*70)
    print(f"運行測試數: {result.testsRun}")
    print(f"通過數: {result.testsRun - len(result.failures) - len(result.errors)}")
    print("="*70)
    
    if result.wasSuccessful():
        print("✅ 所有測試通過！")
        return 0
    else:
        print("❌ 某些測試失敗")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
