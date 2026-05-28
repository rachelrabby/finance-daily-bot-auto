import os
import shutil
from datetime import datetime
from dotenv import load_dotenv

from sources.finance_news import fetch_finance_news
from services.summarizer import summarize_report
from services.renderer import render_markdown, render_pdf
from services.redcity_bot import send_long_text_to_redcity


def get_report_url(html_path: str):
    base_url = os.getenv("REPORT_BASE_URL", "").strip().rstrip("/")

    if not base_url:
        return ""

    filename = os.path.basename(html_path)
    return f"{base_url}/reports/{filename}"


def copy_reports_to_docs(md_path: str, html_path: str, pdf_path: str):
    """
    把生成的日报复制到 docs/reports/，供 GitHub Pages 发布。
    """
    docs_reports_dir = os.path.join("docs", "reports")
    os.makedirs(docs_reports_dir, exist_ok=True)

    copied = []

    for path in [md_path, html_path, pdf_path]:
        if path and os.path.exists(path):
            target = os.path.join(docs_reports_dir, os.path.basename(path))
            shutil.copy2(path, target)
            copied.append(target)

    return copied


def build_short_message(today: str, report_data: dict, md_path: str, html_path: str, pdf_path: str):
    highlights = report_data.get("highlights", [])

    highlight_text = "\n".join(
        [f"{idx}. {item}" for idx, item in enumerate(highlights, start=1)]
    )

    report_url = get_report_url(html_path)

    if report_url:
        link_text = f"""
在线日报：
{report_url}

提示：如果刚收到消息时链接暂时打不开，请等 1-3 分钟后刷新。
"""
    else:
        link_text = """
在线日报链接未配置。
"""

    message = f"""【每日财经日报】{today}

今日重点：
{highlight_text}

覆盖范围：
A股 / 美股 / 港股 / 汇率 / 黄金原油 / 宏观政策 / AI行业
{link_text}
生成文件：
- Markdown：{md_path}
- HTML：{html_path}
- PDF：{pdf_path}

免责声明：本日报仅作信息整理，不构成投资建议。
"""

    return message


def main():
    load_dotenv()

    today = datetime.now().strftime("%Y-%m-%d")

    print("[1/6] 开始抓取财经新闻...")
    news_by_section = fetch_finance_news()

    print("[2/6] 开始调用 DeepSeek 生成摘要...")
    report_data = summarize_report(news_by_section)

    md_path = f"reports/{today}-finance-daily.md"
    pdf_path = f"reports/{today}-finance-daily.pdf"
    html_path = f"reports/{today}-finance-daily.html"

    print("[3/6] 生成 Markdown...")
    markdown_content = render_markdown(report_data, md_path)

    print("[4/6] 生成 HTML / PDF...")
    generated_path = render_pdf(markdown_content, pdf_path)

    if generated_path.endswith(".html"):
        html_path = generated_path

    print("[5/6] 复制日报到 docs/reports，供 GitHub Pages 发布...")
    copied_files = copy_reports_to_docs(md_path, html_path, pdf_path)
    print("已复制文件：", copied_files)

    print("[6/6] 发送群机器人消息...")
    message = build_short_message(today, report_data, md_path, html_path, pdf_path)
    send_long_text_to_redcity(message)

    print("完成。")


if __name__ == "__main__":
    main()
