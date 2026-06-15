@echo off

start "C:\Program Files\Google\Chrome\Application\chrome.exe" "https://www.zillow.com" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\Documents\ZScraperAutomationProfile"

.\.venv\Scripts\python.exe .\main.py 
