import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import markdown


def ensure_reports_dir():
    os.makedirs("reports", exist_ok=True)


def render_markdown(report_data: dict, md_path: str):
    ensure_reports_dir()

    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=False
    )

    template = env.get_template("daily_report.md.j2")

    today = datetime.now().strftime("%Y-%m-%d")

    markdown_content = template.render(
        date=today,
        report=report_data
    )

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return markdown_content


def build_html(markdown_content: str):
    html_body = markdown.markdown(
        markdown_content,
        extensions=["tables", "fenced_code", "toc"]
    )

    html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{
    font-family: "Microsoft YaHei", "SimHei", "Noto Sans CJK SC", sans-serif;
    line-height: 1.7;
    font-size: 14px;
    color: #222;
    padding: 24px;
}}
h1 {{
    font-size: 26px;
    border-bottom: 2px solid #333;
    padding-bottom: 8px;
}}
h2 {{
    font-size: 21px;
    margin-top: 28px;
    border-left: 4px solid #333;
    padding-left: 10px;
}}
h3 {{
    font-size: 17px;
    margin-top: 20px;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
}}
th, td {{
    border: 1px solid #ddd;
    padding: 8px;
}}
th {{
    background: #f5f5f5;
}}
a {{
    color: #0366d6;
    word-break: break-all;
}}
blockquote {{
    border-left: 4px solid #ddd;
    margin: 12px 0;
    padding: 8px 12px;
    background: #f8f8f8;
}}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""
    return html


def render_pdf(markdown_content: str, pdf_path: str):
    ensure_reports_dir()

    html = build_html(markdown_content)
    html_path = pdf_path.replace(".pdf", ".html")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(pdf_path)
        print(f"PDF 已生成：{pdf_path}")
        return pdf_path

    except Exception as e:
        print("[WARN] PDF 生成失败，已改为生成 HTML 文件。")
        print(f"[WARN] 错误原因：{e}")
        print(f"HTML 文件已生成：{html_path}")
        return html_path
