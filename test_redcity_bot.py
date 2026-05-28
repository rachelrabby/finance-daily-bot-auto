import os
import requests

WEBHOOK = os.getenv("REDCITY_BOT_WEBHOOK")

if not WEBHOOK:
    raise RuntimeError("请先设置 REDCITY_BOT_WEBHOOK 环境变量")

payload = {
    "msgtype": "text",
    "text": {
        "content": "测试消息：每日财经日报机器人已接入，后续将每天早上 8:30 自动发送。"
    }
}

try:
    resp = requests.post(
        WEBHOOK,
        json=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=30
    )

    print("status:", resp.status_code)
    print("body:", resp.text)

    resp.raise_for_status()

    print("发送完成，请查看群里是否收到测试消息。")

except Exception as e:
    print("发送失败：", repr(e))
