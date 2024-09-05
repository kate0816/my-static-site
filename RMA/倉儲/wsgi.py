import os
from dotenv import load_dotenv  # 確保已安裝 python-dotenv

# 加載環境變量
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from app import app  # 將 your_app_name 替換為您的 Flask 應用程序的模塊名稱
