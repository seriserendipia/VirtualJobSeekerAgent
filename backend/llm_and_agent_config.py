from aurite import LLMConfig, AgentConfig

followup_email_schema = {
    "type": "object",
    "properties": {
        "subject": {"type": "string", "description": "The subject line of the follow-up email"},
        "body": {"type": "string", "description": "The body text of the follow-up email"}
    },
    "required": ["subject", "body"]
}

# 定义 LLM（只需配置，不需要调用 register_llm）
fast_llm = LLMConfig(
    llm_id="fast_gpt",
    provider="openai",
    model_name="gpt-4o-mini",
    temperature=0.2,
    max_tokens=1024,
    default_system_prompt="You are a helpful assistant."
)

# 定义 Follow-up 邮件 Agent
followup_email_agent = AgentConfig(
    name="Followup Email Generator",
    llm_config_id="fast_gpt",
    description="Generate a professional follow-up email based on resume and job description.",
    input_type="text",
    output_type="structured",
    config_validation_schema=followup_email_schema,
    system_prompt="""
You are an experienced job application assistant.

You will be given a resume and a job description.

Write a professional follow-up email to the recruiter:
- Express strong interest in the position
- Highlight why the applicant is a great fit
- Politely ask for updates on the application process

You MUST reply with a single JSON object:
{
  "subject": "...",
  "body": "..."
}

Do not include any other explanation or comments.
"""
)

# ✍️ 新增用于多轮修改的 Agent
email_edit_agent = AgentConfig(
    name="Email Editor Agent",
    llm_config_id="fast_gpt",
    description="Edit an existing email based on user instruction.",
    input_type="text",
    output_type="text",
    system_prompt="""
You are an email editing assistant.

You will receive:
- A draft email (subject and body)
- A user instruction (e.g. "make it more formal", "shorten the subject")

Revise the email accordingly. Output only the updated email in plain text.
Do NOT include any explanation or comments.
"""
)
