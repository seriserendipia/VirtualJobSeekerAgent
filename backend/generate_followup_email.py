import os
import re
import json
from dotenv import load_dotenv
from aurite import LLMConfig, AgentConfig
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
# async def generate_email(resume_content: str, jd_content: str) -> dict:
#     load_dotenv()
#     aurite = get_aurite()
#     # Register the LLMConfig first
#     await aurite.register_llm_config(fast_llm)
#     email_generator_agent = AgentConfig(
#         name="Email Generate Agent",
#         llm_config_id="fast_gpt",
#         description="Send emails using Gmail MCP server via Aurite agent.",
#         input_type="text",
#         output_type="text",
#         system_prompt=f"""
#             You are an experienced job application assistant.
#             Below is my resume:

#             {resume_content}

#             Below is the job description:

#             {jd_content}

#             Please write a professional follow-up email to the recruiter,
#             expressing strong interest in this position,
#             highlighting why I am a good fit,
#             and politely asking for any updates about the application process.

#             Output the email with exactly two parts labeled as below:

#             Subject: <the email subject line>

#             Body:
#             <the full email body text>

#             Do not add any explanations or extra notes.
#         """
#     )
#     await aurite.register_agent(email_generator_agent)

#     result = await aurite.run_agent(agent_name="Email Generate Agent",
#                                     user_message="Generate an email based on the provided resume and job description.")

#     raw_content = result.primary_text
#     email_json = parse_email_to_json(raw_content)
#     return email_json


def extract_email_from_jd(jd_content: str) -> str | None:
    """
    Attempts to extract an email address from the job description content.
    This is a simple regex; might need more sophisticated parsing.
    """
    # Regex to find common email patterns (e.g., something@domain.com)
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    match = re.search(email_pattern, jd_content)
    if match:
        return match.group(0)
    return None

def extract_company_name_from_jd(jd_content: str) -> str | None:
    """
    Attempts to extract the company name from the job description content.
    This is a placeholder; real-world extraction can be complex.
    Could use NLP models or look for "Company Name:" patterns.
    For simplicity, let's assume the company name is often at the beginning or explicitly stated.
    """
    # Simple heuristic: look for "Company:" or assume first few words if no explicit tag.
    # A more robust solution might involve another LLM call or a dedicated NLP library.
    company_match = re.search(r"(?:Company|Employer)[:\s]*([A-Za-z0-9\s.,-]+)", jd_content, re.IGNORECASE)
    if company_match:
        return company_match.group(1).strip()
    
    # Fallback: simple heuristic for the first line or few words
    first_line = jd_content.split('\n')[0].strip()
    if len(first_line.split()) < 10 and "job description" not in first_line.lower():
        return first_line.split(' for ')[0].strip() # e.g., "Software Engineer at Google" -> "Software Engineer at Google"
    
    # If LLM is good at extracting, could use it
    # For now, return None if not easily found
    return None

def extract_job_title_from_jd(jd_content: str) -> str | None:
    """
    Attempts to extract the job title from the job description content.
    Similar to company name extraction, this is a placeholder.
    """
    # Simple heuristic: often the first bolded or largest text.
    # For now, let's assume it's part of the initial prompt or extract from first line.
    title_match = re.search(r"(?:Job Title|Role)[:\s]*([A-Za-z0-9\s.,-]+)", jd_content, re.IGNORECASE)
    if title_match:
        return title_match.group(1).strip()
    
    # Fallback: assume it's often in the first line if not company name
    first_line = jd_content.split('\n')[0].strip()
    if len(first_line.split()) < 10 and "job description" not in first_line.lower():
        return first_line.split(' at ')[0].strip() # e.g., "Software Engineer at Google" -> "Software Engineer"
    
    return None


