import os
from datetime import datetime
from dotenv import load_dotenv

from sources.finance_news import fetch_finance_news
from services.summarizer import summarize_report
from services.renderer import render_markdown, render_pdf
from services.redcity_bot import send_long_text_to_redcity


def build_short_message(today: str, report_data: dict, md_path: str, pdf_path: str):
    highlights = report_data.get("highlights", [])

    highlight_text = "\n".join(
        [f"{idx}. {item}" for idx, item in enumerate(highlights, start=1)]
    )

    message = f"""【每日财经日报】{today}

今日重点：
{highlight_text}

覆盖范围：
A股 / 美股 / 港股 / 汇率 / 黄金原油 / 宏观政策 / AI行业

本地生成文件：
- Markdown：{md_path}
- PDF：{pdf_path}

免责声明：本日报仅作信息整理，不构成投资建议。
"""

    return message


def main():
    load_dotenv()

    today = datetime.now().strftime("%Y-%m-%d")

    print("[1/5] 开始抓取财经新闻...")
    news_by_section = fetch_finance_news()

    print("[2/5] 开始调用 DeepSeek 生成摘要...")
    report_data = summarize_report(news_by_section)

    md_path = f"reports/{today}-finance-daily.md"
    pdf_path = f"reports/{today}-finance-daily.pdf"

    print("[3/5] 生成 Markdown...")
    markdown_content = render_markdown(report_data, md_path)

    print("[4/5] 生成 PDF...")
    generated_pdf_path = render_pdf(markdown_content, pdf_path)

    print("[5/5] 发送群机器人消息...")
    message = build_short_message(today, report_data, md_path, generated_pdf_path)
    send_long_text_to_redcity(message)

    print("完成。")


if __name__ == "__main__":
    main()
