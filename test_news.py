from sources.finance_news import fetch_finance_news

data = fetch_finance_news()

print("\n========== 抓取结果 ==========")

for section_key, items in data.items():
    print(f"\n【{section_key}】共 {len(items)} 条")

    for idx, item in enumerate(items[:10], start=1):
        print(f"{idx}. {item['title']}")
        print(f"   来源：{item.get('source', '')}")
        print(f"   链接：{item.get('url', '')}")
