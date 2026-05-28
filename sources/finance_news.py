import re
import html
import time
import requests
import feedparser
from urllib.parse import quote_plus
from config import NEWS_PER_SECTION


HEADERS = {
    "User-Agent": "Mozilla/5.0 FinanceDailyBot/1.0",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
}


MAX_RSS_ENTRIES_PER_SOURCE = 80


RSS_SOURCES = [
    {
        "name": "新浪财经滚动",
        "url": "https://rss.sina.com.cn/roll/finance/hot_roll.xml"
    },
    {
        "name": "新浪股票滚动",
        "url": "https://rss.sina.com.cn/roll/stock/hot_roll.xml"
    },
    {
        "name": "FT中文网",
        "url": "https://www.ftchinese.com/rss/news"
    },
    {
        "name": "BBC中文商业",
        "url": "https://feeds.bbci.co.uk/zhongwen/simp/business/rss.xml"
    },
    {
        "name": "36氪",
        "url": "https://36kr.com/feed"
    },
    {
        "name": "CNBC Markets",
        "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"
    },
    {
        "name": "CNBC Business",
        "url": "https://www.cnbc.com/id/10001147/device/rss/rss.html"
    },
    {
        "name": "Yahoo Finance",
        "url": "https://finance.yahoo.com/news/rssindex"
    },
]


SECTION_KEYWORDS = {
    "a_share": {
        "name": "A股",
        "keywords": [
            "a股", "上证", "沪指", "深证", "创业板", "科创板",
            "证监会", "沪深", "北交所", "中国股市", "a-share",
            "沪深两市", "北向资金", "a股市场"
        ]
    },
    "us_stock": {
        "name": "美股",
        "keywords": [
            "美股", "纳斯达克", "道琼斯", "标普", "s&p", "nasdaq",
            "dow", "中概股", "英伟达", "苹果", "微软", "特斯拉",
            "nvidia", "apple", "microsoft", "tesla", "wall street"
        ]
    },
    "hk_stock": {
        "name": "港股",
        "keywords": [
            "港股", "恒生", "恒指", "恒生科技", "香港股市",
            "h股", "南向资金", "港交所", "香港交易所"
        ]
    },
    "fx": {
        "name": "汇率 / 外汇",
        "keywords": [
            "汇率", "外汇", "人民币", "美元指数", "离岸人民币",
            "在岸人民币", "日元", "欧元", "英镑", "exchange rate",
            "forex", "currency", "美元", "yen", "euro", "usd/cny",
            "usdcny", "cny", "dollar index", "fed", "美联储"
        ]
    },
    "commodity": {
        "name": "黄金 / 原油",
        "keywords": [
            "黄金", "金价", "原油", "油价", "布伦特", "wti",
            "大宗商品", "铜", "白银", "天然气", "gold", "oil",
            "brent", "commodity", "crude"
        ]
    },
    "macro": {
        "name": "宏观政策",
        "keywords": [
            "宏观", "央行", "财政", "货币政策", "降息", "降准",
            "cpi", "ppi", "pmi", "gdp", "经济数据", "金融监管",
            "国务院", "发改委", "财政部", "通胀", "利率", "就业"
        ]
    },
    "ai": {
        "name": "AI行业",
        "keywords": [
            "ai", "人工智能", "大模型", "算力", "芯片", "半导体",
            "英伟达", "openai", "deepseek", "机器人", "智能驾驶",
            "数据中心", "gpu", "chatgpt", "anthropic", "llm"
        ]
    }
}


