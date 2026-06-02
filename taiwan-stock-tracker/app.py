import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

# 1. 資料庫連線設定（跟你剛才測試成功的一模一樣）
DB_URI = "postgresql://postgres.dhjoeipygutshnghmbub:Miumiu20050216@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres"
engine = create_engine(DB_URI)

# 網頁標題與設定
st.set_page_config(page_title="台灣股市自動化追蹤系統", layout="wide")
st.title("📊 台灣股市自動化追蹤系統 (Dashboard)")
st.caption("本系統由 Python ETL 管線自動每日更新，資料儲存於 Supabase 雲端資料庫")

# 2. 從雲端資料庫讀取資料
@st.cache_data(ttl=600)  # 快取資料 10 分鐘，避免頻繁讀取資料庫
def load_data():
    query = "SELECT * FROM taiwan_stocks ORDER BY date DESC"
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df

try:
    df = load_data()

    # 3. 側邊欄：讓使用者選擇股票標的
    available_stocks = df['symbol'].unique()
    selected_stock = st.sidebar.selectbox("📈 選擇你要檢視的股票：", available_stocks)

    # 篩選出該股票的資料
    stock_df = df[df['symbol'] == selected_stock].sort_values('date')

    # 4. 顯示最新股價資訊卡片
    latest_data = stock_df.iloc[-1]
    prev_data = stock_df.iloc[-2] if len(stock_df) > 1 else latest_data
    
    price_diff = latest_data['close'] - prev_data['close']
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="最新收盤價", value=f"${latest_data['close']:.2f}", delta=f"{price_diff:.2f}")
    col2.metric(label="今日最高價", value=f"${latest_data['high']:.2f}")
    col3.metric(label="今日最低價", value=f"${latest_data['low']:.2f}")
    col4.metric(label="成交量 (股)", value=f"{int(latest_data['volume']):,}")

    # 5. 繪製互動式折線圖 (收盤價、MA5、MA20)
    st.subheader(f"🔍 {selected_stock} 歷史價格與移動平均線 (MA)")
    
    # 轉換成 Plotly 方便畫圖的格式
    fig = px.line(stock_df, x='date', y=['close', 'ma5', 'ma20'],
                  labels={'value': '價格', 'date': '日期', 'variable': '指標'},
                  title=f"{selected_stock} 趨勢圖")
    
    # 美化圖表
    fig.update_layout(hovermode="x unified", legend_orientation="h", legend_y=1.1)
    st.plotly_chart(fig, use_container_width=True)

    # 6. 顯示原始資料表
    st.subheader("📋 雲端資料庫原始數據 (最新 10 筆)")
    st.dataframe(stock_df.tail(10).sort_values('date', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"連線或讀取資料庫時發生錯誤：{e}")