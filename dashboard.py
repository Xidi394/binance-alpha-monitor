import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import random
import time

# --- 页面配置 ---
st.set_page_config(page_title="Alpha 空投监控台", layout="wide")

# --- 1. 配置区域：你需要手动维护的“活动币”列表 ---
ACTIVE_CAMPAIGNS = {
    'LISTAUSDT': '2025-12-30',
    'BBUSDT': '2025-06-20',
    'REZUSDT': '2025-05-15',
    'NOTUSDT': '2025-04-01',
    'IOUSDT': '2025-08-01',
    'ZKUSDT': '2025-07-15'
}

# --- 2. 核心功能函数 ---

def get_binance_data():
    """尝试从币安获取真实数据"""
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        # 设置超时时间，避免卡死
        response = requests.get(url, timeout=3)
        data = response.json()
        
        # 严格检查数据格式：必须是列表，且里面要有 symbol 字段
        if isinstance(data, list) and len(data) > 0 and 'symbol' in data[0]:
            return data, True # True 表示是真实数据
            
        # 如果返回的是错误字典（比如被封IP）
        return None, False
    except Exception as e:
        return None, False

def get_mock_data():
    """生成仿真数据（当真实接口被封时使用）"""
    mock_list = []
    for symbol, end_date in ACTIVE_CAMPAIGNS.items():
        # 随机生成一些逼真的数据
        base_price = random.uniform(0.1, 5.0)
        mock_list.append({
            'symbol': symbol,
            'lastPrice': str(base_price),
            'highPrice': str(base_price * 1.01), # 波动很小
            'lowPrice': str(base_price * 0.99),
            'quoteVolume': str(random.uniform(5000000, 50000000)), # 500万-5000万U
            'count': random.randint(5000, 50000) # 活跃人数
        })
    return mock_list

def calculate_days_left(end_date_str):
    """计算剩余天数"""
    try:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        delta = end_date - datetime.now()
        return max(delta.days, 0)
    except:
        return 0

# --- 3. 网页显示逻辑 ---

st.title("🚀 Alpha 空投实时监控大屏")

# 侧边栏
with st.sidebar:
    st.header("📢 状态面板")
    st.info("🔥 [新] Binance Megadrop 即将上线 Lista DAO!")
    
# 获取数据流程
with st.spinner('正在连接数据中心...'):
    raw_data, is_real = get_binance_data()

# 状态判断与处理
if is_real:
    st.success("✅ 已连接币安实时接口 (Real-time)")
    df_source = raw_data
else:
    st.warning("⚠️ 警告：当前IP无法连接币安接口（可能被防火墙拦截）。")
    st.caption("💡 已自动切换至 **[演示模式]**，以下为仿真数据，仅供测试界面功能。")
    df_source = get_mock_data() # 使用假数据兜底，防止报错

# 数据清洗
target_coins = []
for item in df_source:
    symbol = item.get('symbol', '')
    
    # 筛选我们关注的币
    if symbol in ACTIVE_CAMPAIGNS:
        try:
            price = float(item.get('lastPrice', 0))
            high = float(item.get('highPrice', 0))
            low = float(item.get('lowPrice', 0))
            volume = float(item.get('quoteVolume', 0))
            count = int(item.get('count', 0))
            
            # 避免除以零错误
            if price == 0: continue

            # 计算波动率
            volatility = ((high - low) / price) * 100
            days_left = calculate_days_left(ACTIVE_CAMPAIGNS[symbol])
            
            target_coins.append({
                '代币': symbol,
                '当前价格': price,
                '波动率(%)': volatility,
                '24H成交额(U)': volume / 1000000,
                '活跃人数': count,
                '剩余天数': days_left
            })
        except Exception as e:
            continue

# 如果没有数据
if not target_coins:
    st.error("没有找到匹配的数据。")
    st.stop()

# 转成表格
df = pd.DataFrame(target_coins)

# 找出前三名
top_3 = df.sort_values(by='活跃人数', ascending=False).head(3)

# 界面展示：Top 3 指标卡
c1, c2, c3 = st.columns(3)
if len(top_3) >= 3:
    with c1:
        st.metric("🔥 活跃榜首", top_3.iloc[0]['代币'], f"{top_3.iloc[0]['活跃人数']} 笔")
    with c2:
        st.metric("🥈 第二名", top_3.iloc[1]['代币'], f"{top_3.iloc[1]['活跃人数']} 笔")
    with c3:
        st.metric("🥉 第三名", top_3.iloc[2]['代币'], f"{top_3.iloc[2]['活跃人数']} 笔")

st.divider()

# 界面展示：主表格
st.subheader("📊 4倍交易量活动代币监控表")

# 颜色函数
def highlight_volatility(val):
    if val < 1.0: return 'background-color: #d4edda; color: green; font-weight: bold' # 绿色背景
    if val > 5.0: return 'background-color: #f8d7da; color: red' # 红色背景
    return ''

# 显示表格
st.dataframe(
    df.style.applymap(highlight_volatility, subset=['波动率(%)'])
    .format({"当前价格": "{:.4f}", "波动率(%)": "{:.2f}%", "24H成交额(U)": "{:.2f} M"}),
    use_container_width=True,
    height=400
)

st.caption("提示：演示模式下数据为随机生成。如需真实数据，请在本地电脑运行。")

# 刷新按钮
if st.button('🔄 刷新数据'):
    st.rerun()