QUERY_PACKS = {
    "a_share": [
        "A股 上证指数 沪深股市 财经",
        "A股 市场 今日 沪深两市",
        "中国股市 上证指数 深证成指 创业板指",
        "北向资金 A股 证监会",
        "A股 公司 财报 业绩 证券"
    ],
    "us_stock": [
        "美股 纳斯达克 道琼斯 标普500 财经",
        "美股 科技股 中概股",
        "Nasdaq Dow S&P 500 markets",
        "Nvidia Apple Microsoft Tesla stock",
        "Wall Street stocks market"
    ],
    "hk_stock": [
        "港股 恒生指数 恒生科技指数 财经",
        "香港股市 港股通 南向资金",
        "恒生指数 港股 最新",
        "港股 科技股 互联网",
        "香港交易所 港股 财经"
    ],
    "fx": [
        "人民币 汇率 美元指数 外汇 财经",
        "离岸人民币 在岸人民币 美元 汇率",
        "美元指数 外汇 市场",
        "日元 欧元 英镑 汇率",
        "forex dollar yuan yen euro market",
        "美元兑人民币 USD CNY exchange rate",
        "人民币 中间价 外汇市场",
        "美联储 美元 汇率 人民币"
    ],
    "commodity": [
        "黄金 原油 大宗商品 财经",
        "国际油价 布伦特 WTI 原油 黄金",
        "现货黄金 原油 期货 大宗商品",
        "gold oil brent wti commodity",
        "黄金价格 原油价格 今日"
    ],
    "macro": [
        "中国 宏观经济 政策 央行 财政 金融",
        "央行 货币政策 财政政策 宏观经济",
        "中国经济 数据 CPI PPI PMI GDP",
        "国务院 发改委 财政部 金融监管",
        "全球经济 通胀 利率 美联储"
    ],
    "ai": [
        "人工智能 AI 大模型 芯片 算力 财经",
        "AI 行业 大模型 算力 芯片 科技",
        "国产大模型 人工智能 半导体 算力",
        "OpenAI DeepSeek 大模型 AI",
        "Nvidia GPU AI data center"
    ],
}


FX_GOOGLE_QUERIES = [
    "人民币 汇率 美元指数 外汇",
    "离岸人民币 在岸人民币 美元 汇率",
    "美元指数 日元 欧元 英镑 汇率",
    "美元兑人民币 USD CNY exchange rate",
    "forex dollar yuan yen euro market",
    "美联储 美元 汇率 人民币",
    "人民币 中间价 外汇市场",
    "外汇市场 美元指数 今日"
]


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = html.unescape(str(text))
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_title(title: str) -> str:
    return " ".join(clean_text(title).lower().split())


def build_bing_news_rss_url(query: str) -> str:
    encoded = quote_plus(query)
    return (
        "https://www.bing.com/news/search"
        f"?q={encoded}&format=rss&mkt=zh-CN&setlang=zh-Hans"
    )


