import aiohttp
import asyncio
import time  # 用于模拟等待
from secrets import resume, job_description, final_email_to

BASE_URL = "http://127.0.0.1:5000"
HEADERS = {"X-From-Extension": "true"}



# 多轮用户指令，可自行添加
user_prompts = [
    "请让语气更正式",
    "再简洁一点",
    "加一句我会 Python 和 SQL",
]

# 用于保存当前内容
current_email_content = ""


async def generate_email(prompt=None):
    global current_email_content

    payload = {
        "resume": resume,
        "job_description": job_description,
    }
    if prompt:
        payload["user_prompt"] = prompt

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/generate_email", headers=HEADERS, json=payload) as response:
            result = await response.json()
            email_text = result.get("final_output") or result.get("generated_email")
            print("\n📧 Generated Email Content:")
            print(email_text)
            current_email_content = email_text  # 更新当前内容


async def revise_email(instruction):
    global current_email_content

    payload = {
        "original_email": current_email_content,
        "instruction": instruction,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/revise_email", headers=HEADERS, json=payload) as response:
            result = await response.json()
            revised = result.get("revised_email")
            print(f"\n🔁 Revised with instruction '{instruction}':")
            print(revised)
            current_email_content = revised  # 更新当前内容


async def send_final_email():
    email_data = {
        "to": final_email_to,
        "subject": "跟进求职邮件",
        "body": current_email_content
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/send-email", headers=HEADERS, json=email_data) as response:
            result = await response.json()
            print("\n🚀 Send Result:")
            print(result)


async def main():
    print("🚦 Initial email generation...")
    await generate_email()

    for idx, prompt in enumerate(user_prompts):
        print(f"\n⏳ Round {idx + 1}: {prompt}")
        await asyncio.sleep(1)
        await revise_email(prompt)

    print("\n✅ Final Confirmation: Sending email...")
    await send_final_email()


if __name__ == "__main__":
    asyncio.run(main())
