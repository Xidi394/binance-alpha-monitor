import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# --- 配置区域：你需要手动维护的“活动币”列表 ---
# 格式：'代币代码': '活动结束日期(年-月-日)'
ACTIVE_CAMPAIGNS = {
    'LISTAUSDT': '2025-12-30',
    'BBUSDT': '2025-06-20',
    'REZUSDT': '2025-05-15',
    'NOTUSDT': '2025-04-01',
    # 你可以随时在这里添加新的活动币
}

# --- 核心函数 ---
def get_binance_data():
    """从币安获取实时数据"""
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, timeout=5)
        return response.json()
    except:
        return []

def calculate_days_left(end_date_str):
    """计算剩余天数"""
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    delta = end_date - datetime.now()
    return max(delta.days, 0)

# --- 网页页面布局 ---
st.set_page_config(page_title="Alpha 空投监控台", layout="wide")

st.title("🚀 Alpha 空投实时监控大屏")
st.markdown("### 监控目标：高倍交易量活动代币 | 核心策略：稳如泰山")

# 侧边栏：模拟的新闻推送
with st.sidebar:
    st.header("📢 币安最新公告 (模拟)")
    st.info("🔥 [新] Binance Megadrop 即将上线 Lista DAO!")
    st.success("✅ IO.NET 空投已开放申领")
    st.warning("⚠️ 距离 BB 活动结束还剩 3 天")

# 1. 获取数据
data = get_binance_data()
if not data:
    st.error("无法连接币安接口，请检查网络...")
    st.stop()

# 2. 数据清洗与计算
target_coins = []
for item in data:
    symbol = item['symbol']
    
    # 只筛选我们在配置区域定义的“活动币”
    if symbol in ACTIVE_CAMPAIGNS:
        price = float(item['lastPrice'])
        high = float(item['highPrice'])
        low = float(item['lowPrice'])
        volume = float(item['quoteVolume'])
        count = int(item['count']) # 交易笔数
        
        # 计算波动率 (越低越好)
        volatility = ((high - low) / price) * 100
        
        # 计算剩余天数
        days_left = calculate_days_left(ACTIVE_CAMPAIGNS[symbol])
        
        target_coins.append({
            '代币': symbol,
            '当前价格': price,
            '波动率(%)': round(volatility, 3),
            '24H成交额(U)': round(volume / 1000000, 2), # 百万单位
            '活跃人数(笔数)': count,
            '活动剩余天数': days_left
        })

# 转成表格格式
if target_coins:
    df = pd.DataFrame(target_coins)
    
    # 3. 找出今日参与最多的前三名 (按活跃人数排序)
    top_3 = df.sort_values(by='活跃人数(笔数)', ascending=False).head(3)
    
    # --- 页面第一行：关键指标 ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("🔥 今日最热项目", top_3.iloc[0]['代币'], f"{top_3.iloc[0]['活跃人数(笔数)']} 笔交易")
    with c2:
        st.metric("🥈 第二名", top_3.iloc[1]['代币'], f"{top_3.iloc[1]['活跃人数(笔数)']} 笔交易")
    with c3:
        st.metric("🥉 第三名", top_3.iloc[2]['代币'], f"{top_3.iloc[2]['活跃人数(笔数)']} 笔交易")
    
    st.divider()

    # --- 页面第二行：详细监控表格 ---
    st.subheader("📊 4倍交易量活动代币监控表")
    
    # 样式高亮：波动率 < 1% 的标绿（适合刷），波动率 > 5% 的标红（危险）
    def highlight_volatility(val):
        color = 'green' if val < 1 else 'red' if val > 5 else 'black'
        return f'color: {color}; font-weight: bold'

    st.dataframe(
        df.style.applymap(highlight_volatility, subset=['波动率(%)'])
        .format({"当前价格": "{:.4f}", "24H成交额(U)": "{:.2f} M"}),
        use_container_width=True,
        height=400
    )
    
    st.caption("提示：'波动率'越低，刷量磨损越小；'活跃人数'越高，流动性越好。")

else:
    st.warning("当前没有匹配的活动代币数据，请检查配置列表。")

# 自动刷新按钮
if st.button('🔄 刷新数据'):
    st.rerun()