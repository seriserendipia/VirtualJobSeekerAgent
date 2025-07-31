import os
import json
import re
import asyncio
import logging

from dotenv import load_dotenv
from aurite import Aurite # From aurite_service, but also directly from aurite for types
from aurite.config.config_models import LLMConfig, AgentConfig, ClientConfig # Correct import for ClientConfig

# Assuming aurite_service.py exists and provides get_aurite()
from aurite_service import get_aurite

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Aurite Initialization and Agent/Client Definitions ---
# This function will handle setting up Aurite's LLM and MCP Client.
# It's separated so it can be called once at application startup (e.g., in server.py)
# or defensively before first agent run.
async def setup_aurite_for_recruiter_search():
    """
    Sets up the Aurite instance with LLM and the MCP Client for Exa Web Search.
    This ensures agents and clients are registered with the Aurite singleton.
    """
    load_dotenv() # Ensure .env variables are loaded
    aurite = get_aurite()
    await aurite.initialize() # Initialize the Aurite instance

    # --- LLM Configuration for Recruiter Search Agent ---
    # Using gpt-4o-mini as per previous discussions for cost-effectiveness
    # Adjust temperature for factual search (lower usually better)
    recruiter_llm_config = LLMConfig(
        llm_id="recruiter_search_gpt",
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.1, # Lower temperature for more factual search results processing
        max_tokens=2048, # Sufficient tokens for processing search snippets
        default_system_prompt="You are a specialized web search assistant for finding recruiter contact information."
    )
    await aurite.register_llm_config(recruiter_llm_config)

    # --- MCP Client Configuration for Smithery Exa ---
    # This ClientConfig defines how Aurite connects to the Exa MCP server.
    # The 'name' here ("exa_recruiter_search_mcp") is important as it links the AgentConfig to this server.
    # IMPORTANT: Ensure SMITHERY_API_KEY and potentially SMITHERY_PROFILE_ID are in your .env
    #            If SMITHERY_PROFILE_ID is not required by Exa, remove it from the http_endpoint.
    exa_recruiter_mcp_client_config = ClientConfig(
        name="exa_recruiter_search_mcp", # A clear, unique name for this MCP server instance
        # It's good practice to make the endpoint configurable via environment variables
        http_endpoint=os.getenv("EXA_MCP_ENDPOINT", "https://server.smithery.ai/exa/mcp?api_key={SMITHERY_API_KEY}&profile={SMITHERY_PROFILE_ID}"),
        capabilities=["tools"], # Indicates this MCP server exposes tools (like 'web_search_exa')
    )
    await aurite.register_client(exa_recruiter_mcp_client_config)

    # --- Recruiter Email Search Agent Configuration ---
    # This Agent will use the 'exa_recruiter_search_mcp' to perform web searches.
    # The 'system_prompt' explicitly guides the LLM to use the 'web_search_exa' tool (provided by the MCP server).
    recruiter_search_agent_config = AgentConfig(
        name="Recruiter Email Search Agent",
        llm_config_id="recruiter_search_gpt",
        description="Searches the web to find recruiter email addresses or official contact pages for a company and job title.",
        input_type="text",
        output_type="text",
        mcp_servers=[exa_recruiter_mcp_client_config.name],
        include_history=False,
        system_prompt=f"""You are a specialized web search assistant whose primary goal is to find recruiter email addresses or official contact pages for a given company and job role.
        You have access to the 'web_search_exa' tool to perform web searches.

        IMPORTANT: You MUST call the 'web_search_exa' tool to get information.
        Based on the user's input (which specifies company and job title), formulate precise search queries using the 'web_search_exa' tool.
        
        Prioritize direct email addresses and official company career pages.
        If a direct email is not found, **please provide the most relevant LinkedIn personal profile URLs for recruiters, as well as other official contact page URLs.**
        **Please avoid providing social media posts that are not personal profiles of recruiters (e.g., generic LinkedIn posts, Reddit threads, Quora answers) or third-party email aggregators (unless they provide a direct company email).**

        When using 'web_search_exa', ensure your query is concise and effective, e.g., "Google recruiter email software engineer", "OpenAI careers contact".

        Format your final output strictly as follows:

        Email Found: <email_address> (or "None")
        Relevant URLs:
        - [Title of URL 1](URL 1)
        - [Title of URL 2](URL 2)
        ...
        
        If no relevant information is found after your searches, output:
        Email Found: None
        Relevant URLs:
        - None
        """
    )
    await aurite.register_agent(recruiter_search_agent_config)


