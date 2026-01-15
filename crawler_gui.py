import tkinter as tk
from tkinter import ttk, messagebox
import threading
from race_crawler import make_day_reports
import os
import glob
import sys

class CrawlerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🐴 HKJC 賽馬爬蟲工具")
        self.root.geometry("550x420")
        self.root.resizable(False, False)
        
        # 設置樣式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 標題
        title_label = ttk.Label(root, text="HKJC 賽馬分段時間爬蟲", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=15)
        
        # 日期輸入框
        date_frame = ttk.Frame(root)
        date_frame.pack(pady=10, padx=20, fill='x')
        
        ttk.Label(date_frame, text="賽事日期:", font=("Arial", 11)).pack(side='left', padx=5)
        self.date_entry = ttk.Entry(date_frame, font=("Arial", 11), width=20)
        self.date_entry.pack(side='left', padx=5)
        self.date_entry.insert(0, "30/11/2025")
        
        ttk.Label(date_frame, text="格式: dd/mm/yyyy", 
                 font=("Arial", 9, "italic"), foreground="gray").pack(side='left', padx=5)
        
        # 場次輸入框
        race_frame = ttk.Frame(root)
        race_frame.pack(pady=10, padx=20, fill='x')
        
        ttk.Label(race_frame, text="場次數量:", font=("Arial", 11)).pack(side='left', padx=5)
        self.race_spinbox = ttk.Spinbox(race_frame, from_=1, to=12, width=10, 
                                        font=("Arial", 11))
        self.race_spinbox.set(10)
        self.race_spinbox.pack(side='left', padx=5)
        
        # 目錄標籤
        dir_label = ttk.Label(root, text="💾 檔案保存位置: C:\\hkjc_app", 
                             font=("Arial", 9, "italic"), foreground="blue")
        dir_label.pack(pady=5)
        
        # 執行按鈕
        self.run_button = ttk.Button(root, text="🚀 開始爬蟲", command=self.run_crawler)
        self.run_button.pack(pady=15)
        
        # 狀態文字框
        self.status_frame = ttk.Frame(root)
        self.status_frame.pack(pady=10, padx=20, fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(self.status_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.status_text = tk.Text(self.status_frame, height=15, width=60, 
                                   font=("Courier", 9), yscrollcommand=scrollbar.set)
        self.status_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.status_text.yview)
        
    def log_message(self, message):
        """添加日誌信息"""
        self.status_text.insert('end', message + '\n')
        self.status_text.see('end')
        self.root.update()
    
    def run_crawler(self):
        """執行爬蟲"""
        race_date = self.date_entry.get().strip()
        max_race_no = int(self.race_spinbox.get())
        
        # 驗證日期格式
        if not self._validate_date(race_date):
            messagebox.showerror("錯誤", "日期格式錯誤！請使用 dd/mm/yyyy 格式")
            return
        
        # 禁用按鈕
        self.run_button.config(state='disabled')
        self.date_entry.config(state='disabled')
        self.race_spinbox.config(state='disabled')
        
        # 清空狀態框
        self.status_text.delete('1.0', 'end')
        
        # 在新線程中執行爬蟲（避免 GUI 凍結）
        thread = threading.Thread(target=self._crawler_thread, args=(race_date, max_race_no))
        thread.daemon = True
        thread.start()
    
    def _crawler_thread(self, race_date, max_race_no):
        """爬蟲線程"""
        try:
            # 改變工作目錄到 C:\hkjc_app
            app_dir = r"C:\hkjc_app"
            if not os.path.exists(app_dir):
                self.log_message(f"❌ 找不到目錄: {app_dir}")
                messagebox.showerror("錯誤", f"找不到目錄：{app_dir}\n\n請確保 hkjc_app 資料夾在 C:\\ 下")
                self.run_button.config(state='normal')
                self.date_entry.config(state='normal')
                self.race_spinbox.config(state='normal')
                return
            
            os.chdir(app_dir)
            
            self.log_message(f"開始爬取 {race_date} 的 {max_race_no} 場賽事...\n")
            self.log_message(f"工作目錄: {os.getcwd()}\n")
            self.log_message("="*60 + "\n")
            
            # 執行爬蟲
            make_day_reports(race_date, max_race_no, save_csv=True, print_report=False)
            
            # 檢查生成的 CSV 檔案
            d, m, y = race_date.split("/")
            date_key = f"{y}{m}{d}"
            
            self.log_message("\n" + "="*60)
            self.log_message("✅ 爬蟲完成！")
            self.log_message("="*60)
            
            # 列出生成的 CSV 檔案
            csv_files = glob.glob(f"sectional_{date_key}_*.csv")
            if csv_files:
                self.log_message(f"\n✓ 已生成 {len(csv_files)} 個 CSV 檔案：\n")
                for csv_file in sorted(csv_files):
                    if os.path.exists(csv_file):
                        file_size = os.path.getsize(csv_file) / 1024  # KB
                        self.log_message(f"  📄 {csv_file} ({file_size:.1f} KB)")
                self.log_message(f"\n📁 檔案位置: {app_dir}")
                self.log_message(f"\n✓ 可以直接用 app_gui.py 查看這些資料！")
            else:
                self.log_message(f"\n⚠️ 找不到生成的 CSV 檔案 (模式: sectional_{date_key}_*.csv)")
            
            messagebox.showinfo("成功", f"✅ 已成功爬取 {max_race_no} 場賽事！\n\nCSV 檔案已保存到:\nC:\\hkjc_app\n\n現在可以用 app_gui.py 查看資料")
            
        except Exception as e:
            self.log_message(f"\n❌ 爬蟲出現錯誤: {str(e)}")
            import traceback
            self.log_message(f"\n{traceback.format_exc()}")
            messagebox.showerror("錯誤", f"爬蟲出錯：{e}")
        
        finally:
            # 重新啟用按鈕
            self.run_button.config(state='normal')
            self.date_entry.config(state='normal')
            self.race_spinbox.config(state='normal')
    
    def _validate_date(self, date_str):
        """驗證日期格式 (dd/mm/yyyy)"""
        parts = date_str.split('/')
        if len(parts) != 3:
            return False
        try:
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            return 1 <= d <= 31 and 1 <= m <= 12 and 2000 <= y <= 2100
        except:
            return False

if __name__ == "__main__":
    root = tk.Tk()
    app = CrawlerGUI(root)
    root.mainloop()
