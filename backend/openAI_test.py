import os
import openai

# This code block safely loads your API key without exposing it.
# It checks if it's in a Colab environment and uses the secret manager.
# Otherwise, it looks for a local .env file.
# Then, it tests the key to ensure it is working before we move on.
try:
    from google.colab import userdata #type: ignore
    os.environ['OPENAI_API_KEY'] = userdata.get('OPENAI_API_KEY')
except ImportError:
    from dotenv import load_dotenv
    load_dotenv()
except Exception as e:
    print(f"Could not load API key. Please ensure it's set up correctly. Error: {e}")

print("🔑 API key found. Testing connection to OpenAI...")

try:
    # Initialize the OpenAI client
    client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])

    # Make a simple API call to the default chat model
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say 'Hello, ChatGPT!'",
            }
        ],
        model="gpt-3.5-turbo",
    )

    # Get the response content
    response_message = chat_completion.choices[0].message.content

    print("\n✅ Success! The API key is working.")
    print(f"🤖 ChatGPT's response: {response_message}")

except openai.AuthenticationError:
    print("\n❌ Authentication Error: The provided OpenAI API key is invalid or has expired.")
    print("Please check your key and try again.")
except openai.RateLimitError:
    print("\n❌ Rate Limit Error: You have exceeded your current quota.")
    print("Please check your plan and billing details on the OpenAI website.")
except openai.APIConnectionError as e:
    print("\n❌ Connection Error: Failed to connect to OpenAI's API.")
    print(f"   Please check your network connection. Details: {e}")
except Exception as e:
    print(f"\n❌ An unexpected error occurred: {e}")