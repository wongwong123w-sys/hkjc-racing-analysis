@echo off
REM HKJC 賽馬爬蟲工具 - Windows 啟動腳本

echo.
echo ================================
echo  HKJC 賽馬分段時間爬蟲工具
echo ================================
echo.
echo 選擇要執行的程式：
echo.
echo 1. 爬取賽事數據 (run_crawler.py)
echo 2. 查看分析應用 (app.py)
echo 3. 結束
echo.

set /p choice="請輸入選項 (1/2/3): "

if "%choice%"=="1" (
    echo.
    echo 正在啟動爬蟲程式...
    echo.
    python run_crawler.py
) else if "%choice%"=="2" (
    echo.
    echo 正在啟動 Streamlit 應用...
    echo.
    python -m streamlit run app.py
) else if "%choice%"=="3" (
    echo 再見！
    exit /b 0
) else (
    echo 無效的選項，請重新選擇
    pause
    goto :eof
)

pause