# --- Main function that server.py will call ---
async def find_recruiter_email_via_web_search(company_name: str, job_title: str = "") -> dict:
    """
    Finds a recruiter's email or contact page by running the Recruiter Email Search Agent.
    This function handles the execution of the agent and parsing its output.
    Args:
        company_name: The name of the company to search for.
        job_title: Optional job title to refine the search.
    Returns:
        A dictionary containing found email/contact URLs, or a message indicating failure.
    """
    aurite = get_aurite()
    # It's ideal to call setup_aurite_for_recruiter_search() once at application startup
    # (e.g., in server.py's __main__ block or an init function).
    # Calling it here ensures it's set up, but might re-register configs on every call if not careful.
    # For now, this is a safe defensive call.
    await setup_aurite_for_recruiter_search() 

    # Prepare the user message for the LLM Agent
    user_message = f"Find the recruiter email or contact page for {company_name} for a {job_title} position." if job_title else f"Find the recruiter email or contact page for {company_name}."
    
    logger.info(f"Running 'Recruiter Email Search Agent' with query: '{user_message}'")
    agent_result = await aurite.run_agent(
        agent_name="Recruiter Email Search Agent", # Use the agent name defined above
        user_message=user_message
    )

      # Parse the output from the agent (MODIFY THIS PART)
    raw_content = agent_result.primary_text if agent_result and hasattr(agent_result, 'primary_text') else ""
    logger.info(f"Raw agent response:\n{raw_content}")

    email_match = re.search(r"Email Found:\s*(.*)", raw_content)
    # url_match_pattern = r"- \[([^\]]+)\]\(([^)]+)\)" # Matches [Title](URL)
    # 稍微复杂一点的正则，处理URL前面可能有None的情况，以及防止匹配过多的行
    urls_section_raw = ""
    urls_section_match = re.search(r"Relevant URLs:\s*\n([\s\S]*)", raw_content) # 确保匹配到“Relevant URLs:”后的内容
    if urls_section_match:
        urls_section_raw = urls_section_match.group(1).strip()

    # 正则表达式来匹配 Markdown 链接格式: - [Title](URL)
    # 捕获组 1 是 Title，捕获组 2 是 URL
    markdown_link_pattern = r"-\s*\[([^\]]+)\]\(([^)]+)\)"

    found_email = email_match.group(1).strip() if email_match else "None"
    relevant_urls = []

    # 遍历urls_section_raw中的每一行，查找匹配的Markdown链接
    for line in urls_section_raw.split('\n'):
        line = line.strip()
        if line.lower() == "- none" or not line: # 如果只有 "- None" 或空行，则跳过
            continue

        link_match = re.search(markdown_link_pattern, line)
        if link_match:
            title = link_match.group(1).strip()
            url = link_match.group(2).strip()
            relevant_urls.append({"url": url, "title": title})
        # else:
            # 如果不符合 Markdown 链接格式，但你仍然想处理类似 "http://example.com - Title" 的旧格式
            # 可以保留旧的解析逻辑作为 fallback，但通常 LLM 会遵循系统提示的格式
            # if line.startswith('-'):
            #     parts = line[1:].strip().split(' - ', 1)
            #     if len(parts) == 2:
            #         relevant_urls.append({"url": parts[0], "title": parts[1]})
            #     elif len(parts) == 1:
            #         relevant_urls.append({"url": parts[0], "title": ""})


    return {
        "found_email": found_email if found_email.lower() != "none" else None,
        "relevant_urls": relevant_urls,
        "raw_agent_response": raw_content # For debugging
    }

# --- Test the function directly when this script is run ---
if __name__ == "__main__":
    import asyncio # Ensure asyncio is imported for running async main

    async def test_recruiter_search_agent():
        print("--- Testing Recruiter Email Search Agent (MCP Server Style) ---")
        
        # Test Case 1: Search for a company with a job title
        company = "Google"
        job = "Software Engineer"
        logger.info(f"\nSearching for recruiter email for {company} - {job}...")
        results = await find_recruiter_email_via_web_search(company, job)
        print(json.dumps(results, indent=4, ensure_ascii=False))

        # Test Case 2: Search for a company without a job title
        company_2 = "OpenAI"
        logger.info(f"\nSearching for recruiter email for {company_2}...")
        results_2 = await find_recruiter_email_via_web_search(company_2)
        print(json.dumps(results_2, indent=4, ensure_ascii=False))
        
        # Test Case 3: A more specific search
        company_3 = "Microsoft"
        logger.info(f"\nSearching for recruiter email for {company_3}...")
        results_3 = await find_recruiter_email_via_web_search(company_3, "Principal AI Researcher")
        print(json.dumps(results_3, indent=4, ensure_ascii=False))

    asyncio.run(test_recruiter_search_agent())