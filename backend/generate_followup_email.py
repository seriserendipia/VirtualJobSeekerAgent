import os
import re
import json
from dotenv import load_dotenv
from aurite import LLMConfig, AgentConfig
import os
from aurite_service import get_aurite

def load_files(resume_path: str, jd_path: str) -> tuple:
    with open(resume_path, "r", encoding="utf-8") as f:
        resume_content = f.read()
    with open(jd_path, "r", encoding="utf-8") as f:
        jd_content = f.read()
    return resume_content, jd_content

def parse_email_to_json(raw_content: str) -> dict:
    subject_match = re.search(r"Subject:\s*(.*)", raw_content)
    body_match = re.search(r"Body:\s*([\s\S]*)", raw_content)

    subject = subject_match.group(1).strip() if subject_match else ""
    body = body_match.group(1).strip() if body_match else ""

    return {"subject": subject, "body": body}



# 定义 LLM（只需配置）
fast_llm = LLMConfig(
    llm_id="fast_gpt",
    provider="openai",
    model_name="gpt-4o-mini",
    temperature=0.2,
    max_tokens=1024,
    default_system_prompt="You are a helpful assistant."
)

# Step 1: Generate a email using aurite by calling OpenAI LLM
async def generate_email(resume_content: str, jd_content: str) -> dict:
    load_dotenv()
    aurite = get_aurite()
    # Register the LLMConfig first
    await aurite.register_llm_config(fast_llm)
    email_generator_agent = AgentConfig(
        name="Email Generate Agent",
        llm_config_id="fast_gpt",
        description="Send emails using Gmail MCP server via Aurite agent.",
        input_type="text",
        output_type="text",
        system_prompt=f"""
            You are an experienced job application assistant.
            Below is my resume:

            {resume_content}

            Below is the job description:

            {jd_content}

            Please write a professional follow-up email to the recruiter,
            expressing strong interest in this position,
            highlighting why I am a good fit,
            and politely asking for any updates about the application process.

            Output the email with exactly two parts labeled as below:

            Subject: <the email subject line>

            Body:
            <the full email body text>

            Do not add any explanations or extra notes.
        """
    )
    await aurite.register_agent(email_generator_agent)

    result = await aurite.run_agent(agent_name="Email Generate Agent",
                                    user_message="Generate an email based on the provided resume and job description.")

    raw_content = result.primary_text
    email_json = parse_email_to_json(raw_content)
    return email_json
    


if __name__ == "__main__":
    resume_path = os.path.join(os.path.dirname(__file__), "..", "samples", "user_resume_sample.txt")
    jd_path = os.path.join(os.path.dirname(__file__), "..", "samples", "jobdescription_sample.txt")

    resume_content, jd_content = load_files(resume_path, jd_path)

    email_dict = generate_followup_email(resume_content, jd_content)

    # 输出漂亮的 JSON 字符串
    print(json.dumps(email_dict, indent=4, ensure_ascii=False))
