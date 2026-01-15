import tkinter as tk
from tkinter import simpledialog, messagebox
from race_crawler import make_day_reports

# 建立隱藏的主視窗
root = tk.Tk()
root.withdraw()  # 隱藏主視窗

# 詢問日期
race_date = simpledialog.askstring(
    "HKJC 爬蟲工具",
    "請輸入賽事日期（格式：dd/mm/yyyy）\n例如：26/11/2025",
    initialvalue="26/11/2025"
)

if race_date is None:  # 用戶取消
    messagebox.showwarning("取消", "已取消爬蟲任務")
    root.destroy()
    exit()

# 詢問場次數
while True:
    max_race_str = simpledialog.askstring(
        "HKJC 爬蟲工具",
        f"請輸入當日場次數（1-12）\n日期：{race_date}",
        initialvalue="9"
    )
    
    if max_race_str is None:  # 用戶取消
        messagebox.showwarning("取消", "已取消爬蟲任務")
        root.destroy()
        exit()
    
    try:
        max_race_no = int(max_race_str)
        if 1 <= max_race_no <= 12:
            break
        else:
            messagebox.showerror("錯誤", "請輸入 1 至 12 之間的數字")
    except ValueError:
        messagebox.showerror("錯誤", "請輸入有效的數字")

# 隱藏視窗並執行爬蟲
root.destroy()

print(f"\n🚀 開始爬取 {race_date} 的 {max_race_no} 場賽事...\n")

try:
    make_day_reports(race_date, max_race_no, save_csv=True, print_report=False)
    print("\n✅ 爬蟲完成！所有 CSV 已存檔。")
    print(f"\n已生成以下檔案：")
    for i in range(1, max_race_no + 1):
        d, m, y = race_date.split("/")
        date_key = f"{y}{m}{d}"
        print(f"  ✓ sectional_{date_key}_{i}.csv")
    
    # 詢問是否啟動應用
    root2 = tk.Tk()
    root2.withdraw()
    result = messagebox.askyesno(
        "爬蟲完成",
        "爬蟲已完成！\n\n是否現在啟動 Streamlit 應用來查看資料？"
    )
    root2.destroy()
    
    if result:
        import subprocess
        subprocess.run(["python", "-m", "streamlit", "run", "app.py"])
    
except Exception as e:
    print(f"\n❌ 爬蟲出錯：{e}")
    root3 = tk.Tk()
    root3.withdraw()
    messagebox.showerror("錯誤", f"爬蟲出錯：{e}")
    root3.destroy()
