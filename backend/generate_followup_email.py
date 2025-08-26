import os
import re
import json
from dotenv import load_dotenv
from aurite.config.config_models import LLMConfig, AgentConfig
from aurite_service import get_aurite


def parse_email_to_json(raw_content: str) -> dict:
    subject_match = re.search(r"Subject:\s*(.*)", raw_content)
    body_match = re.search(r"Body:\s*([\s\S]*)", raw_content)

    subject = subject_match.group(1).strip() if subject_match else ""
    body = body_match.group(1).strip() if body_match else ""

    return {"subject": subject, "body": body}



# Define LLM (configuration only)
fast_llm = LLMConfig(
    llm_id="fast_gpt",
    provider="openai",
    model_name="gpt-4o-mini",
    temperature=0.2,
    max_tokens=1024,
    default_system_prompt="You are a helpful assistant."
)




# Step 1: Generate an email using aurite by calling OpenAI LLM
async def generate_email(resume_content: str, jd_content: str) -> dict:
    load_dotenv()
    aurite = get_aurite()
    await aurite.initialize()  # Initialize Aurite first
    await aurite.register_llm_config(fast_llm)

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
    try:
        await aurite.register_agent(email_generator_agent)
        result = await aurite.run_agent(
            agent_name="Email Generate Agent",
            user_message="Generate an email based on the provided resume and job description."
        )
        raw_content = result.primary_text
        email_json = parse_email_to_json(raw_content)
        return {
            "status": "success",
            "data": {
                "email": email_json
            },
            "message": ""
        }
    except Exception as e:
        return {
            "status": "fail",
            "data": None,
            "message": str(e)
        }

    
    
# Step2: Add a new AgentConfig for email modification, or consider dynamic creation within modify_email.
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

async def modify_email(resume_content: str, jd_content: str, current_email_subject: str, current_email_body: str, user_feedback: str) -> dict:
    """
    Modifies existing email content based on user feedback.
    """
    load_dotenv()
    aurite = get_aurite()  # Returns the singleton Aurite instance.
    await aurite.initialize()  # Initialize Aurite first
    await aurite.register_llm_config(fast_llm)  # Ensure LLM is registered

    # Dynamically generate the system_prompt, including current email content and user feedback
    dynamic_system_prompt = f"""
        You are an experienced email revision assistant.
        This is a job application follow-up email. You can refer to the provided resume and job description below.

        Resume:
        {resume_content}

        Job Description:
        {jd_content}

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
    email_modifier_agent = AgentConfig(
        name="Email Modifier Agent",
        llm_config_id="fast_gpt",
        description="Modify emails based on user feedback via Aurite agent.",
        input_type="text",
        output_type="text",
        system_prompt=dynamic_system_prompt  # Use the dynamically generated prompt
    )
    try:
        await aurite.register_agent(email_modifier_agent)
        result = await aurite.run_agent(
            agent_name="Email Modifier Agent",
            user_message="Modify the email based on the provided feedback."
        )
        raw_content = result.primary_text
        email_json = parse_email_to_json(raw_content)
        return {
            "status": "success",
            "data": {
                "email": email_json
            },
            "message": ""
        }
    except Exception as e:
        return {
            "status": "fail",
            "data": None,
            "message": str(e)
        }



if __name__ == "__main__":

    def load_files(resume_path: str, jd_path: str) -> tuple:
        with open(resume_path, "r", encoding="utf-8") as f:
            resume_content = f.read()
        with open(jd_path, "r", encoding="utf-8") as f:
            jd_content = f.read()
        return resume_content, jd_content

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
    # The returned dict from generate_email is {"status": ..., "data": {"email": {"subject": ..., "body": ...}}, ...}
    # So we need to extract subject/body from initial_email_dict["data"]["email"]
    email_data_1 = initial_email_dict.get("data", {}).get("email", {})
    current_subject_1 = email_data_1.get("subject", "Generated Subject")
    current_body_1 = email_data_1.get("body", "Generated Body")

    try:
        revised_email_dict_1 = asyncio.run(modify_email(resume_content, jd_content, current_subject_1, current_body_1, user_feedback_1))
        print("\nRevised Email (Feedback 1):")
        print(json.dumps(revised_email_dict_1, indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"\nError during email modification (Feedback 1): {e}")

    # Simulate another round of modification
    user_feedback_2 = "Can you shorten the body to be more concise, focusing on key points only?"
    # The returned dict from modify_email is {"status": ..., "data": {"email": {"subject": ..., "body": ...}}, ...}
    email_data_2 = revised_email_dict_1.get("data", {}).get("email", {})
    current_subject_2 = email_data_2.get("subject", "Revised Subject 1")
    current_body_2 = email_data_2.get("body", "Revised Body 1")

    try:
        revised_email_dict_2 = asyncio.run(modify_email(resume_content, jd_content, current_subject_2, current_body_2, user_feedback_2))
        print("\nRevised Email (Feedback 2):")
        print(json.dumps(revised_email_dict_2, indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"\nError during email modification (Feedback 2): {e}")