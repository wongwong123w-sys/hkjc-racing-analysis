import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os

class AppLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("🐴 HKJC 賽馬分析應用")
        self.root.geometry("450x280")
        self.root.resizable(False, False)
        
        # 標題
        title_label = tk.Label(root, text="HKJC 賽馬分段時間分析", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # 說明文字
        info_label = tk.Label(root, text="按下方按鈕啟動 Streamlit 應用\n（會自動在瀏覽器中打開）", 
                             font=("Arial", 11))
        info_label.pack(pady=15)
        
        # 目錄標籤
        dir_label = tk.Label(root, text="📁 工作目錄: C:\\hkjc_app", 
                            font=("Arial", 9, "italic"), foreground="blue")
        dir_label.pack(pady=5)
        
        # 啟動按鈕
        launch_button = tk.Button(root, text="🚀 啟動 Streamlit 應用", 
                                 command=self.launch_streamlit,
                                 font=("Arial", 12, "bold"),
                                 bg="#4CAF50", fg="white",
                                 padx=20, pady=10, width=30)
        launch_button.pack(pady=15)
        
        # 退出按鈕
        exit_button = tk.Button(root, text="❌ 退出", 
                               command=root.quit,
                               font=("Arial", 10),
                               bg="#f44336", fg="white",
                               padx=20, pady=8, width=30)
        exit_button.pack(pady=10)
    
    def launch_streamlit(self):
        """啟動 Streamlit 應用"""
        try:
            # 改變工作目錄到 C:\hkjc_app
            app_dir = r"C:\hkjc_app"
            if not os.path.exists(app_dir):
                messagebox.showerror("錯誤", f"找不到目錄：{app_dir}\n\n請確保 hkjc_app 資料夾在 C:\\ 下")
                return
            
            os.chdir(app_dir)
            current_dir = app_dir
            app_path = os.path.join(current_dir, "app.py")
            
            if not os.path.exists(app_path):
                messagebox.showerror("錯誤", "找不到 app.py 檔案！\n請確保 app.py 在 C:\\hkjc_app 目錄")
                return
            
            messagebox.showinfo("啟動中", "正在啟動 Streamlit 應用...\n應用會在瀏覽器中打開")
            
            # 使用 subprocess 啟動 streamlit
            subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", app_path],
                cwd=current_dir
            )
            
            # 提示用戶
            messagebox.showinfo("成功", "Streamlit 應用已啟動！\n請查看瀏覽器窗口。\n\n此窗口可以關閉。")
            self.root.quit()
            
        except Exception as e:
            messagebox.showerror("錯誤", f"啟動失敗：{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppLauncher(root)
    root.mainloop()
