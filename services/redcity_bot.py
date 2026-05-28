import os
import requests


def send_text_to_redcity(content: str):
    webhook = os.getenv("REDCITY_BOT_WEBHOOK")

    if not webhook:
        raise RuntimeError("缺少 REDCITY_BOT_WEBHOOK 环境变量")

    payload = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }

    resp = requests.post(
        webhook,
        json=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=30
    )

    print("Redcity response status:", resp.status_code)
    print("Redcity response body:", resp.text)

    resp.raise_for_status()
    return resp.text


def split_message(content: str, max_len: int = 3500):
    chunks = []
    current = content

    while len(current) > max_len:
        split_pos = current.rfind("\n", 0, max_len)
        if split_pos == -1:
            split_pos = max_len

        chunks.append(current[:split_pos])
        current = current[split_pos:].lstrip()

    if current:
        chunks.append(current)

    return chunks


def send_long_text_to_redcity(content: str):
    chunks = split_message(content)

    for index, chunk in enumerate(chunks, start=1):
        if len(chunks) > 1:
            chunk = f"【财经日报 {index}/{len(chunks)}】\n\n{chunk}"

        send_text_to_redcity(chunk)
