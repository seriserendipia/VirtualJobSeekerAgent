print('HELLO!')

import aiohttp
import asyncio
import time
import os
# 现在 secrets.py 已经不再需要了，因为所有信息都从文件中读取


BASE_URL = "http://127.0.0.1:5000"
HEADERS = {"X-From-Extension": "true"}

# 定义文件路径
RESUME_FILE = os.path.join("..", "samples", "user_resume_sample.txt")
JD_FILE = os.path.join("..", "samples", "jobdescription_sample.txt")
FINAL_EMAIL_FILE = os.path.join("..", "samples", "final_mail_to.txt")

# 多轮用户指令，可自行添加
user_prompts = [
    "请让语气更正式",
    "再简洁一点",
    "加一句我会 Python 和 SQL",
]

# 用于保存当前内容
current_email_content = ""

# 从文件中读取内容
def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()  # 使用 .strip() 移除首尾空白符和换行符
    except FileNotFoundError:
        print(f"❌ Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        print(f"❌ Error reading file '{file_path}': {e}")
        return None

async def generate_email(prompt=None):
    global current_email_content

    # 从文件中加载简历和 JD
    resume = read_file_content(RESUME_FILE)
    job_description = read_file_content(JD_FILE)

    if not resume or not job_description:
        print("Aborting email generation due to missing file content.")
        return

    payload = {
        "resume": resume,
        "job_description": job_description,
    }
    if prompt:
        payload["user_prompt"] = prompt

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{BASE_URL}/generate_email", headers=HEADERS, json=payload, timeout=10) as response:
                result = await response.json()
                email_text = result.get("final_output") or result.get("generated_email")
                print("\n📧 Generated Email Content:")
                print(email_text)
                current_email_content = email_text
        except aiohttp.ClientConnectorError as e:
            print(f"❌ Connection Error: Could not connect to the server at {BASE_URL}. Please make sure the server is running.")
            print(f"Error details: {e}")
        except asyncio.TimeoutError:
            print(f"❌ Timeout Error: The server at {BASE_URL} took too long to respond.")
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")

async def revise_email(instruction):
    global current_email_content

    payload = {
        "original_email": current_email_content,
        "instruction": instruction,
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{BASE_URL}/revise_email", headers=HEADERS, json=payload, timeout=10) as response:
                result = await response.json()
                revised = result.get("revised_email")
                print(f"\n🔁 Revised with instruction '{instruction}':")
                print(revised)
                current_email_content = revised
        except aiohttp.ClientConnectorError as e:
            print(f"❌ Connection Error: Could not connect to the server at {BASE_URL}. Please make sure the server is running.")
            print(f"Error details: {e}")
        except asyncio.TimeoutError:
            print(f"❌ Timeout Error: The server at {BASE_URL} took too long to respond.")
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")

async def send_final_email():
    # 从文件中加载收件人邮箱
    final_email_to = read_file_content(FINAL_EMAIL_FILE)
    
    if not final_email_to:
        print("Aborting email sending due to missing recipient email.")
        return

    email_data = {
        "to": final_email_to,
        "subject": "跟进求职邮件",
        "body": current_email_content
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{BASE_URL}/send-email", headers=HEADERS, json=email_data, timeout=10) as response:
                result = await response.json()
                print("\n🚀 Send Result:")
                print(result)
        except aiohttp.ClientConnectorError as e:
            print(f"❌ Connection Error: Could not connect to the server at {BASE_URL}. Please make sure the server is running.")
            print(f"Error details: {e}")
        except asyncio.TimeoutError:
            print(f"❌ Timeout Error: The server at {BASE_URL} took too long to respond.")
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")

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