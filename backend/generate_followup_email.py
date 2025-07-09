import os
from openai import OpenAI
from dotenv import load_dotenv


def load_files(resume_path: str, jd_path: str) -> tuple:
    """
    读取简历和 JD 文件内容，返回内容元组 (resume_content, jd_content)
    """
    with open(resume_path, "r", encoding="utf-8") as f:
        resume_content = f.read()

    with open(jd_path, "r", encoding="utf-8") as f:
        jd_content = f.read()

    return resume_content, jd_content


def generate_followup_email(resume_content: str, jd_content: str) -> str:
    """
    调用 GPT-4o 根据简历内容和 JD 内容生成跟进邮件
    """
    # 加载 .env
    load_dotenv()

    # 初始化 OpenAI 客户端
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # 拼接 prompt
    prompt = f"""
You are an experienced job application assistant.
Below is my resume:

{resume_content}

Below is the job description:

{jd_content}

Please write a professional follow-up email to the recruiter,
expressing strong interest in this position,
highlighting why I am a good fit,
and politely asking for any updates about the application process.
"""

    # 调用 GPT-4o
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    # 传入你的文件路径
    resume_path = r"F:\USC\AI Agent\resume.txt"
    jd_path = r"F:\USC\AI Agent\job_description.txt"

    # 调用封装好的文件读取函数
    resume_content, jd_content = load_files(resume_path, jd_path)

    # 调用封装好的 GPT 生成函数
    result = generate_followup_email(resume_content, jd_content)

    print("\n Follow-up Email Draft:\n")
    print(result)
