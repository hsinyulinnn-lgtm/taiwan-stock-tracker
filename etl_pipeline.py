import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
import datetime

# 1. 資料庫連線設定（使用連線池 6543 通訊埠與純英文數字密碼）
DB_URI = "postgresql://postgres.dhjoeipygutshnghmbub:Miumiu20050216@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres"
STOCKS = ["2330.TW", "0050.TW", "00878.TW"]

# 2. 建立資料庫引擎
engine = create_engine(DB_URI)

def get_stock_data(symbol):
    """從 Yahoo Finance 抓取股票資料並計算移動平均線"""
    print(f"🚀 正在處理標的: {symbol}")
    
    # 抓取最近 60 天的歷史資料
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="60d")
    
    if df.empty:
        print(f"⚠️ 找不到 {symbol} 的資料，跳過。")
        return None
        
    # 重設索引，讓日期變成普通欄位
    df = df.reset_index()
    
    # 計算 5 日與 20 日移動平均線 (MA)
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    # 整理出我們要存進資料庫的欄位
    df['symbol'] = symbol
    df = df[['Date', 'symbol', 'Open', 'High', 'Low', 'Close', 'Volume', 'MA5', 'MA20']]
    
    # 將欄位名稱全部改成小寫，避免 PostgreSQL 的大小寫限制問題
    df.columns = ['date', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'ma5', 'ma20']
    
    # 把日期格式統一轉成純日期（去除時區資訊）
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    return df

def run_etl():
    """執行完整的 ETL 流程並寫入 Supabase"""
    all_data = []
    for stock in STOCKS:
        df = get_stock_data(stock)
        if df is not None:
            all_data.append(df)
            
    if all_data:
        # 合併所有股票的 Dataframe
        final_df = pd.concat(all_data, ignore_index=True)
        
        # 寫入 Supabase 資料庫（如果資料表已存在，就覆蓋更新 if_exists='replace'）
        with engine.connect() as conn:
            final_df.to_sql('taiwan_stocks', conn, if_exists='replace', index=False)
        print("✅ 所有資料已成功成功寫入 Supabase 雲端資料庫！")
    else:
        print("❌ 沒有任何資料被處理。")

if __name__ == "__main__":
    run_etl()
