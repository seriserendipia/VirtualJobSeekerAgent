import os
from dotenv import load_dotenv
import asyncio
from aurite import Aurite, AgentConfig, ClientConfig, WorkflowConfig
from llm_and_agent_config import fast_llm, followup_email_agent  # ✅ 导入已有定义


# ========== 1. 初始化 aurite ==========
async def initialize_aurite():
    try:
        try:
            from google.colab import userdata  # type: ignore
            os.environ['OPENAI_API_KEY'] = userdata.get('OPENAI_API_KEY')
            os.environ["SMITHERY_API_KEY"] = userdata.get('SMITHERY_API_KEY')
        except ImportError:
            load_dotenv()

        aurite = Aurite()
        await aurite.initialize()
        print("✅ Aurite initialized successfully")
        return aurite

    except Exception as e:
        print(f"❌ Failed to initialize Aurite: {e}")
        raise


# ========== 2. 创建 Email Sender Agent 和 MCP Gmail Client ==========
def get_gmail_client_config():
    return ClientConfig(
        name="gmail_server",
        command="npx",
        args=[
            "-y",
            "@smithery/cli@latest",
            "run",
            "@gongrzhe/server-gmail-autoauth-mcp",
            "--key",
            os.getenv("SMITHERY_API_KEY", "your-default-key")
        ],
        capabilities=["tools"],
        timeout=20.0
    )

def get_email_sender_agent():
    agent = AgentConfig(
        name="Email Sender Agent",
        system_prompt="You are an email sending agent that can send emails using the Gmail service. Your task is to send emails based on the provided content."
    )
    agent.mcp_servers = ["gmail_server"]
    return agent


# ========== 3. 注册并运行工作流 ==========
async def register_and_run_workflow(resume_text, jd_text):
    aurite = await initialize_aurite()

    # 注册 LLM 和 Agent
    await aurite.register_llm_config(fast_llm)
    await aurite.register_client(get_gmail_client_config())
    await aurite.register_agent(followup_email_agent)
    await aurite.register_agent(get_email_sender_agent())

    # 注册 Workflow
    workflow = WorkflowConfig(
        name="Followup Email Workflow",
        description="Generate and send a follow-up email using resume and job description",
        steps=[
            "Followup Email Generator",
            "Email Sender Agent"
        ]
    )
    await aurite.register_workflow(workflow)

    print("✅ Workflow registered successfully!")

    # 拼接输入（传入 resume + jd）
    initial_input = f"Resume:\n{resume_text}\n\nJob Description:\n{jd_text}"

    # 执行 workflow
    result = await aurite.run_workflow(
        workflow_name="Followup Email Workflow",
        initial_input=initial_input
    )

    print("🎉 Workflow completed. Final message:\n")
    print(result.final_message)

    return result


# ========== 4. 测试入口 ==========
if __name__ == "__main__":
    resume = "John Doe, software engineer with 5 years experience in backend systems."
    jd = "We're hiring a backend Python developer with experience in REST APIs."

    asyncio.run(register_and_run_workflow(resume, jd))