def build_google_news_rss_url(query: str) -> str:
    encoded = quote_plus(query)
    return (
        "https://news.google.com/rss/search"
        f"?q={encoded}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    )


def parse_feed(url: str, source_name: str, max_entries: int = MAX_RSS_ENTRIES_PER_SOURCE):
    items = []

    try:
        parsed = feedparser.parse(
            url,
            request_headers=HEADERS
        )

        if getattr(parsed, "bozo", 0):
            if not source_name.startswith("Bing新闻"):
                print(f"[WARN] {source_name} RSS 可能格式不标准，但继续尝试解析。")

        entries = getattr(parsed, "entries", [])

        if not entries:
            if not source_name.startswith("Bing新闻"):
                print(f"[WARN] {source_name} 没有解析到新闻：{url}")
            return []

        for entry in entries[:max_entries]:
            title = clean_text(getattr(entry, "title", ""))
            link = clean_text(getattr(entry, "link", ""))
            published = clean_text(
                getattr(entry, "published", "")
                or getattr(entry, "updated", "")
            )
            summary = clean_text(
                getattr(entry, "summary", "")
                or getattr(entry, "description", "")
            )

            if not title or not link:
                continue

            items.append({
                "title": title,
                "url": link,
                "published": published,
                "source": source_name,
                "raw_summary": summary
            })

        print(f"[INFO] {source_name} 抓到 {len(items)} 条。")
        return items

    except Exception as e:
        print(f"[WARN] {source_name} 抓取失败：{e}")
        return []


def classify_item(item: dict):
    text = (
        item.get("title", "") + " " +
        item.get("raw_summary", "") + " " +
        item.get("source", "")
    ).lower()

    matched_sections = []

    for section_key, section_info in SECTION_KEYWORDS.items():
        for keyword in section_info["keywords"]:
            if keyword.lower() in text:
                matched_sections.append(section_key)
                break

    return matched_sections


def dedupe_items(items: list):
    seen = set()
    results = []

    for item in items:
        title_key = normalize_title(item.get("title", ""))
        url_key = item.get("url", "")

        if not title_key or not url_key:
            continue

        key = title_key

        if key in seen:
            continue

        seen.add(key)
        results.append(item)

    return results


def fetch_all_rss_news():
    all_items = []

    for source in RSS_SOURCES:
        source_name = source["name"]
        url = source["url"]

        items = parse_feed(url, source_name)
        all_items.extend(items)

        time.sleep(0.4)

    return dedupe_items(all_items)


def fetch_gdelt_for_section(section_key: str):
    section_name = SECTION_KEYWORDS[section_key]["name"]
    queries = QUERY_PACKS.get(section_key, [])

    all_items = []

    for query in queries:
        simple_query = re.sub(r"site:[^\s]+", "", query).strip()

        if not simple_query:
            continue

        params = {
            "query": simple_query,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": 30,
            "sort": "HybridRel",
            "timespan": "7d",
        }

        url = "https://api.gdeltproject.org/api/v2/doc/doc"

        try:
            resp = requests.get(
                url,
                headers=HEADERS,
                params=params,
                timeout=20
            )

            resp.raise_for_status()
            data = resp.json()

            articles = data.get("articles", [])

            for article in articles:
                title = clean_text(article.get("title", ""))
                link = clean_text(article.get("url", ""))
                source = clean_text(
                    article.get("sourceCommonName", "")
                    or article.get("domain", "")
                    or "GDELT"
                )
                published = clean_text(article.get("seendate", ""))

                if not title or not link:
                    continue

                all_items.append({
                    "title": title,
                    "url": link,
                    "published": published,
                    "source": f"GDELT-{source}",
                    "raw_summary": title,
                    "section_key": section_key,
                    "section_name": section_name,
                })

            print(f"[INFO] GDELT-{section_name}-{simple_query[:12]} 抓到 {len(articles)} 条。")
            time.sleep(0.4)

        except Exception as e:
            print(f"[WARN] GDELT-{section_name} 抓取失败：{e}")

    return dedupe_items(all_items)


def fetch_google_news_for_fx():
    section_key = "fx"
    section_name = SECTION_KEYWORDS[section_key]["name"]

    all_items = []

    for query in FX_GOOGLE_QUERIES:
        url = build_google_news_rss_url(query)
        source_name = f"Google新闻-汇率-{query[:12]}"

        items = parse_feed(
            url=url,
            source_name=source_name,
            max_entries=30
        )

        for item in items:
            new_item = item.copy()
            new_item["section_key"] = section_key
            new_item["section_name"] = section_name
            all_items.append(new_item)

        time.sleep(0.4)

    return dedupe_items(all_items)


def fetch_fx_market_snapshot():
    section_key = "fx"
    section_name = SECTION_KEYWORDS[section_key]["name"]

    url = "https://api.frankfurter.app/latest?from=USD&to=CNY,EUR,JPY,GBP,HKD"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        rates = data.get("rates", {})
        date = data.get("date", "")

        if not rates:
            return []

        parts = []

        for currency in ["CNY", "EUR", "JPY", "GBP", "HKD"]:
            if currency in rates:
                parts.append(f"USD/{currency}：{rates[currency]}")

        if not parts:
            return []

        summary = "；".join(parts)

        return [
            {
                "title": f"主要汇率参考数据：{summary}",
                "url": url,
                "published": date,
                "source": "Frankfurter 汇率数据",
                "raw_summary": (
                    f"截至 {date}，主要汇率参考数据为：{summary}。"
                    "该数据仅作市场观察参考，不构成交易建议。"
                ),
                "section_key": section_key,
                "section_name": section_name,
            }
        ]

    except Exception as e:
        print(f"[WARN] 外汇市场数据抓取失败：{e}")
        return []


def fetch_bing_for_section(section_key: str):
    section_name = SECTION_KEYWORDS[section_key]["name"]
    queries = QUERY_PACKS.get(section_key, [])

    all_items = []

    for query in queries:
        url = build_bing_news_rss_url(query)
        source_name = f"Bing新闻-{section_name}-{query[:12]}"

        items = parse_feed(
            url=url,
            source_name=source_name,
            max_entries=30
        )

        all_items.extend(items)
        time.sleep(0.4)

    return dedupe_items(all_items)


def fetch_finance_news():
    result = {
        section_key: []
        for section_key in SECTION_KEYWORDS.keys()
    }

    print("[INFO] 开始抓取公共 RSS 新闻源...")
    all_items = fetch_all_rss_news()

    print(f"[INFO] 公共 RSS 合计抓到 {len(all_items)} 条，开始分类...")

    for item in all_items:
        matched_sections = classify_item(item)

        for section_key in matched_sections:
            if len(result[section_key]) < NEWS_PER_SECTION:
                new_item = item.copy()
                new_item["section_key"] = section_key
                new_item["section_name"] = SECTION_KEYWORDS[section_key]["name"]
                result[section_key].append(new_item)

    print("[INFO] 使用 GDELT 为不足栏目补充新闻...")

    for section_key in result.keys():
        section_name = SECTION_KEYWORDS[section_key]["name"]

        if len(result[section_key]) >= NEWS_PER_SECTION:
            print(f"[INFO] {section_name} 已有 {len(result[section_key])} 条，无需补充。")
            continue

        gdelt_items = fetch_gdelt_for_section(section_key)

        for item in gdelt_items:
            if len(result[section_key]) >= NEWS_PER_SECTION:
                break

            new_item = item.copy()
            new_item["section_key"] = section_key
            new_item["section_name"] = section_name
            result[section_key].append(new_item)

        time.sleep(0.4)

    print("[INFO] 对外汇/汇率栏目使用 Google News RSS 专项补充...")

    if len(result["fx"]) < NEWS_PER_SECTION:
        google_fx_items = fetch_google_news_for_fx()

        for item in google_fx_items:
            if len(result["fx"]) >= NEWS_PER_SECTION:
                break

            result["fx"].append(item)

        time.sleep(0.4)

    if len(result["fx"]) < NEWS_PER_SECTION:
        fx_snapshot_items = fetch_fx_market_snapshot()

        for item in fx_snapshot_items:
            if len(result["fx"]) >= NEWS_PER_SECTION:
                break

            result["fx"].append(item)

    print("[INFO] 对仍不足的栏目尝试 Bing News RSS 兜底...")

    for section_key in result.keys():
        section_name = SECTION_KEYWORDS[section_key]["name"]

        if len(result[section_key]) >= NEWS_PER_SECTION:
            continue

        try:
            bing_items = fetch_bing_for_section(section_key)
        except Exception as e:
            print(f"[WARN] Bing-{section_name} 兜底失败，跳过：{e}")
            bing_items = []

        for item in bing_items:
            if len(result[section_key]) >= NEWS_PER_SECTION:
                break

            new_item = item.copy()
            new_item["section_key"] = section_key
            new_item["section_name"] = section_name
            result[section_key].append(new_item)

        time.sleep(0.4)

    for section_key in result:
        result[section_key] = dedupe_items(result[section_key])[:NEWS_PER_SECTION]

    print("\n========== 新闻抓取统计 ==========")

    total = 0

    for section_key, items in result.items():
        section_name = SECTION_KEYWORDS[section_key]["name"]
        count = len(items)
        total += count

        print(f"[INFO] {section_name}：{count} 条")

        for idx, item in enumerate(items[:3], start=1):
            print(f"  {idx}. {item.get('title', '')}")

    print(f"[INFO] 全部栏目合计：{total} 条")
    print("=================================\n")

    return result
