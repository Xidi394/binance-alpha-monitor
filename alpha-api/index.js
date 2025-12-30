const axios = require('axios');

export default async function handler(req, res) {
    // 允许跨域
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS');
    res.setHeader('Cache-Control', 's-maxage=15, stale-while-revalidate');

    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }

    try {
        // 🎯 调用币安官方 Alpha 交易对接口 (参考官方文档)
        // bapi 通常用于币安前端，包含了 Alpha 板块的专属数据
        const targetUrl = 'https://www.binance.com/bapi/defi/v1/public/alpha-trade/ticker';

        const response = await axios.get(targetUrl, {
            headers: {
                // 伪装成浏览器访问 www.binance.com
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.binance.com/en/dotslot', // Alpha/DotSlot 相关页面
                'Host': 'www.binance.com'
            },
            timeout: 8000
        });

        // 🔍 解析官方数据结构
        // 官方结构通常是: { code: "000000", data: [ ...list ] }
        const rawData = response.data;

        if (rawData.code !== "000000" || !Array.isArray(rawData.data)) {
            throw new Error("Invalid API Response: " + JSON.stringify(rawData));
        }

        const alphaCoins = rawData.data
            .map(item => ({
                symbol: item.symbol,
                // 移除 "USDT" 后缀以显示基础币名
                baseAsset: item.symbol.replace(/USDT$/, ''),
                lastPrice: item.lastPrice,
                priceChangePercent: (parseFloat(item.priceChangePercent) * 100).toFixed(2), // 转换为百分比
                quoteVolume: parseFloat(item.quoteVolume), // 成交额
                // Alpha 接口通常不直接返回 bps，我们用高低价差或买卖价差估算，或者直接忽略
                bps: 0 
            }))
            // 按成交额 (quoteVolume) 从大到小排序，确保抓取到“4倍交易量”的热门币
            .sort((a, b) => b.quoteVolume - a.quoteVolume);

        // 截取前 15 名 (最活跃的 Alpha 代币)
        const top15 = alphaCoins.slice(0, 15);

        res.status(200).json(top15);

    } catch (error) {
        console.error("Alpha API Error:", error.message);
        res.status(500).json({ 
            error: "Fetch Failed", 
            msg: error.message,
            source: "Official Binance Alpha API"
        });
    }
}