# Step 1: Generate an email using aurite by calling OpenAI LLM
async def generate_email(resume_content: str, jd_content: str) -> dict:
    load_dotenv()
    aurite = get_aurite()
    await aurite.register_llm_config(fast_llm)

    # --- New Logic: Try to extract email from JD first ---
    potential_recipient_email = extract_email_from_jd(jd_content)
    
    if potential_recipient_email:
        # If email found in JD, proceed with email generation
        email_generator_agent = AgentConfig(
            name="Email Generate Agent",
            llm_config_id="fast_gpt",
            description="Generate professional follow-up emails.",
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
        email_json["recipient"] = potential_recipient_email # Add found recipient to the output
        return {"status": "email_generated", "email": email_json}
    else:
        # If no email found in JD, signal that web search is needed
        company_name = extract_company_name_from_jd(jd_content)
        job_title = extract_job_title_from_jd(jd_content) # Extract job title for more specific search
        
        return {
            "status": "needs_web_search",
            "company_name": company_name,
            "job_title": job_title,
            "message": "Recipient email not found in JD, web search is needed."
        }
    
    
# Step2: 新增一个 AgentConfig 用于邮件修改，或者考虑在 modify_email 内部动态创建
# Define a new AgentConfig for email modification, or consider dynamic creation within modify_email.
# For clarity, we define a new AgentConfig here.
email_modifier_agent_config = AgentConfig(
    name="Email Modifier Agent",
    llm_config_id="fast_gpt", # Reuse the same LLM configuration
    description="Modify emails based on user feedback via Aurite agent.",
    input_type="text",
    output_type="text",
    # The system_prompt will be dynamically generated within the function
)

async def modify_email(current_email_subject: str, current_email_body: str, user_feedback: str) -> dict:
    """
    Modifies existing email content based on user feedback.
    """
    load_dotenv()
    aurite = get_aurite() # Returns the singleton Aurite instance.
    await aurite.register_llm_config(fast_llm) # Ensure LLM is registered

    # Dynamically generate the system_prompt, including current email content and user feedback
    dynamic_system_prompt = f"""
        You are an experienced email revision assistant.
        Here is the current email content you need to revise:

        Subject: {current_email_subject}

        Body:
        {current_email_body}

        The user wants to modify this email. Here is the user's feedback:
        {user_feedback}

        Please revise the email based on the user's feedback.
        Output the revised email with exactly two parts labeled as below:

        Subject: <the revised email subject line>

        Body:
        <the full revised email body text>

        Do not add any explanations or extra notes.
    """

    # Register or update the modification Agent
    # Note: If an AgentConfig with the same name is already registered, re-registering it updates it.
    # To ensure the latest prompt is used for each modification, we re-register or update here.
    email_modifier_agent = AgentConfig(
        name="Email Modifier Agent",
        llm_config_id="fast_gpt",
        description="Modify emails based on user feedback via Aurite agent.",
        input_type="text",
        output_type="text",
        system_prompt=dynamic_system_prompt # Use the dynamically generated prompt
    )
    await aurite.register_agent(email_modifier_agent)

    result = await aurite.run_agent(agent_name="Email Modifier Agent",
                                    user_message="Modify the email based on the provided feedback.")

    raw_content = result.primary_text
    email_json = parse_email_to_json(raw_content)
    return email_json



if __name__ == "__main__":
    # --- Test generate_email ---
    print("--- Testing initial email generation ---")
    resume_path = os.path.join(os.path.dirname(__file__), "..", "samples", "user_resume_sample.txt")
    jd_path = os.path.join(os.path.dirname(__file__), "..", "samples", "jobdescription_sample.txt")

    resume_content, jd_content = load_files(resume_path, jd_path)

    # Use asyncio.run to execute the async function
    import asyncio
    initial_email_dict = asyncio.run(generate_email(resume_content, jd_content))

    print("\nGenerated Initial Email:")
    print(json.dumps(initial_email_dict, indent=4, ensure_ascii=False))

    # --- Test modify_email ---
    print("\n--- Testing email modification ---")
    # Simulate a user feedback
    user_feedback_1 = "Please make the tone more enthusiastic and add a specific mention of my project X that is relevant to the job."
    current_subject_1 = initial_email_dict.get("subject", "Generated Subject")
    current_body_1 = initial_email_dict.get("body", "Generated Body")

    try:
        revised_email_dict_1 = asyncio.run(modify_email(current_subject_1, current_body_1, user_feedback_1))
        print("\nRevised Email (Feedback 1):")
        print(json.dumps(revised_email_dict_1, indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"\nError during email modification (Feedback 1): {e}")

    # Simulate another round of modification
    user_feedback_2 = "Can you shorten the body to be more concise, focusing on key points only?"
    current_subject_2 = revised_email_dict_1.get("subject", "Revised Subject 1")
    current_body_2 = revised_email_dict_1.get("body", "Revised Body 1")

    try:
        revised_email_dict_2 = asyncio.run(modify_email(current_subject_2, current_body_2, user_feedback_2))
        print("\nRevised Email (Feedback 2):")
        print(json.dumps(revised_email_dict_2, indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"\nError during email modification (Feedback 2): {e}")