import os
import json
from datetime import datetime
from openai import OpenAI
from config import SECTIONS, DEEPSEEK_MODEL


def strip_json_markdown(text: str) -> str:
    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    if text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


def build_prompt(news_by_section: dict) -> str:
    section_texts = []

    for section_key, section_config in SECTIONS.items():
        section_name = section_config["name"]
        items = news_by_section.get(section_key, [])

        lines = [f"## {section_name}"]

        if not items:
            lines.append("暂无新闻。")

        for idx, item in enumerate(items, start=1):
            lines.append(
                f"{idx}. 标题：{item['title']}\n"
                f"   来源：{item.get('source', '')}\n"
                f"   时间：{item.get('published', '')}\n"
                f"   链接：{item['url']}\n"
                f"   原摘要：{item.get('raw_summary', '')}"
            )

        section_texts.append("\n".join(lines))

    all_news_text = "\n\n".join(section_texts)

    prompt = f"""
你是一名严谨的中文财经资讯编辑。请根据下面的公开新闻标题、来源和摘要，生成一份中文财经日报。

要求：
1. 不要编造新闻中没有的信息。
2. 不要编造具体指数点位、涨跌幅、价格等数字。
3. 如果信息不足，请写“公开信息不足，需继续关注”。
4. 语气简洁、客观。
5. 不构成投资建议。
6. 输出必须是 JSON，不要输出 Markdown，不要输出解释文字。

JSON 结构必须如下：

{{
  "highlights": [
    "今日重点1",
    "今日重点2",
    "今日重点3"
  ],
  "market_overview": {{
    "a_share": "A股概览",
    "us_stock": "美股概览",
    "hk_stock": "港股概览",
    "fx": "汇率外汇概览",
    "commodity": "黄金原油概览",
    "macro": "宏观政策概览",
    "ai": "AI行业概览"
  }},
  "sections": {{
    "a_share": [
      {{
        "title": "新闻标题",
        "summary": "2句话以内摘要",
        "source": "来源",
        "url": "链接"
      }}
    ],
    "us_stock": [],
    "hk_stock": [],
    "fx": [],
    "commodity": [],
    "macro": [],
    "ai": []
  }},
  "watchlist": "今日值得继续关注的事项，3到5条。",
  "risk_note": "风险提示，提醒本日报仅供信息参考，不构成投资建议。"
}}

下面是新闻素材：

{all_news_text}
"""

    return prompt


def fallback_summary(news_by_section: dict):
    sections = {}

    for section_key, items in news_by_section.items():
        sections[section_key] = []

        for item in items[:5]:
            sections[section_key].append({
                "title": item["title"],
                "summary": item.get("raw_summary", "暂无摘要。"),
                "source": item.get("source", ""),
                "url": item["url"]
            })

    return {
        "highlights": [
            "今日财经新闻已自动抓取，AI 摘要暂不可用。",
            "请重点关注 A股、美股、港股、汇率、黄金原油、宏观政策和 AI 行业动态。",
            "本日报仅作信息整理，不构成投资建议。"
        ],
        "market_overview": {
            "a_share": "已抓取 A股相关新闻。",
            "us_stock": "已抓取 美股相关新闻。",
            "hk_stock": "已抓取 港股相关新闻。",
            "fx": "已抓取 汇率 / 外汇相关新闻。",
            "commodity": "已抓取 黄金 / 原油相关新闻。",
            "macro": "已抓取 宏观政策相关新闻。",
            "ai": "已抓取 AI 行业相关新闻。"
        },
        "sections": sections,
        "watchlist": "关注主要市场走势、宏观政策变化、汇率波动、商品价格变化及 AI 行业动态。",
        "risk_note": "本日报仅根据公开信息自动整理，不构成任何投资建议。"
    }


def summarize_report(news_by_section: dict):
    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        print("[WARN] 未设置 DEEPSEEK_API_KEY，使用普通摘要。")
        return fallback_summary(news_by_section)

    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    prompt = build_prompt(news_by_section)

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是专业财经资讯编辑，擅长把公开财经新闻整理为简洁、客观的日报。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content
        content = strip_json_markdown(content)

        data = json.loads(content)

        return data

    except Exception as e:
        print(f"[WARN] DeepSeek 总结失败，使用普通摘要。错误：{e}")
        return fallback_summary(news_by_section)
