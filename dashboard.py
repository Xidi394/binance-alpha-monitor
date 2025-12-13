import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import random
import time

# --- 页面配置 ---
st.set_page_config(page_title="Alpha 监控台 (专业版)", layout="wide")

# --- 1. 静态数据库 (你要求的历史与配置) ---
# 正在进行的活动
ACTIVE_CAMPAIGNS = {
    'LISTAUSDT': {'end': '2025-12-30', 'type': 'Megadrop'},
    'BBUSDT':    {'end': '2025-06-20', 'type': 'Megadrop'},
    'REZUSDT':   {'end': '2025-05-15', 'type': 'Launchpool'},
    'NOTUSDT':   {'end': '2025-04-01', 'type': 'Launchpool'},
}

# 历史空投战绩 (用于参考)
HISTORY_AIRDROPS = [
    {'项目': 'ENA', '类型': 'Launchpool', '平均日收益': '1.5%', '最高倍数': '12x'},
    {'项目': 'ETHFI', '类型': 'Launchpool', '平均日收益': '1.2%', '最高倍数': '8x'},
]

# --- 2. 核心数据获取函数 ---

def get_real_market_data():
    """获取真实行情 + K线数据(用于计算4倍量)"""
    market_data = []
    
    # 1. 先拿所有币的24小时数据
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        resp = requests.get(url, timeout=3)
        if resp.status_code != 200: return None # 被封或报错
        all_tickers = resp.json()
    except:
        return None

    # 2. 筛选我们要的币，并深入计算
    for item in all_tickers:
        symbol = item['symbol']
        if symbol in ACTIVE_CAMPAIGNS:
            try:
                # 尝试获取过去7天数据来计算平均量 (为了"4倍量"检测)
                # 注意：如果请求太快，币安会限制，这里做简单处理
                kline_url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=7"
                kline_resp = requests.get(kline_url, timeout=2)
                klines = kline_resp.json()
                
                # 计算过去7天平均成交额
                total_vol = sum([float(k[7]) for k in klines]) # k[7]是成交额
                avg_vol = total_vol / len(klines)
                
                current_vol = float(item['quoteVolume'])
                vol_ratio = current_vol / avg_vol if avg_vol > 0 else 0
                
                market_data.append({
                    'symbol': symbol,
                    'price': float(item['lastPrice']),
                    'volatility': (float(item['highPrice']) - float(item['lowPrice'])) / float(item['lastPrice']) * 100,
                    'volume': current_vol,
                    'volume_ratio': vol_ratio, # 量比 (当前量 / 7日平均量)
                    'count': int(item['count'])
                })
            except:
                continue
                
    return market_data

def get_mock_data_v3():
    """更逼真的演示数据 (带量比)"""
    data = []
    for symbol in ACTIVE_CAMPAIGNS:
        base_vol = random.uniform(5000000, 50000000)
        # 模拟随机出现一个"爆发"的币
        ratio = random.choice([0.8, 1.2, 1.1, 4.5]) 
        
        data.append({
            'symbol': symbol,
            'price': random.uniform(0.5, 5.0),
            'volatility': random.uniform(0.5, 6.0),
            'volume': base_vol,
            'volume_ratio': ratio,
            'count': random.randint(10000, 50000)
        })
    return data

# --- 3. 界面逻辑 ---

st.title("🚀 Alpha 监控台 v3.0 (本地旗舰版)")

# 尝试连接真实网络
with st.spinner('正在连接币安...'):
    real_data = get_real_market_data()

if real_data:
    st.success("✅ 实时数据连接成功！(当前显示的为真实币安数据)")
    df_data = real_data
else:
    st.error("⚠️ 警告：无法连接币安 (IP可能被限制)。已切换至【演示模式】。")
    st.info("💡 提示：要在本地看到真实数据，请务必修复本地 Python 环境。")
    df_data = get_mock_data_v3()

# --- 数据展示区 ---

# 处理数据为 DataFrame
df = pd.DataFrame(df_data)

# 1. 顶部：今日参与最多 Top 3
if not df.empty:
    top3 = df.sort_values('count', ascending=False).head(3)
    c1, c2, c3 = st.columns(3)
    c1.metric("🔥 人气王", top3.iloc[0]['symbol'], f"{top3.iloc[0]['count']} 人")
    if len(top3)>1: c2.metric("🥈 第二名", top3.iloc[1]['symbol'], f"{top3.iloc[1]['count']} 人")
    if len(top3)>2: c3.metric("🥉 第三名", top3.iloc[2]['symbol'], f"{top3.iloc[2]['count']} 人")

st.divider()

# 2. 核心表格：4倍量监控
st.subheader("📊 异常放量监控 (寻找 >4 倍量的稳定币)")

# 样式函数
def highlight_row(row):
    # 如果量比 > 3.5 (接近4倍)，标黄背景
    if row['量比(倍数)'] > 3.5:
        return ['background-color: #ffffcc'] * len(row)
    return [''] * len(row)

if not df.empty:
    # 计算展示用的列
    display_df = pd.DataFrame()
    display_df['代币'] = df['symbol']
    display_df['当前价格'] = df['price']
    display_df['波动率'] = df['volatility'].map('{:.2f}%'.format)
    display_df['24H成交(U)'] = (df['volume'] / 1000000).map('{:.2f} M'.format)
    display_df['量比(倍数)'] = df['volume_ratio'] # 核心指标
    display_df['状态'] = display_df['量比(倍数)'].apply(lambda x: '🚨 爆量' if x > 3.8 else '平稳')
    
    # 结合配置表算剩余天数
    display_df['剩余天数'] = display_df['代币'].apply(lambda x: 
        (datetime.strptime(ACTIVE_CAMPAIGNS[x]['end'], "%Y-%m-%d") - datetime.now()).days 
        if x in ACTIVE_CAMPAIGNS else 0
    )

    st.dataframe(
        display_df.style.apply(highlight_row, axis=1),
        use_container_width=True
    )

# 3. 历史空投库
with st.expander("📚 查看历史空投收益 (参考库)"):
    st.table(pd.DataFrame(HISTORY_AIRDROPS))

# 4. 新闻模拟区 (真实抓取需要付费API，这里用公告链接替代)
st.info("📢 官方公告速递: [点击查看币安最新 Launchpool 公告](https://www.binance.com/en/support/announcement/launchpool-updates)")

if st.button('刷新数据'):
    st.rerun()
